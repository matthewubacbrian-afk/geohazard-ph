from fastapi import APIRouter

from app.schemas.alert import AlertSubscription

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertSubscription])
def list_alert_subscriptions() -> list[AlertSubscription]:
    return []
