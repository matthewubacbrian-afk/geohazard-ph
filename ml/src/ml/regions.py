from __future__ import annotations

import json
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from shapely.geometry import Point, box, shape
from shapely.ops import nearest_points
from shapely.strtree import STRtree

DEFAULT_REGIONS_PATH = Path(__file__).resolve().parents[3] / "web/src/data/philippine-regions.json"
MAX_OFFSHORE_KM = 100.0
EARTH_RADIUS_KM = 6371.0088


@dataclass(frozen=True)
class RegionAssignment:
    rows: list[dict[str, object]]
    assigned_count: int
    unassigned_count: int
    assigned_by_source: dict[str, int]
    unassigned_by_source: dict[str, int]


def load_boundaries(path: Path | str) -> list[dict[str, object]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    boundaries: list[dict[str, object]] = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry")
        properties = feature.get("properties", {})
        name = properties.get("region_name") or properties.get("shapeName")
        if not name or not str(name).strip() or not geometry:
            raise ValueError("Region boundary feature is missing a name or geometry.")
        polygon = shape(geometry)
        if polygon.is_empty or polygon.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError("Region boundary feature must be a nonempty polygon.")
        boundaries.append({"name": str(name).strip(), "geom": polygon})
    if not boundaries:
        raise ValueError("Region boundary file has no named polygons.")
    return boundaries


def _distance_km(first: Point, second: Point) -> float:
    lat1, lon1, lat2, lon2 = map(
        math.radians, (first.y, first.x, second.y, second.x)
    )
    arc = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(arc)))


def assign_regions(
    events: Iterable[Mapping[str, object]],
    regions_path: Path | str = DEFAULT_REGIONS_PATH,
    max_offshore_km: float = MAX_OFFSHORE_KM,
) -> RegionAssignment:
    if not math.isfinite(max_offshore_km) or max_offshore_km < 0:
        raise ValueError("Maximum offshore distance must be non-negative and finite.")

    boundaries = load_boundaries(regions_path)
    polygons = [boundary["geom"] for boundary in boundaries]
    tree = STRtree(polygons)
    assigned = {"phivolcs": 0, "usgs": 0}
    unassigned = {"phivolcs": 0, "usgs": 0}
    rows: list[dict[str, object]] = []

    for event in events:
        source = str(event.get("source", "unknown"))
        try:
            latitude = float(event.get("latitude"))
            longitude = float(event.get("longitude"))
            if not math.isfinite(latitude) or not math.isfinite(longitude):
                raise ValueError("Coordinates must be finite")
        except (TypeError, ValueError, OverflowError):
            unassigned[source] = unassigned.get(source, 0) + 1
            continue

        point = Point(longitude, latitude)
        inside = [
            int(index) for index in tree.query(point) if polygons[int(index)].covers(point)
        ]
        name: str | None = None
        if inside:
            name = min(str(boundaries[index]["name"]) for index in inside)
        else:
            # The asset covers 4-22 degrees N; one degree spans at least 103 km there.
            radius_degrees = max_offshore_km / 100 + 0.1
            candidates = tree.query(
                box(
                    longitude - radius_degrees,
                    latitude - radius_degrees,
                    longitude + radius_degrees,
                    latitude + radius_degrees,
                )
            )
            distances = [
                (
                    _distance_km(point, nearest_points(point, polygons[int(index)])[1]),
                    str(boundaries[int(index)]["name"]),
                )
                for index in candidates
            ]
            if distances:
                distance, closest_name = min(distances)
                if distance <= max_offshore_km:
                    name = closest_name

        if name is None:
            unassigned[source] = unassigned.get(source, 0) + 1
            continue
        row = dict(event)
        row["region_name"] = name
        rows.append(row)
        assigned[source] = assigned.get(source, 0) + 1

    return RegionAssignment(
        rows=rows,
        assigned_count=len(rows),
        unassigned_count=sum(unassigned.values()),
        assigned_by_source=assigned,
        unassigned_by_source=unassigned,
    )
