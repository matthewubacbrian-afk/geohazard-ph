import json
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_db_session
from app.api.v1 import faults, volcano_zones
from app.core.errors import register_error_handlers
from app.services.static_layers import replace_layer


@pytest.mark.parametrize("path", ["/faults", "/volcano-zones"])
def test_reference_route_serializes_provenance_and_empty_states(path):
    app = FastAPI()
    register_error_handlers(app)
    app.include_router(faults.router)
    app.include_router(volcano_zones.router)
    geometry = {"type": "LineString", "coordinates": [[121, 14], [122, 15]]}
    row = SimpleNamespace(
        id="1",
        external_id="source-1",
        name="Reference",
        source="gem",
        source_url="https://example.org/data",
        license_name="test",
        dataset_version="v1",
        imported_at=datetime(2026, 9, 10, tzinfo=UTC),
        source_properties={"reference": "Original publication"},
    )
    results = [(row, json.dumps(geometry))]

    class FakeSession:
        def execute(self, statement):
            assert "ORDER BY" in str(statement)
            return SimpleNamespace(all=lambda: results)

    app.dependency_overrides[get_db_session] = lambda: FakeSession()
    with TestClient(app) as client:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()[0]["geometry"] == geometry
        assert response.json()[0]["source_properties"] == row.source_properties
        assert response.json()[0]["imported_at"] == "2026-09-10T00:00:00Z"
        results.clear()
        assert client.get(path).json() == []
        assert (
            client.get(path, params={"source": "bad"}).json()["error"]["code"] == "validation_error"
        )


def test_empty_import_never_opens_a_transaction():
    class FakeSession:
        def begin(self):
            raise AssertionError("Empty input must not reach persistence")

    with pytest.raises(ValueError, match="must contain"):
        replace_layer(FakeSession(), [], kind="faults", source="gem")
