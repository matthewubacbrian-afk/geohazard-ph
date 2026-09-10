import json
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.fault_line import FaultLine as FaultLineORM
from app.models.volcano_zone import VolcanoZone as VolcanoZoneORM
from app.schemas.fault_line import FaultLine
from app.schemas.static_layer import StaticFeature, StaticLayer
from app.schemas.volcano_zone import VolcanoZone

LAYER_MODELS = {"faults": (FaultLineORM, FaultLine), "volcano_zones": (VolcanoZoneORM, VolcanoZone)}


def replace_layer(session: Session, rows: list[StaticFeature], *, kind: str, source: str) -> int:
    """Replace one source atomically, removing obsolete features on quarterly refresh."""
    if not rows or any(row.source != source for row in rows):
        raise ValueError("Import must contain features belonging to one source")
    model, _ = LAYER_MODELS[kind]
    with session.begin():
        # Serialize refreshes for this source/layer, including the initial empty table.
        session.execute(
            select(func.pg_advisory_xact_lock(func.hashtext(f"static-layer:{kind}:{source}")))
        )
        session.execute(delete(model).where(model.source == source))
        for row in rows:
            values = row.model_dump(mode="json")
            values["geometry"] = func.ST_SetSRID(
                func.ST_GeomFromGeoJSON(json.dumps(row.geometry)), 4326
            )
            session.add(
                model(id=str(uuid5(NAMESPACE_URL, f"{kind}:{source}:{row.external_id}")), **values)
            )
    return len(rows)


def list_layers(session: Session, *, kind: str, source: str | None = None) -> list[StaticLayer]:
    model, schema = LAYER_MODELS[kind]
    statement = select(model, func.ST_AsGeoJSON(model.geometry)).order_by(model.source, model.id)
    if source:
        statement = statement.where(model.source == source)
    return [
        schema(
            id=row.id,
            external_id=row.external_id,
            name=row.name,
            source=row.source,
            source_url=row.source_url,
            license_name=row.license_name,
            dataset_version=row.dataset_version,
            imported_at=row.imported_at,
            source_properties=row.source_properties,
            geometry=json.loads(geometry),
        )
        for row, geometry in session.execute(statement).all()
    ]
