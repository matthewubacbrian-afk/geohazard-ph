"""Rights-aware parsing and local validation for Scene Review datasets."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import date, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from urllib.parse import urlparse

import numpy as np
from PIL import Image, UnidentifiedImageError

from ml.scene_review.labels import (
    BACKGROUND_ID,
    IGNORE_ID,
    LABEL_IDS,
    mask_for_supported_labels,
    validate_mask,
)

RIGHTS_STATUSES = {"approved", "pending_review", "excluded"}
REQUIRED_USES = {"training", "evaluation", "derived_weight_redistribution"}
SCENE_TYPES = frozenset({"indoor", "outdoor", "mixed", "unknown"})
SPLIT_NAMES = frozenset({"train", "validation", "test"})


@dataclass(frozen=True)
class SceneImageRecord:
    image_id: str
    image_path: str
    mask_path: str
    image_sha256: str
    mask_sha256: str
    group_id: str
    scene_type: str
    lighting: str
    occlusion: str
    image_quality: str
    source_image_id: str
    source_page_url: str
    original_image_source: str
    original_image_creator: str
    image_license_name: str
    image_terms_evidence_url: str
    image_retrieval_evidence_url: str
    image_release_or_retrieval_id: str
    image_rights_evidence_scope: str
    image_rights_evidence_reference: str
    image_rights_review_status: str
    image_rights_reviewer: str
    image_rights_decision_date: str
    image_rights_decision_reason: str
    image_permitted_uses: tuple[str, ...]
    image_derived_weight_status: str
    image_derived_weight_restrictions: str
    image_retention_limits: str | None
    image_attribution: str
    annotation_record_id: str
    annotation_provenance: str


@dataclass(frozen=True)
class SceneDatasetManifest:
    schema_version: int
    dataset_id: str
    source_url: str
    terms_evidence_url: str
    license_name: str
    retrieved_at: str
    retrieval_evidence_url: str
    immutable_release_or_retrieval_id: str
    rights_review_status: str
    rights_reviewer: str
    rights_decision_date: str
    rights_decision_reason: str
    permitted_uses: tuple[str, ...]
    derived_weight_status: str
    derived_weight_restrictions: str
    retention_limits: str
    attribution: str
    annotation_provenance: str
    label_schema_version: int
    supported_labels: tuple[str, ...]
    records: tuple[SceneImageRecord, ...]


@dataclass(frozen=True)
class SampleExclusionSummary:
    total_sample_count: int
    excluded_sample_count: int
    retained_sample_count: int
    exclusion_rate: float


@dataclass(frozen=True)
class GroupExclusionSummary:
    total_group_count: int
    retained_group_count: int
    excluded_group_count: int
    minimum_retained_samples_per_group: int
    maximum_retained_samples_per_group: int


@dataclass(frozen=True)
class SplitExclusionSummary(SampleExclusionSummary):
    scene_type_summaries: dict[str, SampleExclusionSummary]
    group_summaries: GroupExclusionSummary


@dataclass(frozen=True)
class SufficiencyPolicy:
    """Predeclared data-retention limits required before real training."""

    maximum_exclusion_rate: float
    minimum_retained_samples_by_split: Mapping[str, int]
    required_scene_types_by_split: Mapping[str, tuple[str, ...]]
    minimum_retained_samples_by_scene_type: Mapping[str, int]
    minimum_retained_groups_by_split: Mapping[str, int]
    minimum_retained_samples_per_group_by_split: Mapping[str, int]
    required_group_ids_by_split: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class DatasetValidationReport:
    image_count: int
    pixel_counts: dict[str, int]
    unsupported_pixel_counts: dict[str, int]
    unsupported_pixel_counts_by_split: dict[str, dict[str, int]]
    run_mask_ignore_pixel_count: int
    run_mask_ignore_sample_count: int
    loss_eligible_sample_count: int
    loss_excluded_sample_count: int
    exclusion_rate: float
    split_summaries: dict[str, SplitExclusionSummary]
    sufficiency_gate_passed: bool | None
    sufficiency_gate_reasons: tuple[str, ...]
    warnings: tuple[str, ...]


def _mapping_to_dataclass(data: Any, cls: type, *, optional_fields: set[str] | None = None):
    if not isinstance(data, dict):
        raise TypeError(f"{cls.__name__} must be a JSON object")
    allowed = {field.name for field in fields(cls)}
    unknown = set(data).difference(allowed)
    missing = allowed.difference(data)
    optional = optional_fields or set()
    missing.difference_update(optional)
    if unknown:
        raise ValueError(f"unknown fields in {cls.__name__}: {sorted(unknown)}")
    if missing:
        raise ValueError(f"missing fields in {cls.__name__}: {sorted(missing)}")
    values = dict(data)
    for field in fields(cls):
        if field.name in optional and field.name not in values:
            values[field.name] = None
    tuple_fields = {"image_permitted_uses", "permitted_uses", "supported_labels", "records"}
    for field_name in tuple_fields.intersection(values):
        value = values[field_name]
        if not isinstance(value, (list, tuple)):
            raise TypeError(f"{cls.__name__}.{field_name} must be a JSON array")
        values[field_name] = tuple(value)
    return cls(**values)


def load_manifest(path: Path) -> SceneDatasetManifest:
    """Load a strict JSON manifest and construct immutable record dataclasses."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("unable to read manifest JSON or file") from exc
    if not isinstance(data, dict):
        raise TypeError("manifest must be a JSON object")
    if not isinstance(data.get("records"), list):
        raise TypeError("SceneDatasetManifest.records must be a JSON array")
    records = tuple(
        _mapping_to_dataclass(item, SceneImageRecord, optional_fields={"image_retention_limits"})
        for item in data["records"]
    )
    data = dict(data)
    data["records"] = records
    return _mapping_to_dataclass(data, SceneDatasetManifest)


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be nonempty text")
    return value.strip()


