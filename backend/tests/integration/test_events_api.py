from fastapi.testclient import TestClient

from app.main import app


def test_events_endpoint_returns_sample_event():
    response = TestClient(app).get("/api/v1/events")

    assert response.status_code == 200
    assert response.json()[0]["source"] == "usgs"
