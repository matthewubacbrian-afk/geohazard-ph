from pydantic import BaseModel


class Volcano(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    current_alert_level: int | None = None