def _valid_url(value: object, field_name: str) -> str:
    text = _required_text(value, field_name)
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{field_name} must be an HTTP(S) URL")
    return text


def _valid_date(value: object, field_name: str) -> None:
    text = _required_text(value, field_name)
    try:
        date.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO date") from exc


def _validate_use_set(uses: object, field_name: str) -> None:
    if not isinstance(uses, tuple) or not all(isinstance(use, str) for use in uses):
        raise ValueError(f"{field_name} must be a list of use names")
    missing = REQUIRED_USES.difference(uses)
    if missing:
        raise ValueError(f"{field_name} missing required use(s): {sorted(missing)}")


def _validate_rights_status(status: object, field_name: str) -> None:
    if not isinstance(status, str) or status not in RIGHTS_STATUSES:
        raise ValueError(f"{field_name} must be one of {sorted(RIGHTS_STATUSES)}")
    if status != "approved":
        raise ValueError(
            f"{field_name} must be approved; pending/excluded records cannot enter a training manifest"
        )


def _validate_approved_permission(status: object, restrictions: object, prefix: str) -> None:
    if not isinstance(status, str) or status != "permitted":
        raise ValueError(f"{prefix} derived_weight_status must be permitted")
    _required_text(restrictions, f"{prefix} derived_weight_restrictions")


def _validate_date_and_rights_decision(
    status: object, reviewer: object, decision_date: object, reason: object, prefix: str
) -> None:
    _validate_rights_status(status, f"{prefix} rights_review_status")
    _required_text(reviewer, f"{prefix} rights_reviewer")
    _valid_date(decision_date, f"{prefix} rights_decision_date")
    _required_text(reason, f"{prefix} rights_decision_reason")


