from dataclasses import replace
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

import numpy as np
import pytest

from ml.scene_review.artifacts import checkpoint_directory_sha256
from ml.scene_review.evaluate import (
    EvaluationThresholds,
    compare_to_baseline,
    evaluate_model,
)
from ml.scene_review.manifest import (
    DatasetValidationReport,
    manifest_fingerprint,
    split_assignments_fingerprint,
)
from ml.scene_review.splits import DatasetSplits

LABELS = ("open_ground", "obstacle")


def _thresholds(**overrides):
    values = {
        "minimum_iou_by_label": {label: 0.5 for label in LABELS},
        "minimum_precision_by_label": {label: 0.5 for label in LABELS},
        "minimum_recall_by_label": {label: 0.5 for label in LABELS},
        "maximum_false_cue_rate": 0.5,
        "maximum_false_cue_rate_regression": 0.2,
        "maximum_metric_regression_by_label": {label: 0.2 for label in LABELS},
        "open_ground_component_overlap_iou": 0.5,
        "minimum_open_ground_component_coverage": 0.5,
        "maximum_open_ground_component_coverage_regression": 0.2,
        "minimum_prediction_score": 0.5,
        "minimum_samples_per_slice": 1,
    }
    values.update(overrides)
    return EvaluationThresholds(**values)


