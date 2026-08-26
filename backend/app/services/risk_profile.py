from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from app.schemas.risk_profile import RiskProfile


class RiskProfileNotFound(Exception):
    pass


def load_profiles(path: Path | str) -> list[RiskProfile]:
    path = Path(path)
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [RiskProfile(**item) for item in data]


def get_profile(region_name: str, profiles: list[RiskProfile]) -> RiskProfile:
    lower_name = region_name.lower()
    for profile in profiles:
        if profile.region_name.lower() == lower_name:
            return profile
    raise RiskProfileNotFound(f"Risk profile not found for region: {region_name}")


def summarize_profiles(profiles: list[RiskProfile]) -> dict[str, int]:
    return dict(Counter(p.label for p in profiles))
