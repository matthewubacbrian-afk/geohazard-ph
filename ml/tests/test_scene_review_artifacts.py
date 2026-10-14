import json

import pytest

from ml.scene_review.artifacts import export_artifact


class _Evaluation:
    def __init__(self, passed_thresholds=True):
        self.passed_thresholds = passed_thresholds
        self.test_split_sha256 = "a" * 64
        self.threshold_failures = ()
        self.unsupported_pixel_counts = {"glass_facade": 3}
        self.sample_counts = {
            "total": 2,
            "ignore_containing": 1,
            "evaluated": 2,
            "ignore_exclusion_rate": 0.5,
        }
        self.per_label_iou = {"open_ground": 0.8}
        self.per_label_precision = {"open_ground": 0.9}
        self.per_label_recall = {"open_ground": 0.85}
        self.per_label_pixel_counts = {
            "open_ground": {"true_positive": 4, "false_positive": 1, "false_negative": 1}
        }
        empty_slice = {
            "sample_count": 0,
            "evaluated_sample_count": 0,
            "ignore_containing_sample_count": 0,
            "unsupported_pixel_counts": {},
            "sufficient": False,
            "per_label_metrics": {},
        }
        self.slice_metrics = {
            "scene_type": {"outdoor": {**empty_slice, "sample_count": 2}},
            "lighting": {},
            "occlusion": {},
            "image_quality": {},
            "source_group": {
                "group_count": 1,
                "groups_meeting_minimum": 1,
                "sample_count": 2,
                "evaluated_sample_count": 2,
                "ignore_containing_sample_count": 1,
                "minimum_samples_per_group": 1,
                "aggregate_per_label_metrics": {},
            },
        }
        self.false_visual_cue_rate = 0.1
        self.open_ground_component_coverage = 0.75
        self.thresholds = {
            "minimum_iou_by_label": {"open_ground": 0.7},
            "minimum_precision_by_label": {"open_ground": 0.7},
            "minimum_recall_by_label": {"open_ground": 0.7},
            "maximum_metric_regression_by_label": {"open_ground": 0.2},
            "maximum_false_cue_rate": 0.5,
            "maximum_false_cue_rate_regression": 0.2,
            "open_ground_component_overlap_iou": 0.5,
            "minimum_open_ground_component_coverage": 0.5,
            "maximum_open_ground_component_coverage_regression": 0.2,
            "minimum_prediction_score": 0.5,
            "minimum_samples_per_slice": 1,
        }


def _training_metadata():
    return {
        "model_id": "model/name",
        "model_revision": "b" * 40,
        "code_revision": "c" * 40,
        "code_worktree_dirty": False,
        "best_epoch": 2,
        "best_validation_loss": 0.25,
        "runtime_versions": {"python": "3.11"},
        "manifest_sha256": "d" * 64,
        "split_assignments_sha256": "f" * 64,
        "seed": 7,
        "epochs": 2,
        "batch_size": 1,
        "learning_rate": 0.001,
        "supported_labels": ["open_ground"],
        "image_preprocessing": {"class": "ImageProcessor", "config_sha256": "e" * 64},
        "split_counts": {
            "train": {"total_sample_count": 4, "ignore_containing_sample_count": 1,
                      "loss_eligible_sample_count": 3, "loss_excluded_sample_count": 1,
                      "exclusion_rate": 0.25, "retained_counts_by_scene_type": {"outdoor": 3},
                      "unsupported_pixel_counts_by_canonical_label": {}},
            "validation": {"total_sample_count": 2, "ignore_containing_sample_count": 0,
                           "loss_eligible_sample_count": 2, "loss_excluded_sample_count": 0,
                           "exclusion_rate": 0.0, "retained_counts_by_scene_type": {"outdoor": 2},
                           "unsupported_pixel_counts_by_canonical_label": {}},
        },
        "unsupported_pixel_counts_by_canonical_label": {},
        "sufficiency_gate_passed": True,
    }


def test_export_writes_complete_immutable_aggregate_artifact(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"synthetic weights")

    artifact_dir = export_artifact(
        checkpoint_path=checkpoint,
        evaluation_report=_Evaluation(),
        training_metadata=_training_metadata(),
        sufficiency_gate_passed=True,
        version="v-test-1",
        output_root=tmp_path / "artifacts",
    )

    metadata = json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))
    assert artifact_dir == tmp_path / "artifacts" / "v-test-1"
    assert (artifact_dir / "model" / "model.safetensors").read_bytes() == b"synthetic weights"
    assert metadata["evaluation"]["passed_thresholds"] is True
    assert metadata["labels"] == ["open_ground"]
    assert metadata["training"]["manifest_sha256"] == "d" * 64
    assert metadata["split_counts"]["test"]["evaluated_sample_count"] == 2
    assert "image_id" not in repr(metadata)
    assert "source_image_id" not in repr(metadata)
    assert str(tmp_path) not in repr(metadata)
    assert "rights" not in repr(metadata)


def test_export_rejects_failed_gate_evaluation_and_overwrite(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    args = {
        "checkpoint_path": checkpoint,
        "evaluation_report": _Evaluation(),
        "training_metadata": _training_metadata(),
        "sufficiency_gate_passed": True,
        "version": "v1",
        "output_root": tmp_path / "artifacts",
    }

    with pytest.raises(ValueError, match="sufficiency gate"):
        export_artifact(**{**args, "sufficiency_gate_passed": False})
    with pytest.raises(ValueError, match="evaluation thresholds"):
        export_artifact(**{**args, "evaluation_report": _Evaluation(False)})
    export_artifact(**args)
    with pytest.raises(FileExistsError, match="already exists"):
        export_artifact(**args)


def test_export_rejects_incomplete_provenance_and_local_or_rights_fields(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    args = {
        "checkpoint_path": checkpoint,
        "evaluation_report": _Evaluation(),
        "training_metadata": {**_training_metadata(), "dataset_path": "C:/private/manifest.json"},
        "sufficiency_gate_passed": True,
        "version": "v1",
        "output_root": tmp_path / "artifacts",
    }
    with pytest.raises(ValueError, match="private or path metadata"):
        export_artifact(**args)

    args["training_metadata"].pop("dataset_path")
    args["training_metadata"]["image_rights_evidence_url"] = "https://source.invalid/rights"
    with pytest.raises(ValueError, match="private or path metadata"):
        export_artifact(**args)

    args["training_metadata"].pop("image_rights_evidence_url")
    del args["training_metadata"]["model_revision"]
    with pytest.raises(ValueError, match="complete training provenance"):
        export_artifact(**args)


def test_export_rejects_training_from_dirty_worktree(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    metadata = _training_metadata()
    metadata["code_worktree_dirty"] = True

    with pytest.raises(ValueError, match="clean code revision"):
        export_artifact(
            checkpoint_path=checkpoint,
            evaluation_report=_Evaluation(),
            training_metadata=metadata,
            sufficiency_gate_passed=True,
            version="v-dirty",
            output_root=tmp_path / "artifacts",
        )
