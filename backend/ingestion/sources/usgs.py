from datetime import UTC, datetime

from app.schemas.hazard_event import HazardEvent


def parse_usgs_feature(feature: dict) -> HazardEvent:
    properties = feature["properties"]
    longitude, latitude, depth_km = feature["geometry"]["coordinates"]
    return HazardEvent(
        id=f"usgs-{feature['id']}",
        hazard_type="earthquake",
        source="usgs",
        external_id=feature["id"],
        magnitude=properties.get("mag"),
        depth_km=depth_km,
        latitude=latitude,
        longitude=longitude,
        place_name=properties.get("place") or "Unknown location",
        occurred_at=datetime.fromtimestamp(properties["time"] / 1000, tz=UTC),
    )
