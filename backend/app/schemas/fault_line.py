from pydantic import BaseModel


class FaultLine(BaseModel):
    id: str
    name: str
    source: str
    max_magnitude_estimate: float | None = None
