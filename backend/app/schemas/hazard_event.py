from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HazardEvent(BaseModel):
    id: str
    hazard_type: Literal["earthquake", "volcanic", "landslide"]
    source: str
    external_id: str | None = None
    magnitude: float | None = None
    depth_km: float | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    place_name: str
    occurred_at: datetime
    alert_level: str | None = None
