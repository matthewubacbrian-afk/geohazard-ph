from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db_session
from app.schemas.fault_line import FaultLine
from app.services.static_layers import list_layers

router = APIRouter(prefix="/faults", tags=["faults"])


@router.get("", response_model=list[FaultLine])
def list_faults(
    source: Literal["gem", "phivolcs"] | None = Query(default=None),
    db: Session = Depends(get_db_session),
) -> list[FaultLine]:
    return list_layers(db, kind="faults", source=source)
