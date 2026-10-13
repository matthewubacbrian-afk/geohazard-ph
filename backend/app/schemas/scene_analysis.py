from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class SceneAnalysisRequest(StrictSchema):
    image_base64: str = Field(min_length=1)
    mime_type: Literal["image/jpeg"]
    accept_quality_warning: bool = False


class ImagePoint(StrictSchema):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class CandidateRegion(StrictSchema):
    rank: int = Field(ge=1, le=5)
    surface_class: Literal[
        "floor-other", "floor-stone", "floor-tile", "floor-wood", "ground-other",
        "road", "pavement", "grass", "gravel",
    ]
    polygon: list[ImagePoint] = Field(min_length=5, max_length=64)
    area_fraction: float = Field(gt=0, le=1)
    compactness: float = Field(ge=0, le=1)
    model_confidence: float = Field(ge=0, le=1)
    ranking_score: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def validate_closed_polygon(self):
        if self.polygon[0] != self.polygon[-1]:
            raise ValueError("polygon must be closed")
        vertices = self.polygon[:-1]
        if len({(point.x, point.y) for point in vertices}) < 4:
            raise ValueError("polygon must have at least four distinct vertices")
        signed_area = sum(
            first.x * second.y - second.x * first.y
            for first, second in zip(vertices, vertices[1:] + vertices[:1])
        ) / 2
        if signed_area <= 0:
            raise ValueError("polygon must be clockwise in image coordinates")
        return self


class VisualCue(StrictSchema):
    class_name: str = Field(min_length=1)
    model_confidence: float = Field(ge=0, le=1)


class SceneAnalysisResponse(StrictSchema):
    model_version: str = Field(min_length=1)
    result_status: Literal["candidates_found", "no_clear_candidate"]
    candidate_regions: list[CandidateRegion] = Field(max_length=5)
    visual_cues: list[VisualCue]
    limitations: list[str] = Field(min_length=2, max_length=2)

    @model_validator(mode="after")
    def validate_limitations(self):
        if self.limitations != [
            "Visual scene cues only; this result does not determine whether any area is safe.",
            "Blur, obstruction, lighting, or viewpoint can hide visual cues; one image cannot assess structural stability, hidden hazards, or route access.",
        ]:
            raise ValueError("limitations must match the fixed scene-analysis caveats")
        return self

    @model_validator(mode="after")
    def validate_result_status(self):
        has_candidates = bool(self.candidate_regions)
        if has_candidates != (self.result_status == "candidates_found"):
            raise ValueError("result_status must agree with candidate_regions")
        return self
