from app.schemas.hazard_event import HazardEvent


def validate_event(payload: dict) -> HazardEvent:
    return HazardEvent.model_validate(payload)
