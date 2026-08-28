from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.hazard_event import HazardEvent
from app.services.events import list_events

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[HazardEvent])
def get_events(
    since: datetime | None = Query(default=None, description="Return events at/after this time"),
    db: Session = Depends(get_db_session),
) -> list[HazardEvent]:
    return list_events(db, since=since)
