import json

import pytest

from ml.regions import assign_regions


def _write_square_regions(tmp_path):
    def square(name, west, east):
        return {
            "type": "Feature",
            "properties": {"region_name": name},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[west, 0], [east, 0], [east, 1], [west, 1], [west, 0]]],
            },
        }

    path = tmp_path / "regions.json"
    path.write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [square("First Region", 0, 1), square("Second Region", 2, 3)],
        }),
        encoding="utf-8",
    )
    return path


def test_assign_regions_uses_100_km_offshore_limit(tmp_path):
    boundary = _write_square_regions(tmp_path)
    events = [
        {"source": "phivolcs", "latitude": 0.5, "longitude": 0.5},
        {"source": "usgs", "latitude": 0.5, "longitude": 1.2},
        {"source": "usgs", "latitude": 0.5, "longitude": 4.0},
        {"source": "phivolcs", "latitude": "bad", "longitude": 0.5},
    ]

    result = assign_regions(events, regions_path=boundary)

    assert [row["region_name"] for row in result.rows] == ["First Region", "First Region"]
    assert result.assigned_by_source == {"phivolcs": 1, "usgs": 1}
    assert result.unassigned_by_source == {"phivolcs": 1, "usgs": 1}
    assert result.assigned_count == 2
    assert result.unassigned_count == 2


def test_assign_regions_chooses_nearest_region_and_includes_boundary(tmp_path):
    boundary = _write_square_regions(tmp_path)
    events = [
        {"source": "usgs", "latitude": 0.5, "longitude": 1.0},
        {"source": "usgs", "latitude": 0.5, "longitude": 1.8},
    ]

    result = assign_regions(events, regions_path=boundary)

    assert [row["region_name"] for row in result.rows] == ["First Region", "Second Region"]


def test_assign_regions_enforces_100_km_cutoff(tmp_path):
    boundary = _write_square_regions(tmp_path)
    events = [
        {"source": "usgs", "latitude": 0.5, "longitude": -0.89},
        {"source": "usgs", "latitude": 0.5, "longitude": -0.91},
    ]

    result = assign_regions(events, regions_path=boundary)

    assert [row["longitude"] for row in result.rows] == [-0.89]
    assert result.unassigned_by_source["usgs"] == 1


def test_assign_regions_rejects_empty_boundary_file(tmp_path):
    path = tmp_path / "empty.json"
    path.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")

    with pytest.raises(ValueError, match="boundary"):
        assign_regions([{"source": "usgs", "latitude": 0, "longitude": 0}], regions_path=path)


def test_assign_regions_finds_pinned_asset_from_any_working_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    result = assign_regions([{"source": "phivolcs", "latitude": 13.4, "longitude": 123.3}])

    assert result.rows[0]["region_name"] == "Bicol Region"
