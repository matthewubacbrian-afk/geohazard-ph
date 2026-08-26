from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class SourceReport:
    source: str
    accepted_rows: int
    rejected_rows: int


ALIASES = {
    "source_event_id": ("id", "event_id", "source_event_id"),
    "region_name": ("region_name", "region", "province", "location", "place"),
    "magnitude": ("magnitude", "mag"),
    "depth_km": ("depth_km", "depth", "depth (km)"),
    "latitude": ("latitude", "lat"),
    "longitude": ("longitude", "lon", "lng", "long"),
    "occurred_at": ("occurred_at", "time", "date - time (philippine time)", "date_time"),
}


def _canonical_columns(frame: pd.DataFrame) -> pd.DataFrame:
    lower_to_original = {column.strip().lower(): column for column in frame.columns}
    mapped: dict[str, pd.Series] = {}
    for canonical, aliases in ALIASES.items():
        for alias in aliases:
            if alias in lower_to_original:
                mapped[canonical] = frame[lower_to_original[alias]]
                break
    return pd.DataFrame(mapped)


def _dedup_key(row: dict[str, object]) -> tuple[object, ...]:
    occurred = pd.to_datetime(row["occurred_at"], errors="coerce", utc=True)
    rounded_time = occurred.floor("h").isoformat() if not pd.isna(occurred) else ""
    return (
        rounded_time,
        round(float(row["latitude"]), 1),
        round(float(row["longitude"]), 1),
        round(float(row["magnitude"]), 1),
    )


def normalize_csv(path: Path, source: str) -> tuple[list[dict[str, object]], SourceReport]:
    raw = pd.read_csv(path)
    frame = _canonical_columns(raw)
    frame["source"] = source
    if "source_event_id" not in frame:
        frame["source_event_id"] = None

    required = ["region_name", "magnitude", "depth_km", "latitude", "longitude", "occurred_at"]
    for column in required:
        if column not in frame:
            frame[column] = pd.NA

    for column in ["magnitude", "depth_km", "latitude", "longitude"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    raw_times = pd.to_datetime(frame["occurred_at"], errors="coerce")
    if source == "phivolcs":
        if raw_times.dt.tz is not None:
            raw_times = raw_times.dt.tz_localize(None)
        localized = raw_times.dt.tz_localize("Asia/Manila", ambiguous="NaT", nonexistent="NaT")
        frame["occurred_at"] = localized.dt.tz_convert("UTC")
    else:
        if raw_times.dt.tz is None:
            frame["occurred_at"] = raw_times.dt.tz_localize("UTC", ambiguous="NaT", nonexistent="NaT")
        else:
            frame["occurred_at"] = raw_times.dt.tz_convert("UTC")
    frame["region_name"] = frame["region_name"].astype("string").str.strip()

    valid = frame.dropna(subset=required)
    rows = valid[
        ["source", "source_event_id", "region_name", "magnitude", "depth_km", "latitude", "longitude", "occurred_at"]
    ].to_dict(orient="records")
    report = SourceReport(source, accepted_rows=len(rows), rejected_rows=len(frame) - len(rows))
    return rows, report


def load_and_merge_sources(
    phivolcs_paths: Iterable[Path],
    usgs_paths: Iterable[Path],
) -> tuple[list[dict[str, object]], dict[str, SourceReport]]:
    all_rows: list[dict[str, object]] = []
    report_totals = {
        "phivolcs": SourceReport("phivolcs", 0, 0),
        "usgs": SourceReport("usgs", 0, 0),
    }

    for source, paths in (("phivolcs", phivolcs_paths), ("usgs", usgs_paths)):
        accepted = 0
        rejected = 0
        for path in paths:
            rows, report = normalize_csv(path, source)
            all_rows.extend(rows)
            accepted += report.accepted_rows
            rejected += report.rejected_rows
        report_totals[source] = SourceReport(source, accepted, rejected)

    seen: dict[tuple[object, ...], dict[str, object]] = {}
    for row in all_rows:
        key = _dedup_key(row)
        if key in seen:
            if row.get("source_event_id") and not seen[key].get("source_event_id"):
                seen[key] = row
            continue
        seen[key] = row
    merged = list(seen.values())
    return merged, report_totals
