"""Held-out Scene Review metrics and baseline comparison."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import ndimage

from ml.scene_review.artifacts import checkpoint_directory_sha256
from ml.scene_review.labels import BACKGROUND_ID, IGNORE_ID, LABEL_IDS
from ml.scene_review.manifest import (
    SCENE_TYPES,
    DatasetValidationReport,
    manifest_fingerprint,
    split_assignments_fingerprint,
)
from ml.scene_review.splits import DatasetSplits, validate_splits

_SLICE_CATEGORIES = {
    "scene_type": SCENE_TYPES,
    "lighting": frozenset({"day", "night", "dawn", "dusk", "mixed", "unknown"}),
    "occlusion": frozenset({"none", "low", "moderate", "high", "unknown"}),
    "image_quality": frozenset({"good", "fair", "poor", "unknown"}),
}
_METRICS = ("iou", "precision", "recall")


@dataclass(frozen=True)
class EvaluationThresholds:
    minimum_iou_by_label: Mapping[str, float]
    minimum_precision_by_label: Mapping[str, float]
    minimum_recall_by_label: Mapping[str, float]
    maximum_false_cue_rate: float
    maximum_false_cue_rate_regression: float
    maximum_metric_regression_by_label: Mapping[str, float]
    open_ground_component_overlap_iou: float
    minimum_open_ground_component_coverage: float
    maximum_open_ground_component_coverage_regression: float
    minimum_prediction_score: float
    minimum_samples_per_slice: int


@dataclass(frozen=True)
class EvaluationReport:
    per_label_iou: Mapping[str, float | None]
    per_label_precision: Mapping[str, float | None]
    per_label_recall: Mapping[str, float | None]
    false_visual_cue_rate: float | None
    open_ground_component_coverage: float | None
    slice_metrics: Mapping[str, Any]
    sample_counts: Mapping[str, Any]
    per_label_pixel_counts: Mapping[str, Mapping[str, int]]
    unsupported_pixel_counts: Mapping[str, int]
    test_split_sha256: str
    model_id: str
    model_revision: str
    checkpoint_sha256: str
    manifest_sha256: str
    split_assignments_sha256: str
    schema_version: int
    label_schema_version: int
    supported_labels: tuple[str, ...]
    passed_thresholds: bool
    threshold_failures: tuple[str, ...]
    thresholds: EvaluationThresholds
    baseline_comparison: BaselineComparison | None = None


@dataclass(frozen=True)
class BaselineComparison:
    baseline_metrics: Mapping[str, Any]
    per_label_metric_deltas: Mapping[str, Mapping[str, float | None]]
    false_visual_cue_rate_delta: float | None
    open_ground_component_coverage_delta: float | None
    passed_required_non_regression: bool
    failures: tuple[str, ...]


def _validate_thresholds(thresholds: EvaluationThresholds, labels: tuple[str, ...]) -> None:
    if not isinstance(thresholds, EvaluationThresholds):
        raise TypeError("thresholds must be an EvaluationThresholds instance")
    maps = (
        thresholds.minimum_iou_by_label,
        thresholds.minimum_precision_by_label,
        thresholds.minimum_recall_by_label,
        thresholds.maximum_metric_regression_by_label,
    )
    if any(not isinstance(values, Mapping) or set(values) != set(labels) for values in maps):
        raise ValueError("thresholds must be declared for every supported label")
    numbers = [
        thresholds.maximum_false_cue_rate,
        thresholds.maximum_false_cue_rate_regression,
        thresholds.open_ground_component_overlap_iou,
        thresholds.minimum_open_ground_component_coverage,
        thresholds.maximum_open_ground_component_coverage_regression,
        thresholds.minimum_prediction_score,
    ]
    numbers.extend(value for values in maps for value in values.values())
    if any(
        not isinstance(value, (float, int))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or not 0 <= value <= 1
        for value in numbers
    ):
        raise ValueError("metric thresholds must be finite values between zero and one")
    if thresholds.open_ground_component_overlap_iou <= 0:
        raise ValueError("open-ground component overlap IoU must be greater than zero")
    if (
        not isinstance(thresholds.minimum_samples_per_slice, int)
        or isinstance(thresholds.minimum_samples_per_slice, bool)
        or thresholds.minimum_samples_per_slice < 1
    ):
        raise ValueError("minimum_samples_per_slice must be a positive integer")


def _counts_for_label(truth: np.ndarray, prediction: np.ndarray, valid: np.ndarray, mask_id: int):
    actual = (truth == mask_id) & valid
    predicted = (prediction == mask_id) & valid
    true_positive = int(np.count_nonzero(actual & predicted))
    false_positive = int(np.count_nonzero(~actual & predicted & valid))
    false_negative = int(np.count_nonzero(actual & ~predicted))
    union = true_positive + false_positive + false_negative
    return true_positive, false_positive, false_negative, union


def _metrics(counts: tuple[int, int, int, int]) -> dict[str, float | None]:
    true_positive, false_positive, false_negative, union = counts
    predicted_count = true_positive + false_positive
    actual_count = true_positive + false_negative
    return {
        "iou": true_positive / union if union else None,
        "precision": true_positive / predicted_count if predicted_count else None,
        "recall": true_positive / actual_count if actual_count else None,
    }


def _class_counts(truth: np.ndarray, prediction: np.ndarray, valid: np.ndarray, labels: tuple[str, ...]):
    return {
        label: _counts_for_label(truth, prediction, valid, LABEL_IDS[label]) for label in labels
    }


def _components(mask: np.ndarray) -> list[np.ndarray]:
    labels, count = ndimage.label(mask, structure=np.ones((3, 3), dtype=np.uint8))
    return [labels == index for index in range(1, count + 1)]


def _component_iou(first: np.ndarray, second: np.ndarray, valid: np.ndarray) -> float:
    intersection = int(np.count_nonzero(first & second & valid))
    union = int(np.count_nonzero((first | second) & valid))
    return intersection / union if union else 0.0


def _component_metrics(
    truth: np.ndarray, prediction: np.ndarray, valid: np.ndarray, overlap_threshold: float
) -> tuple[int, int, int, int]:
    ground_truth_ground = _components((truth == LABEL_IDS["open_ground"]) & valid)
    predicted_ground = _components((prediction == LABEL_IDS["open_ground"]) & valid)
    covered = sum(
        any(_component_iou(component, candidate, valid) >= overlap_threshold
            for candidate in predicted_ground)
        for component in ground_truth_ground
    )

    false_cues = 0
    cue_count = 0
    for label in LABEL_IDS:
        if label == "open_ground":
            continue
        target_id = LABEL_IDS[label]
        truth_components = _components((truth == target_id) & valid)
        predicted_components = _components((prediction == target_id) & valid)
        for component in predicted_components:
            cue_count += 1
            if not any(
                _component_iou(component, actual, valid) >= overlap_threshold
                for actual in truth_components
            ):
                false_cues += 1
    return covered, len(ground_truth_ground), false_cues, cue_count


def _safe_slice_value(field: str, value: object) -> str:
    allowed = _SLICE_CATEGORIES[field]
    return value if isinstance(value, str) and value in allowed else "other"


def _record_groups(dataset: object) -> tuple[object, ...]:
    records = getattr(dataset, "_records", None)
    if not isinstance(records, tuple) or len(records) != len(dataset):
        raise ValueError("evaluation dataset must expose ordered manifest records")
    return records


def evaluate_model(
    model: object,
    dataset: object,
    thresholds: EvaluationThresholds,
    *,
    splits: DatasetSplits,
    sufficiency_report: DatasetValidationReport,
    training_metadata: Mapping[str, Any],
    checkpoint_path: Path,
) -> EvaluationReport:
    """Evaluate an explicitly held-out test dataset, masking ignore pixels."""
    if not isinstance(sufficiency_report, DatasetValidationReport):
        raise TypeError("sufficiency_report must be a DatasetValidationReport")
    if sufficiency_report.sufficiency_gate_passed is not True:
        raise ValueError("evaluation requires a passing sufficiency gate")
    manifest = getattr(dataset, "_manifest", getattr(dataset, "manifest", None))
    supported = getattr(manifest, "supported_labels", None)
    manifest_records = getattr(manifest, "records", None)
    if not isinstance(supported, tuple) or not supported:
        raise ValueError("evaluation dataset must declare supported labels")
    if not isinstance(splits, DatasetSplits):
        raise TypeError("evaluation requires the declared DatasetSplits")
    if not isinstance(manifest_records, tuple):
        raise TypeError("evaluation dataset must expose its full manifest records")
    validate_splits(manifest_records, splits)
    labels = tuple(supported)
    if len(labels) != len(set(labels)) or not set(labels).issubset(LABEL_IDS):
        raise ValueError("evaluation dataset has an invalid supported-label set")
    _validate_thresholds(thresholds, labels)
    if not isinstance(training_metadata, Mapping):
        raise TypeError("evaluation requires the matching training metadata")
    required_training_identity = {
        "model_id", "model_revision", "checkpoint_sha256", "manifest_sha256",
        "split_assignments_sha256", "schema_version", "label_schema_version",
        "supported_labels",
    }
    if not required_training_identity.issubset(training_metadata):
        raise ValueError("training metadata is missing evaluation provenance")
    current_manifest_sha256 = manifest_fingerprint(manifest)
    current_split_sha256 = split_assignments_fingerprint(splits)
    current_checkpoint_sha256 = checkpoint_directory_sha256(checkpoint_path)
    if (
        training_metadata["manifest_sha256"] != current_manifest_sha256
        or training_metadata["split_assignments_sha256"] != current_split_sha256
        or training_metadata["schema_version"] != getattr(manifest, "schema_version", None)
        or training_metadata["label_schema_version"]
        != getattr(manifest, "label_schema_version", None)
        or tuple(training_metadata["supported_labels"]) != labels
        or training_metadata["checkpoint_sha256"] != current_checkpoint_sha256
    ):
        raise ValueError("evaluation inputs must match the training provenance")
    if (
        not isinstance(training_metadata["model_id"], str)
        or not training_metadata["model_id"]
        or not isinstance(training_metadata["model_revision"], str)
        or not training_metadata["model_revision"]
    ):
        raise ValueError("training metadata has invalid model identity")
    model_config = getattr(model, "config", None)
    checkpoint_provenance = getattr(model_config, "scene_review_provenance", None)
    expected_checkpoint_provenance = {
        key: training_metadata[key]
        for key in (
            "model_id", "model_revision", "manifest_sha256",
            "split_assignments_sha256", "schema_version", "label_schema_version",
        )
    }
    expected_checkpoint_provenance["supported_labels"] = list(labels)
    if checkpoint_provenance != expected_checkpoint_provenance:
        raise ValueError("evaluation model must match the checkpoint training provenance")
    if len(dataset) == 0:
        raise ValueError("held-out test dataset must not be empty")
    records = _record_groups(dataset)
    test_ids = tuple(splits.test_ids)
    if tuple(record.image_id for record in records) != test_ids:
        raise ValueError("evaluation dataset records must exactly match the held-out test split")
    test_summary = sufficiency_report.split_summaries.get("test")
    if (
        sufficiency_report.image_count != len(manifest_records)
        or test_summary is None
        or getattr(test_summary, "total_sample_count", None) != len(test_ids)
        or sufficiency_report.manifest_sha256 != manifest_fingerprint(manifest)
        or sufficiency_report.split_assignments_sha256
        != split_assignments_fingerprint(splits)
    ):
        raise ValueError("sufficiency report must cover the same manifest and split assignment")
    test_input_identity = {
        "records": sorted(
            (
                record.image_id,
                record.image_sha256.lower(),
                record.mask_sha256.lower(),
            )
            for record in records
        ),
        "schema_version": getattr(manifest, "schema_version", None),
        "label_schema_version": getattr(manifest, "label_schema_version", None),
        "supported_labels": tuple(sorted(labels)),
    }
    test_split_sha256 = hashlib.sha256(
        json.dumps(
            test_input_identity,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    aggregate_counts = {label: [0, 0, 0, 0] for label in labels}
    slice_counts: dict[str, dict[str, dict[str, list[int]]]] = {
        name: {value: {label: [0, 0, 0, 0] for label in labels} for value in categories}
        for name, categories in _SLICE_CATEGORIES.items()
    }
    slice_samples: dict[str, Counter[str]] = {
        name: Counter() for name in _SLICE_CATEGORIES
    }
    slice_evaluated: dict[str, Counter[str]] = {
        name: Counter() for name in _SLICE_CATEGORIES
    }
    slice_ignored: dict[str, Counter[str]] = {
        name: Counter() for name in _SLICE_CATEGORIES
    }
    slice_unsupported: dict[str, dict[str, Counter[str]]] = {
        name: {} for name in _SLICE_CATEGORIES
    }
    group_counts: dict[str, dict[str, list[int]]] = {}
    group_total_samples: Counter[str] = Counter()
    group_evaluated_samples: Counter[str] = Counter()
    group_ignored_samples: Counter[str] = Counter()
    unsupported: Counter[str] = Counter()
    ignore_containing = 0
    evaluated = 0
    covered_components = 0
    total_ground_components = 0
    false_cues = 0
    predicted_cues = 0

    for index, record in enumerate(records):
        sample = dataset[index]
        truth = np.asarray(sample["run_mask"])
        valid = np.asarray(sample.get("evaluation_mask", truth != IGNORE_ID), dtype=bool)
        if truth.ndim != 2 or valid.shape != truth.shape:
            raise ValueError("evaluation masks must be two-dimensional and aligned")
        valid &= truth != IGNORE_ID
        if np.any(~valid):
            ignore_containing += 1
        prediction = _predict_mask(model, sample, truth.shape, labels, thresholds.minimum_prediction_score)
        if prediction.shape != truth.shape:
            raise ValueError("predicted mask dimensions must match the indexed target mask")
        allowed_prediction_ids = {LABEL_IDS[label] for label in labels} | {BACKGROUND_ID}
        if {int(value) for value in np.unique(prediction)}.difference(allowed_prediction_ids):
            raise ValueError("predicted mask contains unsupported or invalid class IDs")
        sample_unsupported: Counter[str] = Counter()
        for label, count in sample.get("unsupported_pixel_counts", {}).items():
            if label in LABEL_IDS and isinstance(count, int) and count >= 0:
                unsupported[label] += count
                sample_unsupported[label] += count

        counts = _class_counts(truth, prediction, valid, labels)
        for label, label_counts in counts.items():
            for position, count in enumerate(label_counts):
                aggregate_counts[label][position] += count
        if np.any(valid):
            evaluated += 1
        component_coverage = _component_metrics(
            truth, prediction, valid, thresholds.open_ground_component_overlap_iou
        )
        covered_components += component_coverage[0]
        total_ground_components += component_coverage[1]
        false_cues += component_coverage[2]
        predicted_cues += component_coverage[3]

        for field in _SLICE_CATEGORIES:
            category = _safe_slice_value(field, getattr(record, field, None))
            slice_samples[field][category] += 1
            category_counts = slice_counts[field].setdefault(
                category, {label: [0, 0, 0, 0] for label in labels}
            )
            if np.any(valid):
                slice_evaluated[field][category] += 1
            if np.any(~valid):
                slice_ignored[field][category] += 1
            slice_unsupported[field].setdefault(category, Counter()).update(sample_unsupported)
            for label, label_counts in counts.items():
                for position, count in enumerate(label_counts):
                    category_counts[label][position] += count
        group = getattr(record, "group_id", None)
        if isinstance(group, str) and group:
            group_counts.setdefault(group, {label: [0, 0, 0, 0] for label in labels})
            group_total_samples[group] += 1
            group_evaluated_samples[group] += int(np.any(valid))
            group_ignored_samples[group] += int(np.any(~valid))
            for label, label_counts in counts.items():
                for position, count in enumerate(label_counts):
                    group_counts[group][label][position] += count

    per_label = {label: _metrics(tuple(counts)) for label, counts in aggregate_counts.items()}
    per_label_iou = {label: values["iou"] for label, values in per_label.items()}
    per_label_precision = {label: values["precision"] for label, values in per_label.items()}
    per_label_recall = {label: values["recall"] for label, values in per_label.items()}
    false_cue_rate = false_cues / predicted_cues if predicted_cues else None
    ground_coverage = (
        covered_components / total_ground_components if total_ground_components else None
    )
    failures: list[str] = []
    for label in labels:
        for metric_name, actual, thresholds_by_label in (
            ("IoU", per_label_iou[label], thresholds.minimum_iou_by_label),
            ("precision", per_label_precision[label], thresholds.minimum_precision_by_label),
            ("recall", per_label_recall[label], thresholds.minimum_recall_by_label),
        ):
            if actual is None or actual < thresholds_by_label[label]:
                failures.append(f"{label} {metric_name} threshold not met")
    if false_cue_rate is None or false_cue_rate > thresholds.maximum_false_cue_rate:
        failures.append("false visual-cue rate threshold not met")
    if ground_coverage is None:
        failures.append("open-ground component coverage unavailable")
    elif ground_coverage < thresholds.minimum_open_ground_component_coverage:
        failures.append("open-ground component coverage threshold not met")

    serialized_slices: dict[str, Any] = {}
    for field, categories in _SLICE_CATEGORIES.items():
        serialized_slices[field] = {}
        for category in sorted(categories | {"other"}):
            count = slice_samples[field][category]
            category_counts = slice_counts[field].get(
                category, {label: [0, 0, 0, 0] for label in labels}
            )
            metric_values = {
                label: _metrics(tuple(category_counts[label]))
                for label in labels
            }
            serialized_slices[field][category] = {
                "sample_count": count,
                "evaluated_sample_count": slice_evaluated[field][category],
                "ignore_containing_sample_count": slice_ignored[field][category],
                "unsupported_pixel_counts": dict(slice_unsupported[field].get(category, {})),
                "sufficient": slice_evaluated[field][category]
                >= thresholds.minimum_samples_per_slice,
                "per_label_metrics": metric_values,
            }
    qualifying_groups = [
        (group_id, group_metric)
        for group_id, group_metric in group_counts.items()
        if group_evaluated_samples[group_id] >= thresholds.minimum_samples_per_slice
    ]
    group_metric_values = {
        label: {
            metric: [
                _metrics(tuple(group[label]))[metric]
                for _, group in qualifying_groups
                if _metrics(tuple(group[label]))[metric] is not None
            ]
            for metric in _METRICS
        }
        for label in labels
    }
    serialized_slices["source_group"] = {
        "group_count": len(group_counts),
        "groups_meeting_minimum": len(qualifying_groups),
        "sample_count": sum(group_total_samples.values()),
        "evaluated_sample_count": sum(group_evaluated_samples.values()),
        "ignore_containing_sample_count": sum(group_ignored_samples.values()),
        "minimum_samples_per_group": thresholds.minimum_samples_per_slice,
        "aggregate_per_label_metrics": {
            label: {
                metric: {
                    "minimum": min(group_metric_values[label][metric], default=None),
                    "maximum": max(group_metric_values[label][metric], default=None),
                }
                for metric in _METRICS
            }
            for label in labels
        },
    }
    sample_counts = {
        "total": len(dataset),
        "ignore_containing": ignore_containing,
        "evaluated": evaluated,
        "loss_excluded_if_training": ignore_containing,
        "evaluation_excluded_without_valid_pixels": len(dataset) - evaluated,
        "ignore_exclusion_rate": ignore_containing / len(dataset),
        "false_visual_cue_components": false_cues,
        "predicted_visual_cue_components": predicted_cues,
        "covered_open_ground_components": covered_components,
        "open_ground_components": total_ground_components,
        "retained_by_test_sufficiency_gate": (
            getattr(test_summary, "retained_sample_count", None) if test_summary else None
        ),
    }
    return EvaluationReport(
        per_label_iou=per_label_iou,
        per_label_precision=per_label_precision,
        per_label_recall=per_label_recall,
        false_visual_cue_rate=false_cue_rate,
        open_ground_component_coverage=ground_coverage,
        slice_metrics=serialized_slices,
        sample_counts=sample_counts,
        per_label_pixel_counts={
            label: {
                "true_positive": counts[0],
                "false_positive": counts[1],
                "false_negative": counts[2],
            }
            for label, counts in aggregate_counts.items()
        },
        unsupported_pixel_counts=dict(unsupported),
        test_split_sha256=test_split_sha256,
        model_id=training_metadata["model_id"],
        model_revision=training_metadata["model_revision"],
        checkpoint_sha256=current_checkpoint_sha256,
        manifest_sha256=current_manifest_sha256,
        split_assignments_sha256=current_split_sha256,
        schema_version=manifest.schema_version,
        label_schema_version=manifest.label_schema_version,
        supported_labels=labels,
        passed_thresholds=not failures,
        threshold_failures=tuple(failures),
        thresholds=thresholds,
    )


def _predict_mask(
    model: object,
    sample: Mapping[str, Any],
    target_shape: tuple[int, int],
    labels: tuple[str, ...],
    minimum_score: float,
) -> np.ndarray:
    predict = getattr(model, "predict_scene_mask", None)
    if callable(predict):
        prediction = np.asarray(predict(sample))
        if prediction.ndim != 2 or not np.issubdtype(prediction.dtype, np.integer):
            raise ValueError("predict_scene_mask must return a two-dimensional integer mask")
        return prediction

    try:
        import torch
        from torch.nn import functional
    except ImportError as exc:
        raise RuntimeError("PyTorch is required to evaluate model outputs") from exc
    pixel_values = sample["pixel_values"]
    if not isinstance(pixel_values, torch.Tensor):
        pixel_values = torch.as_tensor(pixel_values)
    arguments = {"pixel_values": pixel_values.unsqueeze(0)}
    if sample.get("pixel_mask") is not None:
        pixel_mask = sample["pixel_mask"]
        if not isinstance(pixel_mask, torch.Tensor):
            pixel_mask = torch.as_tensor(pixel_mask)
        arguments["pixel_mask"] = pixel_mask.unsqueeze(0)
    model.eval()
    with torch.inference_mode():
        output = model(**arguments)
    logits = output.logits[0]
    masks = output.pred_masks[0]
    class_probabilities = logits.softmax(dim=-1)[:, : len(labels)]
    scores, class_indices = class_probabilities.max(dim=-1)
    masks = functional.interpolate(
        masks[:, None], size=target_shape, mode="bilinear", align_corners=False
    )[:, 0].sigmoid()
    score_map = torch.zeros(target_shape, dtype=torch.float32, device=masks.device)
    class_map = torch.full(target_shape, BACKGROUND_ID, dtype=torch.int64, device=masks.device)
    for query in range(len(scores)):
        if scores[query] < minimum_score:
            continue
        selected = masks[query] >= 0.5
        weighted_score = masks[query] * scores[query]
        replace = selected & (weighted_score > score_map)
        score_map[replace] = weighted_score[replace]
        class_map[replace] = LABEL_IDS[labels[int(class_indices[query])]]
    return class_map.cpu().numpy()


def compare_to_baseline(
    candidate: EvaluationReport, baseline: EvaluationReport
) -> BaselineComparison:
    """Require candidate IoU/precision/recall drops to stay within declared limits."""
    if not isinstance(candidate, EvaluationReport) or not isinstance(baseline, EvaluationReport):
        raise TypeError("candidate and baseline must be EvaluationReport values")
    if set(candidate.per_label_iou) != set(baseline.per_label_iou):
        raise ValueError("candidate and baseline must cover the same supported labels")
    if candidate.test_split_sha256 != baseline.test_split_sha256:
        raise ValueError("candidate and baseline must evaluate the same held-out test samples")
    thresholds = candidate.thresholds
    if (
        thresholds.minimum_prediction_score != baseline.thresholds.minimum_prediction_score
        or thresholds.open_ground_component_overlap_iou
        != baseline.thresholds.open_ground_component_overlap_iou
    ):
        raise ValueError("candidate and baseline must use the same prediction and overlap thresholds")
    if not thresholds.maximum_metric_regression_by_label:
        raise ValueError("baseline non-regression thresholds must be declared")
    deltas: dict[str, dict[str, float | None]] = {}
    failures: list[str] = []
    for label in candidate.per_label_iou:
        allowed_drop = thresholds.maximum_metric_regression_by_label.get(label)
        if allowed_drop is None:
            raise ValueError("baseline non-regression threshold missing for supported label")
        deltas[label] = {}
        for metric_name, candidate_values, baseline_values in (
            ("iou", candidate.per_label_iou, baseline.per_label_iou),
            ("precision", candidate.per_label_precision, baseline.per_label_precision),
            ("recall", candidate.per_label_recall, baseline.per_label_recall),
        ):
            candidate_value, baseline_value = candidate_values[label], baseline_values[label]
            delta = (
                candidate_value - baseline_value
                if candidate_value is not None and baseline_value is not None
                else None
            )
            deltas[label][metric_name] = delta
            if delta is None or delta < -allowed_drop:
                failures.append(f"{label} {metric_name} regressed beyond declared maximum")
    false_cue_delta = (
        candidate.false_visual_cue_rate - baseline.false_visual_cue_rate
        if candidate.false_visual_cue_rate is not None
        and baseline.false_visual_cue_rate is not None
        else None
    )
    if (
        false_cue_delta is None
        or false_cue_delta > thresholds.maximum_false_cue_rate_regression
    ):
        failures.append("false visual-cue rate regressed beyond declared maximum")
    coverage_delta = (
        candidate.open_ground_component_coverage - baseline.open_ground_component_coverage
        if candidate.open_ground_component_coverage is not None
        and baseline.open_ground_component_coverage is not None
        else None
    )
    if (
        coverage_delta is None
        or coverage_delta < -thresholds.maximum_open_ground_component_coverage_regression
    ):
        failures.append("open-ground component coverage regressed beyond declared maximum")
    return BaselineComparison(
        {
            "per_label_iou": dict(baseline.per_label_iou),
            "per_label_precision": dict(baseline.per_label_precision),
            "per_label_recall": dict(baseline.per_label_recall),
            "false_visual_cue_rate": baseline.false_visual_cue_rate,
            "open_ground_component_coverage": baseline.open_ground_component_coverage,
        },
        deltas,
        false_cue_delta,
        coverage_delta,
        not failures,
        tuple(failures),
    )
