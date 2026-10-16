import json
from dataclasses import fields

import pytest

from ml.scene_review.manifest import SceneImageRecord
from ml.scene_review.splits import (
    DatasetSplits,
    make_grouped_splits,
    splits_to_json,
    validate_splits,
)


def scene_record(image_id, group_id, image_sha256=None):
    values = {field.name: "" for field in fields(SceneImageRecord)}
    values.update(
        image_id=image_id,
        group_id=group_id,
        image_sha256=image_sha256 or f"hash-{image_id}",
        image_permitted_uses=(),
        image_retention_limits=None,
    )
    return SceneImageRecord(**values)


def records_for_groups(group_sizes):
    return [
        scene_record(f"image-{group_index}-{item_index}", f"group-{group_index}")
        for group_index, size in enumerate(group_sizes)
        for item_index in range(size)
    ]


def test_grouped_splits_are_deterministic_sorted_and_serialize_seed():
    records = records_for_groups([4, 3, 2, 2, 1, 1])

    first = make_grouped_splits(records, seed=37)
    second = make_grouped_splits(records, seed=37)

    assert first == second
    assert first.train_ids == tuple(sorted(first.train_ids))
    assert first.validation_ids == tuple(sorted(first.validation_ids))
    assert first.test_ids == tuple(sorted(first.test_ids))
    payload = json.loads(splits_to_json(first, seed=37))
    assert payload["seed"] == 37
    assert payload["train_ids"] == list(first.train_ids)


def test_grouped_splits_do_not_depend_on_manifest_record_order():
    records = records_for_groups([4, 3, 2, 2, 1, 1])

    original_order = make_grouped_splits(records, seed=37)
    reversed_order = make_grouped_splits(list(reversed(records)), seed=37)

    assert original_order == reversed_order


def test_grouped_splits_keep_every_source_group_whole():
    records = records_for_groups([3, 2, 2, 1, 1, 1])
    splits = make_grouped_splits(records, seed=5)

    validate_splits(records, splits)
    split_for_image = {
        image_id: split_name
        for split_name, image_ids in (
            ("train", splits.train_ids),
            ("validation", splits.validation_ids),
            ("test", splits.test_ids),
        )
        for image_id in image_ids
    }
    for record in records:
        assert (
            split_for_image[record.image_id]
            == split_for_image[
                next(item.image_id for item in records if item.group_id == record.group_id)
            ]
        )


def test_validate_splits_rejects_duplicate_image_hash_across_splits():
    records = [
        scene_record("one", "group-one", "same-content"),
        scene_record("two", "group-two", "same-content"),
        scene_record("three", "group-three", "other-content"),
    ]
    splits = DatasetSplits(("one",), ("two",), ("three",))

    with pytest.raises(ValueError, match="hash"):
        validate_splits(records, splits)


def test_validate_splits_rejects_group_leakage_across_splits():
    records = [
        scene_record("one", "same-group", "hash-one"),
        scene_record("two", "same-group", "hash-two"),
        scene_record("three", "other-group", "hash-three"),
    ]
    splits = DatasetSplits(("one",), ("two",), ("three",))

    with pytest.raises(ValueError, match="group leakage"):
        validate_splits(records, splits)


@pytest.mark.parametrize(
    "ratios",
    [
        (0.7, 0.2),
        (0.7, 0.2, 0.2),
        (0.7, 0.3, 0.0),
        (0.7, -0.1, 0.4),
    ],
)
def test_grouped_splits_reject_invalid_ratios(ratios):
    with pytest.raises(ValueError, match="ratios"):
        make_grouped_splits(records_for_groups([1, 1, 1]), ratios=ratios)


def test_validate_splits_requires_exact_one_time_ids_and_nonempty_splits():
    records = records_for_groups([1, 1, 1])
    duplicate = DatasetSplits(("image-0-0",), ("image-1-0",), ("image-1-0",))
    with pytest.raises(ValueError, match="exactly once"):
        validate_splits(records, duplicate)

    missing = DatasetSplits(("image-0-0",), ("image-1-0",), ("unknown",))
    with pytest.raises(ValueError, match="exactly once"):
        validate_splits(records, missing)

    empty = DatasetSplits(("image-0-0", "image-1-0"), ("image-2-0",), ())
    with pytest.raises(ValueError, match="nonempty"):
        validate_splits(records, empty)


def test_grouped_splits_reject_fewer_than_three_source_groups():
    with pytest.raises(ValueError, match="three source groups"):
        make_grouped_splits(records_for_groups([3, 1]))
