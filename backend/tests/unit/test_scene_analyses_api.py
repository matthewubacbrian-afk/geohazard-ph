import asyncio
import base64
import json
import logging
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from io import BytesIO
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image
from pydantic import ValidationError

from app.api.v1.scene_analyses import (
    LIMITATIONS,
    MAX_REQUEST_BODY_BYTES,
    _read_bounded_body,
    router,
)
from app.schemas.scene_analysis import CandidateRegion, SceneAnalysisResponse
from app.services.scene_analysis import PanopticSegment


def jpeg() -> bytes:
    image = Image.new("RGB", (16, 16), "green")
    data = BytesIO()
    image.save(data, format="JPEG")
    return data.getvalue()


class FakeSegmenter:
    def segment(self, image):
        return [PanopticSegment("grass", np.ones((image.height, image.width), dtype=bool), 0.8)]


@pytest.fixture
def client(monkeypatch):
    from app.api.v1 import scene_analyses

    override = lambda: FakeSegmenter()
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[scene_analyses.get_segmenter] = override
    return TestClient(app, raise_server_exceptions=False)


def payload(data: bytes | None = None, *, accept_quality_warning: bool = True) -> bytes:
    body = {
        "image_base64": base64.b64encode(data or jpeg()).decode(),
        "mime_type": "image/jpeg",
    }
    body["accept_quality_warning"] = accept_quality_warning
    return json.dumps(body).encode()


def test_schema_is_strict_and_consistent():
    response = SceneAnalysisResponse.model_validate({
        "model_version": "pinned",
        "result_status": "no_clear_candidate",
        "candidate_regions": [],
        "visual_cues": [],
        "limitations": LIMITATIONS,
    })
    assert response.model_dump().keys() == {
        "model_version", "result_status", "candidate_regions", "visual_cues", "limitations"
    }
    with pytest.raises(ValidationError):
        SceneAnalysisResponse.model_validate({**response.model_dump(), "unexpected": True})


