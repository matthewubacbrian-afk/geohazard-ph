from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.config import get_settings
from app.schemas.hazard_event import EventSummary, HazardEvent
from app.services.events import list_events, summarize_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[HazardEvent])
def get_events(
    since: datetime | None = Query(default=None, description="Return events at/after this time"),
    db: Session = Depends(get_db_session),
) -> list[HazardEvent]:
    return list_events(db, since=since)


@router.get("/summary", response_model=EventSummary)
def get_events_summary(
    west: float | None = Query(default=None),
    south: float | None = Query(default=None),
    east: float | None = Query(default=None),
    north: float | None = Query(default=None),
    region_name: str | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> EventSummary:
    west_default, south_default, east_default, north_default = get_settings().ph_bbox
    return summarize_events(
        db,
        west if west is not None else west_default,
        south if south is not None else south_default,
        east if east is not None else east_default,
        north if north is not None else north_default,
        region_name=region_name,
    )
