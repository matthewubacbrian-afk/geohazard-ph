import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError
from starlette.websockets import WebSocketDisconnect

from app.api.v1.realtime import get_event_subscription
from app.main import app
from app.schemas.event_change import EventChange
from app.services.realtime import broker_ready


def event():
    return EventChange(
        id=uuid4(),
        canonical_id=uuid4(),
        is_primary=True,
        hazard_type="earthquake",
        source="usgs",
        latitude=15,
        longitude=121,
        occurred_at="2026-08-29T09:30:00Z",
        place_name="Sample",
    )


def test_socket_delivers_event_and_closes_subscription_on_disconnect():
    row = event()
    closed = []

    @asynccontextmanager
    async def subscription():
        async def changes():
            yield row
            await asyncio.Event().wait()

        try:
            yield changes()
        finally:
            closed.append(True)

    app.dependency_overrides[get_event_subscription] = lambda: subscription
    try:
        with TestClient(app) as client, client.websocket_connect("/ws/events") as websocket:
            assert websocket.receive_json() == row.model_dump(mode="json")
        assert closed == [True]
    finally:
        app.dependency_overrides.pop(get_event_subscription)


def test_socket_rejects_untrusted_browser_origin():
    with TestClient(app) as client:
        with (
            pytest.raises(WebSocketDisconnect) as error,
            client.websocket_connect("/ws/events", headers={"origin": "https://untrusted.test"}),
        ):
            pass
        assert error.value.code == 1008


def test_broker_outage_rejects_stream_and_status_reports_unavailable():
    @asynccontextmanager
    async def unavailable():
        raise ConnectionError("secret")
        yield  # pragma: no cover

    app.dependency_overrides[get_event_subscription] = lambda: unavailable
    app.dependency_overrides[broker_ready] = lambda: False
    try:
        with TestClient(app) as client:
            with (
                pytest.raises(WebSocketDisconnect) as error,
                client.websocket_connect("/ws/events"),
            ):
                pass
            assert error.value.code == 1013
            response = client.get("/api/v1/subscribe")
            assert response.status_code == 200
            assert response.json() == {
                "status": "unavailable",
                "channel": "events:updates",
                "endpoint": "/ws/events",
            }
    finally:
        app.dependency_overrides.pop(get_event_subscription)
        app.dependency_overrides.pop(broker_ready)
