from fastapi import APIRouter

router = APIRouter(prefix="/hazards", tags=["hazards"])


@router.get("/{hazard_type}")
def get_hazard_summary(hazard_type: str) -> dict[str, str]:
    return {"hazard_type": hazard_type, "status": "stub"}
