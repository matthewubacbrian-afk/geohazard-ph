from fastapi import FastAPI, HTTPException, Query
from fastapi.testclient import TestClient

from app.core.errors import register_error_handlers


def test_error_envelopes_hide_validation_input_and_internal_details():
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/test")
    def route(number: int = Query()):
        if number == 0:
            raise HTTPException(
                404, detail={"code": "sample_not_found", "message": "Missing sample"}
            )
        raise RuntimeError("secret database path")

    client = TestClient(app, raise_server_exceptions=False)
    for value, status, code in [
        ("private-token", 422, "validation_error"),
        ("0", 404, "sample_not_found"),
        ("1", 500, "internal_error"),
    ]:
        response = client.get("/test", params={"number": value})
        assert response.status_code == status
        assert response.json()["error"]["status"] == status
        assert response.json()["error"]["code"] == code
        assert "private-token" not in response.text
        assert "secret database path" not in response.text


def test_structured_logging_retains_ingest_counts():
    import json
    import logging

    from app.core.logging import StructuredFormatter

    record = logging.makeLogRecord(
        {
            "levelname": "INFO",
            "name": "ingestion",
            "msg": "complete",
            "source": "usgs",
            "fetched": 3,
            "processed": 2,
        }
    )
    payload = json.loads(StructuredFormatter().format(record))
    assert payload["fetched"] == 3
    assert payload["processed"] == 2
    assert payload["source"] == "usgs"
