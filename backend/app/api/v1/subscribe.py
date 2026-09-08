from fastapi import APIRouter, Depends

from app.schemas.realtime import RealtimeStatus
from app.services.realtime import broker_ready

router = APIRouter(prefix="/subscribe", tags=["subscribe"])


@router.get("", response_model=RealtimeStatus)
async def subscription_status(ready: bool = Depends(broker_ready)) -> RealtimeStatus:
    return RealtimeStatus(status="ok" if ready else "unavailable")
