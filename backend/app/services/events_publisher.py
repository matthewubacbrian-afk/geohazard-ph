import logging

from redis import Redis

from app.config import get_settings
from app.schemas.event_change import EventChange

CHANNEL = "events:updates"
logger = logging.getLogger(__name__)


def get_publisher_client() -> Redis:
    return Redis.from_url(get_settings().redis_url, socket_connect_timeout=2, socket_timeout=2)


def publish(events: list[EventChange]) -> None:
    """Best-effort post-commit callback. Database success survives broker failure."""
    if not events:
        return
    try:
        messages = [EventChange.model_validate(event).model_dump_json() for event in events]
        with get_publisher_client() as client, client.pipeline(transaction=False) as pipeline:
            for message in messages:
                pipeline.publish(CHANNEL, message)
            pipeline.execute()
    except Exception as exc:  # noqa: BLE001 - post-commit callback must never raise
        # Contain all callback failures; exception text may include Redis credentials.
        logger.error(
            "event publish failed",
            extra={"error_type": type(exc).__name__, "event_count": len(events)},
        )
