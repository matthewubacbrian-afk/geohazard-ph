from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from ml.clean_merge import load_and_merge_sources
from ml.clustering import fit_kmeans
from ml.features import RegionFeatures, build_region_features
from ml.regions import DEFAULT_REGIONS_PATH, MAX_OFFSHORE_KM, assign_regions
from ml.train import _input_file_record, _validated_source_paths

REFIT_K_CANDIDATES = (3, 4, 5)
REFIT_RANDOM_STATE = 42


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
        labels = fit_kmeans(
            shared_features, k_values=REFIT_K_CANDIDATES, random_state=REFIT_RANDOM_STATE
        ).risk_labels
        shared_refit.update({
            "labels": labels,
            "change_count": sum(labels[name] != saved_labels[name] for name in labels),
            "unavailable_reason": None,
        })

    seed_changes = {name: 0 for name in names}
    seed_fits: list[dict[str, object]] = []
    for seed in range(20):
        labels = fit_kmeans(
            saved_features, k_values=REFIT_K_CANDIDATES, random_state=seed
        ).risk_labels
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
        labels = fit_kmeans(
            retained, k_values=REFIT_K_CANDIDATES, random_state=REFIT_RANDOM_STATE
        ).risk_labels
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
        "comparison_parameters": {
            "k_candidates": list(REFIT_K_CANDIDATES),
            "shared_window_random_state": REFIT_RANDOM_STATE,
            "seed_sweep_random_states": list(range(20)),
            "leave_one_region_out_random_state": REFIT_RANDOM_STATE,
            "baseline_training_k_candidates": None,
            "baseline_training_random_state": None,
            "parameter_match_verified": False,
        },
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


def _sparse_region_sensitivity(
    region_coverage: list[dict[str, object]],
    saved_labels: dict[str, str],
    shared_features: list[RegionFeatures],
) -> dict[str, object]:
    names = sorted(saved_labels)
    coverage_by_name: dict[str, int] = {}
    for region in region_coverage:
        name = region.get("region_name")
        if not isinstance(name, str) or name not in saved_labels:
            raise ValueError("Coverage includes a region absent from saved labels.")
        if name in coverage_by_name:
            raise ValueError(f"Coverage repeats region: {name}")

        source_counts = region.get("shared_window_count_by_source")
        if not isinstance(source_counts, dict):
            raise ValueError(  # noqa: TRY004
                f"Coverage counts are missing for region: {name}"
            )
        values = [source_counts.get(source) for source in ("phivolcs", "usgs")]
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in values
        ):
            raise ValueError(f"Coverage counts are invalid for region: {name}")
        coverage_by_name[name] = sum(values)

    features_by_name: dict[str, RegionFeatures] = {}
    for feature in shared_features:
        name = feature.region_name
        if name not in saved_labels or name in features_by_name:
            raise ValueError(f"Shared-window features have an invalid region: {name}")
        features_by_name[name] = feature

    counts = {name: coverage_by_name.get(name, 0) for name in names}
    for name, feature in features_by_name.items():
        if feature.event_count != counts[name]:
            raise ValueError(f"Shared-window count does not match features for region: {name}")
    if any(count > 0 and name not in features_by_name for name, count in counts.items()):
        raise ValueError("Positive shared-window count has no feature row.")

    thresholds = [0, *sorted({count + 1 for count in counts.values()})]
    scenarios: list[dict[str, object]] = []
    for threshold in thresholds:
        included = sorted(
            name for name in names
            if name in features_by_name and counts[name] >= threshold
        )
        excluded = sorted(set(names).difference(included))
        reasons = {
            name: (
                "no_shared_window_observations"
                if name not in features_by_name
                else "below_minimum_event_count"
            )
            for name in excluded
        }
        labels = None
        changed = None
        change_count = None
        unavailable_reason = "insufficient_regions"
        if len(included) >= 2:
            rows = [features_by_name[name] for name in included]
            labels = fit_kmeans(
                rows,
                k_values=REFIT_K_CANDIDATES,
                random_state=REFIT_RANDOM_STATE,
            ).risk_labels
            labels = dict(sorted(labels.items()))
            changed = sorted(name for name in included if labels[name] != saved_labels[name])
            change_count = len(changed)
            unavailable_reason = None
        scenarios.append({
            "minimum_shared_window_events": threshold,
            "included_regions": included,
            "excluded_regions": excluded,
            "exclusion_reason_by_region": reasons,
            "labels": labels,
            "changed_regions": changed,
            "change_count": change_count,
            "unavailable_reason": unavailable_reason,
        })

    return {
        "count_basis": "combined_sources_in_shared_window",
        "thresholds_are_policy": False,
        "comparison_parameters": {
            "k_candidates": list(REFIT_K_CANDIDATES),
            "random_state": REFIT_RANDOM_STATE,
            "parameter_match_verified": False,
        },
        "scenarios": scenarios,
    }


