import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import CheckConstraint, DateTime, Float, Index, Numeric, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class HazardEvent(Base):
    __tablename__ = "hazard_events"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_hazard_events_source_external_id"),
        CheckConstraint(
            "hazard_type IN ('earthquake', 'volcanic', 'landslide')",
            name="ck_hazard_events_hazard_type",
        ),
        Index("idx_hazard_events_occurred_at", "occurred_at"),
        Index("idx_hazard_events_geo", "location"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hazard_type: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    external_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    magnitude: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    depth_km: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    place_name: Mapped[str] = mapped_column(Text)
    alert_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[object] = mapped_column(Geography(geometry_type="POINT", srid=4326))
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
