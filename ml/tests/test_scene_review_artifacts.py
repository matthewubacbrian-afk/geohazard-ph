import json

import pytest

from ml.scene_review.artifacts import checkpoint_directory_sha256, export_artifact


class _Evaluation:
    def __init__(self, passed_thresholds=True):
        self.passed_thresholds = passed_thresholds
        self.test_split_sha256 = "a" * 64
        self.model_id = "model/name"
        self.model_revision = "b" * 40
        self.checkpoint_sha256 = "9" * 64
        self.manifest_sha256 = "d" * 64
        self.split_assignments_sha256 = "f" * 64
        self.schema_version = 1
        self.label_schema_version = 2
        self.supported_labels = ("open_ground",)
        self.threshold_failures = ()
        self.baseline_comparison = None
        self.unsupported_pixel_counts = {"glass_facade": 3}
        self.sample_counts = {
            "total": 2,
            "ignore_containing": 1,
            "evaluated": 2,
            "ignore_exclusion_rate": 0.5,
            "false_visual_cue_components": 1,
            "predicted_visual_cue_components": 10,
            "covered_open_ground_components": 3,
            "open_ground_components": 4,
        }
        self.per_label_iou = {"open_ground": 0.8}
        self.per_label_precision = {"open_ground": 8 / 9}
        self.per_label_recall = {"open_ground": 8 / 9}
        self.per_label_pixel_counts = {
            "open_ground": {"true_positive": 8, "false_positive": 1, "false_negative": 1}
        }
        empty_slice = {
            "sample_count": 0,
            "evaluated_sample_count": 0,
            "ignore_containing_sample_count": 0,
            "unsupported_pixel_counts": {},
            "sufficient": False,
            "per_label_metrics": {
                "open_ground": {"iou": None, "precision": None, "recall": None}
            },
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
                "aggregate_per_label_metrics": {
                    "open_ground": {
                        "iou": {"minimum": 0.8, "maximum": 0.8},
                        "precision": {"minimum": 8 / 9, "maximum": 8 / 9},
                        "recall": {"minimum": 8 / 9, "maximum": 8 / 9},
                    }
                },
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
        "schema_version": 1,
        "label_schema_version": 2,
        "code_revision": "c" * 40,
        "code_worktree_dirty": False,
        "best_epoch": 2,
        "best_validation_loss": 0.25,
        "runtime_versions": {"python": "3.11"},
        "manifest_sha256": "d" * 64,
        "split_assignments_sha256": "f" * 64,
        "checkpoint_sha256": "9" * 64,
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


def _bind_checkpoint(checkpoint, metadata, report):
    digest = checkpoint_directory_sha256(checkpoint)
    metadata["checkpoint_sha256"] = digest
    report.checkpoint_sha256 = digest


def _set_pixel_counts(report, true_positive, false_positive, false_negative):
    report.per_label_pixel_counts["open_ground"] = {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }
    report.per_label_iou["open_ground"] = true_positive / (
        true_positive + false_positive + false_negative
    )
    report.per_label_precision["open_ground"] = true_positive / (
        true_positive + false_positive
    )
    report.per_label_recall["open_ground"] = true_positive / (
        true_positive + false_negative
    )


def test_export_writes_complete_immutable_aggregate_artifact(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"synthetic weights")
    training_metadata = _training_metadata()
    evaluation_report = _Evaluation()
    _bind_checkpoint(checkpoint, training_metadata, evaluation_report)

    artifact_dir = export_artifact(
        checkpoint_path=checkpoint,
        evaluation_report=evaluation_report,
        training_metadata=training_metadata,
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
    _bind_checkpoint(checkpoint, args["training_metadata"], args["evaluation_report"])

    with pytest.raises(ValueError, match="sufficiency gate"):
        export_artifact(**{**args, "sufficiency_gate_passed": False})
    with pytest.raises(ValueError, match="evaluation thresholds"):
        export_artifact(**{**args, "evaluation_report": _Evaluation(False)})
    export_artifact(**args)
    with pytest.raises(FileExistsError, match="already exists"):
        export_artifact(**args)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("model_id", "another/model"),
        ("model_revision", "a" * 40),
        ("checkpoint_sha256", "8" * 64),
        ("manifest_sha256", "7" * 64),
        ("split_assignments_sha256", "6" * 64),
        ("supported_labels", ("obstacle",)),
        ("schema_version", 2),
        ("label_schema_version", 3),
    ],
)
def test_export_rejects_evaluation_provenance_mismatch(tmp_path, field, value):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    metadata = _training_metadata()
    report = _Evaluation()
    _bind_checkpoint(checkpoint, metadata, report)
    setattr(report, field, value)
    if field == "supported_labels":
        report.per_label_iou = {"obstacle": 0.8}
        report.per_label_precision = {"obstacle": 8 / 9}
        report.per_label_recall = {"obstacle": 8 / 9}
        report.per_label_pixel_counts = {
            "obstacle": {"true_positive": 8, "false_positive": 1, "false_negative": 1}
        }
        for threshold_key in (
            "minimum_iou_by_label",
            "minimum_precision_by_label",
            "minimum_recall_by_label",
            "maximum_metric_regression_by_label",
        ):
            report.thresholds[threshold_key] = {"obstacle": 0.2}
        for slices in (
            report.slice_metrics["scene_type"],
            report.slice_metrics["lighting"],
            report.slice_metrics["occlusion"],
            report.slice_metrics["image_quality"],
        ):
            for summary in slices.values():
                summary["per_label_metrics"] = {
                    "obstacle": {"iou": None, "precision": None, "recall": None}
                }
        report.slice_metrics["source_group"]["aggregate_per_label_metrics"] = {
            "obstacle": {
                metric: {"minimum": 0.8, "maximum": 0.8}
                for metric in ("iou", "precision", "recall")
            }
        }

    with pytest.raises(ValueError, match="evaluation provenance must match training"):
        export_artifact(
            checkpoint_path=checkpoint,
            evaluation_report=report,
            training_metadata=metadata,
            sufficiency_gate_passed=True,
            version="v-mismatch",
            output_root=tmp_path / "artifacts",
        )


