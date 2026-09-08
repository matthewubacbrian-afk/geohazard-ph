from typing import Literal

from pydantic import AwareDatetime, BaseModel, Field, HttpUrl


class Volcano(BaseModel):
    id: str
    name: str
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    current_alert_level: int | None = Field(default=None, ge=0, le=5)
    source: Literal["phivolcs"] = "phivolcs"
    source_url: HttpUrl | None = None
    bulletin_url: HttpUrl | None = None
    bulletin_at: AwareDatetime | None = None
    retrieved_at: AwareDatetime | None = None
    stale: bool = False
