import logging
import time
from functools import lru_cache
from threading import Lock

from app.config import get_settings
from app.schemas.volcano import Volcano
from ingestion.sources.phivolcs_volcano import (
    PhivolcsFetchError,
    PhivolcsParseError,
    fetch_volcano_bulletins,
)

logger = logging.getLogger(__name__)


class VolcanoFeedUnavailable(Exception):
    pass


class VolcanoFeed:
    """Per-process single-flight cache with bounded, explicitly labelled stale data."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: list[Volcano] = []
        self._fetched_at = float("-inf")
        self._retry_at = float("-inf")

    def list(self) -> list[Volcano]:
        settings = get_settings()
        with self._lock:
            now = time.monotonic()
            if self._rows and now - self._fetched_at < settings.phivolcs_volcano_cache_seconds:
                return [row.model_copy() for row in self._rows]
            if now >= self._retry_at:
                try:
                    rows = fetch_volcano_bulletins(settings)
                    if not rows:
                        raise PhivolcsParseError("Empty source")
                    self._rows = rows
                    self._fetched_at = time.monotonic()
                    return [row.model_copy() for row in rows]
                except (PhivolcsFetchError, PhivolcsParseError) as exc:
                    self._retry_at = time.monotonic() + 60
                    logger.warning(
                        "volcano refresh failed", extra={"error_type": type(exc).__name__}
                    )
            age = time.monotonic() - self._fetched_at
            if self._rows and age <= settings.phivolcs_volcano_stale_seconds:
                return [row.model_copy(update={"stale": True}) for row in self._rows]
            raise VolcanoFeedUnavailable("Volcano bulletins temporarily unavailable")


@lru_cache
def get_volcano_feed() -> VolcanoFeed:
    return VolcanoFeed()