def _validate_dataset_rights(manifest: SceneDatasetManifest) -> None:
    if not isinstance(manifest.schema_version, int) or isinstance(manifest.schema_version, bool):
        raise TypeError("manifest schema version must be an integer")
    if not isinstance(manifest.label_schema_version, int) or isinstance(
        manifest.label_schema_version, bool
    ):
        raise TypeError("label schema version must be an integer")
    _required_text(manifest.dataset_id, "dataset_id")
    _valid_url(manifest.source_url, "source_url")
    _valid_url(manifest.terms_evidence_url, "terms_evidence_url")
    _required_text(manifest.license_name, "license_name")
    _valid_url(manifest.retrieval_evidence_url, "retrieval_evidence_url")
    _required_text(manifest.immutable_release_or_retrieval_id, "immutable_release_or_retrieval_id")
    _required_text(manifest.retention_limits, "retention_limits")
    _required_text(manifest.attribution, "attribution")
    _required_text(manifest.annotation_provenance, "annotation_provenance")
    _validate_date_and_rights_decision(
        manifest.rights_review_status,
        manifest.rights_reviewer,
        manifest.rights_decision_date,
        manifest.rights_decision_reason,
        "dataset",
    )
    _validate_use_set(manifest.permitted_uses, "permitted_uses")
    _validate_approved_permission(
        manifest.derived_weight_status, manifest.derived_weight_restrictions, "dataset"
    )
    try:
        datetime.fromisoformat(manifest.retrieved_at)
    except (AttributeError, ValueError) as exc:
        raise ValueError("retrieved_at must be an ISO timestamp") from exc
    if manifest.label_schema_version != 2:
        raise ValueError("label schema version must be 2 (scene-review-v2)")
    if manifest.schema_version != 1:
        raise ValueError("manifest schema version must be 1")
    if not isinstance(manifest.supported_labels, tuple) or not all(
        isinstance(label, str) for label in manifest.supported_labels
    ):
        raise ValueError("supported_labels must be a list of label names")
    if len(set(manifest.supported_labels)) != len(manifest.supported_labels):
        raise ValueError("supported_labels must not contain duplicates")
    unknown = set(manifest.supported_labels).difference(LABEL_IDS)
    if unknown:
        raise ValueError(f"unknown labels in supported_labels: {sorted(unknown)}")


def _validate_record_rights(record: SceneImageRecord, manifest: SceneDatasetManifest) -> None:
    _validate_date_and_rights_decision(
        record.image_rights_review_status,
        record.image_rights_reviewer,
        record.image_rights_decision_date,
        record.image_rights_decision_reason,
        "image",
    )
    for field_name in (
        "image_id",
        "image_path",
        "mask_path",
        "group_id",
        "scene_type",
        "lighting",
        "occlusion",
        "image_quality",
        "source_image_id",
        "original_image_source",
        "original_image_creator",
        "image_license_name",
        "image_release_or_retrieval_id",
        "image_rights_evidence_scope",
        "image_rights_evidence_reference",
        "image_attribution",
        "annotation_record_id",
        "annotation_provenance",
    ):
        _required_text(getattr(record, field_name), f"image {field_name}")
    _valid_url(record.source_page_url, "source_page_url")
    _valid_url(record.image_terms_evidence_url, "image_terms_evidence_url")
    _valid_url(record.image_retrieval_evidence_url, "image_retrieval_evidence_url")
    if record.image_retention_limits is not None and not isinstance(
        record.image_retention_limits, str
    ):
        raise ValueError("image_retention_limits must be text or null")
    _validate_use_set(record.image_permitted_uses, "image_permitted_uses")
    _validate_approved_permission(
        record.image_derived_weight_status, record.image_derived_weight_restrictions, "image"
    )
    if record.image_rights_evidence_scope not in {"image_specific", "shared_grant"}:
        raise ValueError("image_rights_evidence_scope must be image_specific or shared_grant")
    evidence_covers_image = (
        record.source_image_id in record.image_rights_evidence_reference
        or record.source_page_url in record.image_rights_evidence_reference
    )
    if not evidence_covers_image:
        if record.image_rights_evidence_scope == "shared_grant":
            raise ValueError("shared grant must expressly cover this image by source ID or page URL")
        raise ValueError("image-specific rights evidence must identify the source image")
    if record.image_retention_limits is None:
        if (
            record.image_terms_evidence_url != manifest.terms_evidence_url
            or record.image_license_name != manifest.license_name
        ):
            raise ValueError("image-specific retention limits are required when image terms differ")
    else:
        _required_text(record.image_retention_limits, "image_retention_limits")
    for key, value in (("image_sha256", record.image_sha256), ("mask_sha256", record.mask_sha256)):
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-fA-F]{64}", value) is None:
            raise ValueError(f"{key} must be a 64-character SHA-256 hex digest")


