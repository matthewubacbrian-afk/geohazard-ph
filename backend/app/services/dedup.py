from app.schemas.hazard_event import HazardEvent


def dedup_key(event: HazardEvent) -> tuple[str, str | None]:
    return (event.source, event.external_id)
