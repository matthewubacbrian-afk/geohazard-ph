"""Canonical Scene Review mask labels and run-specific label mappings."""

from collections.abc import Sequence

import numpy as np

LABEL_IDS: dict[str, int] = {
    "open_ground": 0,
    "obstacle": 1,
    "glass_facade": 2,
    "overhead_lines": 3,
    "visible_building_damage": 4,
}
BACKGROUND_ID = 5
IGNORE_ID = 255

_ID_TO_LABEL = {mask_id: label for label, mask_id in LABEL_IDS.items()}
_VALID_MASK_IDS = frozenset((*_ID_TO_LABEL, BACKGROUND_ID, IGNORE_ID))


def _validated_supported_labels(supported_labels: set[str] | Sequence[str]) -> set[str]:
    labels = set(supported_labels)
    unknown_labels = labels.difference(LABEL_IDS)
    if unknown_labels:
        raise ValueError(f"unknown labels: {sorted(unknown_labels)}")
    return labels


def validate_mask(mask: np.ndarray, supported_labels: set[str]) -> None:
    """Validate a canonical indexed mask; supported labels do not restrict its IDs."""
    _validated_supported_labels(supported_labels)
    if not isinstance(mask, np.ndarray) or mask.ndim != 2:
        raise ValueError("mask must be a two-dimensional numpy array")
    if not np.issubdtype(mask.dtype, np.integer):
        raise ValueError("mask dtype must be integer")
    if mask.size == 0:
        raise ValueError("mask must contain at least one pixel")

    present_ids = {int(mask_id) for mask_id in np.unique(mask)}
    unknown_ids = present_ids.difference(_VALID_MASK_IDS)
    if unknown_ids:
        raise ValueError(f"unknown mask IDs: {sorted(unknown_ids)}")
    if present_ids == {IGNORE_ID}:
        raise ValueError("mask cannot contain only ignore pixels")


def mask_for_supported_labels(
    mask: np.ndarray, supported_labels: set[str],
) -> tuple[np.ndarray, dict[str, int]]:
    """Copy a canonical mask and ignore/count target pixels unsupported by this run."""
    labels = _validated_supported_labels(supported_labels)
    validate_mask(mask, labels)

    run_mask = mask.copy()
    remapped_counts: dict[str, int] = {}
    for label, mask_id in LABEL_IDS.items():
        if label not in labels:
            count = int(np.count_nonzero(mask == mask_id))
            if count:
                run_mask[mask == mask_id] = IGNORE_ID
                remapped_counts[label] = count
    return run_mask, remapped_counts


def labels_for_ids(class_ids: set[int]) -> set[str]:
    """Return canonical target labels for model class IDs, rejecting non-target IDs."""
    unknown_ids = set(class_ids).difference(_ID_TO_LABEL)
    if unknown_ids:
        raise ValueError(f"unknown target IDs: {sorted(unknown_ids)}")
    return {_ID_TO_LABEL[class_id] for class_id in class_ids}


def training_id_map(supported_labels: Sequence[str]) -> dict[int, int]:
    """Map selected canonical target IDs to contiguous model IDs in canonical order."""
    labels = _validated_supported_labels(supported_labels)
    if len(labels) != len(supported_labels):
        raise ValueError("supported labels must not contain duplicates")
    return {
        LABEL_IDS[label]: training_id
        for training_id, label in enumerate(label for label in LABEL_IDS if label in labels)
    }
