import hashlib
import json

import numpy as np
import pytest
from PIL import Image

from ml.scene_review.dataset import SceneReviewDataset
from ml.scene_review.manifest import load_manifest

USES = ["training", "evaluation", "derived_weight_redistribution"]


def write_dataset(
    tmp_path, image_pixels, mask_pixels, *, supported_labels=("open_ground", "obstacle")
):
    data_root = tmp_path / "data"
    image_path = data_root / "images" / "scene.png"
    mask_path = data_root / "masks" / "scene.png"
    image_path.parent.mkdir(parents=True)
    mask_path.parent.mkdir(parents=True)
    Image.fromarray(np.asarray(image_pixels, dtype=np.uint8)).save(image_path)
    Image.fromarray(np.asarray(mask_pixels, dtype=np.uint8)).save(mask_path)
    image_bytes = image_path.read_bytes()
    mask_bytes = mask_path.read_bytes()
    record = {
        "image_id": "scene-1",
        "image_path": "images/scene.png",
        "mask_path": "masks/scene.png",
        "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
        "mask_sha256": hashlib.sha256(mask_bytes).hexdigest(),
        "group_id": "group-1",
        "scene_type": "outdoor",
        "lighting": "day",
        "occlusion": "low",
        "image_quality": "good",
        "source_image_id": "source-image-1",
        "source_page_url": "https://source.example/images/1",
        "original_image_source": "Example archive",
        "original_image_creator": "Creator",
        "image_license_name": "Image grant",
        "image_terms_evidence_url": "https://source.example/terms/1",
        "image_retrieval_evidence_url": "https://source.example/release/v1",
        "image_release_or_retrieval_id": "release-v1/image-1",
        "image_rights_evidence_scope": "image_specific",
        "image_rights_evidence_reference": "source-image-1 grant clause 4",
        "image_rights_review_status": "approved",
        "image_rights_reviewer": "Reviewer",
        "image_rights_decision_date": "2026-10-15",
        "image_rights_decision_reason": "Grant permits all required uses",
        "image_permitted_uses": USES,
        "image_derived_weight_status": "permitted",
        "image_derived_weight_restrictions": "No additional restrictions",
        "image_retention_limits": None,
        "image_attribution": "Creator / archive",
        "annotation_record_id": "annotation-1",
        "annotation_provenance": "scene-review-v2 synthetic test annotation",
    }
    manifest = {
        "schema_version": 1,
        "dataset_id": "synthetic-scene-test",
        "source_url": "https://source.example/dataset",
        "terms_evidence_url": "https://source.example/terms/1",
        "license_name": "Image grant",
        "retrieved_at": "2026-10-15T12:00:00Z",
        "retrieval_evidence_url": "https://source.example/release/v1",
        "immutable_release_or_retrieval_id": "release-v1",
        "rights_review_status": "approved",
        "rights_reviewer": "Reviewer",
        "rights_decision_date": "2026-10-15",
        "rights_decision_reason": "Terms permit required uses",
        "permitted_uses": USES,
        "derived_weight_status": "permitted",
        "derived_weight_restrictions": "No additional restrictions",
        "retention_limits": "Retain under source grant terms",
        "attribution": "Creator / archive",
        "annotation_provenance": "scene-review-v2 synthetic test annotation",
        "label_schema_version": 2,
        "supported_labels": list(supported_labels),
        "records": [record],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return data_root, manifest_path


class FakeImageProcessor:
    def __init__(self):
        self.seen_modes = []

    def __call__(self, *, images, return_tensors):
        self.seen_modes.append(images.mode)
        width, height = images.size
        return {
            "pixel_values": np.zeros((1, 3, height, width), dtype=np.float32),
            "pixel_mask": np.ones((1, height, width), dtype=np.int64),
        }


def make_dataset(tmp_path, image, mask, *, supported_labels=("open_ground", "obstacle")):
    root, manifest_path = write_dataset(tmp_path, image, mask, supported_labels=supported_labels)
    processor = FakeImageProcessor()
    dataset = SceneReviewDataset(
        load_manifest(manifest_path),
        root,
        record_ids=("scene-1",),
        image_processor=processor,
    )
    return dataset, processor


def test_returns_rgb_image_features_and_connected_component_detr_targets(tmp_path):
    image = np.arange(20, dtype=np.uint8).reshape(4, 5)
    mask = np.array(
        [
            [0, 0, 5, 1, 1],
            [0, 5, 5, 1, 5],
            [5, 5, 0, 5, 0],
            [5, 5, 5, 5, 5],
        ],
        dtype=np.uint8,
    )
    dataset, processor = make_dataset(
        tmp_path, image, mask, supported_labels=("obstacle", "open_ground")
    )

    sample = dataset[0]

    assert processor.seen_modes == ["RGB"]
    assert sample["pixel_values"].shape == (3, 4, 5)
    assert sample["pixel_mask"].shape == (4, 5)
    targets = sample["labels"]
    assert targets["class_labels"].tolist() == [0, 0, 0, 1]
    assert targets["masks"].shape == (4, 4, 5)
    assert targets["boxes"].shape == (4, 4)
    assert targets["boxes"][0].tolist() == pytest.approx([0.2, 0.25, 0.4, 0.5])
    assert sample["loss_eligible"] is True
    assert not sample["run_ignore_mask"].any()
    assert sample["unsupported_pixel_counts"] == {}


def test_background_only_scene_has_empty_targets_and_remains_loss_eligible(tmp_path):
    image = np.zeros((2, 3, 3), dtype=np.uint8)
    mask = np.full((2, 3), 5, dtype=np.uint8)
    dataset, _ = make_dataset(tmp_path, image, mask)

    sample = dataset[0]

    assert sample["labels"]["class_labels"].shape == (0,)
    assert sample["labels"]["masks"].shape == (0, 2, 3)
    assert sample["labels"]["boxes"].shape == (0, 4)
    assert sample["loss_eligible"] is True


def test_ignore_and_unsupported_pixels_make_sample_loss_ineligible_and_mask_evaluation(tmp_path):
    image = np.zeros((2, 3, 3), dtype=np.uint8)
    mask = np.array([[0, 1, 2], [255, 0, 5]], dtype=np.uint8)
    dataset, _ = make_dataset(tmp_path, image, mask, supported_labels=("open_ground",))

    sample = dataset[0]

    assert sample["loss_eligible"] is False
    assert sample["run_ignore_mask"].tolist() == [[False, True, True], [True, False, False]]
    assert sample["evaluation_mask"].tolist() == [[True, False, False], [False, True, True]]
    assert sample["unsupported_pixel_counts"] == {"obstacle": 1, "glass_facade": 1}
    assert sample["labels"]["class_labels"].tolist() == [0]


def test_dataset_rejects_unknown_record_ids_and_mismatched_image_mask_dimensions(tmp_path):
    image = np.zeros((2, 3, 3), dtype=np.uint8)
    mask = np.zeros((2, 3), dtype=np.uint8)
    root, manifest_path = write_dataset(tmp_path, image, mask)
    processor = FakeImageProcessor()

    with pytest.raises(ValueError, match="record IDs"):
        SceneReviewDataset(
            load_manifest(manifest_path),
            root,
            record_ids=("missing",),
            image_processor=processor,
        )

    other_root, other_manifest = write_dataset(
        tmp_path / "mismatch", image, np.zeros((3, 2), dtype=np.uint8)
    )
    with pytest.raises(ValueError, match="dimension mismatch"):
        SceneReviewDataset(
            load_manifest(other_manifest),
            other_root,
            record_ids=("scene-1",),
            image_processor=processor,
        )
