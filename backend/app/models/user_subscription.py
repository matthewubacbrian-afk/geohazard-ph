from dataclasses import dataclass


@dataclass(frozen=True)
class UserSubscriptionModel:
    id: str
    latitude: float
    longitude: float
    radius_km: float
