from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ml.clean_merge import load_and_merge_sources
from ml.regions import DEFAULT_REGIONS_PATH, MAX_OFFSHORE_KM, assign_regions
from ml.train import _input_file_record, _validated_source_paths


@dataclass(frozen=True)
class VerifiedInputs:
    metadata: dict[str, object]
    profiles: list[dict[str, object]]
    features: pd.DataFrame
    assigned_rows: list[dict[str, object]]


def _read_json(path: Path, expected_type: type) -> object:
    if not path.is_file():
        raise ValueError(f"Required artifact file not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid artifact JSON: {path}") from exc
    if not isinstance(value, expected_type):
        raise ValueError(f"Unexpected artifact JSON shape: {path}")
    return value


def _load_verified_inputs(
    artifact_dir: Path,
    phivolcs_paths: list[Path],
    usgs_paths: list[Path],
) -> VerifiedInputs:
    phivolcs_paths, usgs_paths = _validated_source_paths(phivolcs_paths, usgs_paths)
    metadata = _read_json(artifact_dir / "metadata.json", dict)
    if not isinstance(metadata.get("model_version"), str) or not metadata["model_version"]:
        raise ValueError("metadata.model_version is missing or malformed.")
    profiles = _read_json(artifact_dir / "risk_profiles.json", list)
    feature_path = artifact_dir / "region_features.csv"
    if not feature_path.is_file():
        raise ValueError(f"Required artifact file not found: {feature_path}")
    try:
        features = pd.read_csv(feature_path)
    except (OSError, pd.errors.ParserError) as exc:
        raise ValueError(f"Invalid region_features.csv: {feature_path}") from exc

    expected_files = metadata.get("input_files")
    actual_files = [
        _input_file_record(path, source)
        for source, paths in (("phivolcs", phivolcs_paths), ("usgs", usgs_paths))
        for path in paths
    ]
    if not isinstance(expected_files, list) or sorted(expected_files, key=str) != sorted(
        actual_files, key=str
    ):
        raise ValueError("input_files do not match the saved source hashes and sizes.")

    assignment_metadata = metadata.get("region_assignment")
    if not isinstance(assignment_metadata, dict):
        raise ValueError("region_assignment metadata is missing or malformed.")
    boundary_hash = hashlib.sha256(DEFAULT_REGIONS_PATH.read_bytes()).hexdigest()
    if assignment_metadata.get("boundary_sha256") != boundary_hash:
        raise ValueError("region_assignment.boundary_sha256 does not match the boundary asset.")
    if assignment_metadata.get("max_offshore_km") != MAX_OFFSHORE_KM:
        raise ValueError("region_assignment.max_offshore_km is unsupported.")

    merged_rows, source_reports = load_and_merge_sources(phivolcs_paths, usgs_paths)
    actual_reports = {
        source: {"accepted": report.accepted_rows, "rejected": report.rejected_rows}
        for source, report in source_reports.items()
    }
    if metadata.get("source_reports") != actual_reports:
        raise ValueError("source_reports do not match the saved source counts.")
    assignment = assign_regions(merged_rows, max_offshore_km=MAX_OFFSHORE_KM)
    if assignment_metadata.get("assigned_by_source") != assignment.assigned_by_source:
        raise ValueError("region_assignment.assigned_by_source does not match saved counts.")
    if assignment_metadata.get("excluded_by_source") != assignment.unassigned_by_source:
        raise ValueError("region_assignment.excluded_by_source does not match saved counts.")

    if not all(isinstance(profile, dict) for profile in profiles):
        raise ValueError("risk_profiles.json contains a malformed profile.")
    profile_names = [profile.get("region_name") for profile in profiles]
    if len(profile_names) != len(set(profile_names)):
        raise ValueError("risk_profiles.json has duplicate region_name values.")
    if "region_name" not in features:
        raise ValueError("region_features.csv is missing region_name.")
    feature_names = features["region_name"].tolist()
    if len(feature_names) != len(set(feature_names)) or set(feature_names) != set(profile_names):
        raise ValueError("region_features.csv region_name values do not match profiles.")
    return VerifiedInputs(metadata, profiles, features, assignment.rows)


def build_validation_report(
    artifact_dir: Path,
    phivolcs_paths: list[Path],
    usgs_paths: list[Path],
) -> dict[str, object]:
    verified = _load_verified_inputs(artifact_dir, phivolcs_paths, usgs_paths)
    return {
        "artifact_version": verified.metadata.get("model_version"),
        "input_files": verified.metadata["input_files"],
        "review_state": "requires_domain_review",
    }
