"""Rights-aware parsing and local validation for Scene Review datasets."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
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
RIGHTS_FIELDS = {
    "source_image_id",
    "source_page_url",
    "original_image_source",
    "original_image_creator",
    "image_license_name",
    "image_terms_evidence_url",
    "image_retrieval_evidence_url",
    "image_release_or_retrieval_id",
    "image_rights_evidence_scope",
    "image_rights_evidence_reference",
    "image_rights_review_status",
    "image_rights_reviewer",
    "image_rights_decision_date",
    "image_rights_decision_reason",
    "image_permitted_uses",
    "image_derived_weight_status",
    "image_derived_weight_restrictions",
    "image_attribution",
    "annotation_record_id",
    "annotation_provenance",
}


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
class DatasetValidationReport:
    image_count: int
    pixel_counts: dict[str, int]
    unsupported_pixel_counts: dict[str, int]
    run_mask_ignore_pixel_count: int
    run_mask_ignore_sample_count: int
    loss_eligible_sample_count: int
    loss_excluded_sample_count: int
    exclusion_rate: float
    scene_type_counts: dict[str, int]
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
    if (
        record.source_image_id not in record.image_rights_evidence_reference
        and record.source_page_url not in record.image_rights_evidence_reference
    ):
        raise ValueError("image rights evidence reference must identify/cover the source image")
    if (
        record.image_rights_evidence_scope == "shared_grant"
        and record.source_image_id not in record.image_rights_evidence_reference
        and record.source_page_url not in record.image_rights_evidence_reference
    ):
        raise ValueError("shared grant must expressly cover this image by source ID or page URL")
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


def validate_dataset(manifest: SceneDatasetManifest, data_root: Path) -> DatasetValidationReport:
    """Validate an approved local manifest and return aggregate counts without paths."""
    _validate_dataset_rights(manifest)
    if not isinstance(manifest.records, tuple) or not all(
        isinstance(record, SceneImageRecord) for record in manifest.records
    ):
        raise ValueError("records must be an array of SceneImageRecord objects")
    if not manifest.records:
        raise ValueError("manifest must contain at least one image record")

    image_ids: set[str] = set()
    pixel_counts = {**{label: 0 for label in LABEL_IDS}, "background": 0, "ignore": 0}
    unsupported_counts: Counter[str] = Counter()
    scene_type_counts: Counter[str] = Counter()
    ignore_pixel_count = 0
    ignore_sample_count = 0

    for record in manifest.records:
        if record.image_id in image_ids:
            raise ValueError("duplicate image_id in manifest")
        image_ids.add(record.image_id)
        _validate_record_rights(record, manifest)
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
        run_ignore_count = int(np.count_nonzero(canonical_mask == IGNORE_ID)) + sum(
            remapped.values()
        )
        ignore_pixel_count += run_ignore_count
        ignore_sample_count += int(run_ignore_count > 0)
        scene_type_counts[record.scene_type] += 1

    excluded = ignore_sample_count
    eligible = len(manifest.records) - excluded
    return DatasetValidationReport(
        image_count=len(manifest.records),
        pixel_counts=pixel_counts,
        unsupported_pixel_counts=dict(unsupported_counts),
        run_mask_ignore_pixel_count=ignore_pixel_count,
        run_mask_ignore_sample_count=ignore_sample_count,
        loss_eligible_sample_count=eligible,
        loss_excluded_sample_count=excluded,
        exclusion_rate=excluded / len(manifest.records),
        scene_type_counts=dict(scene_type_counts),
        warnings=(),
    )
