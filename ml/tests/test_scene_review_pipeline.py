import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from PIL import Image

from ml.scene_review.artifacts import export_artifact
from ml.scene_review.dataset import SceneReviewDataset
from ml.scene_review.evaluate import EvaluationThresholds, evaluate_model
from ml.scene_review.manifest import SufficiencyPolicy, load_manifest, validate_dataset
from ml.scene_review.splits import DatasetSplits
from ml.scene_review.train import TrainingConfig, train_model


def _approved_manifest(tmp_path):
    data_root = tmp_path / "data"
    records = []
    for index, split_id in enumerate(("train-image", "validation-image", "test-image")):
        image_path = data_root / f"images/{index}.png"
        mask_path = data_root / f"masks/{index}.png"
        image_path.parent.mkdir(parents=True, exist_ok=True)
        mask_path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(np.full((1, 3, 3), index, dtype=np.uint8)).save(image_path)
        Image.fromarray(np.array([[0, 1, 5]], dtype=np.uint8)).save(mask_path)
        records.append({
            "image_id": split_id,
            "image_path": f"images/{index}.png",
            "mask_path": f"masks/{index}.png",
            "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
            "mask_sha256": hashlib.sha256(mask_path.read_bytes()).hexdigest(),
            "group_id": f"group-{index}",
            "scene_type": "outdoor",
            "lighting": "day",
            "occlusion": "none",
            "image_quality": "good",
            "source_image_id": f"source-{index}",
            "source_page_url": f"https://example.invalid/{index}",
            "original_image_source": "Synthetic fixture",
            "original_image_creator": "Test",
            "image_license_name": "Synthetic fixture grant",
            "image_terms_evidence_url": "https://example.invalid/terms",
            "image_retrieval_evidence_url": f"https://example.invalid/release/{index}",
            "image_release_or_retrieval_id": f"release/{index}",
            "image_rights_evidence_scope": "image_specific",
            "image_rights_evidence_reference": f"Synthetic grant covers source-{index}",
            "image_rights_review_status": "approved",
            "image_rights_reviewer": "Test reviewer",
            "image_rights_decision_date": "2026-10-15",
            "image_rights_decision_reason": "Synthetic fixture authorization",
            "image_permitted_uses": ["training", "evaluation", "derived_weight_redistribution"],
            "image_derived_weight_status": "permitted",
            "image_derived_weight_restrictions": "Synthetic fixture only",
            "image_retention_limits": None,
            "image_attribution": "Synthetic fixture",
            "annotation_record_id": f"annotation-{index}",
            "annotation_provenance": "scene-review-v2 synthetic test fixture",
        })
    raw = {
        "schema_version": 1,
        "dataset_id": "synthetic-scene-review",
        "source_url": "https://example.invalid/dataset",
        "terms_evidence_url": "https://example.invalid/terms",
        "license_name": "Synthetic fixture grant",
        "retrieved_at": "2026-10-15T00:00:00Z",
        "retrieval_evidence_url": "https://example.invalid/release",
        "immutable_release_or_retrieval_id": "synthetic-v1",
        "rights_review_status": "approved",
        "rights_reviewer": "Test reviewer",
        "rights_decision_date": "2026-10-15",
        "rights_decision_reason": "Synthetic fixture only",
        "permitted_uses": ["training", "evaluation", "derived_weight_redistribution"],
        "derived_weight_status": "permitted",
        "derived_weight_restrictions": "Synthetic fixture only",
        "retention_limits": "Temporary pytest fixture",
        "attribution": "Synthetic fixture",
        "annotation_provenance": "scene-review-v2 synthetic test fixture",
        "label_schema_version": 2,
        "supported_labels": ["open_ground", "obstacle"],
        "records": records,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(raw), encoding="utf-8")
    return data_root, load_manifest(manifest_path)


class _Processor:
    def __call__(self, *, images, return_tensors):
        width, height = images.size
        return {"pixel_values": torch.ones((1, 3, height, width))}

    def save_pretrained(self, path):
        Path(path, "preprocessor_config.json").write_text(
            '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
        )


class _Model:
    def __init__(self):
        self.config = SimpleNamespace()

    def save_pretrained(self, path):
        Path(path, "config.json").write_text(
            json.dumps({
                "model_type": "detr",
                "scene_review_provenance": self.config.scene_review_provenance,
            }),
            encoding="utf-8",
        )
        Path(path, "model.safetensors").write_bytes(b"synthetic-checkpoint")

    def predict_scene_mask(self, sample):
        return sample["run_mask"]