def test_candidate_polygon_requires_four_distinct_clockwise_vertices():
    candidate = {
        "rank": 1,
        "surface_class": "grass",
        "polygon": [
            {"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0},
            {"x": 1.0, "y": 1.0}, {"x": 0.0, "y": 1.0},
            {"x": 0.0, "y": 0.0},
        ],
        "area_fraction": 0.5,
        "compactness": 0.8,
        "model_confidence": 0.9,
        "ranking_score": 0.8,
    }
    CandidateRegion.model_validate(candidate)
    with pytest.raises(ValidationError):
        CandidateRegion.model_validate({**candidate, "polygon": [
            {"x": 0.0, "y": 0.0}, {"x": 0.0, "y": 1.0},
            {"x": 1.0, "y": 1.0}, {"x": 1.0, "y": 0.0},
            {"x": 0.0, "y": 0.0},
        ]})


def test_fake_segmenter_success_and_exact_wire_fields(client):
    response = client.post("/api/v1/scene-analyses", content=payload(), headers={"content-type": "application/json"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"model_version", "result_status", "candidate_regions", "visual_cues", "limitations"}
    assert body["result_status"] == "candidates_found"
    assert body["candidate_regions"][0]["surface_class"] == "grass"
    assert set(body["candidate_regions"][0]) == {
        "rank", "surface_class", "polygon", "area_fraction", "compactness", "model_confidence", "ranking_score"
    }


def test_blurry_image_returns_quality_warning_unless_user_overrides(client):
    response = client.post(
        "/api/v1/scene-analyses",
        content=payload(jpeg(), accept_quality_warning=False),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "scene_image_quality_warning"
    assert "blurry" in response.json()["error"]["message"].lower()


def test_quality_warning_is_default_when_override_field_is_omitted(client):
    request_body = json.loads(payload(jpeg()))
    request_body.pop("accept_quality_warning")
    response = client.post(
        "/api/v1/scene-analyses",
        json=request_body,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "scene_image_quality_warning"


def test_quality_override_reaches_model(client):
    response = client.post(
        "/api/v1/scene-analyses",
        content=payload(jpeg(), accept_quality_warning=True),
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 200


def test_endpoint_model_version_uses_approved_fixed_pin(client, monkeypatch):
    from app.api.v1 import scene_analyses

    class OverrideSettings:
        scene_analysis_model_cache_dir = None
        scene_analysis_model_id = "attacker/alternate-model"
        scene_analysis_model_revision = "mutable"

    monkeypatch.setattr(scene_analyses, "get_settings", lambda: OverrideSettings())
    response = client.post("/api/v1/scene-analyses", content=payload(), headers={"content-type": "application/json"})

    assert response.status_code == 200
    assert response.json()["model_version"] == (
        "facebook/detr-resnet-50-panoptic@d53b52a799403a8867920f82c869e40732b47037"
    )


def test_cpu_analysis_runs_off_event_loop_thread(monkeypatch):
    from starlette.requests import Request

    from app.api.v1 import scene_analyses

    caller_thread = threading.get_ident()
    analysis_thread = None
    original_analyze_scene = scene_analyses.analyze_scene

    def record_analysis_thread(image, segmenter, *, accept_quality_warning=False):
        nonlocal analysis_thread
        analysis_thread = threading.get_ident()
        return original_analyze_scene(
            image, segmenter, accept_quality_warning=accept_quality_warning
        )

    monkeypatch.setattr(scene_analyses, "analyze_scene", record_analysis_thread)
    request_body = payload()
    request_messages = iter([
        {"type": "http.request", "body": request_body, "more_body": False},
    ])

    async def receive():
        return next(request_messages)

    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "POST", "scheme": "http", "path": "/api/v1/scene-analyses",
        "raw_path": b"/api/v1/scene-analyses", "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
        "client": ("test", 1), "server": ("test", 80), "state": {},
    }
    response = asyncio.run(scene_analyses.post_scene_analysis(Request(scope, receive), FakeSegmenter()))

    assert response.model_version.startswith("facebook/detr-resnet-50-panoptic@")
    assert analysis_thread != caller_thread


def test_concurrent_dependency_resolution_creates_one_segmenter(monkeypatch, tmp_path):
    from app.api.v1 import scene_analyses

    calls = 0
    created = []
    barrier = threading.Barrier(8)

    class Settings:
        scene_analysis_model_cache_dir = tmp_path

    class Segmenter:
        def __init__(self, cache_dir):
            nonlocal calls
            calls += 1
            time.sleep(0.03)
            created.append(self)

    monkeypatch.setattr(scene_analyses, "get_settings", lambda: Settings())
    monkeypatch.setattr(scene_analyses, "LocalPanopticSegmenter", Segmenter)
    monkeypatch.setattr(scene_analyses, "_segmenter", None)

    def resolve_dependency():
        barrier.wait()
        return scene_analyses.get_segmenter()

    with ThreadPoolExecutor(max_workers=8) as pool:
        segmenters = list(pool.map(lambda _: resolve_dependency(), range(8)))

    assert calls == 1
    assert all(segmenter is created[0] for segmenter in segmenters)


def test_model_adapter_serializes_concurrent_inference(monkeypatch, tmp_path):
    from app.services.scene_analysis_model import LocalPanopticSegmenter

    state_lock = threading.Lock()
    active_calls = 0
    maximum_active_calls = 0

    class Processor:
        def __call__(self, **kwargs):
            return {}

        def post_process_panoptic_segmentation(self, output, target_sizes):
            return [{"segments_info": [], "segmentation": np.zeros(target_sizes[0])}]

    class Model:
        config = SimpleNamespace(id2label={})

        def __call__(self, **kwargs):
            nonlocal active_calls, maximum_active_calls
            with state_lock:
                active_calls += 1
                maximum_active_calls = max(maximum_active_calls, active_calls)
            time.sleep(0.03)
            with state_lock:
                active_calls -= 1
            return object()

    model = LocalPanopticSegmenter(tmp_path)
    load_calls = 0

    def load_once():
        nonlocal load_calls
        if model._model is None:
            load_calls += 1
            time.sleep(0.03)
            model._processor = Processor()
            model._model = Model()

    model._load = load_once
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace(inference_mode=nullcontext))
    image = Image.new("RGB", (2, 2))

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(model.segment, [image] * 4))

    assert results == [[], [], [], []]
    assert load_calls == 1
    assert maximum_active_calls == 1


@pytest.mark.parametrize("content,content_type", [
    (b"{", "application/json"),
    (b'{"image_base64":"!!!","mime_type":"image/jpeg"}', "application/json"),
    (b'{"image_base64":"eA==","mime_type":"image/png"}', "application/json"),
    (b'{"image_base64":"eA==","mime_type":"image/jpeg"}', "application/json"),
    (payload(), "text/plain"),
])
def test_invalid_request_returns_typed_422(client, content, content_type):
    response = client.post("/api/v1/scene-analyses", content=content, headers={"content-type": content_type})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_scene_image"


@pytest.mark.parametrize("length", [None, 5_593_001])
def test_body_over_cap_returns_typed_413_without_reading_body(client, length):
    headers = {"content-type": "application/json"}
    if length is not None:
        headers["content-length"] = str(length)
    response = client.post("/api/v1/scene-analyses", content=b"x" * 5_593_001, headers=headers)
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "scene_image_too_large"


def test_raw_asgi_chunked_body_cap_plus_one_without_content_length(client):
    body = b"x" * (MAX_REQUEST_BODY_BYTES + 1)
    receive_calls = 0
    sent = []

    async def receive():
        nonlocal receive_calls
        receive_calls += 1
        if receive_calls == 1:
            return {"type": "http.request", "body": body, "more_body": True}
        return {"type": "http.request", "body": b"should-not-be-read", "more_body": False}

    async def send(message):
        sent.append(message)

    scope = {
        "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
        "method": "POST", "scheme": "http", "path": "/api/v1/scene-analyses",
        "raw_path": b"/api/v1/scene-analyses", "query_string": b"", "root_path": "",
        "headers": [(b"content-type", b"application/json")], "client": ("test", 1),
        "server": ("test", 80), "state": {},
    }
    asyncio.run(client.app(scope, receive, send))
    status = next(message["status"] for message in sent if message["type"] == "http.response.start")
    assert status == 413
    assert receive_calls == 1
    assert len(body) == MAX_REQUEST_BODY_BYTES + 1


def test_exact_cap_is_accepted_and_invalid_json_is_422(client):
    response = client.post("/api/v1/scene-analyses", content=b" " * 5_593_000, headers={"content-type": "application/json"})
    assert response.status_code == 422


def test_empty_body_is_typed_422(client):
    response = client.post("/api/v1/scene-analyses", content=b"", headers={"content-type": "application/json"})
    assert response.status_code == 422


def test_stream_reader_consumes_at_most_cap_plus_one():
    observed = []

    class CountingBytes(bytes):
        def __getitem__(self, key):
            if isinstance(key, slice):
                observed.append(key.stop)
            return super().__getitem__(key)

    class StreamingRequest:
        def __init__(self):
            self.headers = {}

        async def stream(self):
            yield CountingBytes(b"x" * (MAX_REQUEST_BODY_BYTES + 100))

    with pytest.raises(OverflowError):
        asyncio.run(_read_bounded_body(StreamingRequest()))
    assert observed == [MAX_REQUEST_BODY_BYTES + 1]


def test_model_unavailable_is_typed_503(client, monkeypatch):
    from app.api.v1 import scene_analyses
    from app.services.scene_analysis import SceneAnalysisUnavailable

    class UnavailableSegmenter:
        def segment(self, image):
            raise SceneAnalysisUnavailable

    client.app.dependency_overrides[scene_analyses.get_segmenter] = lambda: UnavailableSegmenter()
    response = client.post("/api/v1/scene-analyses", content=payload(), headers={"content-type": "application/json"})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "scene_analysis_unavailable"


def test_body_is_not_logged_or_echoed(client, caplog):
    secret = b"private-image-marker"
    content = json.dumps({"image_base64": base64.b64encode(secret).decode(), "mime_type": "image/jpeg"}).encode()
    with caplog.at_level(logging.DEBUG):
        response = client.post("/api/v1/scene-analyses", content=content, headers={"content-type": "application/json"})
    assert secret.decode() not in caplog.text
    assert secret.decode() not in response.text


def test_endpoint_does_not_persist_images(client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = client.post("/api/v1/scene-analyses", content=payload(), headers={"content-type": "application/json"})
    assert response.status_code == 200
    assert list(tmp_path.iterdir()) == []