def _read_json(path: Path, expected_type: type) -> object:
    if not path.is_file():
        raise ValueError(f"Required artifact file not found: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Invalid artifact JSON: {path}") from exc
    if not isinstance(value, expected_type):
        raise ValueError(f"Unexpected artifact JSON shape: {path}")  # noqa: TRY004
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
        raise ValueError("region_assignment metadata is missing or malformed.")  # noqa: TRY004
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
        "boundary_sha256": verified.metadata["region_assignment"]["boundary_sha256"],
        "assignment_rule": {
            "max_offshore_km": verified.metadata["region_assignment"]["max_offshore_km"],
            "assigned_by_source": verified.metadata["region_assignment"]["assigned_by_source"],
            "excluded_by_source": verified.metadata["region_assignment"]["excluded_by_source"],
        },
        **coverage,
        "label_stability": _label_stability(
            _saved_features(verified.features), saved_labels, shared_rows
        ),
        "review_state": "requires_domain_review",
        "limitations": [
            "A shared date window does not equalize catalog completeness or magnitude thresholds.",
            "Event density is a coordinate-spread proxy, not events per square kilometer.",
            "Classifier accuracy and confidence are in-sample, not independent validation.",
            "Sensitivity checks do not establish predictive accuracy or official hazard levels.",
            "Original training settings are absent from metadata; refits use current defaults.",
        ],
    }


def _markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _render_markdown(report: dict[str, object]) -> str:
    source_coverage = report["source_coverage"]
    shared_window = report["shared_window"]
    regions = report["regions"]
    stability = report["label_stability"]
    lines = [
        "# Regional Risk Profile Validation Report",
        "",
        f"Artifact version: `{_markdown_cell(report['artifact_version'])}`",
        "",
        "**Review state: requires domain review. The current export remains on hold.**",
        "",
        "## Source coverage",
        "",
        "| Source | Assigned events | First UTC event | Last UTC event |",
        "| --- | ---: | --- | --- |",
    ]
    for source in ("phivolcs", "usgs"):
        details = source_coverage[source]
        lines.append(
            f"| {source.upper()} | {details['assigned_count']} | "
            f"{details['first_occurred_at'] or 'n/a'} | "
            f"{details['last_occurred_at'] or 'n/a'} |"
        )
    lines.extend(["", "## Shared observation window", ""])
    if shared_window["available"]:
        lines.append(f"{shared_window['start']} through {shared_window['end']} (inclusive UTC).")
    else:
        lines.append(f"Unavailable: {shared_window['unavailable_reason']}.")
    lines.extend([
        "",
        "## Regional coverage",
        "",
        "| Region | PHIVOLCS | USGS | PHIVOLCS in window | USGS in window |",
        "| --- | ---: | ---: | ---: | ---: |",
    ])
    for region in regions:
        assigned = region["assigned_by_source"]
        in_window = region["shared_window_count_by_source"]
        lines.append(
            f"| {_markdown_cell(region['region_name'])} | {assigned['phivolcs']} | "
            f"{assigned['usgs']} | {in_window['phivolcs']} | {in_window['usgs']} |"
        )
    lines.extend([
        "",
        "## Regional observation spans",
        "",
        "| Region | PHIVOLCS UTC span | USGS UTC span |",
        "| --- | --- | --- |",
    ])
    for region in regions:
        first = region["first_occurred_at_by_source"]
        last = region["last_occurred_at_by_source"]
        phivolcs_span = f"{first['phivolcs']} to {last['phivolcs']}" if first["phivolcs"] else "n/a"
        usgs_span = f"{first['usgs']} to {last['usgs']}" if first["usgs"] else "n/a"
        lines.append(
            f"| {_markdown_cell(region['region_name'])} | {phivolcs_span} | {usgs_span} |"
        )
    lines.extend([
        "",
        "## Label stability",
        "",
        (
            "Comparison K candidates: "
            f"{', '.join(map(str, stability['comparison_parameters']['k_candidates']))}; "
            f"fixed refit seed: {stability['comparison_parameters']['shared_window_random_state']}."
        ),
        "Original training settings were not recorded, so parameter matching is unverified.",
        "",
        (
            f"Seed sweep: {stability['seed_sweep']['fit_count']} fits "
            "(seeds 0-19). Leave-one-region-out: "
            f"{stability['leave_one_region_out']['fit_count']} fits."
        ),
        "",
        "| Region | Saved label | Seed changes | Leave-one-out changes |",
        "| --- | --- | ---: | ---: |",
    ])
    for name, label in stability["saved_labels"].items():
        seed_count = stability["seed_sweep"]["change_count_by_region"][name]
        leave_count = stability["leave_one_region_out"]["change_count_by_region"][name]
        lines.append(f"| {_markdown_cell(name)} | {label} | {seed_count} | {leave_count} |")
    shared_refit = stability["shared_window_refit"]
    lines.extend(["", "Shared-window refit: "])
    if shared_refit["unavailable_reason"]:
        lines[-1] += f"unavailable ({shared_refit['unavailable_reason']})."
    else:
        lines[-1] += f"{shared_refit['change_count']} saved labels changed among included regions."
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a held regional risk-profile bundle")
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--phivolcs-csv", action="append", type=Path, required=True)
    parser.add_argument("--usgs-csv", action="append", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output_dir.resolve().is_relative_to(args.artifact_dir.resolve()):
            raise ValueError("--output-dir must be outside --artifact-dir.")
        report = build_validation_report(
            args.artifact_dir, args.phivolcs_csv, args.usgs_csv
        )
        markdown = _render_markdown(report)
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "validation-report.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
        (args.output_dir / "validation-report.md").write_text(markdown, encoding="utf-8")
        print(f"Validation report written to {args.output_dir}")
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
