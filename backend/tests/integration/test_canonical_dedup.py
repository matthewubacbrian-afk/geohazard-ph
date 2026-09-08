from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM


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