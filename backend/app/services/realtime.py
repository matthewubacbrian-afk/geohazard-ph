from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import get_settings
from app.schemas.event_change import EventChange
from app.services.events_publisher import CHANNEL


@asynccontextmanager
async def subscribe_events() -> AsyncIterator[AsyncIterator[EventChange]]:
    """Subscribe before the WS handshake, eliminating the first-message race."""
    async with (
        Redis.from_url(
            get_settings().redis_url,
            socket_connect_timeout=2,
            socket_timeout=5,
            health_check_interval=15,
        ) as client,
        client.pubsub() as subscription,
    ):
        await subscription.subscribe(CHANNEL)
        acknowledgement = await subscription.get_message(timeout=5)
        if not acknowledgement or acknowledgement["type"] != "subscribe":
            raise RedisError("Subscription not acknowledged")

        async def changes() -> AsyncIterator[EventChange]:
            while True:
                message = await subscription.get_message(ignore_subscribe_messages=True, timeout=1)
                if message and message["type"] == "message":
                    yield EventChange.model_validate_json(message["data"])

        yield changes()


async def broker_ready() -> bool:
    try:
        async with Redis.from_url(
            get_settings().redis_url, socket_connect_timeout=2, socket_timeout=2
        ) as client:
            return bool(await client.ping())
    except RedisError:
        return False
