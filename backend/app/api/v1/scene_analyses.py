import asyncio
import base64
import binascii
import json
from threading import Lock

from fastapi import APIRouter, Depends, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.config import get_settings
from app.core.errors import error_response
from app.schemas.scene_analysis import SceneAnalysisRequest, SceneAnalysisResponse
from app.services.scene_analysis import (
    MAX_IMAGE_BYTES,
    InvalidSceneImage,
    PanopticSegmenter,
    SceneAnalysisUnavailable,
    SceneImageQualityWarning,
    analyze_scene,
    decode_scene_image,
)
from app.services.scene_analysis_model import MODEL_ID, MODEL_REVISION, LocalPanopticSegmenter

MAX_REQUEST_BODY_BYTES = 5_593_000
LIMITATIONS = [
    "Visual scene cues only; this result does not determine whether any area is safe.",
    "Blur, obstruction, lighting, or viewpoint can hide visual cues. A single image cannot verify structural integrity, earthquake resistance, ground conditions, falling-glass or electrical hazards, egress, accessibility, routes, unseen areas, or changing conditions.",
]

router = APIRouter(prefix="/scene-analyses", tags=["scene-analyses"])
_analysis_semaphore = asyncio.Semaphore(1)
_segmenter_lock = Lock()
_segmenter: LocalPanopticSegmenter | None = None


def get_segmenter() -> LocalPanopticSegmenter:
    global _segmenter
    with _segmenter_lock:
        if _segmenter is None:
            settings = get_settings()
            _segmenter = LocalPanopticSegmenter(
                cache_dir=settings.scene_analysis_model_cache_dir,
            )
        return _segmenter


async def _read_bounded_body(request: Request) -> bytes:
    declared = request.headers.get("content-length")
    if declared:
        try:
            if int(declared) > MAX_REQUEST_BODY_BYTES:
                raise OverflowError
        except (ValueError, OverflowError):
            raise OverflowError from None
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        remaining = MAX_REQUEST_BODY_BYTES + 1 - total
        consumed = chunk[:remaining]
        total += len(consumed)
        if total > MAX_REQUEST_BODY_BYTES:
            raise OverflowError
        chunks.append(consumed)
    return b"".join(chunks)


@router.post("", response_model=SceneAnalysisResponse)
async def post_scene_analysis(
    request: Request,
    segmenter: PanopticSegmenter = Depends(get_segmenter),
) -> SceneAnalysisResponse | JSONResponse:
    async with _analysis_semaphore:
        return await _handle_scene_analysis(request, segmenter)


async def _handle_scene_analysis(
    request: Request,
    segmenter: PanopticSegmenter,
) -> SceneAnalysisResponse | JSONResponse:
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        return error_response(422, "invalid_scene_image", "A JSON JPEG image request is required")
    try:
        body = await _read_bounded_body(request)
    except OverflowError:
        return error_response(413, "scene_image_too_large", "The request exceeds the image size limit")
    try:
        parsed = SceneAnalysisRequest.model_validate_json(body)
        image_bytes = base64.b64decode(parsed.image_base64, validate=True)
        if len(image_bytes) > MAX_IMAGE_BYTES:
            return error_response(413, "scene_image_too_large", "The decoded image exceeds the size limit")
        image = decode_scene_image(image_bytes, parsed.mime_type)
        result = await run_in_threadpool(
            analyze_scene,
            image,
            segmenter,
            accept_quality_warning=parsed.accept_quality_warning,
        )
    except SceneImageQualityWarning:
        return error_response(
            422,
            "scene_image_quality_warning",
            "This photo may be blurry. Retake it or continue with reduced reliability.",
        )
    except (ValidationError, binascii.Error, UnicodeDecodeError, json.JSONDecodeError, InvalidSceneImage, ValueError):
        return error_response(422, "invalid_scene_image", "The request must contain a valid bounded JPEG image")
    except SceneAnalysisUnavailable:
        return error_response(503, "scene_analysis_unavailable", "Scene analysis is temporarily unavailable")

    version = f"{MODEL_ID}@{MODEL_REVISION}"
    return SceneAnalysisResponse(
        model_version=version,
        result_status=result.result_status,
        candidate_regions=[candidate.__dict__ | {"polygon": [point.__dict__ for point in candidate.polygon]} for candidate in result.candidate_regions],
        visual_cues=[cue.__dict__ for cue in result.visual_cues],
        limitations=LIMITATIONS,
    )