class _Trainer:
    def fit(self, train_dataset, validation_dataset, *, epochs, output_dir, on_validation_epoch_end):
        assert train_dataset == ("train-image",)
        assert validation_dataset == ("validation-image",)
        on_validation_epoch_end(1, 0.25)


def test_synthetic_pipeline_trains_evaluates_and_exports_only_to_tmp_path(tmp_path, monkeypatch):
    from ml.scene_review import train as train_module

    monkeypatch.setattr(train_module, "_code_worktree_dirty", lambda: False)
    data_root, manifest = _approved_manifest(tmp_path)
    splits = DatasetSplits(("train-image",), ("validation-image",), ("test-image",))
    policy = SufficiencyPolicy(
        maximum_exclusion_rate=0.0,
        minimum_retained_samples_by_split={"train": 1, "validation": 1, "test": 1},
        required_scene_types_by_split={
            "train": ("outdoor",), "validation": ("outdoor",), "test": ("outdoor",)
        },
        minimum_retained_samples_by_scene_type={},
        minimum_retained_groups_by_split={"train": 1, "validation": 1, "test": 1},
        minimum_retained_samples_per_group_by_split={"train": 1, "validation": 1, "test": 1},
        required_group_ids_by_split={"train": (), "validation": (), "test": ()},
    )
    result = train_model(
        manifest,
        splits,
        TrainingConfig(
            model_id="synthetic/model",
            model_revision="a" * 40,
            seed=3,
            epochs=1,
            batch_size=1,
            learning_rate=0.001,
            supported_labels=("open_ground", "obstacle"),
            sufficiency_policy=policy,
            data_root=data_root,
            output_dir=tmp_path / "run",
        ),
        model_cache=tmp_path / "model-cache",
        model_loader=lambda **kwargs: _Model(),
        image_processor_factory=lambda **kwargs: _Processor(),
        trainer_factory=lambda **kwargs: _Trainer(),
        dataset_factory=lambda **kwargs: tuple(kwargs["record_ids"]),
    )
    split_by_id = {
        image_id: split
        for split, ids in (("train", splits.train_ids), ("validation", splits.validation_ids), ("test", splits.test_ids))
        for image_id in ids
    }
    gate = validate_dataset(
        manifest, data_root, split_by_image_id=split_by_id, sufficiency_policy=policy
    )
    assert gate.sufficiency_gate_passed is True
    test_dataset = SceneReviewDataset(
        manifest, data_root, splits.test_ids, image_processor=_Processor()
    )
    thresholds = EvaluationThresholds(
        minimum_iou_by_label={"open_ground": 1.0, "obstacle": 1.0},
        minimum_precision_by_label={"open_ground": 1.0, "obstacle": 1.0},
        minimum_recall_by_label={"open_ground": 1.0, "obstacle": 1.0},
        maximum_false_cue_rate=0.0,
        maximum_false_cue_rate_regression=0.0,
        maximum_metric_regression_by_label={"open_ground": 0.0, "obstacle": 0.0},
        open_ground_component_overlap_iou=1.0,
        minimum_open_ground_component_coverage=1.0,
        maximum_open_ground_component_coverage_regression=0.0,
        minimum_prediction_score=0.5,
        minimum_samples_per_slice=1,
    )
    evaluation_model = _Model()
    evaluation_model.config.scene_review_provenance = json.loads(
        (result.checkpoint_path / "config.json").read_text(encoding="utf-8")
    )["scene_review_provenance"]
    assert evaluation_model.config.scene_review_provenance["model_id"] == (
        result.training_metadata["model_id"]
    )
    evaluation = evaluate_model(
        evaluation_model,
        test_dataset,
        thresholds,
        splits=splits,
        sufficiency_report=gate,
        training_metadata=result.training_metadata,
        checkpoint_path=result.checkpoint_path,
    )
    assert evaluation.passed_thresholds, evaluation.threshold_failures
    artifact_dir = export_artifact(
        checkpoint_path=result.checkpoint_path,
        evaluation_report=evaluation,
        training_metadata=result.training_metadata,
        sufficiency_gate_passed=gate.sufficiency_gate_passed,
        version="synthetic-v1",
        output_root=tmp_path / "model_artifacts" / "scene_review",
    )
    assert artifact_dir.is_relative_to(tmp_path)
    assert (artifact_dir / "metadata.json").is_file()
    assert not (artifact_dir / "images").exists()