def _record(image_id, **overrides):
    values = {
        "image_id": image_id,
        "image_sha256": f"hash-{image_id}",
        "mask_sha256": f"mask-hash-{image_id}",
        "scene_type": "outdoor",
        "lighting": "day",
        "occlusion": "low",
        "image_quality": "good",
        "group_id": f"private-group-{image_id}",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class _Dataset:
    def __init__(self, masks, *, records=None, unsupported=None):
        self.manifest = SimpleNamespace(
            supported_labels=LABELS, schema_version=1, label_schema_version=2
        )
        self._records = tuple(records or [_record(str(index)) for index in range(len(masks))])
        self._manifest_records = (
            _record("train-only", group_id="train-group", image_sha256="1" * 64),
            _record("validation-only", group_id="validation-group", image_sha256="2" * 64),
            *self._records,
        )
        self.manifest.records = self._manifest_records
        self.samples = [
            {
                "run_mask": mask,
                "evaluation_mask": mask != 255,
                "unsupported_pixel_counts": (unsupported or [{}] * len(masks))[index],
            }
            for index, mask in enumerate(masks)
        ]

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        return self.samples[index]


class _Model:
    def __init__(self, predictions):
        self.predictions = predictions
        self.calls = 0

    def predict_scene_mask(self, sample):
        prediction = self.predictions[self.calls]
        self.calls += 1
        return prediction


def _passing_gate(dataset, splits):
    return DatasetValidationReport(
        image_count=3,
        pixel_counts={},
        unsupported_pixel_counts={},
        unsupported_pixel_counts_by_split={},
        run_mask_ignore_pixel_count=0,
        run_mask_ignore_sample_count=0,
        loss_eligible_sample_count=1,
        loss_excluded_sample_count=0,
        exclusion_rate=0.0,
        split_summaries={"test": SimpleNamespace(total_sample_count=1)},
        sufficiency_gate_passed=True,
        sufficiency_gate_reasons=(),
        warnings=(),
        manifest_sha256=manifest_fingerprint(dataset.manifest),
        split_assignments_sha256=split_assignments_fingerprint(splits),
    )


def _evaluate(
    model,
    dataset,
    thresholds,
    *,
    sufficiency_report=None,
    splits=None,
    training_metadata_overrides=None,
):
    splits = splits or DatasetSplits(
        ("train-only",),
        ("validation-only",),
        tuple(record.image_id for record in dataset._records),
    )
    with TemporaryDirectory() as temporary:
        checkpoint = Path(temporary)
        (checkpoint / "config.json").write_text("{}", encoding="utf-8")
        (checkpoint / "model.safetensors").write_bytes(b"fixture")
        training_metadata = {
            "model_id": "test/model",
            "model_revision": "a" * 40,
            "checkpoint_sha256": checkpoint_directory_sha256(checkpoint),
            "manifest_sha256": manifest_fingerprint(dataset.manifest),
            "split_assignments_sha256": split_assignments_fingerprint(splits),
            "schema_version": 1,
            "label_schema_version": 2,
            "supported_labels": list(LABELS),
        }
        model.config = SimpleNamespace(
            scene_review_provenance={
                key: training_metadata[key]
                for key in (
                    "model_id", "model_revision", "manifest_sha256",
                    "split_assignments_sha256", "schema_version",
                    "label_schema_version", "supported_labels",
                )
            }
        )
        training_metadata.update(training_metadata_overrides or {})
        return evaluate_model(
            model,
            dataset,
            thresholds,
            splits=splits,
            sufficiency_report=sufficiency_report or _passing_gate(dataset, splits),
            training_metadata=training_metadata,
            checkpoint_path=checkpoint,
        )


def test_evaluation_masks_ignore_pixels_and_reports_pixel_metrics_and_components():
    truth = np.array([[0, 0, 1, 5], [0, 255, 1, 5]], dtype=np.uint8)
    prediction = np.array([[0, 1, 1, 1], [0, 0, 1, 5]], dtype=np.uint8)
    dataset = _Dataset([truth], unsupported=[{"glass_facade": 2}])

    report = _evaluate(
        _Model([prediction]),
        dataset,
        _thresholds(),
    )

    assert report.per_label_iou == {"open_ground": 2 / 3, "obstacle": 0.5}
    assert report.per_label_precision == {"open_ground": 1.0, "obstacle": 0.5}
    assert report.per_label_recall == {"open_ground": 2 / 3, "obstacle": 1.0}
    assert report.per_label_pixel_counts["open_ground"] == {
        "true_positive": 2,
        "false_positive": 0,
        "false_negative": 1,
    }
    assert report.false_visual_cue_rate == 0.0
    assert report.open_ground_component_coverage == 1.0
    assert report.manifest_sha256 == manifest_fingerprint(dataset.manifest)
    assert report.split_assignments_sha256 == split_assignments_fingerprint(
        DatasetSplits(("train-only",), ("validation-only",), ("0",))
    )
    assert report.supported_labels == LABELS
    assert "private-group" not in repr(report)
    assert report.sample_counts["total"] == 1
    assert report.sample_counts["ignore_containing"] == 1
    assert report.sample_counts["evaluated"] == 1
    assert report.sample_counts["ignore_exclusion_rate"] == 1.0
    assert report.unsupported_pixel_counts == {"glass_facade": 2}
    assert report.passed_thresholds


def test_evaluation_decodes_pinned_detr_style_outputs_offline():
    torch = pytest.importorskip("torch")
    truth = np.array([[0, 1]], dtype=np.uint8)
    dataset = _Dataset([truth])
    dataset.samples[0]["pixel_values"] = torch.ones((3, 1, 2))

    class DetrOutputModel:
        def eval(self):
            return self

        def __call__(self, **kwargs):
            assert tuple(kwargs["pixel_values"].shape) == (1, 3, 1, 2)
            return SimpleNamespace(
                logits=torch.tensor([[[10.0, 0.0, -10.0], [0.0, 10.0, -10.0]]]),
                pred_masks=torch.tensor([[[[10.0, -10.0]], [[-10.0, 10.0]]]]),
            )

    report = _evaluate(DetrOutputModel(), dataset, _thresholds())

    assert report.per_label_iou == {"open_ground": 1.0, "obstacle": 1.0}
    assert report.per_label_recall == {"open_ground": 1.0, "obstacle": 1.0}


def test_evaluation_requires_test_split_passing_gate_and_predeclared_thresholds():
    truth = np.array([[0, 1]], dtype=np.uint8)
    dataset = _Dataset([truth])
    model = _Model([truth])

    with pytest.raises(ValueError, match="test split"):
        _evaluate(
            model,
            dataset,
            _thresholds(),
            splits=DatasetSplits(("train-only",), tuple(record.image_id for record in dataset._records), ("validation-only",)),
        )
    with pytest.raises(ValueError, match="passing sufficiency"):
        _evaluate(
            model,
            dataset,
            _thresholds(),
            sufficiency_report=replace(
                _passing_gate(dataset, DatasetSplits(("train-only",), ("validation-only",), ("0",))),
                sufficiency_gate_passed=False
            ),
        )
    with pytest.raises(ValueError, match="thresholds must be declared"):
        _evaluate(
            model,
            dataset,
            _thresholds(minimum_iou_by_label={}),
        )


@pytest.mark.parametrize(
    "identity_override",
    [
        {"model_id": "another/model"},
        {"model_revision": "b" * 40},
        {"checkpoint_sha256": "0" * 64},
        {"manifest_sha256": "0" * 64},
        {"split_assignments_sha256": "0" * 64},
        {"supported_labels": ["open_ground"]},
        {"schema_version": 2},
        {"label_schema_version": 3},
    ],
)
def test_evaluation_rejects_training_provenance_mismatch(identity_override):
    truth = np.array([[0, 1]], dtype=np.uint8)
    dataset = _Dataset([truth])
    with pytest.raises(ValueError, match="training provenance"):
        _evaluate(
            _Model([truth]),
            dataset,
            _thresholds(),
            training_metadata_overrides=identity_override,
        )


def test_gate_is_bound_to_exact_manifest_even_when_counts_match():
    truth = np.array([[0, 1]], dtype=np.uint8)
    dataset = _Dataset([truth])
    splits = DatasetSplits(("train-only",), ("validation-only",), ("0",))
    stale_gate = _passing_gate(dataset, splits)
    changed_records = list(dataset.manifest.records)
    changed_records[0] = _record(
        "train-only", group_id="changed-group", image_sha256="1" * 64
    )
    dataset.manifest.records = tuple(changed_records)

    with pytest.raises(ValueError, match="same manifest and split assignment"):
        _evaluate(_Model([truth]), dataset, _thresholds(), splits=splits, sufficiency_report=stale_gate)


def test_gate_is_bound_to_exact_split_assignment_even_when_counts_match():
    truth = np.array([[0, 1]], dtype=np.uint8)
    dataset = _Dataset([truth])
    original_splits = DatasetSplits(("train-only",), ("validation-only",), ("0",))
    stale_gate = _passing_gate(dataset, original_splits)
    changed_splits = DatasetSplits(("validation-only",), ("train-only",), ("0",))

    with pytest.raises(ValueError, match="same manifest and split assignment"):
        _evaluate(
            _Model([truth]), dataset, _thresholds(),
            splits=changed_splits, sufficiency_report=stale_gate,
        )


def test_empty_class_and_insufficient_slice_are_reported_and_fail_acceptance():
    truth = np.array([[0, 0]], dtype=np.uint8)
    dataset = _Dataset([truth], records=[_record("a", scene_type="indoor")])

    report = _evaluate(
        _Model([truth]),
        dataset,
        _thresholds(minimum_samples_per_slice=2),
    )

    assert report.per_label_iou["obstacle"] is None
    assert report.slice_metrics["scene_type"]["outdoor"]["sample_count"] == 0
    assert report.slice_metrics["scene_type"]["indoor"]["sample_count"] == 1
    assert not report.passed_thresholds
    assert any("obstacle" in failure for failure in report.threshold_failures)


def test_false_visual_cue_rate_uses_unmatched_predicted_cue_components():
    truth = np.array([[0, 5, 5, 5]], dtype=np.uint8)
    prediction = np.array([[0, 1, 5, 5]], dtype=np.uint8)

    report = _evaluate(
        _Model([prediction]),
        _Dataset([truth]),
        _thresholds(maximum_false_cue_rate=0.0),
    )

    assert report.false_visual_cue_rate == 1.0
    assert "false visual-cue rate threshold not met" in report.threshold_failures


def test_open_ground_component_coverage_obeys_predeclared_minimum():
    truth = np.array([[0, 0, 0, 0, 1]], dtype=np.uint8)
    prediction = np.array([[0, 5, 5, 5, 1]], dtype=np.uint8)

    report = _evaluate(
        _Model([prediction]),
        _Dataset([truth]),
        _thresholds(minimum_open_ground_component_coverage=1.0),
    )

    assert report.open_ground_component_coverage == 0.0
    assert "open-ground component coverage threshold not met" in report.threshold_failures


def test_slice_reports_do_not_expose_arbitrary_metadata_or_group_ids():
    truth = np.array([[0, 1]], dtype=np.uint8)
    record = _record(
        "a",
        lighting="private-location-name",
        occlusion="private-camera-id",
        image_quality="private-user-note",
    )
    dataset = _Dataset([truth], records=[record])

    report = _evaluate(
        _Model([truth]),
        dataset,
        _thresholds(minimum_samples_per_slice=2),
    )

    rendered = repr(report)
    assert "private-location-name" not in rendered
    assert "private-camera-id" not in rendered
    assert "private-user-note" not in rendered
    assert "private-group-a" not in rendered
    assert report.slice_metrics["lighting"]["other"]["sample_count"] == 1
    assert report.slice_metrics["source_group"]["group_count"] == 1
    assert report.slice_metrics["source_group"]["groups_meeting_minimum"] == 0
    assert report.slice_metrics["scene_type"]["outdoor"]["sufficient"] is False


def test_baseline_comparison_enforces_declared_per_label_non_regression():
    truth = np.array([[0, 0, 1, 1]], dtype=np.uint8)
    baseline = _evaluate(
        _Model([np.array([[0, 1, 1, 1]], dtype=np.uint8)]),
        _Dataset([truth]),
        _thresholds(),
    )
    candidate = _evaluate(
        _Model([truth]),
        _Dataset([truth]),
        _thresholds(),
    )

    comparison = compare_to_baseline(candidate, baseline)

    assert comparison.passed_required_non_regression
    assert comparison.per_label_metric_deltas["open_ground"]["iou"] > 0


def test_baseline_comparison_fails_when_class_regression_exceeds_threshold():
    truth = np.array([[0, 0, 1, 1]], dtype=np.uint8)
    baseline = _evaluate(
        _Model([truth]),
        _Dataset([truth]),
        _thresholds(),
    )
    candidate = _evaluate(
        _Model([np.array([[0, 0, 0, 0]], dtype=np.uint8)]),
        _Dataset([truth]),
        _thresholds(),
    )

    comparison = compare_to_baseline(candidate, baseline)

    assert not comparison.passed_required_non_regression
    assert comparison.per_label_metric_deltas["obstacle"]["iou"] == -1.0


def test_baseline_comparison_enforces_false_cue_and_component_coverage_regression():
    truth = np.array([[0, 0, 1, 1]], dtype=np.uint8)
    baseline = _evaluate(_Model([truth]), _Dataset([truth]), _thresholds())
    candidate = _evaluate(_Model([truth]), _Dataset([truth]), _thresholds())
    baseline = replace(baseline, false_visual_cue_rate=0.0, open_ground_component_coverage=1.0)
    candidate = replace(
        candidate,
        false_visual_cue_rate=0.5,
        open_ground_component_coverage=0.5,
        thresholds=_thresholds(
            maximum_false_cue_rate_regression=0.1,
            maximum_open_ground_component_coverage_regression=0.1,
        ),
    )

    comparison = compare_to_baseline(candidate, baseline)

    assert not comparison.passed_required_non_regression
    assert comparison.false_visual_cue_rate_delta == 0.5
    assert comparison.open_ground_component_coverage_delta == -0.5


def test_baseline_comparison_requires_same_prediction_decoding_thresholds():
    truth = np.array([[0, 0, 1, 1]], dtype=np.uint8)
    baseline = _evaluate(_Model([truth]), _Dataset([truth]), _thresholds())
    candidate = _evaluate(_Model([truth]), _Dataset([truth]), _thresholds())
    candidate = replace(candidate, thresholds=_thresholds(minimum_prediction_score=0.8))

    with pytest.raises(ValueError, match="same prediction and overlap thresholds"):
        compare_to_baseline(candidate, baseline)


def test_baseline_comparison_requires_identical_held_out_samples():
    truth = np.array([[0, 0, 1, 1]], dtype=np.uint8)
    baseline = _evaluate(_Model([truth]), _Dataset([truth]), _thresholds())
    candidate_dataset = _Dataset([truth], records=[_record("different-test-image")])
    candidate = _evaluate(_Model([truth]), candidate_dataset, _thresholds())

    with pytest.raises(ValueError, match="same held-out test samples"):
        compare_to_baseline(candidate, baseline)


def test_baseline_comparison_rejects_changed_annotation_hash():
    truth = np.array([[0, 0, 1, 1]], dtype=np.uint8)
    baseline = _evaluate(_Model([truth]), _Dataset([truth]), _thresholds())
    changed_annotation = _record("0", mask_sha256="changed-mask-hash")
    candidate = _evaluate(
        _Model([truth]),
        _Dataset([truth], records=[changed_annotation]),
        _thresholds(),
    )

    with pytest.raises(ValueError, match="same held-out test samples"):
        compare_to_baseline(candidate, baseline)
