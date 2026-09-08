from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field


class EventChange(BaseModel):
    """Resolved, committed source row; shared with Person A per ADR 0002."""

    id: UUID
    hazard_type: Literal["earthquake", "volcanic", "landslide"]
    source: str
    external_id: str | None = None
    canonical_id: UUID
    is_primary: bool
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    magnitude: float | None = Field(default=None, allow_inf_nan=False)
    depth_km: float | None = Field(default=None, allow_inf_nan=False)
    occurred_at: AwareDatetime
    place_name: str
