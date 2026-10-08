from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional

import json

from shapely.geometry import MultiPolygon, Point, Polygon, shape
from shapely.prepared import prep


@dataclass(frozen=True)
class RegionAssignment:
    rows: list[dict[str, object]]
    assigned_count: int
    unassigned_count: int
    unassigned_by_source: dict[str, int]


def load_boundaries(path: Path | str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = []
    for feat in data.get("features", []):
        geom = feat.get("geometry")
        props = feat.get("properties", {})
        name = props.get("region_name") or props.get("shapeName")
        if not name or not geom:
            continue
        out.append({"name": str(name), "geom": shape(geom)})
    return out


def assign_regions(
    events: Iterable[Mapping[str, object]],
    regions_path: Path | str = "web/src/data/philippine-regions.json",
) -> RegionAssignment:
    boundaries = load_boundaries(regions_path)
    # prep for speed
    items = []
    for b in boundaries:
        items.append((str(b["name"]).strip(), prep(b["geom"])))
    unassigned = {"phivolcs": 0, "usgs": 0}
    out_rows = []
    for ev in events:
        try:
            lat = float(ev.get("latitude"))
            lon = float(ev.get("longitude"))
        except Exception:
            # skip impossible
            src = str(ev.get("source", "unknown"))
            unassigned[src] = unassigned.get(src, 0) + 1
            continue
        pt = Point(lon, lat)
        matched = None
        for name, gprep in items:
            if gprep.contains(pt):
                matched = name
                break
        if matched is None:
            src = str(ev.get("source", "unknown"))
            unassigned[src] = unassigned.get(src, 0) + 1
            continue
        row = dict(ev)
        row["region_name"] = matched
        out_rows.append(row)
    return RegionAssignment(
        rows=out_rows,
        assigned_count=len(out_rows),
        unassigned_count=sum(unassigned.values()),
        unassigned_by_source=unassigned,
    )
