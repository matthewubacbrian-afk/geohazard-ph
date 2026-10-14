from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ml.clean_merge import load_and_merge_sources
from ml.clustering import fit_kmeans
from ml.features import RegionFeatures, build_region_features
from ml.regions import DEFAULT_REGIONS_PATH, MAX_OFFSHORE_KM, assign_regions
from ml.train import _input_file_record, _validated_source_paths


@dataclass(frozen=True)
class VerifiedInputs:
    metadata: dict[str, object]
    profiles: list[dict[str, object]]
    features: pd.DataFrame
    assigned_rows: list[dict[str, object]]


def _utc_timestamp(value: object) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("assigned event has invalid occurred_at") from exc
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        raise ValueError("assigned event has invalid occurred_at")
    return timestamp.tz_convert("UTC")


def _coverage(assigned_rows: list[dict[str, object]]) -> dict[str, object]:
    sources = ("phivolcs", "usgs")
    timed_rows: list[tuple[str, str, pd.Timestamp]] = []
    for row in assigned_rows:
        source = str(row["source"])
        if source not in sources:
            raise ValueError(f"assigned event has unsupported source: {source}")
        timed_rows.append((str(row["region_name"]), source, _utc_timestamp(row["occurred_at"])))

    source_coverage: dict[str, dict[str, object]] = {}
    source_spans: dict[str, tuple[pd.Timestamp, pd.Timestamp]] = {}
    for source in sources:
        times = [time for _, event_source, time in timed_rows if event_source == source]
        if times:
            source_spans[source] = (min(times), max(times))
        source_coverage[source] = {
            "assigned_count": len(times),
            "first_occurred_at": min(times).isoformat() if times else None,
            "last_occurred_at": max(times).isoformat() if times else None,
        }

    window_start = max((span[0] for span in source_spans.values()), default=None)
    window_end = min((span[1] for span in source_spans.values()), default=None)
    available = len(source_spans) == len(sources) and window_start <= window_end
    shared_window = {
        "start": window_start.isoformat() if available else None,
        "end": window_end.isoformat() if available else None,
        "available": available,
        "unavailable_reason": None if available else "no_shared_observation_window",
    }

    regions: list[dict[str, object]] = []
    for region_name in sorted({name for name, _, _ in timed_rows}):
        by_source = {
            source: [
                time
                for name, event_source, time in timed_rows
                if name == region_name and event_source == source
            ]
            for source in sources
        }
        regions.append({
            "region_name": region_name,
            "assigned_by_source": {source: len(times) for source, times in by_source.items()},
            "first_occurred_at_by_source": {
                source: min(times).isoformat() if times else None
                for source, times in by_source.items()
            },
            "last_occurred_at_by_source": {
                source: max(times).isoformat() if times else None
                for source, times in by_source.items()
            },
            "shared_window_count_by_source": {
                source: sum(window_start <= time <= window_end for time in times) if available else 0
                for source, times in by_source.items()
            },
        })
    return {
        "source_coverage": source_coverage,
        "shared_window": shared_window,
        "regions": regions,
    }


def _saved_features(frame: pd.DataFrame) -> list[RegionFeatures]:
    columns = (
        "region_name", "event_count", "mean_magnitude", "max_magnitude",
        "mean_depth_km", "event_density",
    )
    missing = set(columns).difference(frame.columns)
    if missing:
        raise ValueError(f"region_features.csv is missing columns: {', '.join(sorted(missing))}")
    try:
        return [
            RegionFeatures(
                region_name=str(row.region_name),
                event_count=int(row.event_count),
                mean_magnitude=float(row.mean_magnitude),
                max_magnitude=float(row.max_magnitude),
                mean_depth_km=float(row.mean_depth_km),
                event_density=float(row.event_density),
            )
            for row in frame.loc[:, columns].sort_values("region_name").itertuples(index=False)
        ]
    except (TypeError, ValueError) as exc:
        raise ValueError("region_features.csv has invalid feature values.") from exc


def _label_stability(
    saved_features: list[RegionFeatures],
    saved_labels: dict[str, str],
    shared_rows: list[dict[str, object]],
) -> dict[str, object]:
    names = sorted(saved_labels)
    if {row.region_name for row in saved_features} != set(names):
        raise ValueError("Saved feature regions do not match saved labels.")
    shared_features = list(build_region_features(shared_rows).values())
    shared_features.sort(key=lambda row: row.region_name)
    shared_refit: dict[str, object] = {
        "included_regions": [row.region_name for row in shared_features],
        "labels": None,
        "change_count": None,
        "unavailable_reason": "insufficient_regions",
    }
    if len(shared_features) >= 2:
        labels = fit_kmeans(shared_features, random_state=42).risk_labels
        shared_refit.update({
            "labels": labels,
            "change_count": sum(labels[name] != saved_labels[name] for name in labels),
            "unavailable_reason": None,
        })

    seed_changes = {name: 0 for name in names}
    seed_fits: list[dict[str, object]] = []
    for seed in range(20):
        labels = fit_kmeans(saved_features, random_state=seed).risk_labels
        changed = sorted(name for name in names if labels[name] != saved_labels[name])
        seed_fits.append({"seed": seed, "included_regions": names, "changed_regions": changed})
        for name in changed:
            seed_changes[name] += 1

    leave_changes = {name: 0 for name in names}
    comparisons = {name: 0 for name in names}
    leave_fits: list[dict[str, object]] = []
    for omitted in names:
        retained = [row for row in saved_features if row.region_name != omitted]
        included = [row.region_name for row in retained]
        if len(retained) < 2:
            leave_fits.append({
                "omitted_region": omitted,
                "included_regions": included,
                "changed_regions": None,
                "unavailable_reason": "insufficient_regions",
            })
            continue
        labels = fit_kmeans(retained, random_state=42).risk_labels
        changed = sorted(name for name in included if labels[name] != saved_labels[name])
        leave_fits.append({
            "omitted_region": omitted,
            "included_regions": included,
            "changed_regions": changed,
            "unavailable_reason": None,
        })
        for name in included:
            comparisons[name] += 1
        for name in changed:
            leave_changes[name] += 1

    return {
        "saved_labels": dict(sorted(saved_labels.items())),
        "shared_window_refit": shared_refit,
        "seed_sweep": {
            "seeds": list(range(20)),
            "fit_count": len(seed_fits),
            "included_regions": names,
            "change_count_by_region": seed_changes,
            "fits": seed_fits,
        },
        "leave_one_region_out": {
            "fit_count": sum(fit["unavailable_reason"] is None for fit in leave_fits),
            "comparisons_per_region": comparisons,
            "change_count_by_region": leave_changes,
            "fits": leave_fits,
        },
    }


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
    coverage = _coverage(verified.assigned_rows)
    window = coverage["shared_window"]
    shared_rows = []
    if window["available"]:
        start = _utc_timestamp(window["start"])
        end = _utc_timestamp(window["end"])
        shared_rows = [
            row for row in verified.assigned_rows
            if start <= _utc_timestamp(row["occurred_at"]) <= end
        ]
    saved_labels = {str(profile["region_name"]): str(profile["label"]) for profile in verified.profiles}
    return {
        "artifact_version": verified.metadata.get("model_version"),
        "input_files": verified.metadata["input_files"],
        **coverage,
        "label_stability": _label_stability(
            _saved_features(verified.features), saved_labels, shared_rows
        ),
        "review_state": "requires_domain_review",
    }
