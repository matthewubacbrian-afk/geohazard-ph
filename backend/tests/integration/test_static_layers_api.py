from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.static_layers import replace_layer
from ingestion.sources.static_layers import parse_features


def test_import_refresh_api_and_source_isolation(client, migrated_engine):
    with migrated_engine.begin() as connection:
        connection.execute(text("TRUNCATE fault_lines, volcano_zones"))
    for kind, path, geometry in [
        ("faults", "/api/v1/faults", {"type": "LineString", "coordinates": [[121, 14], [122, 15]]}),
        (
            "volcano_zones",
            "/api/v1/volcano-zones",
            {"type": "Polygon", "coordinates": [[[121, 14], [122, 14], [122, 15], [121, 14]]]},
        ),
    ]:
        assert client.get(path).json() == []
        for source in ["gem", "phivolcs"]:
            rows = parse_features(
                [{"id": "1", "properties": {"name": "Reference"}, "geometry": geometry}],
                kind=kind,
                source=source,
                source_url="https://example.org/source",
                license_name="test",
                dataset_version="v1",
            )
            with Session(migrated_engine) as session:
                replace_layer(session, rows, kind=kind, source=source)
        before = client.get(path).json()
        assert len(before) == 2
        assert before[0]["geometry"] == geometry
        assert before[0]["imported_at"]
        with Session(migrated_engine) as session:
            replace_layer(session, rows, kind=kind, source="phivolcs")
        assert [row["id"] for row in client.get(path).json()] == [row["id"] for row in before]
        assert len(client.get(path, params={"source": "gem"}).json()) == 1
        assert (
            client.get(path, params={"source": "invalid"}).json()["error"]["code"]
            == "validation_error"
        )


def test_refresh_removes_obsolete_features_and_rolls_back_failure(client, migrated_engine):
    import pytest
    from sqlalchemy.exc import IntegrityError

    with migrated_engine.begin() as connection:
        connection.execute(text("TRUNCATE fault_lines"))
    rows = parse_features(
        [
            {
                "id": identifier,
                "properties": {"name": identifier},
                "geometry": {"type": "LineString", "coordinates": [[121, 14], [122, 15]]},
            }
            for identifier in ["old", "retained"]
        ],
        kind="faults",
        source="gem",
        source_url="https://example.org",
        license_name="test",
        dataset_version="v1",
    )
    with Session(migrated_engine) as session:
        replace_layer(session, rows, kind="faults", source="gem")
    with Session(migrated_engine) as session:
        replace_layer(session, rows[1:], kind="faults", source="gem")
    assert [row["external_id"] for row in client.get("/api/v1/faults").json()] == ["retained"]
    with Session(migrated_engine) as session, pytest.raises(IntegrityError):
        replace_layer(session, [rows[0], rows[0]], kind="faults", source="gem")
    assert [row["external_id"] for row in client.get("/api/v1/faults").json()] == ["retained"]
