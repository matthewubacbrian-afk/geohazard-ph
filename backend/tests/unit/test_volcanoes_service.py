from datetime import UTC, datetime

import pytest

from app.schemas.volcano import Volcano
from app.services import volcanoes

ROW = Volcano(
    id="phivolcs:taal",
    name="Taal",
    current_alert_level=1,
    retrieved_at=datetime(2026, 9, 8, tzinfo=UTC),
)


def test_cache_refresh_failure_is_bounded_stale_and_rate_limited(monkeypatch):
    clock = [0]
    calls = []
    monkeypatch.setattr(volcanoes.time, "monotonic", lambda: clock[0])

    def fetch(_settings):
        calls.append(1)
        if len(calls) > 1:
            raise volcanoes.PhivolcsFetchError("sensitive details")
        return [ROW]

    monkeypatch.setattr(volcanoes, "fetch_volcano_bulletins", fetch)
    feed = volcanoes.VolcanoFeed()
    assert feed.list()[0].stale is False
    clock[0] = 10
    assert feed.list()[0].stale is False
    assert len(calls) == 1
    clock[0] = 301
    assert feed.list()[0].stale is True
    clock[0] = 310
    assert feed.list()[0].retrieved_at == ROW.retrieved_at
    assert len(calls) == 2
    clock[0] = 3601
    with pytest.raises(volcanoes.VolcanoFeedUnavailable):
        feed.list()


def test_cold_failure_is_not_an_empty_success(monkeypatch):
    def fetch(_settings):
        raise volcanoes.PhivolcsParseError("invalid")

    monkeypatch.setattr(volcanoes, "fetch_volcano_bulletins", fetch)
    with pytest.raises(volcanoes.VolcanoFeedUnavailable):
        volcanoes.VolcanoFeed().list()
