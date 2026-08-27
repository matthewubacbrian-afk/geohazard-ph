from math import asin, cos, radians, sin, sqrt


def distance_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    radius_km = 6371.0
    dlat = radians(lat_b - lat_a)
    dlon = radians(lon_b - lon_a)
    a = sin(dlat / 2) ** 2 + cos(radians(lat_a)) * cos(radians(lat_b)) * sin(dlon / 2) ** 2
    return 2 * radius_km * asin(sqrt(a))
