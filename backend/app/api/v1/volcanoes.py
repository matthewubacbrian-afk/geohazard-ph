from fastapi import APIRouter

from app.schemas.volcano import Volcano

router = APIRouter(prefix="/volcanoes", tags=["volcanoes"])


@router.get("", response_model=list[Volcano])
def list_volcanoes() -> list[Volcano]:
    return []
