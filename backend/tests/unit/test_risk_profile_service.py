from pathlib import Path

import pytest

from app.schemas.risk_profile import RiskProfile
from app.services.risk_profile import RiskProfileNotFound, get_profile, load_profiles, summarize_profiles


FIXTURE = Path("tests/fixtures/risk_profiles.json")


def test_summarize_profiles_counts_labels():
    profiles = [
        RiskProfile(region_name="Bicol Region", cluster=2, label="High", confidence=0.82),
        RiskProfile(region_name="Eastern Visayas", cluster=2, label="High", confidence=0.79),
        RiskProfile(region_name="Palawan", cluster=0, label="Low", confidence=0.91),
    ]

    assert summarize_profiles(profiles) == {"High": 2, "Low": 1}


def test_load_profiles_reads_generated_artifact():
    profiles = load_profiles(FIXTURE)

    assert [p.region_name for p in profiles[:2]] == ["ARMM", "Bicol Region"]
    assert profiles[1].label == "Moderate"
    assert profiles[1].feature_importances["event_count"] == 0.2957


def test_get_profile_is_case_insensitive():
    profile = get_profile("bicol region", load_profiles(FIXTURE))

    assert profile.label == "Moderate"


def test_get_profile_raises_for_missing_region():
    with pytest.raises(RiskProfileNotFound):
        get_profile("Unknown Region", load_profiles(FIXTURE))
