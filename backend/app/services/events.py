from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import EventSummary, HazardEvent


def list_events(
    session: Session,
    since: datetime | None = None,
    source: str | None = None,
    include_duplicates: bool = False,
) -> list[HazardEvent]:
    stmt = select(HazardEventORM).order_by(HazardEventORM.occurred_at.desc())
    if not include_duplicates and source is None:
        stmt = stmt.where(HazardEventORM.is_primary.is_(True))
    if since is not None:
        stmt = stmt.where(HazardEventORM.occurred_at >= since)
    if source is not None:
        stmt = stmt.where(HazardEventORM.source == source)
    rows = session.execute(stmt).scalars().all()
    return [_to_schema(row) for row in rows]


def summarize_events(
    session: Session,
    west: float,
    south: float,
    east: float,
    north: float,
    region_name: str | None = None,
    source: str | None = None,
) -> EventSummary:
    stmt = select(
        func.count(
            func.distinct(func.coalesce(HazardEventORM.canonical_id, HazardEventORM.id))
        ).label("count"),
        func.avg(HazardEventORM.magnitude).label("avg_mag"),
        func.max(HazardEventORM.magnitude).label("max_mag"),
        func.max(HazardEventORM.occurred_at).label("latest"),
    ).where(
        HazardEventORM.latitude.between(south, north),
        HazardEventORM.longitude.between(west, east),
        HazardEventORM.is_primary.is_(True),
    )
    if source is not None:
        stmt = stmt.where(HazardEventORM.source == source)
    row = session.execute(stmt).one()
    return EventSummary(
        region_name=region_name,
        event_count=int(row.count),
        avg_magnitude=round(float(row.avg_mag), 2) if row.avg_mag is not None else None,
        max_magnitude=float(row.max_mag) if row.max_mag is not None else None,
        latest_occurred_at=row.latest,
    )


def _to_schema(row: HazardEventORM) -> HazardEvent:
    return HazardEvent(
        id=f"{row.source}-{row.external_id}" if row.source and row.external_id else str(row.id),
        hazard_type=row.hazard_type,
        source=row.source,
        external_id=row.external_id,
        canonical_id=str(row.canonical_id) if row.canonical_id is not None else None,
        is_primary=row.is_primary,
        match_confidence=float(row.match_confidence) if row.match_confidence is not None else None,
        magnitude=float(row.magnitude) if row.magnitude is not None else None,
        depth_km=float(row.depth_km) if row.depth_km is not None else None,
        latitude=row.latitude,
        longitude=row.longitude,
        place_name=row.place_name,
        occurred_at=row.occurred_at,
        alert_level=row.alert_level,
    )
