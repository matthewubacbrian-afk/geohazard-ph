from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent


def list_events(session: Session, since: datetime | None = None) -> list[HazardEvent]:
    stmt = select(HazardEventORM).order_by(HazardEventORM.occurred_at.desc())
    if since is not None:
        stmt = stmt.where(HazardEventORM.occurred_at >= since)
    rows = session.execute(stmt).scalars().all()
    return [_to_schema(row) for row in rows]


def _to_schema(row: HazardEventORM) -> HazardEvent:
    return HazardEvent(
        id=f"{row.source}-{row.external_id}" if row.source else str(row.id),
        hazard_type=row.hazard_type,
        source=row.source,
        external_id=row.external_id,
        magnitude=float(row.magnitude) if row.magnitude is not None else None,
        depth_km=float(row.depth_km) if row.depth_km is not None else None,
        latitude=row.latitude,
        longitude=row.longitude,
        place_name=row.place_name,
        occurred_at=row.occurred_at,
        alert_level=row.alert_level,
    )
