from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.event_change import EventChange
from app.services import events_publisher, realtime


def test_redis_delivers_primary_and_demoted_changes_to_two_clients(monkeypatch):
    # Isolate test messages from a locally running dashboard.
    channel = f"events:test:{uuid4()}"
    monkeypatch.setattr(events_publisher, "CHANNEL", channel)
    monkeypatch.setattr(realtime, "CHANNEL", channel)
    row = EventChange(
        id=uuid4(),
        canonical_id=uuid4(),
        is_primary=True,
        hazard_type="earthquake",
        source="phivolcs",
        latitude=15,
        longitude=121,
        occurred_at="2026-08-29T09:30:00Z",
        place_name="Sample",
    )
    demoted = row.model_copy(update={"id": uuid4(), "is_primary": False, "source": "usgs"})
    with (
        TestClient(app) as client,
        client.websocket_connect("/ws/events") as first,
        client.websocket_connect("/ws/events") as second,
    ):
        # Both handshakes complete only after Redis acknowledges each subscription.
        events_publisher.publish([row, demoted])
        for socket in (first, second):
            assert socket.receive_json() == row.model_dump(mode="json")
            assert socket.receive_json() == demoted.model_dump(mode="json")
