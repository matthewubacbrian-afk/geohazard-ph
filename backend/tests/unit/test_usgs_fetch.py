import pytest
import requests

from app.config import get_settings
from ingestion.sources.usgs import USGSFetchError, fetch_recent_events


class FakeResponse:
    status_code = 200

    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class FakeBadResponse:
    status_code = 500

    def raise_for_status(self) -> None:
        raise requests.HTTPError("500 Server Error")


def test_fetch_recent_events_parses_fixture(monkeypatch):
    import requests

    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "abc123",
                "properties": {
                    "mag": 4.8,
                    "place": "12 km E of Sample, Philippines",
                    "time": 1787788800000,
                },
                "geometry": {"coordinates": [121.0, 14.5, 35.0]},
            }
        ],
    }

    captured = {}

    def fake_get(url, params=None, **kwargs):
        captured["url"] = url
        captured["params"] = params
        return FakeResponse(payload)

    monkeypatch.setattr(requests, "get", fake_get)

    events = fetch_recent_events(get_settings())

    assert len(events) == 1
    assert events[0].source == "usgs"
    assert events[0].latitude == 14.5
    assert captured["params"]["minlatitude"] == 4.0


def test_fetch_recent_events_raises_on_http_error(monkeypatch):
    import requests

    def fake_get(url, params=None, **kwargs):
        return FakeBadResponse()

    monkeypatch.setattr(requests, "get", fake_get)

    with pytest.raises(USGSFetchError, match="USGS feed request failed") as error:
        fetch_recent_events(get_settings())
    assert isinstance(error.value.__cause__, requests.HTTPError)
