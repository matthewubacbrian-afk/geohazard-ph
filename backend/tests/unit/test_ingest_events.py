from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.schemas import event_change as sealed
from app.schemas.hazard_event import HazardEvent
from app.services.ingest import ingest_events


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, *, fail_on_commit=False):
        self.rows = []
        self.fail_on_commit = fail_on_commit
        self.committed = False
        self.added = []

    def execute(self, _statement):
        return FakeResult(self.rows)

    def add(self, row):
        self.added.append(row)
        row.id = row.id or uuid4()
        self.rows.append(row)

    def flush(self):
        for row in self.added:
            row.id = row.id or uuid4()

    def commit(self):
        self.committed = True
        if self.fail_on_commit:
            raise RuntimeError("commit failed")


def _make_event(external_id: str, magnitude: float) -> HazardEvent:
    return HazardEvent(
        id=f"evt-{external_id}",
        hazard_type="earthquake",
        source="usgs",
        external_id=external_id,
        magnitude=magnitude,
        depth_km=30.0,
        latitude=14.5,
        longitude=121.0,
        place_name="Sample, Philippines",
        occurred_at=datetime(2026, 8, 28, tzinfo=UTC),
    )


def test_ingest_events_invokes_callback_after_commit_with_sealed_changes():
    session = FakeSession()
    received = []

    def on_committed(changes):
        received.extend(changes)

    count = ingest_events(session, [_make_event("a1", 4.0), _make_event("a2", 5.0)], on_committed=on_committed)

    assert count == 2
    assert session.committed is True
    assert len(received) == 2
    assert all(isinstance(change, sealed.EventChange) for change in received)
    assert all(change.canonical_id is not None for change in received)
    assert all(change.is_primary is True for change in received)


def test_ingest_events_does_not_invoke_callback_when_commit_fails():
    session = FakeSession(fail_on_commit=True)
    received = []

    def on_committed(changes):
        received.extend(changes)

    with pytest.raises(RuntimeError, match="commit failed"):
        ingest_events(session, [_make_event("c1", 4.0)], on_committed=on_committed)

    assert received == []
