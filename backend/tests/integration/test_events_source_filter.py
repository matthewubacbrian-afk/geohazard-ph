from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent
from app.services.ingest import ingest_events


def _make_event(source: str, external_id: str, magnitude: float) -> HazardEvent:
    return HazardEvent(
        id=f"{source}-{external_id}",
        hazard_type="earthquake",
        source=source,
        external_id=external_id,
        magnitude=magnitude,
        depth_km=30.0,
        latitude=14.5,
        longitude=121.0,
        place_name="Sample, Philippines",
        occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
    )


def test_events_source_filter_limits_results(client, migrated_engine):
    with Session(migrated_engine) as session:
        session.add(
            HazardEventORM(
                hazard_type="earthquake",
                source="usgs",
                external_id="usgs-1",
                canonical_id=None,
                is_primary=True,
                magnitude=4.2,
                depth_km=20.0,
                latitude=14.5,
                longitude=121.0,
                place_name="Sample, Philippines",
                location="SRID=4326;POINT(121 14.5)",
                occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
            )
        )
        session.add(
            HazardEventORM(
                hazard_type="earthquake",
                source="phivolcs",
                external_id="ph-1",
                canonical_id=None,
                is_primary=False,
                magnitude=4.2,
                depth_km=20.0,
                latitude=14.5,
                longitude=121.0,
                place_name="Sample, Philippines",
                location="SRID=4326;POINT(121 14.5)",
                occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
            )
        )
        session.commit()

    primary_response = client.get("/api/v1/events")
    duplicate_response = client.get("/api/v1/events?include_duplicates=true")
    source_response = client.get("/api/v1/events?source=phivolcs")

    assert primary_response.status_code == 200
    assert len(primary_response.json()) == 1
    assert len(duplicate_response.json()) == 2
    assert source_response.json() == []


def test_ingest_events_can_match_and_broadcast_primary_demotion(client, migrated_engine):
    received = []

    def on_committed(changes):
        received.extend(changes)

    with Session(migrated_engine) as session:
        pair = [
            _make_event("usgs", "e1", 4.2),
            _make_event("phivolcs", "p1", 4.2),
        ]
        ingest_events(session, pair, on_committed=on_committed)
        session.commit()

    primary_response = client.get("/api/v1/events")
    duplicate_response = client.get("/api/v1/events?include_duplicates=true")

    assert primary_response.status_code == 200
    assert len(primary_response.json()) == 1
    assert len(duplicate_response.json()) == 2
    assert len(received) == 2
    assert len({change.canonical_id for change in received}) == 1
    assert {change.is_primary for change in received} == {False, True}
    assert {change.source for change in received} == {"usgs", "phivolcs"}
