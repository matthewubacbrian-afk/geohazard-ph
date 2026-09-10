from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.volcano_zone import VolcanoZone
from app.services.static_layers import list_layers

router = APIRouter(prefix="/volcano-zones", tags=["volcano-zones"])


@router.get("", response_model=list[VolcanoZone])
def list_volcano_zones(
    source: Literal["gem", "phivolcs"] | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> list[VolcanoZone]:
    return list_layers(db, kind="volcano_zones", source=source)
