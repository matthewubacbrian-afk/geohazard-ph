from app.services.proximity import distance_km


def test_distance_km_returns_zero_for_same_point():
    assert distance_km(14.5995, 120.9842, 14.5995, 120.9842) == 0
