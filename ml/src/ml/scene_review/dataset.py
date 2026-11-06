"""Validated image/mask loading and DETR segmentation target preparation."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image
from scipy import ndimage

from ml.scene_review.labels import (
    IGNORE_ID,
    mask_for_supported_labels,
    training_id_map,
)
from ml.scene_review.manifest import (
    SceneDatasetManifest,
    validate_dataset,
)


class DetrImageProcessor(Protocol):
    """Callable image processor interface used by Transformers DETR models."""

    def __call__(self, *, images: Image.Image, return_tensors: str) -> Mapping[str, object]: ...


class SceneReviewDataset:
    """Load validated scene images and per-component DETR targets.

    Component connectivity is 8-neighbor. All target masks retain original image
    resolution; the DETR segmentation loss resizes prediction masks to target size.
    Samples with any run-specific ignore pixels remain available for evaluation,
    but are marked ineligible for training and validation loss.
    """

    def __init__(
        self,
        manifest: SceneDatasetManifest,
        data_root: Path,
        record_ids: Sequence[str],
        image_processor: DetrImageProcessor,
    ) -> None:
        validate_dataset(manifest, data_root)
        records_by_id = {record.image_id: record for record in manifest.records}
        if not isinstance(record_ids, Sequence) or isinstance(record_ids, (str, bytes)):
            raise TypeError("record_ids must be a sequence of image IDs")
        if any(not isinstance(image_id, str) or not image_id for image_id in record_ids):
            raise ValueError("record IDs must be nonempty strings")
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("record IDs must be unique")
        unknown_ids = set(record_ids).difference(records_by_id)
        if unknown_ids:
            raise ValueError("record IDs must all exist in the validated manifest")
        if not callable(image_processor):
            raise TypeError("image_processor must be callable")

        self._manifest = manifest
        self._data_root = data_root.resolve()
        self._records = tuple(records_by_id[image_id] for image_id in record_ids)
        self._image_processor = image_processor
        self._supported_labels = set(manifest.supported_labels)
        self._training_ids = training_id_map(manifest.supported_labels)

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, index: int) -> dict[str, object]:
        record = self._records[index]
        image_path = self._data_root / Path(record.image_path)
        mask_path = self._data_root / Path(record.mask_path)
        with Image.open(image_path) as source_image:
            image = source_image.convert("RGB")
        with Image.open(mask_path) as source_mask:
            canonical_mask = np.asarray(source_mask).copy()

        run_mask, unsupported_pixel_counts = mask_for_supported_labels(
            canonical_mask, self._supported_labels
        )
        ignore_mask = run_mask == IGNORE_ID
        evaluation_mask = ~ignore_mask
        processed = self._image_processor(images=image, return_tensors="pt")
        if not isinstance(processed, Mapping) or "pixel_values" not in processed:
            raise ValueError("image_processor must return pixel_values")
        pixel_values = _unbatch(processed["pixel_values"])
        pixel_mask = _unbatch(processed["pixel_mask"]) if "pixel_mask" in processed else None
        targets = _component_targets(run_mask, self._training_ids, pixel_values)
        sample: dict[str, object] = {
            "pixel_values": pixel_values,
            "labels": targets,
            "run_mask": run_mask,
            "run_ignore_mask": ignore_mask,
            "evaluation_mask": evaluation_mask,
            "loss_eligible": not bool(np.any(ignore_mask)),
            "unsupported_pixel_counts": unsupported_pixel_counts,
        }
        if pixel_mask is not None:
            sample["pixel_mask"] = pixel_mask
        return sample


def _unbatch(value: object) -> object:
    shape = getattr(value, "shape", None)
    if shape is None or len(shape) == 0:
        raise ValueError("image_processor outputs must have a batch dimension")
    if shape[0] != 1:
        raise ValueError("image_processor must process exactly one image per dataset item")
    return value[0]


def _component_targets(
    run_mask: np.ndarray,
    training_ids: Mapping[int, int],
    processed_pixel_values: object,
) -> dict[str, object]:
    height, width = run_mask.shape
    structure = np.ones((3, 3), dtype=np.uint8)
    instance_masks: list[np.ndarray] = []
    class_labels: list[int] = []
    boxes: list[list[float]] = []
    for canonical_id in sorted(training_ids):
        components, component_count = ndimage.label(run_mask == canonical_id, structure=structure)
        for component_id in range(1, component_count + 1):
            instance_mask = components == component_id
            y_values, x_values = np.nonzero(instance_mask)
            x_min, x_max = int(x_values.min()), int(x_values.max()) + 1
            y_min, y_max = int(y_values.min()), int(y_values.max()) + 1
            instance_masks.append(instance_mask)
            class_labels.append(training_ids[canonical_id])
            box_width, box_height = x_max - x_min, y_max - y_min
            boxes.append(
                [
                    (x_min + x_max) / (2 * width),
                    (y_min + y_max) / (2 * height),
                    box_width / width,
                    box_height / height,
                ]
            )

    masks_array = (
        np.stack(instance_masks).astype(np.float32, copy=False)
        if instance_masks
        else np.zeros((0, height, width), dtype=np.float32)
    )
    classes_array = np.asarray(class_labels, dtype=np.int64)
    boxes_array = np.asarray(boxes, dtype=np.float32).reshape((-1, 4))
    if type(processed_pixel_values).__module__.split(".", maxsplit=1)[0] == "torch":
        import torch

        return {
            "class_labels": torch.as_tensor(classes_array, dtype=torch.long),
            "masks": torch.as_tensor(masks_array, dtype=torch.float32),
            "boxes": torch.as_tensor(boxes_array, dtype=torch.float32),
        }
    return {
        "class_labels": classes_array,
        "masks": masks_array,
        "boxes": boxes_array,
    }
