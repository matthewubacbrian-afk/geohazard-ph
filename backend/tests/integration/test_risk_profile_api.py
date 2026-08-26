from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


def test_risk_profile_clusters_endpoint_returns_profiles(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RISK_PROFILE_EXPORT_PATH", "tests/fixtures/risk_profiles.json")

    response = TestClient(app).get("/api/v1/risk-profile/clusters")

    assert response.status_code == 200
    assert response.json()[0]["region_name"] == "Bicol Region"


def test_risk_profile_detail_endpoint_returns_region(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RISK_PROFILE_EXPORT_PATH", "tests/fixtures/risk_profiles.json")

    response = TestClient(app).get("/api/v1/risk-profile/Bicol%20Region")

    assert response.status_code == 200
    assert response.json()["label"] == "High"


def test_risk_profile_detail_endpoint_returns_404(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("RISK_PROFILE_EXPORT_PATH", "tests/fixtures/risk_profiles.json")

    response = TestClient(app).get("/api/v1/risk-profile/Unknown")

    assert response.status_code == 404
