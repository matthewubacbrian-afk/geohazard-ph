from datetime import datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


class StaticLayerColumns:
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    external_id: Mapped[str] = mapped_column(Text)
    name: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(Text)
    license_name: Mapped[str] = mapped_column(Text)
    dataset_version: Mapped[str] = mapped_column(Text)
    source_properties: Mapped[dict[str, Any]] = mapped_column(JSONB)
    geometry: Mapped[Any] = mapped_column(Geometry("GEOMETRY", srid=4326, spatial_index=False))
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
