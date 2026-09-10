import asyncio
import concurrent.futures
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, suppress

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from redis.exceptions import RedisError

from app.config import get_settings
from app.schemas.event_change import EventChange
from app.services.realtime import subscribe_events

router = APIRouter(tags=["realtime"])
logger = logging.getLogger(__name__)
Subscription = Callable[[], AbstractAsyncContextManager[AsyncIterator[EventChange]]]


def get_event_subscription() -> Subscription:
    return subscribe_events


@router.websocket("/ws/events")
async def event_updates(
    websocket: WebSocket,
    subscription: Subscription = Depends(get_event_subscription),
) -> None:
    origin = websocket.headers.get("origin")
    if origin and origin not in get_settings().cors_origins:
        await websocket.close(code=1008)
        return
    try:
        async with subscription() as changes:
            await websocket.accept()
            await _relay(websocket, changes)
    except WebSocketDisconnect:
        pass
    except (asyncio.CancelledError, concurrent.futures.CancelledError):
        # TestClient and shutdown paths may cancel running tasks; allow
        # cancellation to proceed without surfacing an error to the test
        # harness so subscription cleanup (finally blocks) runs.
        pass
    except (RedisError, ValidationError, TimeoutError) as exc:
        logger.warning("realtime stream unavailable", extra={"error_type": type(exc).__name__})
        with suppress(RuntimeError, WebSocketDisconnect):
            await websocket.close(code=1013, reason="Realtime unavailable; reconnect")


async def _relay(websocket: WebSocket, changes: AsyncIterator[EventChange]) -> None:
    async def send() -> None:
        async for change in changes:
            await asyncio.wait_for(websocket.send_text(change.model_dump_json()), timeout=5)

    async def receive() -> None:
        while True:
            message = await websocket.receive()
            if message["type"] == "websocket.disconnect":
                return

    tasks = {asyncio.create_task(send()), asyncio.create_task(receive())}
    try:
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
