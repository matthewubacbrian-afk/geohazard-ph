import gzip
import ssl
from pathlib import Path

import pytest

from app.config import get_settings
from ingestion.sources.phivolcs_earthquake import (
    PhivolcsFetchError,
    _parse_bulletin_table,
    fetch_recent_events,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class FakeResponse:
    def __init__(self, content: bytes, headers=None):
        self.content = content
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return self.content


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
    captured: dict[str, object] = {}
    html = (FIXTURES / "phivolcs_earthquake_sample.html").read_text(encoding="utf-8")

    def fake_urlopen(request, **kwargs: object) -> FakeResponse:
        captured["url"] = request.full_url
        captured["timeout"] = kwargs["timeout"]
        captured["user_agent"] = request.get_header("User-agent")
        captured["verify_mode"] = kwargs["context"].verify_mode
        return FakeResponse(html.encode("utf-8"))

    monkeypatch.setattr("ingestion.sources.phivolcs_earthquake.urlopen", fake_urlopen)
    get_settings.cache_clear()
    settings = get_settings()

    events = fetch_recent_events(settings)

    assert len(events) == 2
    assert events[0].source == "phivolcs"
    assert events[0].place_name == "010 km N 46° W of Polillo (Quezon)"
    assert captured == {
        "url": settings.phivolcs_earthquake_feed_url,
        "timeout": 30,
        "user_agent": "GeoHazard-PH/0.1",
        "verify_mode": ssl.CERT_REQUIRED,
    }


def test_fetch_recent_events_accepts_verified_gzip_feed(monkeypatch):
    import requests

    html = (FIXTURES / "phivolcs_earthquake_sample.html").read_bytes()
    captured = {}

    def fake_urlopen(request, *, context, timeout):
        captured.update(url=request.full_url, context=context, timeout=timeout)
        return FakeResponse(gzip.compress(html), {"Content-Encoding": "gzip"})

    monkeypatch.setattr(requests, "get", lambda *_args, **_kwargs: (_ for _ in ()).throw(
        requests.exceptions.SSLError("incomplete certificate chain")
    ))
    monkeypatch.setattr("ingestion.sources.phivolcs_earthquake.urlopen", fake_urlopen, raising=False)

    events = fetch_recent_events(get_settings())

    assert len(events) == 2
    assert captured["url"] == get_settings().phivolcs_earthquake_feed_url
    assert captured["timeout"] == 30
    assert captured["context"].verify_mode == ssl.CERT_REQUIRED


def test_fetch_recent_events_wraps_http_errors(monkeypatch):
    def fake_urlopen(request, **kwargs: object) -> FakeResponse:
        raise RuntimeError("connection failed")

    monkeypatch.setattr("ingestion.sources.phivolcs_earthquake.urlopen", fake_urlopen)

    with pytest.raises(PhivolcsFetchError, match="request failed"):
        fetch_recent_events(get_settings())


def test_fetch_recent_events_rejects_invalid_utf8(monkeypatch):
    monkeypatch.setattr(
        "ingestion.sources.phivolcs_earthquake.urlopen",
        lambda _request, **_kwargs: FakeResponse(b"\xff"),
    )

    with pytest.raises(PhivolcsFetchError, match="parsing failed"):
        fetch_recent_events(get_settings())
