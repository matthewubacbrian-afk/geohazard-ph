from dataclasses import dataclass


@dataclass(frozen=True)
class LandslideZoneModel:
    id: str
    name: str
    susceptibility: str
