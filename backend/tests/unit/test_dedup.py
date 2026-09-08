from datetime import UTC, datetime

from app.schemas.hazard_event import HazardEvent
from app.services.dedup import dedup_key


def test_dedup_key_uses_source_and_external_id():
    event = HazardEvent(
        id="sample",
        hazard_type="earthquake",
        source="usgs",
        external_id="usgs-1",
        latitude=14.5,
        longitude=121.0,
        place_name="Sample",
        occurred_at=datetime(2026, 8, 27, tzinfo=UTC),
    )

    assert dedup_key(event) == ("usgs", "usgs-1")


def test_dedup_key_falls_back_to_content_key_without_external_id():
    event = HazardEvent(
        id="a", hazard_type="earthquake", source="usgs", external_id=None,
        latitude=14.5, longitude=121.0, place_name="Sample",
        occurred_at=datetime(2026, 8, 27, tzinfo=UTC), magnitude=4.2,
    )
    twin = HazardEvent(
        id="b", hazard_type="earthquake", source="usgs", external_id=None,
        latitude=14.5, longitude=121.0, place_name="Sample",
        occurred_at=datetime(2026, 8, 27, tzinfo=UTC), magnitude=4.2,
    )
    assert dedup_key(event)[0] == "usgs"
    assert dedup_key(event) == dedup_key(twin)          # same content -> same key
    assert dedup_key(event)[1].startswith("content:")


def test_dedup_key_with_external_id_uses_source_and_external_id():
    event = HazardEvent(
        id="x", hazard_type="earthquake", source="usgs", external_id="usgs-1",
        latitude=14.5, longitude=121.0, place_name="Sample",
        occurred_at=datetime(2026, 8, 27, tzinfo=UTC),
    )
    assert dedup_key(event) == ("usgs", "usgs-1")


def test_hazard_event_model_has_canonical_identity_columns():
    from app.models import HazardEvent as HazardEventORM

    row = HazardEventORM(
        hazard_type="earthquake",
        source="usgs",
        external_id="evt-1",
        magnitude=5.4,
        latitude=14.5,
        longitude=121.0,
        place_name="Sample",
        location="SRID=4326;POINT(121 14.5)",
        occurred_at=datetime(2026, 8, 27, tzinfo=UTC),
        canonical_id=None,
        is_primary=True,
        match_confidence=0.95,
    )

    assert row.canonical_id is None
    assert row.is_primary is True
    assert row.match_confidence == 0.95
