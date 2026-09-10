from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class StaticFeature(BaseModel):
    external_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    source: Literal["gem", "phivolcs"]
    source_url: HttpUrl
    license_name: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    geometry: dict[str, Any]
    source_properties: dict[str, Any] = Field(default_factory=dict)


class StaticLayer(StaticFeature):
    id: str
    imported_at: datetime
