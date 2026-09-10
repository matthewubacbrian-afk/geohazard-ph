"""Read reviewed vector data; never infer fault traces or hazard buffers."""

import hashlib
import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

from shapely.geometry import box, shape

from app.schemas.static_layer import StaticFeature

LayerKind = Literal["faults", "volcano_zones"]


def _validate_coordinates(value: Any, *, require_2d: bool = True) -> None:
    if not isinstance(value, (list, tuple)) or not value:
        raise ValueError("Missing geometry coordinates")
    if isinstance(value[0], (int, float)):
        if len(value) not in ({2} if require_2d else {2, 3}) or any(
            isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n)
            for n in value
        ):
            raise ValueError("Coordinates must be finite 2D WGS84 positions")
        if not (-180 <= value[0] <= 180 and -90 <= value[1] <= 90):
            raise ValueError("Coordinates outside WGS84 bounds")
    else:
        for child in value:
            _validate_coordinates(child, require_2d=require_2d)


def parse_features(
    features: Iterable[dict[str, Any]],
    *,
    kind: LayerKind,
    source: str,
    source_url: str,
    license_name: str,
    dataset_version: str,
    bbox: tuple[float, float, float, float] = (116, 4, 128, 22),
) -> list[StaticFeature]:
    allowed = {
        "faults": {"LineString", "MultiLineString"},
        "volcano_zones": {"Polygon", "MultiPolygon"},
    }[kind]
    rows = []
    seen = set()
    count = 0
    for feature in features:
        count += 1
        if not isinstance(feature, dict):
            raise ValueError("Each feature must be an object")  # noqa: TRY004
        geometry = feature.get("geometry") or {}
        if not isinstance(geometry, dict):
            raise ValueError("Feature geometry must be an object")  # noqa: TRY004
        if geometry.get("type") not in allowed:
            raise ValueError(f"Unsupported geometry for {kind}")
        _validate_coordinates(geometry.get("coordinates"), require_2d=False)
        spatial = shape(geometry)
        if spatial.is_empty or not spatial.is_valid:
            raise ValueError("Invalid or empty geometry")
        if not spatial.intersects(box(*bbox)):
            continue
        _validate_coordinates(geometry.get("coordinates"))
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            raise ValueError("Feature properties must be an object")  # noqa: TRY004
        external_id = feature.get("id")
        if external_id is None:
            external_id = next(
                (
                    properties[key]
                    for key in ("catalog_id", "id", "fault_id", "OBJECTID")
                    if properties.get(key) is not None
                ),
                None,
            )
        if external_id is None:
            external_id = hashlib.sha256(
                json.dumps(
                    {"geometry": geometry, "properties": properties},
                    sort_keys=True,
                    allow_nan=False,
                ).encode()
            ).hexdigest()
        external_id = str(external_id)
        if external_id in seen:
            raise ValueError(f"Duplicate feature identifier: {external_id}")
        seen.add(external_id)
        rows.append(
            StaticFeature(
                external_id=external_id,
                name=str(
                    properties.get("name")
                    or properties.get("Name")
                    or properties.get("fault_name")
                    or external_id
                ),
                source=source,
                source_url=source_url,
                license_name=license_name,
                dataset_version=dataset_version,
                geometry=geometry,
                source_properties=properties,
            )
        )
    if count == 0:
        raise ValueError("Source contains no features")
    return rows


def read_features(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() in {".geojson", ".json"}:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict) or payload.get("type") != "FeatureCollection":
            raise ValueError("Expected WGS84 FeatureCollection")
        crs = payload.get("crs")
        if crs is not None and crs != {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"},
        }:
            raise ValueError("GeoJSON must use WGS84 longitude/latitude (CRS84)")
        if not isinstance(payload.get("features"), list):
            raise ValueError("FeatureCollection.features must be an array")
        return payload["features"]
    if path.suffix.lower() != ".shp":
        raise ValueError("Provide GeoJSON or a shapefile; digitize atlas PDFs in GIS first")
    import fiona
    from fiona.transform import transform_geom

    with fiona.open(path) as collection:
        if not collection.crs:
            raise ValueError("Shapefile needs a declared CRS (.prj)")
        return [
            {
                "type": "Feature",
                "properties": dict(feature["properties"]),
                "geometry": dict(transform_geom(collection.crs, "EPSG:4326", feature["geometry"])),
            }
            for feature in collection
        ]
