from pathlib import Path

from ml.features import RegionFeatures, build_region_features, load_region_events


def test_build_region_features_aggregates_region_events():
    events = load_region_events(Path("tests/fixtures/sample_region_events.csv"))

    features = build_region_features(events)
    bicol = features["Bicol Region"]

    assert isinstance(bicol, RegionFeatures)
    assert bicol.event_count == 2
    assert bicol.mean_magnitude == 4.9
    assert bicol.max_magnitude == 5.1
    assert bicol.mean_depth_km == 27.5
    assert bicol.event_density > 0


def test_build_region_features_counts_sources_when_present():
    rows = [
        {
            "source": "phivolcs",
            "region_name": "Bicol Region",
            "magnitude": 5.0,
            "depth_km": 20.0,
            "latitude": 13.0,
            "longitude": 123.0,
        },
        {
            "source": "usgs",
            "region_name": "Bicol Region",
            "magnitude": 6.0,
            "depth_km": 30.0,
            "latitude": 13.2,
            "longitude": 123.2,
        },
    ]

    features = build_region_features(rows)["Bicol Region"]

    assert features.phivolcs_event_count == 1
    assert features.usgs_event_count == 1
