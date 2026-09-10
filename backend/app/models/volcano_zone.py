from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.models.hazard_event import Base
from app.models.static_layer import StaticLayerColumns


class VolcanoZone(StaticLayerColumns, Base):
    __tablename__ = "volcano_zones"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_volcano_zones_source_external_id"),
        CheckConstraint("source IN ('gem', 'phivolcs')", name="ck_volcano_zones_source"),
        CheckConstraint(
            "GeometryType(geometry) IN ('POLYGON', 'MULTIPOLYGON') AND ST_IsValid(geometry) "
            "AND NOT ST_IsEmpty(geometry)",
            name="ck_volcano_zones_geometry",
        ),
        Index("idx_volcano_zones_geometry", "geometry", postgresql_using="gist"),
    )
