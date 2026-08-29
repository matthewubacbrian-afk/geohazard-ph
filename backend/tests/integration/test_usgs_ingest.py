from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import HazardEvent as HazardEventORM
from app.schemas.hazard_event import HazardEvent
from app.services.ingest import ingest_usgs_events


def _make_event(external_id: str, magnitude: float) -> HazardEvent:
    return HazardEvent(
        id=f"usgs-{external_id}",
        hazard_type="earthquake",
        source="usgs",
        external_id=external_id,
        magnitude=magnitude,
        depth_km=30.0,
        latitude=14.5,
        longitude=121.0,
        place_name="Sample, Philippines",
        occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
    )


def test_ingest_usgs_events_upserts_deduplicates(migrated_engine):
    with Session(migrated_engine) as session:
        ingested = ingest_usgs_events(session, [_make_event("e1", 4.0), _make_event("e1", 4.5)])
        assert ingested == 1

        rows = session.execute(select(HazardEventORM)).scalars().all()
        assert len(rows) == 1
        assert float(rows[0].magnitude) == 4.5


def test_ingest_usgs_events_dedupes_events_without_external_id(migrated_engine):
    from app.schemas.hazard_event import HazardEvent as HazardEventSchema

    def make(mag: float) -> HazardEventSchema:
        return HazardEventSchema(
            id=f"noext-{mag}", hazard_type="earthquake", source="usgs",
            external_id=None, magnitude=mag, depth_km=30.0,
            latitude=14.5, longitude=121.0, place_name="Sample, Philippines",
            occurred_at=datetime(2026, 8, 27, tzinfo=UTC),
        )

    with Session(migrated_engine) as session:
        ingest_usgs_events(session, [make(4.2)])
        ingested = ingest_usgs_events(session, [make(4.2)])
        rows = session.execute(select(HazardEventORM)).scalars().all()
        assert ingested == 1
        assert len(rows) == 1
