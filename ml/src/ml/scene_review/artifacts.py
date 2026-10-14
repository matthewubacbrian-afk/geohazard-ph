"""Validated export of immutable Scene Review model artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
from pathlib import Path, PureWindowsPath
from typing import Any

from ml.scene_review.labels import LABEL_IDS
from ml.scene_review.manifest import SCENE_TYPES

_ARTIFACT_SCHEMA_VERSION = 1
_TRAINING_FIELDS = (
    "model_id",
    "model_revision",
    "code_revision",
    "code_worktree_dirty",
    "best_epoch",
    "best_validation_loss",
    "runtime_versions",
    "manifest_sha256",
    "split_assignments_sha256",
    "seed",
    "epochs",
    "batch_size",
    "learning_rate",
    "supported_labels",
    "image_preprocessing",
    "split_counts",
    "unsupported_pixel_counts_by_canonical_label",
    "sufficiency_gate_passed",
)
_MODEL_FILE = re.compile(
    r"(?:config\.json|preprocessor_config\.json|model\.safetensors|pytorch_model\.bin|"
    r"(?:model|pytorch_model)-[0-9]+-of-[0-9]+\.(?:safetensors|bin)|"
    r"(?:model|pytorch_model)\.(?:safetensors|bin)\.index\.json)"
)
_PRIVATE_KEYS = {"image_id", "group_id", "source_image_id", "rights", "attribution"}
_PATH_KEY = re.compile(r"(?:^|_)(?:path|root|directory|dir)$", re.IGNORECASE)
_SLICE_CATEGORIES = {
    "scene_type": SCENE_TYPES | {"other"},
    "lighting": frozenset({"day", "night", "dawn", "dusk", "mixed", "unknown", "other"}),
    "occlusion": frozenset({"none", "low", "moderate", "high", "unknown", "other"}),
    "image_quality": frozenset({"good", "fair", "poor", "unknown", "other"}),
}
_SAMPLE_COUNT_FIELDS = {
    "total",
    "ignore_containing",
    "evaluated",
    "loss_excluded_if_training",
    "evaluation_excluded_without_valid_pixels",
    "ignore_exclusion_rate",
    "false_visual_cue_components",
    "predicted_visual_cue_components",
    "covered_open_ground_components",
    "open_ground_components",
    "retained_by_test_sufficiency_gate",
}


def export_artifact(
    *,
    checkpoint_path: Path,
    evaluation_report: object,
    training_metadata: Mapping[str, Any],
    sufficiency_gate_passed: bool,
    version: str,
    output_root: Path,
) -> Path:
    """Export a passing reviewed checkpoint without local data or rights records.

    ``output_root`` is injectable for isolated tests. The CLI fixes it to the
    repository's ``ml/model_artifacts/scene_review`` directory.
    """
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", version) or version in {".", ".."}:
        raise ValueError("version must be a simple immutable artifact version name")
    if not isinstance(checkpoint_path, Path) or not checkpoint_path.is_dir():
        raise ValueError("checkpoint_path must be an existing model directory")
    if not isinstance(output_root, Path):
        raise TypeError("output_root must be a Path")
    if sufficiency_gate_passed is not True:
        raise ValueError("artifact export requires a passing sufficiency gate")
    if _field(evaluation_report, "passed_thresholds") is not True:
        raise ValueError("artifact export requires passing evaluation thresholds")
    required_metrics = (
        "per_label_iou",
        "per_label_precision",
        "per_label_recall",
        "per_label_pixel_counts",
        "false_visual_cue_rate",
        "open_ground_component_coverage",
        "thresholds",
        "test_split_sha256",
        "sample_counts",
    )
    if any(_field(evaluation_report, name, _MISSING) is _MISSING for name in required_metrics):
        raise ValueError("evaluation report is missing complete provenance or metrics")
    if not isinstance(training_metadata, Mapping):
        raise TypeError("training_metadata must be a mapping")
    _validate_public_value(training_metadata)
    if set(_TRAINING_FIELDS).difference(training_metadata):
        raise ValueError("training metadata is missing complete training provenance")
    if training_metadata.get("sufficiency_gate_passed") is not True:
        raise ValueError("training metadata does not record a passing sufficiency gate")
    _validate_training_metadata(training_metadata)
    evaluation = _evaluation_metadata(evaluation_report)
    labels = set(training_metadata["supported_labels"])
    for key in ("per_label_iou", "per_label_precision", "per_label_recall"):
        if not isinstance(evaluation[key], Mapping) or set(evaluation[key]) != labels:
            raise ValueError("evaluation labels must match the trained supported labels")
    if set(evaluation["per_label_pixel_counts"]) != labels:
        raise ValueError("evaluation pixel counts must match the trained supported labels")
    for label_counts in evaluation["per_label_pixel_counts"].values():
        if not isinstance(label_counts, Mapping) or set(label_counts) != {
            "true_positive", "false_positive", "false_negative"
        } or any(
            not isinstance(count, int) or isinstance(count, bool) or count < 0
            for count in label_counts.values()
        ):
            raise ValueError("evaluation pixel counts are malformed")
    threshold_values = evaluation["thresholds"]
    if not isinstance(threshold_values, Mapping):
        raise TypeError("evaluation thresholds must be a mapping")
    for key in (
        "minimum_iou_by_label",
        "minimum_precision_by_label",
        "minimum_recall_by_label",
        "maximum_metric_regression_by_label",
    ):
        if not isinstance(threshold_values.get(key), Mapping) or set(threshold_values[key]) != labels:
            raise ValueError("evaluation thresholds must match the trained supported labels")
    _validate_public_value(evaluation)

    output_root = output_root.resolve()
    artifact_dir = output_root / version
    if artifact_dir.exists():
        raise FileExistsError("artifact version already exists; exports are immutable")
    model_files = _model_files(checkpoint_path)
    output_root.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir()
    try:
        model_dir = artifact_dir / "model"
        model_dir.mkdir()
        for source in model_files:
            shutil.copyfile(source, model_dir / source.name)
        checkpoint_sha256 = _directory_sha256(model_dir)
        metadata = {
            "artifact_schema_version": _ARTIFACT_SCHEMA_VERSION,
            "artifact_version": version,
            "model": {
                "id": training_metadata["model_id"],
                "revision": training_metadata["model_revision"],
                "code_revision": training_metadata["code_revision"],
                "code_worktree_dirty": training_metadata["code_worktree_dirty"],
                "best_epoch": training_metadata["best_epoch"],
                "best_validation_loss": training_metadata["best_validation_loss"],
                "checkpoint_sha256": checkpoint_sha256,
            },
            "labels": list(training_metadata["supported_labels"]),
            "training": {key: training_metadata[key] for key in _TRAINING_FIELDS},
            "evaluation": evaluation,
            "split_counts": _aggregate_split_counts(training_metadata, evaluation),
            "limitations": [
                "Visual outputs are not a safety assessment or emergency decision tool.",
                "Real-scene recognition has not been validated unless explicitly recorded by evaluation.",
            ],
        }
        _validate_public_value(metadata)
        (artifact_dir / "metadata.json").write_text(
            json.dumps(
                metadata, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False
            )
            + "\n",
            encoding="utf-8",
        )
    except Exception:
        shutil.rmtree(artifact_dir, ignore_errors=True)
        raise
    return artifact_dir


_MISSING = object()


def _field(value: object, name: str, default: object = None) -> object:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _json_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_value(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ValueError("metadata contains unsupported value types")


def _validate_training_metadata(metadata: Mapping[str, Any]) -> None:
    for key in ("manifest_sha256", "split_assignments_sha256"):
        if not _is_sha256(metadata[key]):
            raise ValueError("training metadata is missing complete training provenance")
    for key in ("model_revision", "code_revision"):
        value = metadata[key]
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", value):
            raise ValueError("training metadata is missing complete training provenance")
    if not isinstance(metadata["code_worktree_dirty"], bool):
        raise TypeError("code_worktree_dirty must be a boolean")
    if metadata["code_worktree_dirty"]:
        raise ValueError("artifact export requires training from a clean code revision")
    for key in ("model_id", "runtime_versions", "supported_labels", "split_counts"):
        if not metadata[key]:
            raise ValueError("training metadata is missing complete training provenance")
    if not isinstance(metadata["model_id"], str):
        raise TypeError("training model_id must be text")
    if not isinstance(metadata["runtime_versions"], Mapping):
        raise TypeError("training runtime_versions must be a mapping")
    if not isinstance(metadata["supported_labels"], (list, tuple)):
        raise TypeError("training supported_labels must be a sequence")
    if (
        not metadata["supported_labels"]
        or not all(isinstance(label, str) for label in metadata["supported_labels"])
        or len(set(metadata["supported_labels"])) != len(metadata["supported_labels"])
        or not set(metadata["supported_labels"]).issubset(LABEL_IDS)
    ):
        raise ValueError("training supported_labels must be canonical scene classes")
    if not isinstance(metadata["split_counts"], Mapping):
        raise TypeError("training split_counts must be a mapping")
    if any(
        not isinstance(metadata[key], (int, float))
        or isinstance(metadata[key], bool)
        or not math.isfinite(metadata[key])
        or metadata[key] <= 0
        for key in ("epochs", "batch_size", "learning_rate")
    ):
        raise ValueError("training metadata is missing complete training provenance")
    for split in ("train", "validation"):
        summary = metadata["split_counts"].get(split)
        if not isinstance(summary, Mapping):
            raise TypeError("training split summary must be a mapping")
        for field in (
            "total_sample_count",
            "ignore_containing_sample_count",
            "loss_eligible_sample_count",
            "loss_excluded_sample_count",
        ):
            count = summary.get(field)
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                raise ValueError("training split counts are incomplete")
        exclusion_rate = summary.get("exclusion_rate")
        if (
            not isinstance(exclusion_rate, (float, int))
            or isinstance(exclusion_rate, bool)
            or not math.isfinite(exclusion_rate)
            or not 0 <= exclusion_rate <= 1
        ):
            raise ValueError("training split exclusion rate is invalid")
        _validate_class_counts(summary.get("unsupported_pixel_counts_by_canonical_label"))
        scene_counts = summary.get("retained_counts_by_scene_type")
        if not isinstance(scene_counts, Mapping) or not set(scene_counts).issubset(SCENE_TYPES):
            raise ValueError("retained scene counts must use controlled categories")
        if any(not isinstance(count, int) or isinstance(count, bool) or count < 0
               for count in scene_counts.values()):
            raise ValueError("retained scene counts are invalid")
    _validate_class_counts(metadata["unsupported_pixel_counts_by_canonical_label"])
    if (
        not isinstance(metadata["best_epoch"], int)
        or isinstance(metadata["best_epoch"], bool)
        or not 1 <= metadata["best_epoch"] <= metadata["epochs"]
        or not isinstance(metadata["best_validation_loss"], (int, float))
        or not math.isfinite(metadata["best_validation_loss"])
    ):
        raise ValueError("training metadata is missing complete checkpoint-selection provenance")


def _evaluation_metadata(report: object) -> dict[str, object]:
    evaluation = {
        key: _json_value(_field(report, key))
        for key in (
            "passed_thresholds",
            "test_split_sha256",
            "per_label_iou",
            "per_label_precision",
            "per_label_recall",
            "per_label_pixel_counts",
            "false_visual_cue_rate",
            "open_ground_component_coverage",
            "threshold_failures",
            "thresholds",
            "slice_metrics",
            "sample_counts",
            "unsupported_pixel_counts",
        )
    }
    if not _is_sha256(evaluation["test_split_sha256"]):
        raise ValueError("evaluation report is missing complete provenance or metrics")
    if evaluation["passed_thresholds"] is not True:
        raise ValueError("artifact export requires passing evaluation thresholds")
    if evaluation["threshold_failures"]:
        raise ValueError("passing evaluation cannot contain threshold failures")
    if not isinstance(evaluation["sample_counts"], Mapping):
        raise TypeError("evaluation sample_counts must be a mapping")
    evaluation["sample_counts"] = {
        key: value
        for key, value in evaluation["sample_counts"].items()
        if key in _SAMPLE_COUNT_FIELDS
    }
    for field in (
        "per_label_iou",
        "per_label_precision",
        "per_label_recall",
        "per_label_pixel_counts",
    ):
        if not isinstance(evaluation[field], Mapping):
            raise TypeError(f"evaluation {field} must be a mapping")
    if not isinstance(evaluation["slice_metrics"], Mapping):
        raise TypeError("evaluation slice_metrics must be a mapping")
    evaluation["slice_metrics"] = _sanitize_slice_metrics(evaluation["slice_metrics"])
    if not isinstance(evaluation["unsupported_pixel_counts"], Mapping) or not set(
        evaluation["unsupported_pixel_counts"]
    ).issubset(LABEL_IDS):
        raise ValueError("evaluation unsupported-pixel counts must use canonical labels")
    threshold_values = evaluation["thresholds"]
    if not isinstance(threshold_values, Mapping):
        raise TypeError("evaluation thresholds must be a mapping")
    required_thresholds = {
        "minimum_iou_by_label",
        "minimum_precision_by_label",
        "minimum_recall_by_label",
        "maximum_false_cue_rate",
        "maximum_false_cue_rate_regression",
        "maximum_metric_regression_by_label",
        "open_ground_component_overlap_iou",
        "minimum_open_ground_component_coverage",
        "maximum_open_ground_component_coverage_regression",
        "minimum_prediction_score",
        "minimum_samples_per_slice",
    }
    if set(threshold_values) != required_thresholds:
        raise ValueError("evaluation thresholds are incomplete")
    return evaluation


def _validate_class_counts(counts: object) -> None:
    if not isinstance(counts, Mapping) or not set(counts).issubset(LABEL_IDS):
        raise ValueError("unsupported pixel counts must use canonical class names")
    if any(not isinstance(count, int) or isinstance(count, bool) or count < 0
           for count in counts.values()):
        raise ValueError("unsupported pixel counts must be nonnegative integers")


def _sanitize_slice_metrics(slices: Mapping[str, Any]) -> dict[str, object]:
    if set(slices) != {*_SLICE_CATEGORIES, "source_group"}:
        raise ValueError("evaluation slices must use controlled categories")
    sanitized: dict[str, object] = {}
    for field, allowed_categories in _SLICE_CATEGORIES.items():
        values = slices[field]
        if not isinstance(values, Mapping) or not set(values).issubset(allowed_categories):
            raise ValueError("evaluation slices must use controlled categories")
        sanitized[field] = dict(values)
    group_summary = slices["source_group"]
    required_group_fields = {
        "group_count",
        "groups_meeting_minimum",
        "sample_count",
        "evaluated_sample_count",
        "ignore_containing_sample_count",
        "minimum_samples_per_group",
        "aggregate_per_label_metrics",
    }
    if not isinstance(group_summary, Mapping) or set(group_summary) != required_group_fields:
        raise ValueError("source-group evaluation must contain aggregate counts only")
    sanitized["source_group"] = dict(group_summary)
    return sanitized


def _aggregate_split_counts(
    training_metadata: Mapping[str, Any], evaluation: Mapping[str, object]
) -> dict[str, object]:
    splits = training_metadata["split_counts"]
    result: dict[str, object] = {}
    for split in ("train", "validation"):
        summary = splits.get(split)
        if not isinstance(summary, Mapping):
            raise TypeError("training split counts must be mappings")
        result[split] = {
            key: summary[key]
            for key in (
                "total_sample_count",
                "ignore_containing_sample_count",
                "loss_eligible_sample_count",
                "loss_excluded_sample_count",
                "exclusion_rate",
                "retained_counts_by_scene_type",
                "unsupported_pixel_counts_by_canonical_label",
            )
            if key in summary
        }
    sample_counts = evaluation.get("sample_counts")
    if not isinstance(sample_counts, Mapping):
        raise TypeError("evaluation sample_counts must be a mapping")
    result["test"] = {
        "total_sample_count": sample_counts.get("total", 0),
        "ignore_containing_sample_count": sample_counts.get("ignore_containing", 0),
        "evaluated_sample_count": sample_counts.get("evaluated", 0),
        "ignore_exclusion_rate": sample_counts.get("ignore_exclusion_rate", 0.0),
        "unsupported_pixel_counts_by_canonical_label": _field(
            evaluation, "unsupported_pixel_counts", {}
        ),
    }
    return result


def _validate_public_value(value: object, *, key: str = "") -> None:
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            normalized = str(child_key).lower()
            if (
                normalized in _PRIVATE_KEYS
                or "rights" in normalized
                or "attribution" in normalized
                or "url" in normalized
                or normalized.endswith(
                    ("_image_id", "_group_id", "_source_image_id", "image_ids", "group_ids", "source_image_ids")
                )
                or _PATH_KEY.search(normalized)
            ):
                raise ValueError("artifact metadata contains private or path metadata")
            _validate_public_value(child, key=normalized)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _validate_public_value(child, key=key)
    elif isinstance(value, str):
        windows_path = PureWindowsPath(value)
        if (
            Path(value).is_absolute()
            or windows_path.is_absolute()
            or value.startswith(("file:", "http://", "https://"))
        ):
            raise ValueError("artifact metadata contains private or path metadata")


def _model_files(checkpoint_path: Path) -> tuple[Path, ...]:
    files = tuple(sorted(path for path in checkpoint_path.iterdir() if path.is_file()))
    if not files or any(not _MODEL_FILE.fullmatch(path.name) for path in files):
        raise ValueError("checkpoint directory contains unsupported or non-model files")
    names = {path.name for path in files}
    if "config.json" not in names or "preprocessor_config.json" not in names or not any(
        name.endswith((".safetensors", ".bin")) for name in names
    ):
        raise ValueError("checkpoint must include model weights and both model/processor configs")
    for path in files:
        if path.suffix == ".json":
            try:
                _validate_public_value(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError("checkpoint configuration must be readable JSON") from exc
    return files


def _directory_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for file_path in sorted(item for item in path.iterdir() if item.is_file()):
        digest.update(file_path.name.encode("utf-8"))
        with file_path.open("rb") as source:
            while chunk := source.read(1024 * 1024):
                digest.update(chunk)
    return digest.hexdigest()


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-fA-F]{64}", value) is not None
