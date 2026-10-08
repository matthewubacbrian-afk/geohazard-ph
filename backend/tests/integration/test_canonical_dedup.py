from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent
from app.services.ingest import ingest_events


def _row(source: str, external_id: str, canonical_id, is_primary: bool):
    return HazardEventORM(
        hazard_type="earthquake",
        source=source,
        external_id=external_id,
        canonical_id=canonical_id,
        is_primary=is_primary,
        magnitude=5.0,
        depth_km=20.0,
        latitude=14.5,
        longitude=121.0,
        place_name="Sample, Philippines",
        location="SRID=4326;POINT(121 14.5)",
        occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
    )


def test_events_primary_only_and_source_filter(client, migrated_engine):
    with Session(migrated_engine) as session:
        usgs = _row("usgs", "usgs-1", None, True)
        session.add(usgs)
        session.flush()
        usgs.canonical_id = usgs.id
        session.add(_row("phivolcs", "phivolcs-1", usgs.id, False))
        session.commit()

    primary_response = client.get("/api/v1/events")
    duplicate_response = client.get("/api/v1/events?include_duplicates=true")
    source_response = client.get("/api/v1/events?source=phivolcs")

    assert primary_response.status_code == 200
    assert len(primary_response.json()) == 1
    assert len(duplicate_response.json()) == 2
    assert source_response.json() == []


def test_events_summary_counts_canonical_events(client, migrated_engine):
    with Session(migrated_engine) as session:
        primary = _row("phivolcs", "phivolcs-1", None, True)
        session.add(primary)
        session.flush()
        primary.canonical_id = primary.id
        session.add(_row("usgs", "usgs-1", primary.id, False))
        session.commit()

    response = client.get("/api/v1/events/summary")

    assert response.status_code == 200
    assert response.json()["event_count"] == 1


def test_source_revision_splits_then_rejoins_canonical_event(client, migrated_engine):
    occurred_at = datetime(2026, 8, 28, tzinfo=UTC)

    def event(source: str, external_id: str, latitude: float) -> HazardEvent:
        return HazardEvent(
            id=f"{source}-{external_id}",
            hazard_type="earthquake",
            source=source,
            external_id=external_id,
            magnitude=5.0,
            latitude=latitude,
            longitude=121.0,
            place_name="Sample, Philippines",
            occurred_at=occurred_at,
        )

    usgs = event("usgs", "revised-u", 14.5)
    phivolcs = event("phivolcs", "revised-p", 14.5)
    changes = []
    with Session(migrated_engine) as session:
        ingest_events(session, [usgs, phivolcs])
        assert client.get("/api/v1/events/summary").json()["event_count"] == 1

        ingest_events(
            session,
            [event("phivolcs", "revised-p", 15.0)],
            on_committed=changes.extend,
        )
        assert client.get("/api/v1/events/summary").json()["event_count"] == 2
        assert {change.source for change in changes} == {"usgs", "phivolcs"}
        assert all(change.is_primary for change in changes)

        changes.clear()
        ingest_events(session, [phivolcs], on_committed=changes.extend)

    assert client.get("/api/v1/events/summary").json()["event_count"] == 1
    assert len(client.get("/api/v1/events").json()) == 1
    assert {change.is_primary for change in changes} == {False, True}


def test_reconciliation_previews_then_repairs_a_persisted_false_merge(migrated_engine):
    from app.services.dedup import reconcile_canonical_events

    with Session(migrated_engine) as session:
        first = _row("usgs", "stale-u", None, False)
        session.add(first)
        session.flush()
        first.canonical_id = first.id
        second = _row("phivolcs", "stale-p", first.id, True)
        second.latitude = 15.0
        second.location = "SRID=4326;POINT(121 15)"
        session.add(second)
        session.commit()

    with Session(migrated_engine) as session:
        assert reconcile_canonical_events(session, apply=False) == (2, 2)

    with Session(migrated_engine) as session:
        rows = session.query(HazardEventORM).all()
        assert len({row.canonical_id for row in rows}) == 1
        assert reconcile_canonical_events(session, apply=True) == (2, 2)

    with Session(migrated_engine) as session:
        rows = session.query(HazardEventORM).all()
        assert len({row.canonical_id for row in rows}) == 2
        assert all(row.is_primary for row in rows)
