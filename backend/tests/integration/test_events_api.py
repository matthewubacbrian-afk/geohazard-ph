from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM


def test_events_endpoint_returns_db_rows(client, migrated_engine):
    with Session(migrated_engine) as session:
        session.add(
            HazardEventORM(
                hazard_type="earthquake",
                source="usgs",
                external_id="live-1",
                magnitude=4.2,
                depth_km=25.0,
                latitude=15.0,
                longitude=120.0,
                place_name="Seeded, Philippines",
                location="SRID=4326;POINT(120.0 15.0)",
                occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
            )
        )
        session.commit()

    response = client.get("/api/v1/events")

    assert response.status_code == 200
    bodies = response.json()
    assert any(body["external_id"] == "live-1" for body in bodies)
    assert all("occurred_at" in body for body in bodies)


def test_events_endpoint_filters_by_since(client, migrated_engine):
    with Session(migrated_engine) as session:
        session.add(
            HazardEventORM(
                hazard_type="earthquake",
                source="usgs",
                external_id="older-1",
                magnitude=4.0,
                depth_km=20.0,
                latitude=14.0,
                longitude=121.0,
                place_name="Older, Philippines",
                location="SRID=4326;POINT(121.0 14.0)",
                occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
            )
        )
        session.commit()

    response = client.get("/api/v1/events?since=2027-01-01T00:00:00Z")

    assert response.status_code == 200
    assert response.json() == []


def test_events_summary_endpoint_aggregates_bbox(client, migrated_engine):
    with Session(migrated_engine) as session:
        session.add(
            HazardEventORM(
                hazard_type="earthquake",
                source="usgs",
                external_id="s1",
                magnitude=4.0,
                depth_km=20.0,
                latitude=14.0,
                longitude=121.0,
                place_name="A, Philippines",
                location="SRID=4326;POINT(121.0 14.0)",
                occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
            )
        )
        session.add(
            HazardEventORM(
                hazard_type="earthquake",
                source="usgs",
                external_id="s2",
                magnitude=5.0,
                depth_km=25.0,
                latitude=15.0,
                longitude=120.0,
                place_name="B, Philippines",
                location="SRID=4326;POINT(120.0 15.0)",
                occurred_at=datetime(2026, 8, 29, tzinfo=UTC),
            )
        )
        session.commit()

    response = client.get("/api/v1/events/summary?west=116&south=4&east=128&north=22&region_name=PH")

    assert response.status_code == 200
    body = response.json()
    assert body["event_count"] == 2
    assert body["avg_magnitude"] == 4.5
    assert body["max_magnitude"] == 5.0
    assert body["region_name"] == "PH"


def test_events_summary_endpoint_defaults_to_ph_bbox(client):
    response = client.get("/api/v1/events/summary")
    assert response.status_code == 200
    assert "event_count" in response.json()
