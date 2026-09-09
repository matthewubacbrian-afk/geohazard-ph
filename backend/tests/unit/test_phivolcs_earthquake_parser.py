from pathlib import Path

import pytest

from app.config import get_settings
from ingestion.sources.phivolcs_earthquake import (
    PhivolcsFetchError,
    fetch_recent_events,
    _parse_bulletin_table,
)


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self) -> None:
        return None


def test_parse_bulletin_table_maps_all_earthquake_rows():
    html = (FIXTURES / "phivolcs_earthquake_sample.html").read_text(encoding="utf-8")

    events = _parse_bulletin_table(html)
    event = events[0]

    assert len(events) == 2
    assert event.id == "phivolcs-2026_0906_1409_B1"
    assert event.source == "phivolcs"
    assert event.hazard_type == "earthquake"
    assert event.external_id == "2026_0906_1409_B1"
    assert event.magnitude == 1.7
    assert event.depth_km == 4.0
    assert event.latitude == 14.77
    assert event.longitude == 121.87
    assert event.place_name == "010 km N 46° W of Polillo (Quezon)"
    assert event.occurred_at.isoformat() == "2026-09-06T14:09:00+00:00"


def test_parse_bulletin_table_rejects_missing_data_table():
    with pytest.raises(PhivolcsFetchError, match="could not locate"):
        _parse_bulletin_table("<p>Magnitude: 5.2</p>")


def test_fetch_recent_events_uses_configured_feed(monkeypatch):
    import requests

    captured: dict[str, object] = {}
    html = (FIXTURES / "phivolcs_earthquake_sample.html").read_text(encoding="utf-8")

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        captured["url"] = url
        captured["timeout"] = kwargs["timeout"]
        captured["headers"] = kwargs["headers"]
        captured["verify"] = kwargs["verify"]
        return FakeResponse(html)

    monkeypatch.setattr(requests, "get", fake_get)
    get_settings.cache_clear()
    settings = get_settings()

    events = fetch_recent_events(settings)

    assert len(events) == 2
    assert events[0].source == "phivolcs"
    assert captured == {
        "url": settings.phivolcs_earthquake_feed_url,
        "timeout": 30,
        "headers": {"User-Agent": "GeoHazard-PH/0.1"},
        "verify": settings.phivolcs_ssl_verify,
    }


def test_fetch_recent_events_wraps_http_errors(monkeypatch):
    import requests

    def fake_get(url: str, **kwargs: object) -> FakeResponse:
        raise RuntimeError("connection failed")

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(PhivolcsFetchError, match="request failed"):
        fetch_recent_events(get_settings())