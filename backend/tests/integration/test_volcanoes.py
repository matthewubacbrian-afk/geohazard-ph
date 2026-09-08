from datetime import UTC, datetime
from pathlib import Path

from app.services import volcanoes
from ingestion.sources.phivolcs_volcano import parse_volcano_bulletins


def test_volcano_endpoint_serves_saved_source_and_failure_envelope(client, monkeypatch):
    from app.main import app

    html = (Path(__file__).resolve().parents[1] / "fixtures/phivolcs_volcano.html").read_text()

    def fetch(settings):
        return parse_volcano_bulletins(html, settings.phivolcs_volcano_url, datetime.now(UTC))

    monkeypatch.setattr(volcanoes, "fetch_volcano_bulletins", fetch)
    app.dependency_overrides[volcanoes.get_volcano_feed] = volcanoes.VolcanoFeed
    try:
        response = client.get("/api/v1/volcanoes")
        assert response.status_code == 200
        assert len(response.json()) == 5
        assert response.json()[0]["source"] == "phivolcs"
        assert response.json()[0]["retrieved_at"]

        def unavailable(_settings):
            raise volcanoes.PhivolcsFetchError("secret")

        monkeypatch.setattr(volcanoes, "fetch_volcano_bulletins", unavailable)
        response = client.get("/api/v1/volcanoes")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "volcano_feed_unavailable"
        assert "secret" not in response.text
    finally:
        app.dependency_overrides.pop(volcanoes.get_volcano_feed)
