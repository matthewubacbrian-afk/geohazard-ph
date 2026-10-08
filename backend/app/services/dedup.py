import hashlib
import math

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent


MATCH_TIME_TOLERANCE_SECONDS = 120
MATCH_DISTANCE_TOLERANCE_KM = 5.0
MATCH_MAGNITUDE_TOLERANCE = 0.5


def dedup_key(event: HazardEvent) -> tuple[str, str | None]:
    if event.external_id is not None:
        return (event.source, event.external_id)
    # Content key lets null-external-id events be deduplicated by what they are.
    token = (
        f"{event.occurred_at.isoformat()}|{event.latitude}|{event.longitude}"
        f"|{event.magnitude if event.magnitude is not None else ''}"
    )
    return (event.source, f"content:{hashlib.sha256(token.encode()).hexdigest()[:16]}")


def match_and_link(session: Session) -> None:
    rows = sorted(session.execute(select(HazardEventORM)).scalars().all(), key=_primary_sort_key)
    groups: list[list[HazardEventORM]] = []
    for row in rows:
        compatible = [
            (min(_match_confidence(row, member) for member in group), group)
            for group in groups
            if all(row.source != member.source and _events_match(row, member) for member in group)
        ]
        if compatible:
            compatible.sort(key=lambda item: (-item[0], str(min(member.id for member in item[1]))))
            compatible[0][1].append(row)
        else:
            groups.append([row])

    for group in groups:
        canonical_id = min(row.id for row in group)
        primary = min(group, key=_primary_sort_key)
        for row in group:
            row.canonical_id = canonical_id
            row.is_primary = row is primary
            row.match_confidence = _match_confidence(row, primary) if len(group) > 1 else None


def reconcile_canonical_events(session: Session, *, apply: bool = False) -> tuple[int, int]:
    rows = session.execute(select(HazardEventORM)).scalars().all()
    before = {
        row.id: (row.canonical_id, row.is_primary, row.match_confidence)
        for row in rows
    }
    match_and_link(session)
    changed = sum(
        before[row.id] != (row.canonical_id, row.is_primary, row.match_confidence)
        for row in rows
    )
    if apply:
        session.commit()
    else:
        session.rollback()
    return len(rows), changed


def _events_match(left: HazardEventORM, right: HazardEventORM) -> bool:
    if left.hazard_type != right.hazard_type:
        return False
    elapsed_seconds = abs((left.occurred_at - right.occurred_at).total_seconds())
    if elapsed_seconds > MATCH_TIME_TOLERANCE_SECONDS:
        return False
    if _distance_km(left.latitude, left.longitude, right.latitude, right.longitude) > MATCH_DISTANCE_TOLERANCE_KM:
        return False
    if left.magnitude is None or right.magnitude is None:
        return False
    return abs(float(left.magnitude) - float(right.magnitude)) <= MATCH_MAGNITUDE_TOLERANCE


def _distance_km(
    latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float
) -> float:
    radius_km = 6371.0
    latitude_delta = math.radians(latitude_b - latitude_a)
    longitude_delta = math.radians(longitude_b - longitude_a)
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(math.radians(latitude_a))
        * math.cos(math.radians(latitude_b))
        * math.sin(longitude_delta / 2) ** 2
    )
    return radius_km * 2 * math.asin(math.sqrt(haversine))


def _primary_sort_key(row: HazardEventORM) -> tuple[int, object, object, str]:
    return (
        0 if row.source == "phivolcs" else 1,
        row.occurred_at,
        row.created_at,
        str(row.id),
    )


def _match_confidence(row: HazardEventORM, primary: HazardEventORM) -> float:
    if row.magnitude is None or primary.magnitude is None:
        raise ValueError("magnitude is required to compute match confidence")

    time_score = (
        1
        - abs((row.occurred_at - primary.occurred_at).total_seconds())
        / MATCH_TIME_TOLERANCE_SECONDS
    )
    distance_score = 1 - _distance_km(
        row.latitude,
        row.longitude,
        primary.latitude,
        primary.longitude,
    ) / MATCH_DISTANCE_TOLERANCE_KM
    magnitude_score = (
        1 - abs(float(row.magnitude) - float(primary.magnitude)) / MATCH_MAGNITUDE_TOLERANCE
    )
    return max(0.0, min(1.0, min(time_score, distance_score, magnitude_score)))
