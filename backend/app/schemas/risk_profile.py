from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RiskProfile(BaseModel):
    region_name: str
    cluster: int = 0
    label: str = ""
    confidence: float = 0.0
    feature_importances: dict[str, float] = {}
    model_version: str = ""
    generated_at: str = ""
    dataset_snapshot: str = ""


class RiskProfileSummary(BaseModel):
    label_counts: dict[str, int]
    total_profiles: int
