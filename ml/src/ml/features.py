from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import pandas as pd


@dataclass(frozen=True)
class RegionFeatures:
    region_name: str
    event_count: int
    mean_magnitude: float
    max_magnitude: float
    mean_depth_km: float
    event_density: float
    phivolcs_event_count: int = 0
    usgs_event_count: int = 0


def load_region_events(path: Path) -> list[dict[str, object]]:
    return pd.read_csv(path).to_dict(orient="records")


def build_region_features(events: Iterable[Mapping[str, object]]) -> dict[str, RegionFeatures]:
    frame = pd.DataFrame(events)
    if frame.empty:
        return {}

    required = {"region_name", "magnitude", "depth_km", "latitude", "longitude"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Region event rows are missing columns: {', '.join(sorted(missing))}")

    features: dict[str, RegionFeatures] = {}
    for region_name, group in frame.groupby("region_name"):
        lat_span = max(float(group["latitude"].max()) - float(group["latitude"].min()), 0.1)
        lon_span = max(float(group["longitude"].max()) - float(group["longitude"].min()), 0.1)
        density = round(float(len(group)) / (lat_span * lon_span), 6)
        source_counts = group.get("source", pd.Series([], dtype=str)).value_counts()
        features[str(region_name)] = RegionFeatures(
            region_name=str(region_name),
            event_count=int(len(group)),
            mean_magnitude=round(float(group["magnitude"].mean()), 2),
            max_magnitude=round(float(group["magnitude"].max()), 2),
            mean_depth_km=round(float(group["depth_km"].mean()), 2),
            event_density=density,
            phivolcs_event_count=int(source_counts.get("phivolcs", 0)),
            usgs_event_count=int(source_counts.get("usgs", 0)),
        )
    return features
