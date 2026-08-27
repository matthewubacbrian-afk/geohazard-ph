from fastapi import APIRouter

router = APIRouter(prefix="/subscribe", tags=["subscribe"])


@router.get("")
def subscription_status() -> dict[str, str]:
    return {"status": "realtime channel stub"}
