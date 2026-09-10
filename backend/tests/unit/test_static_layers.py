import pytest

from ingestion.sources.static_layers import parse_features


def feature(geometry=None):
    return {
        "type": "Feature",
        "id": "fault-1",
        "properties": {"name": "Test fault"},
        "geometry": geometry or {"type": "LineString", "coordinates": [[121, 14], [122, 15]]},
    }


def parse(features, kind="faults"):
    return parse_features(
        features,
        kind=kind,
        source="gem",
        source_url="https://example.org/data",
        license_name="CC-BY-SA-4.0",
        dataset_version="test",
    )


def test_preserves_geometry_identity_and_provenance():
    row = parse([feature()])[0]
    assert row.external_id == "fault-1"
    assert row.geometry["coordinates"] == [[121, 14], [122, 15]]
    assert row.source == "gem"
    assert row.dataset_version == "test"
    assert str(row.source_url) == "https://example.org/data"


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Point", "coordinates": [121, 14]},
        {"type": "LineString", "coordinates": [[121, 95], [122, 15]]},
        {"type": "LineString", "coordinates": [[121, 14], [float("nan"), 15]]},
    ],
)
def test_rejects_wrong_or_invalid_geometry(geometry):
    with pytest.raises(ValueError):
        parse([feature(geometry)])


def test_filters_features_outside_philippines():
    assert parse([feature({"type": "LineString", "coordinates": [[0, 0], [1, 1]]})]) == []


def test_rejects_duplicate_ids_and_empty_imports():
    with pytest.raises(ValueError):
        parse([feature(), feature()])
    with pytest.raises(ValueError):
        parse([])


def test_accepts_polygon_holes_without_fabricating_buffers():
    geometry = {
        "type": "Polygon",
        "coordinates": [
            [[121, 14], [122, 14], [122, 15], [121, 15], [121, 14]],
            [[121.2, 14.2], [121.4, 14.2], [121.4, 14.4], [121.2, 14.2]],
        ],
    }
    row = parse([feature(geometry)], kind="volcano_zones")[0]
    assert row.geometry == geometry


def test_reads_gem_crs84_and_catalog_identity(tmp_path):
    import json

    from ingestion.sources.static_layers import read_features

    path = tmp_path / "gem.geojson"
    row = feature()
    del row["id"]
    row["properties"]["catalog_id"] = "GEM-1"
    payload = {
        "type": "FeatureCollection",
        "features": [row],
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
    }
    path.write_text(json.dumps(payload))
    assert parse(read_features(path))[0].external_id == "GEM-1"
    payload["crs"]["properties"]["name"] = "EPSG:3857"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="WGS84"):
        read_features(path)


def test_reads_projected_shapefile_and_requires_crs(tmp_path):
    import fiona

    from ingestion.sources.static_layers import read_features

    path = tmp_path / "faults.shp"
    schema = {"geometry": "LineString", "properties": {"name": "str"}}
    with fiona.open(path, "w", driver="ESRI Shapefile", crs="EPSG:3857", schema=schema) as output:
        output.write(
            {
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[13469658.39, 1574216.55], [13580977.88, 1689200.14]],
                },
                "properties": {"name": "Projected fault"},
            }
        )
    row = parse(read_features(path))[0]
    assert row.geometry["coordinates"][0] == pytest.approx([121, 14], abs=0.001)
    path.with_suffix(".prj").unlink()
    with pytest.raises(ValueError, match="CRS"):
        read_features(path)
