from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.models.hazard_event import Base
from app.models.static_layer import StaticLayerColumns


class FaultLine(StaticLayerColumns, Base):
    __tablename__ = "fault_lines"
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_fault_lines_source_external_id"),
        CheckConstraint("source IN ('gem', 'phivolcs')", name="ck_fault_lines_source"),
        CheckConstraint(
            "GeometryType(geometry) IN ('LINESTRING', 'MULTILINESTRING') AND ST_IsValid(geometry) "
            "AND NOT ST_IsEmpty(geometry)",
            name="ck_fault_lines_geometry",
        ),
        Index("idx_fault_lines_geometry", "geometry", postgresql_using="gist"),
    )
