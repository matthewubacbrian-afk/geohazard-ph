from datetime import UTC, datetime

from fastapi import APIRouter

from app.schemas.hazard_event import HazardEvent

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[HazardEvent])
def list_events() -> list[HazardEvent]:
    return [
        HazardEvent(
            id="sample-usgs-001",
            hazard_type="earthquake",
            source="usgs",
            external_id="usgs-sample-001",
            magnitude=5.2,
            depth_km=32.0,
            latitude=14.5995,
            longitude=120.9842,
            place_name="Sample event near Manila, Philippines",
            occurred_at=datetime(2026, 8, 27, tzinfo=UTC),
        )
    ]
