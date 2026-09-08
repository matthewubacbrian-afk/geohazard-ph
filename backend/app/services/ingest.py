from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import EventChange, HazardEvent
from app.services.dedup import dedup_key, match_and_link


def ingest_events(session: Session, events: list[HazardEvent], on_committed=None) -> int:
    latest_by_key = {dedup_key(event): event for event in events}
    if not latest_by_key:
        return 0

    keys = list(latest_by_key)
    existing = session.execute(
        select(HazardEventORM).where(
            HazardEventORM.source.in_([source for source, _external_id in keys]),
        )
    ).scalars().all()
    rows_by_key = {dedup_key(row): row for row in existing}

    touched: set[HazardEventORM] = set()
    for key, event in latest_by_key.items():
        row = rows_by_key.get(key)
        if row is None:
            row = _new_row(event)
            session.add(row)
        else:
            _update_row(row, event)
        touched.add(row)

    match_and_link(session)
    session.flush()
    session.commit()

    if on_committed is not None:
        on_committed([_to_event_change(row) for row in touched])

    return len(touched)


def ingest_usgs_events(session: Session, events: list[HazardEvent], on_committed=None) -> int:
    return ingest_events(session, events, on_committed=on_committed)


def _new_row(event: HazardEvent) -> HazardEventORM:
    return HazardEventORM(
        hazard_type=event.hazard_type,
        source=event.source,
        external_id=event.external_id,
        magnitude=event.magnitude,
        depth_km=event.depth_km,
        latitude=event.latitude,
        longitude=event.longitude,
        place_name=event.place_name,
        alert_level=event.alert_level,
        location=f"SRID=4326;POINT({event.longitude} {event.latitude})",
        occurred_at=event.occurred_at,
    )


def _update_row(row: HazardEventORM, event: HazardEvent) -> None:
    row.magnitude = event.magnitude
    row.depth_km = event.depth_km
    row.latitude = event.latitude
    row.longitude = event.longitude
    row.place_name = event.place_name
    row.alert_level = event.alert_level
    row.location = f"SRID=4326;POINT({event.longitude} {event.latitude})"
    row.occurred_at = event.occurred_at


def _to_event_change(row: HazardEventORM) -> EventChange:
    return EventChange(
        id=str(row.id),
        hazard_type=row.hazard_type,
        source=row.source,
        external_id=row.external_id,
        canonical_id=str(getattr(row, "canonical_id", None)) if getattr(row, "canonical_id", None) is not None else None,
        is_primary=getattr(row, "is_primary", None),
        latitude=row.latitude,
        longitude=row.longitude,
        magnitude=float(row.magnitude) if row.magnitude is not None else None,
        depth_km=float(row.depth_km) if row.depth_km is not None else None,
        occurred_at=row.occurred_at,
        place_name=row.place_name,
    )
