from fastapi import APIRouter, Depends

from app.schemas.volcano import Volcano
from app.services.volcanoes import VolcanoFeed, get_volcano_feed

router = APIRouter(prefix="/volcanoes", tags=["volcanoes"])


@router.get("", response_model=list[Volcano])
def list_volcanoes(feed: VolcanoFeed = Depends(get_volcano_feed)) -> list[Volcano]:
    return feed.list()