def test_export_rejects_checkpoint_changed_after_evaluation(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    weights = checkpoint / "model.safetensors"
    weights.write_bytes(b"evaluated weights")
    metadata = _training_metadata()
    report = _Evaluation()
    _bind_checkpoint(checkpoint, metadata, report)
    weights.write_bytes(b"different checkpoint")

    with pytest.raises(ValueError, match="training checkpoint"):
        export_artifact(
            checkpoint_path=checkpoint,
            evaluation_report=report,
            training_metadata=metadata,
            sufficiency_gate_passed=True,
            version="v-checkpoint-changed",
            output_root=tmp_path / "artifacts",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("per_label_iou", -0.1),
        ("per_label_iou", float("nan")),
        ("per_label_iou", None),
        ("per_label_iou", 1.1),
        ("per_label_precision", -0.1),
        ("per_label_recall", float("nan")),
        ("false_visual_cue_rate", 1.1),
        ("open_ground_component_coverage", -0.1),
        ("false_visual_cue_rate", None),
    ],
)
def test_export_rejects_nonfinite_or_out_of_range_metrics(tmp_path, field, value):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    metadata = _training_metadata()
    report = _Evaluation()
    _bind_checkpoint(checkpoint, metadata, report)
    if field.startswith("per_label_"):
        getattr(report, field)["open_ground"] = value
    else:
        setattr(report, field, value)

    with pytest.raises(ValueError, match="evaluation metrics are invalid"):
        export_artifact(
            checkpoint_path=checkpoint,
            evaluation_report=report,
            training_metadata=metadata,
            sufficiency_gate_passed=True,
            version="v-invalid-metric",
            output_root=tmp_path / "artifacts",
        )


@pytest.mark.parametrize(
    ("field", "value", "counts"),
    [
        ("per_label_iou", 0.6, (3, 1, 1)),
        ("per_label_precision", 0.6, (3, 2, 1)),
        ("per_label_recall", 0.6, (3, 1, 2)),
        ("false_visual_cue_rate", 0.6, None),
        ("open_ground_component_coverage", 0.4, None),
    ],
)
def test_export_recomputes_declared_threshold_satisfaction(tmp_path, field, value, counts):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    metadata = _training_metadata()
    report = _Evaluation()
    _bind_checkpoint(checkpoint, metadata, report)
    if field.startswith("per_label_"):
        _set_pixel_counts(report, *counts)
    else:
        setattr(report, field, value)
        if field == "false_visual_cue_rate":
            report.sample_counts["false_visual_cue_components"] = 6
        else:
            report.sample_counts["covered_open_ground_components"] = 2
            report.sample_counts["open_ground_components"] = 5

    with pytest.raises(ValueError, match="evaluation thresholds are inconsistent"):
        export_artifact(
            checkpoint_path=checkpoint,
            evaluation_report=report,
            training_metadata=metadata,
            sufficiency_gate_passed=True,
            version="v-threshold-mismatch",
            output_root=tmp_path / "artifacts",
        )


