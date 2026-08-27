from ingestion.sources.usgs import parse_usgs_feature


def test_parse_usgs_feature_maps_coordinates_and_time():
    event = parse_usgs_feature(
        {
            "id": "abc123",
            "properties": {
                "mag": 4.8,
                "place": "12 km E of Sample, Philippines",
                "time": 1787788800000,
            },
            "geometry": {"coordinates": [121.0, 14.5, 35.0]},
        }
    )

    assert event.id == "usgs-abc123"
    assert event.latitude == 14.5
    assert event.longitude == 121.0
    assert event.depth_km == 35.0
