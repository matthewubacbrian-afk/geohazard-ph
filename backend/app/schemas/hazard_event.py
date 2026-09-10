from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HazardEvent(BaseModel):
    id: str
    hazard_type: Literal["earthquake", "volcanic", "landslide"]
    source: str
    external_id: str | None = None
    canonical_id: str | None = None
    is_primary: bool | None = None
    match_confidence: float | None = None
    magnitude: float | None = None
    depth_km: float | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    place_name: str
    occurred_at: datetime
    alert_level: str | None = None


class EventSummary(BaseModel):
    region_name: str | None = None
    event_count: int = 0
    avg_magnitude: float | None = None
    max_magnitude: float | None = None
    latest_occurred_at: datetime | None = None
