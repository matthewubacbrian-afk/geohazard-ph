from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent
from app.services.dedup import dedup_key


def ingest_usgs_events(session: Session, events: list[HazardEvent]) -> int:
    latest_by_key = {dedup_key(event): event for event in events}
    if not latest_by_key:
        return 0

    keys = list(latest_by_key)
    existing = session.execute(
        select(HazardEventORM).where(
            HazardEventORM.source.in_([source for source, _external_id in keys]),
            HazardEventORM.external_id.in_([external_id for _source, external_id in keys]),
        )
    ).scalars()
    rows_by_key = {dedup_key(row): row for row in existing}

    changed = 0
    for key, event in latest_by_key.items():
        row = rows_by_key.get(key)
        if row is None:
            session.add(_new_row(event))
        else:
            _update_row(row, event)
        changed += 1

    session.commit()
    return changed


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
