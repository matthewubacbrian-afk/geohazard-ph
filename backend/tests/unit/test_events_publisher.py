from uuid import uuid4

import pytest
from redis.exceptions import ConnectionError

from app.schemas.event_change import EventChange
from app.services import events_publisher


def change(**values):
    return EventChange(
        id=uuid4(),
        canonical_id=uuid4(),
        is_primary=True,
        hazard_type="earthquake",
        source="phivolcs",
        external_id="ph-1",
        latitude=15,
        longitude=121,
        magnitude=5.2,
        depth_km=10,
        occurred_at="2026-08-29T09:30:00Z",
        place_name="Sample",
        **values,
    )


def test_publish_sends_resolved_primary_and_demoted_rows(monkeypatch):
    sent = []

    class Client:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def pipeline(self, **kwargs):
            return self

        def publish(self, channel, message):
            sent.append((channel, message))

        def execute(self):
            pass

    monkeypatch.setattr(events_publisher, "get_publisher_client", Client)
    primary = change()
    demoted = primary.model_copy(update={"id": uuid4(), "is_primary": False, "source": "usgs"})
    events_publisher.publish([primary, demoted])
    assert [EventChange.model_validate_json(m).is_primary for _, m in sent] == [True, False]
    assert all(c == "events:updates" for c, _ in sent)


def test_publish_failure_cannot_fail_committed_ingest(monkeypatch, caplog):
    def unavailable():
        raise ConnectionError("secret must not appear")

    monkeypatch.setattr(events_publisher, "get_publisher_client", unavailable)
    events_publisher.publish([change()])
    assert "publish failed" in caplog.text
    assert "secret" not in caplog.text


def test_event_change_rejects_unresolved_identity_and_naive_time():
    with pytest.raises(ValueError):
        EventChange.model_validate({**change().model_dump(), "canonical_id": None})
    with pytest.raises(ValueError):
        EventChange.model_validate({**change().model_dump(), "occurred_at": "2026-08-29T09:30:00"})
