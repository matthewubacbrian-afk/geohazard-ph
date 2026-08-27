from dataclasses import dataclass


@dataclass(frozen=True)
class FaultLineModel:
    id: str
    name: str
    source: str
