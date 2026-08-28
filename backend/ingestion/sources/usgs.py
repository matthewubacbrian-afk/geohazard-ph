from datetime import UTC, datetime

import requests

from app.config import Settings
from app.schemas.hazard_event import HazardEvent


class USGSFetchError(RuntimeError):
    pass


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


def fetch_recent_events(
    settings: Settings, *, session: requests.Session | None = None
) -> list[HazardEvent]:
    west, south, east, north = settings.ph_bbox
    params = {
        "minlatitude": south,
        "maxlatitude": north,
        "minlongitude": west,
        "maxlongitude": east,
        "eventtype": "earthquake",
        "format": "geojson",
        "orderby": "time",
        "limit": 200,
    }
    http = session or requests
    response = http.get(settings.usgs_feed_url, params=params, timeout=30)
    try:
        response.raise_for_status()
    except Exception as exc:
        raise USGSFetchError(f"USGS feed request failed: {exc}") from exc
    data = response.json()
    return [parse_usgs_feature(feature) for feature in data.get("features", [])]