def test_export_recomputes_optional_baseline_non_regression(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    metadata = _training_metadata()
    report = _Evaluation()
    _bind_checkpoint(checkpoint, metadata, report)
    report.thresholds["maximum_metric_regression_by_label"] = {"open_ground": 0.1}
    report.baseline_comparison = {
        "baseline_metrics": {
            "per_label_iou": {"open_ground": 1.0},
            "per_label_precision": {"open_ground": 8 / 9},
            "per_label_recall": {"open_ground": 8 / 9},
            "false_visual_cue_rate": 0.1,
            "open_ground_component_coverage": 0.75,
        },
        "per_label_metric_deltas": {
            "open_ground": {"iou": -0.2, "precision": 0.0, "recall": 0.0}
        },
        "false_visual_cue_rate_delta": 0.0,
        "open_ground_component_coverage_delta": 0.0,
        "passed_required_non_regression": True,
        "failures": [],
    }

    with pytest.raises(ValueError, match="baseline non-regression thresholds are inconsistent"):
        export_artifact(
            checkpoint_path=checkpoint,
            evaluation_report=report,
            training_metadata=metadata,
            sufficiency_gate_passed=True,
            version="v-baseline-mismatch",
            output_root=tmp_path / "artifacts",
        )

    passing_report = _Evaluation()
    _bind_checkpoint(checkpoint, metadata, passing_report)
    passing_report.baseline_comparison = {
        "baseline_metrics": {
            "per_label_iou": {"open_ground": 0.7},
            "per_label_precision": {"open_ground": 0.8},
            "per_label_recall": {"open_ground": 0.8},
            "false_visual_cue_rate": 0.1,
            "open_ground_component_coverage": 0.75,
        },
        "per_label_metric_deltas": {
            "open_ground": {
                "iou": 0.1,
                "precision": 8 / 9 - 0.8,
                "recall": 8 / 9 - 0.8,
            }
        },
        "false_visual_cue_rate_delta": 0.0,
        "open_ground_component_coverage_delta": 0.0,
        "passed_required_non_regression": True,
        "failures": [],
    }
    artifact_dir = export_artifact(
        checkpoint_path=checkpoint,
        evaluation_report=passing_report,
        training_metadata=metadata,
        sufficiency_gate_passed=True,
        version="v-baseline-passing",
        output_root=tmp_path / "artifacts",
    )
    assert json.loads((artifact_dir / "metadata.json").read_text(encoding="utf-8"))[
        "evaluation"
    ]["baseline_comparison"]["passed_required_non_regression"]


def test_export_recomputes_baseline_deltas_from_included_baseline_metrics(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    metadata = _training_metadata()
    report = _Evaluation()
    _bind_checkpoint(checkpoint, metadata, report)
    report.baseline_comparison = {
        "baseline_metrics": {
            "per_label_iou": {"open_ground": 0.7},
            "per_label_precision": {"open_ground": 0.8},
            "per_label_recall": {"open_ground": 0.8},
            "false_visual_cue_rate": 0.1,
            "open_ground_component_coverage": 0.75,
        },
        "per_label_metric_deltas": {
            "open_ground": {"iou": 0.0, "precision": 8 / 9 - 0.8, "recall": 8 / 9 - 0.8}
        },
        "false_visual_cue_rate_delta": 0.0,
        "open_ground_component_coverage_delta": 0.0,
        "passed_required_non_regression": True,
        "failures": [],
    }

    with pytest.raises(ValueError, match="baseline comparison is inconsistent"):
        export_artifact(
            checkpoint_path=checkpoint,
            evaluation_report=report,
            training_metadata=metadata,
            sufficiency_gate_passed=True,
            version="v-tampered-baseline-delta",
            output_root=tmp_path / "artifacts",
        )


def test_export_rejects_out_of_range_slice_metrics(tmp_path):
    checkpoint = tmp_path / "checkpoint"
    checkpoint.mkdir()
    (checkpoint / "config.json").write_text('{"model_type":"detr"}', encoding="utf-8")
    (checkpoint / "preprocessor_config.json").write_text(
        '{"image_processor_type":"DetrImageProcessor"}', encoding="utf-8"
    )
    (checkpoint / "model.safetensors").write_bytes(b"weights")
    metadata = _training_metadata()
    report = _Evaluation()
    _bind_checkpoint(checkpoint, metadata, report)
    report.slice_metrics["scene_type"]["outdoor"]["per_label_metrics"][
        "open_ground"
    ]["iou"] = 1.1

    with pytest.raises(ValueError, match="evaluation metrics are invalid"):
        export_artifact(
            checkpoint_path=checkpoint,
            evaluation_report=report,
            training_metadata=metadata,
            sufficiency_gate_passed=True,
            version="v-out-of-range-slice",
            output_root=tmp_path / "artifacts",
        )


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
