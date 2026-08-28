from sqlalchemy import inspect

from app.models import HazardEvent


def test_hazard_event_model_table_and_columns():
    columns = {c.name: c for c in inspect(HazardEvent).columns}

    assert HazardEvent.__tablename__ == "hazard_events"
    for col in [
        "id",
        "hazard_type",
        "source",
        "external_id",
        "magnitude",
        "depth_km",
        "latitude",
        "longitude",
        "place_name",
        "alert_level",
        "location",
        "raw_payload",
        "occurred_at",
        "created_at",
    ]:
        assert col in columns


def test_hazard_event_unique_constraint_on_source_external_id():
    constraints = [
        c
        for c in inspect(HazardEvent).local_table.constraints
        if c.name == "uq_hazard_events_source_external_id"
    ]
    assert len(constraints) == 1
