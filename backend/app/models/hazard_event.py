from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class HazardEventModel:
    id: str
    hazard_type: str
    source: str
    occurred_at: datetime
    latitude: float
    longitude: float
