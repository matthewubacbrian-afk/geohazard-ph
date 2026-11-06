"""Deterministic, source-group-separated dataset splits."""

from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

from ml.scene_review.manifest import SceneImageRecord

SPLIT_NAMES = ("train", "validation", "test")
DEFAULT_RATIOS = (0.70, 0.15, 0.15)


@dataclass(frozen=True)
class DatasetSplits:
    train_ids: tuple[str, ...]
    validation_ids: tuple[str, ...]
    test_ids: tuple[str, ...]


def _validate_ratios(ratios: tuple[float, float, float]) -> tuple[float, float, float]:
    if not isinstance(ratios, tuple) or len(ratios) != 3:
        raise ValueError("ratios must contain exactly three values")
    if any(
        not isinstance(ratio, (int, float))
        or isinstance(ratio, bool)
        or not math.isfinite(ratio)
        or ratio <= 0
        for ratio in ratios
    ):
        raise ValueError("ratios must be finite positive values")
    normalized = tuple(float(ratio) for ratio in ratios)
    if not math.isclose(sum(normalized), 1.0, rel_tol=0.0, abs_tol=1e-9):
        raise ValueError("ratios must sum to 1")
    return normalized


def make_grouped_splits(
    records: Sequence[SceneImageRecord],
    *,
    seed: int = 42,
    ratios: tuple[float, float, float] = DEFAULT_RATIOS,
) -> DatasetSplits:
    """Shuffle source groups with a fixed seed and greedily balance image counts."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")
    ratios = _validate_ratios(ratios)
    if not records:
        raise ValueError("records must not be empty")

    image_ids = [record.image_id for record in records]
    if any(not isinstance(image_id, str) or not image_id for image_id in image_ids):
        raise ValueError("every record must have a nonempty image_id")
    if len(image_ids) != len(set(image_ids)):
        raise ValueError("record image IDs must be unique")

    groups: dict[str, list[str]] = defaultdict(list)
    for record in records:
        if not isinstance(record.group_id, str) or not record.group_id:
            raise ValueError("every record must have a nonempty group_id")
        groups[record.group_id].append(record.image_id)
    if len(groups) < len(SPLIT_NAMES):
        raise ValueError("at least three source groups are required for nonempty splits")

    group_ids = sorted(groups)
    random.Random(seed).shuffle(group_ids)
    targets = [len(records) * ratio for ratio in ratios]
    assigned_counts = [0, 0, 0]
    assigned: list[list[str]] = [[], [], []]

    for position, group_id in enumerate(group_ids):
        remaining_groups = len(group_ids) - position
        empty_splits = [
            index for index, image_ids_for_split in enumerate(assigned) if not image_ids_for_split
        ]
        candidates = empty_splits if remaining_groups <= len(empty_splits) else list(range(3))
        split_index = max(
            candidates,
            key=lambda index: (targets[index] - assigned_counts[index], -index),
        )
        assigned[split_index].extend(groups[group_id])
        assigned_counts[split_index] += len(groups[group_id])

    splits = DatasetSplits(
        train_ids=tuple(sorted(assigned[0])),
        validation_ids=tuple(sorted(assigned[1])),
        test_ids=tuple(sorted(assigned[2])),
    )
    validate_splits(records, splits)
    return splits


def validate_splits(records: Sequence[SceneImageRecord], splits: DatasetSplits) -> None:
    """Validate exact image coverage and prevent group or image-hash leakage."""
    if not isinstance(splits, DatasetSplits):
        raise TypeError("splits must be a DatasetSplits instance")
    split_ids = (splits.train_ids, splits.validation_ids, splits.test_ids)
    if any(not isinstance(ids, tuple) for ids in split_ids):
        raise ValueError("split image IDs must be tuples")
    if any(not ids for ids in split_ids):
        raise ValueError("all three dataset splits must be nonempty")

    record_ids = [record.image_id for record in records]
    if any(not isinstance(image_id, str) or not image_id for image_id in record_ids):
        raise ValueError("every record must have a nonempty image_id")
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("record image IDs must be unique")
    assigned_ids = [image_id for ids in split_ids for image_id in ids]
    if len(assigned_ids) != len(set(assigned_ids)) or set(assigned_ids) != set(record_ids):
        raise ValueError("split IDs must contain every record image ID exactly once")

    split_by_image_id = {
        image_id: split_index for split_index, ids in enumerate(split_ids) for image_id in ids
    }
    groups: dict[str, set[int]] = defaultdict(set)
    hashes: dict[str, set[int]] = defaultdict(set)
    for record in records:
        if not isinstance(record.group_id, str) or not record.group_id:
            raise ValueError("every record must have a nonempty group_id")
        if not isinstance(record.image_sha256, str) or not record.image_sha256:
            raise ValueError("every record must have a nonempty image_sha256")
        split_index = split_by_image_id[record.image_id]
        groups[record.group_id].add(split_index)
        hashes[record.image_sha256.lower()].add(split_index)
    if any(len(split_indexes) > 1 for split_indexes in groups.values()):
        raise ValueError("source group leakage across splits")
    if any(len(split_indexes) > 1 for split_indexes in hashes.values()):
        raise ValueError("image hash leakage across splits")


def splits_to_json(splits: DatasetSplits, *, seed: int) -> str:
    """Serialize sorted split IDs and the seed as stable JSON."""
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise TypeError("seed must be an integer")
    if not isinstance(splits, DatasetSplits):
        raise TypeError("splits must be a DatasetSplits instance")
    validate_ids = (splits.train_ids, splits.validation_ids, splits.test_ids)
    all_ids = [image_id for ids in validate_ids for image_id in ids]
    if any(not ids for ids in validate_ids):
        raise ValueError("all three dataset splits must be nonempty")
    if any(not isinstance(image_id, str) or not image_id for image_id in all_ids):
        raise ValueError("split IDs must be nonempty strings")
    if len(all_ids) != len(set(all_ids)):
        raise ValueError("split IDs must be unique")
    if any(tuple(sorted(ids)) != ids for ids in validate_ids):
        raise ValueError("split IDs must be sorted before serialization")
    return json.dumps(
        {
            "schema_version": 1,
            "seed": seed,
            "train_ids": list(splits.train_ids),
            "validation_ids": list(splits.validation_ids),
            "test_ids": list(splits.test_ids),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
