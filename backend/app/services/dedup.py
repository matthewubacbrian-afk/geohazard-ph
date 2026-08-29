import hashlib

from app.schemas.hazard_event import HazardEvent


def dedup_key(event: HazardEvent) -> tuple[str, str | None]:
    if event.external_id is not None:
        return (event.source, event.external_id)
    # Content key lets null-external-id events be deduplicated by what they are.
    token = (
        f"{event.occurred_at.isoformat()}|{event.latitude}|{event.longitude}"
        f"|{event.magnitude if event.magnitude is not None else ''}"
    )
    return (event.source, f"content:{hashlib.sha256(token.encode()).hexdigest()[:16]}")
