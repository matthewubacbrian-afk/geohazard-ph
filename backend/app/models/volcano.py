from dataclasses import dataclass


@dataclass(frozen=True)
class VolcanoModel:
    id: str
    name: str
    current_alert_level: int | None = None