def _safe_local_file(data_root: Path, relative_path: str) -> Path:
    windows_path = PureWindowsPath(relative_path)
    posix_path = PurePosixPath(relative_path)
    if (
        windows_path.is_absolute()
        or windows_path.drive
        or posix_path.is_absolute()
        or ".." in posix_path.parts
    ):
        raise ValueError("manifest image/mask path must be a safe relative path")
    candidate = (data_root / Path(*posix_path.parts)).resolve()
    root = data_root.resolve()
    if candidate == root or root not in candidate.parents:
        raise ValueError("manifest image/mask path escapes data root")
    if not candidate.is_file():
        raise ValueError("manifest image/mask file does not exist")
    return candidate


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_image(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            if image.format not in {"JPEG", "PNG"}:
                raise ValueError("image must be JPEG or PNG")
            image.load()
            return image.size
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError("image is not a readable JPEG or PNG") from exc


def _read_indexed_mask(path: Path) -> np.ndarray:
    try:
        with Image.open(path) as image:
            if image.format != "PNG" or image.mode not in {"L", "P", "I", "I;16", "I;16B", "I;16L"}:
                raise ValueError("mask must be an indexed/single-channel PNG")
            image.load()
            return np.asarray(image).copy()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError("mask is not a readable PNG") from exc


def _validate_sufficiency_policy(policy: SufficiencyPolicy) -> None:
    if (
        not isinstance(policy.maximum_exclusion_rate, (float, int))
        or isinstance(policy.maximum_exclusion_rate, bool)
        or not 0 <= policy.maximum_exclusion_rate <= 1
    ):
        raise ValueError("maximum_exclusion_rate must be between 0 and 1")
    if set(policy.minimum_retained_samples_by_split) != SPLIT_NAMES:
        raise ValueError("sufficiency policy must declare minimums for train, validation, and test")
    if set(policy.required_scene_types_by_split) != SPLIT_NAMES:
        raise ValueError("sufficiency policy must declare scene coverage for every split")
    if set(policy.minimum_retained_groups_by_split) != SPLIT_NAMES:
        raise ValueError("sufficiency policy must declare group minimums for every split")
    if set(policy.minimum_retained_samples_per_group_by_split) != SPLIT_NAMES:
        raise ValueError(
            "sufficiency policy must declare per-group sample minimums for every split"
        )
    if set(policy.required_group_ids_by_split) != SPLIT_NAMES:
        raise ValueError("sufficiency policy must declare required group coverage for every split")
    for count in policy.minimum_retained_samples_by_split.values():
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("split minimum retained sample counts must be positive integers")
    for scene_types in policy.required_scene_types_by_split.values():
        if (
            not isinstance(scene_types, tuple)
            or not scene_types
            or not all(isinstance(scene_type, str) for scene_type in scene_types)
        ):
            raise ValueError("each split must declare at least one required scene type")
        if not set(scene_types).issubset(SCENE_TYPES):
            raise ValueError("required scene types must use controlled categories")
    if not set(policy.minimum_retained_samples_by_scene_type).issubset(SCENE_TYPES):
        raise ValueError("minimum-count scene types must use controlled categories")
    for count in policy.minimum_retained_samples_by_scene_type.values():
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("scene type minimum retained sample counts must be positive integers")
    for count in policy.minimum_retained_groups_by_split.values():
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("split minimum retained group counts must be positive integers")
    for count in policy.minimum_retained_samples_per_group_by_split.values():
        if not isinstance(count, int) or isinstance(count, bool) or count < 1:
            raise ValueError("per-group minimum retained sample counts must be positive integers")
    for group_ids in policy.required_group_ids_by_split.values():
        if not isinstance(group_ids, tuple) or not all(
            isinstance(group_id, str) and group_id.strip() for group_id in group_ids
        ):
            raise ValueError("required group IDs must be tuples of nonempty text")


def _summary(total: int, excluded: int) -> SampleExclusionSummary:
    return SampleExclusionSummary(
        total_sample_count=total,
        excluded_sample_count=excluded,
        retained_sample_count=total - excluded,
        exclusion_rate=excluded / total if total else 0.0,
    )


def _sufficiency_failures(
    summaries: Mapping[str, SplitExclusionSummary],
    policy: SufficiencyPolicy,
    retained_group_ids_by_split: Mapping[str, set[str]],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for split in sorted(SPLIT_NAMES):
        summary = summaries[split]
        if summary.exclusion_rate > policy.maximum_exclusion_rate:
            reasons.append(f"{split} exclusion rate exceeds declared maximum")
        if summary.retained_sample_count < policy.minimum_retained_samples_by_split[split]:
            reasons.append(f"{split} minimum retained sample count not met")
        groups = summary.group_summaries
        if groups.retained_group_count < policy.minimum_retained_groups_by_split[split]:
            reasons.append(f"{split} minimum retained group count not met")
        if groups.total_group_count and (
            groups.minimum_retained_samples_per_group
            < policy.minimum_retained_samples_per_group_by_split[split]
        ):
            reasons.append(f"{split} per-group retained sample minimum not met")
        required_groups = set(policy.required_group_ids_by_split[split])
        # Group identifiers are used locally for this decision and never included in output.
        if required_groups and not required_groups.issubset(
            retained_group_ids_by_split.get(split, set())
        ):
            reasons.append(f"{split} required group coverage not met")
        retained_scene_types = {
            scene_type
            for scene_type, scene_summary in summary.scene_type_summaries.items()
            if scene_summary.retained_sample_count > 0
        }
        missing_scene_types = set(policy.required_scene_types_by_split[split]).difference(
            retained_scene_types
        )
        if missing_scene_types:
            reasons.append(f"{split} required scene coverage not met")
    for scene_type, minimum in policy.minimum_retained_samples_by_scene_type.items():
        retained_count = sum(
            summary.scene_type_summaries.get(scene_type, _summary(0, 0)).retained_sample_count
            for summary in summaries.values()
        )
        if retained_count < minimum:
            reasons.append(f"{scene_type} minimum retained sample count not met")
    return tuple(reasons)


def validate_dataset(
    manifest: SceneDatasetManifest,
    data_root: Path,
    *,
    split_by_image_id: Mapping[str, str] | None = None,
    sufficiency_policy: SufficiencyPolicy | None = None,
) -> DatasetValidationReport:
    """Validate local data and report aggregate counts; no gate is implied by omission."""
    _validate_dataset_rights(manifest)
    if not isinstance(manifest.records, tuple) or not all(
        isinstance(record, SceneImageRecord) for record in manifest.records
    ):
        raise ValueError("records must be an array of SceneImageRecord objects")
    if not manifest.records:
        raise ValueError("manifest must contain at least one image record")

    if split_by_image_id is None:
        if sufficiency_policy is not None:
            raise ValueError("split assignments are required to evaluate the sufficiency policy")
        split_assignments = {record.image_id: "unsplit" for record in manifest.records}
    else:
        image_ids = {record.image_id for record in manifest.records}
        if not all(
            isinstance(image_id, str) and isinstance(split, str)
            for image_id, split in split_by_image_id.items()
        ):
            raise ValueError("split assignments must map image IDs to split names")
        if set(split_by_image_id) != image_ids:
            raise ValueError("split assignments must cover each manifest record exactly once")
        if not set(split_by_image_id.values()).issubset(SPLIT_NAMES):
            raise ValueError("split assignments must use train, validation, or test")
        split_assignments = dict(split_by_image_id)

    if sufficiency_policy is not None:
        _validate_sufficiency_policy(sufficiency_policy)
        if split_by_image_id is None:
            raise ValueError("split assignments are required to evaluate the sufficiency policy")

    image_ids: set[str] = set()
    pixel_counts = {**{label: 0 for label in LABEL_IDS}, "background": 0, "ignore": 0}
    unsupported_counts: Counter[str] = Counter()
    unsupported_counts_by_split: dict[str, Counter[str]] = {}
    split_totals: Counter[str] = Counter()
    split_exclusions: Counter[str] = Counter()
    split_scene_totals: dict[str, Counter[str]] = {}
    split_scene_exclusions: dict[str, Counter[str]] = {}
    split_group_retained: dict[str, Counter[str]] = {}
    split_group_totals: dict[str, Counter[str]] = {}
    group_splits: dict[str, str] = {}
    ignore_pixel_count = 0
    ignore_sample_count = 0

    for record in manifest.records:
        if record.image_id in image_ids:
            raise ValueError("duplicate image_id in manifest")
        image_ids.add(record.image_id)
        _validate_record_rights(record, manifest)
        if record.scene_type not in SCENE_TYPES:
            raise ValueError("scene_type must use one of the controlled categories")
        image_path = _safe_local_file(data_root, record.image_path)
        mask_path = _safe_local_file(data_root, record.mask_path)
        if _file_sha256(image_path) != record.image_sha256.lower():
            raise ValueError("image SHA-256 hash mismatch")
        if _file_sha256(mask_path) != record.mask_sha256.lower():
            raise ValueError("mask SHA-256 hash mismatch")
        image_size = _read_image(image_path)
        canonical_mask = _read_indexed_mask(mask_path)
        validate_mask(canonical_mask, set(manifest.supported_labels))
        if image_size != (canonical_mask.shape[1], canonical_mask.shape[0]):
            raise ValueError("image/mask dimension mismatch")

        for label, mask_id in LABEL_IDS.items():
            pixel_counts[label] += int(np.count_nonzero(canonical_mask == mask_id))
        pixel_counts["background"] += int(np.count_nonzero(canonical_mask == BACKGROUND_ID))
        pixel_counts["ignore"] += int(np.count_nonzero(canonical_mask == IGNORE_ID))
        _, remapped = mask_for_supported_labels(canonical_mask, set(manifest.supported_labels))
        unsupported_counts.update(remapped)
        split = split_assignments[record.image_id]
        unsupported_counts_by_split.setdefault(split, Counter()).update(remapped)
        run_ignore_count = int(np.count_nonzero(canonical_mask == IGNORE_ID)) + sum(
            remapped.values()
        )
        ignore_pixel_count += run_ignore_count
        ignore_sample_count += int(run_ignore_count > 0)
        previous_split = group_splits.setdefault(record.group_id, split)
        if previous_split != split:
            raise ValueError("scene group records must remain in a single data split")
        split_totals[split] += 1
        split_scene_totals.setdefault(split, Counter())[record.scene_type] += 1
        split_group_totals.setdefault(split, Counter())[record.group_id] += 1
        if run_ignore_count == 0:
            split_group_retained.setdefault(split, Counter())[record.group_id] += 1
        if run_ignore_count > 0:
            split_exclusions[split] += 1
            split_scene_exclusions.setdefault(split, Counter())[record.scene_type] += 1

    excluded = ignore_sample_count
    eligible = len(manifest.records) - excluded
    split_summaries: dict[str, SplitExclusionSummary] = {}
    for split, total_count in split_totals.items():
        excluded_count = split_exclusions[split]
        scene_summaries = {
            scene_type: _summary(
                split_scene_totals[split][scene_type],
                split_scene_exclusions.get(split, Counter())[scene_type],
            )
            for scene_type in sorted(SCENE_TYPES)
        }
        group_counts = split_group_totals.get(split, Counter())
        retained_by_group = split_group_retained.get(split, Counter())
        retained_group_values = [retained_by_group[group_id] for group_id in group_counts]
        group_summaries = GroupExclusionSummary(
            total_group_count=len(group_counts),
            retained_group_count=sum(count > 0 for count in retained_group_values),
            excluded_group_count=sum(count == 0 for count in retained_group_values),
            minimum_retained_samples_per_group=min(retained_group_values, default=0),
            maximum_retained_samples_per_group=max(retained_group_values, default=0),
        )
        split_summaries[split] = SplitExclusionSummary(
            **_summary(total_count, excluded_count).__dict__,
            scene_type_summaries=scene_summaries,
            group_summaries=group_summaries,
        )
    gate_reasons: tuple[str, ...] = ()
    gate_passed: bool | None = None
    if sufficiency_policy is not None:
        for split in sorted(SPLIT_NAMES):
            split_summaries.setdefault(
                split,
                SplitExclusionSummary(
                    **_summary(0, 0).__dict__,
                    scene_type_summaries={},
                    group_summaries=GroupExclusionSummary(0, 0, 0, 0, 0),
                ),
            )
        retained_group_ids = {
            split: {group_id for group_id, count in counts.items() if count > 0}
            for split, counts in split_group_retained.items()
        }
        gate_reasons = _sufficiency_failures(
            split_summaries, sufficiency_policy, retained_group_ids
        )
        gate_passed = not gate_reasons
    return DatasetValidationReport(
        image_count=len(manifest.records),
        pixel_counts=pixel_counts,
        unsupported_pixel_counts=dict(unsupported_counts),
        unsupported_pixel_counts_by_split={
            split: dict(counts) for split, counts in unsupported_counts_by_split.items()
        },
        run_mask_ignore_pixel_count=ignore_pixel_count,
        run_mask_ignore_sample_count=ignore_sample_count,
        loss_eligible_sample_count=eligible,
        loss_excluded_sample_count=excluded,
        exclusion_rate=excluded / len(manifest.records),
        split_summaries=split_summaries,
        sufficiency_gate_passed=gate_passed,
        sufficiency_gate_reasons=gate_reasons,
        warnings=(
            ("sufficiency gate undeclared; this count report does not authorize training",)
            if sufficiency_policy is None
            else ()
        ),
    )
