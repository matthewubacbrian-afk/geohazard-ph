from fastapi import APIRouter

from app.schemas.fault_line import FaultLine

router = APIRouter(prefix="/faults", tags=["faults"])


@router.get("", response_model=list[FaultLine])
def list_faults() -> list[FaultLine]:
    return []
