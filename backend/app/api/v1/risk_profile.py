from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas.risk_profile import RiskProfile
from app.services.risk_profile import RiskProfileNotFound, get_profile, load_profiles

router = APIRouter(prefix="/risk-profile", tags=["risk-profile"])


@router.get("/clusters", response_model=list[RiskProfile])
def list_risk_profiles() -> list[RiskProfile]:
    return load_profiles(get_settings().risk_profile_export_path)


@router.get("/{region_name}", response_model=RiskProfile)
def retrieve_risk_profile(region_name: str) -> RiskProfile:
    profiles = load_profiles(get_settings().risk_profile_export_path)
    try:
        return get_profile(region_name, profiles)
    except RiskProfileNotFound as exc:
        raise HTTPException(
            status_code=404, detail={"code": "risk_profile_not_found", "message": str(exc)}
        ) from exc
