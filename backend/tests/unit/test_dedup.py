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
