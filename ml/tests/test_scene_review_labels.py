import numpy as np
import pytest

from ml.scene_review.labels import (
    BACKGROUND_ID,
    IGNORE_ID,
    LABEL_IDS,
    labels_for_ids,
    mask_for_supported_labels,
    training_id_map,
    validate_mask,
)


def test_label_ids_are_canonical_and_background_is_not_a_target():
    assert LABEL_IDS == {
        "open_ground": 0,
        "obstacle": 1,
        "glass_facade": 2,
        "overhead_lines": 3,
        "visible_building_damage": 4,
    }
    assert BACKGROUND_ID == 5
    assert IGNORE_ID == 255


def test_validate_mask_accepts_canonical_ids_even_if_run_supports_subset():
    mask = np.array([[0, 1, 2, 3, 4, BACKGROUND_ID, IGNORE_ID]], dtype=np.uint8)

    validate_mask(mask, {"open_ground"})


def test_mask_for_supported_labels_maps_unsupported_targets_to_ignore_and_counts():
    mask = np.array([[0, 1, 1, 2, 4, BACKGROUND_ID, IGNORE_ID]], dtype=np.uint8)

    run_mask, counts = mask_for_supported_labels(mask, {"open_ground", "glass_facade"})

    assert run_mask.tolist() == [[0, IGNORE_ID, IGNORE_ID, 2, IGNORE_ID, BACKGROUND_ID, IGNORE_ID]]
    assert counts == {"obstacle": 2, "visible_building_damage": 1}
    assert mask.tolist() == [[0, 1, 1, 2, 4, BACKGROUND_ID, IGNORE_ID]]


def test_mask_for_supported_labels_returns_empty_counts_when_all_targets_supported():
    mask = np.array([[0, 4, BACKGROUND_ID]], dtype=np.uint8)

    run_mask, counts = mask_for_supported_labels(mask, set(LABEL_IDS))

    assert np.array_equal(run_mask, mask)
    assert counts == {}


@pytest.mark.parametrize(
    "mask",
    [
        np.array([[0, 6]], dtype=np.uint8),
        np.array([[0, 254]], dtype=np.uint8),
    ],
)
def test_validate_mask_rejects_unknown_ids(mask):
    with pytest.raises(ValueError, match="unknown mask IDs"):
        validate_mask(mask, set(LABEL_IDS))


def test_validate_mask_rejects_non_integer_dtype():
    with pytest.raises(ValueError, match="integer"):
        validate_mask(np.array([[0.0, 1.0]]), set(LABEL_IDS))


def test_validate_mask_rejects_wrong_dimensions():
    with pytest.raises(ValueError, match="two-dimensional"):
        validate_mask(np.array([0, 1], dtype=np.uint8), set(LABEL_IDS))


def test_validate_mask_rejects_all_ignore_mask():
    with pytest.raises(ValueError, match="only ignore"):
        validate_mask(np.full((2, 2), IGNORE_ID, dtype=np.uint8), set(LABEL_IDS))


def test_background_only_mask_is_valid_and_has_no_detr_target_labels():
    mask = np.full((2, 3), BACKGROUND_ID, dtype=np.uint8)

    validate_mask(mask, set())

    assert labels_for_ids(set()) == set()
    assert training_id_map([]) == {}


def test_labels_for_ids_maps_only_canonical_target_ids():
    assert labels_for_ids({0, 2, 4}) == {
        "open_ground",
        "glass_facade",
        "visible_building_damage",
    }
    with pytest.raises(ValueError, match="unknown target IDs"):
        labels_for_ids({5})


def test_training_id_map_is_contiguous_in_canonical_order():
    assert training_id_map(["visible_building_damage", "open_ground", "glass_facade"]) == {
        0: 0,
        2: 1,
        4: 2,
    }


def test_helpers_reject_unknown_label_names():
    with pytest.raises(ValueError, match="unknown labels"):
        validate_mask(np.array([[0]], dtype=np.uint8), {"not_a_label"})
    with pytest.raises(ValueError, match="unknown labels"):
        mask_for_supported_labels(np.array([[0]], dtype=np.uint8), {"not_a_label"})
    with pytest.raises(ValueError, match="unknown labels"):
        training_id_map(["not_a_label"])
