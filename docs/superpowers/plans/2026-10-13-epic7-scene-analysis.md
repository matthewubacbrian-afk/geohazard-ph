# Epic 7 Camera-Based Scene Review — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a privacy-preserving camera scene review flow to web and mobile that uses one Python vision endpoint to rank visible floor/ground candidates and explain the visual cues without claiming safety.

**Architecture:** Capture a still image in each client, downscale/re-encode to bounded JPEG, and send the same strict JSON contract to FastAPI. The backend validates the request in bounded memory, runs the pinned DETR ResNet-50 panoptic model through an injected adapter, extracts normalized connected-region polygons, and ranks them with the approved formula. Clients retain only the local preview while the feature screen is active, display the same candidate polygons and checklist, and clear transient image data on retake or exit.

**Tech Stack:** FastAPI, Pydantic v2, Python 3.11+, Pillow, pinned CPU PyTorch/Transformers or a measured compatible CPU runtime, React 18, TypeScript, MediaDevices Canvas API, React Native CLI, react-native-image-picker, pytest, Ruff, Vitest, Jest.

**Spec:** `docs/superpowers/specs/2026-10-13-epic7-scene-analysis-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/api-contracts.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, `docs/glossary.md`, and `docs/git-workflow.md`.
- Work only on `feat/epic7-scene-analysis` in its attached worktree. Conventional Commits; one logical change per commit.
- Write a failing test before each behavior change; run it and confirm the expected failure before implementation.
- Keep all Python image decode, orientation normalization, inference, and mask processing in memory. Consume ASGI `request.stream()` incrementally and never read more than 5,593,000 request bytes; never log or persist request bodies/images.
- Maximum decoded JPEG: 4 MiB, 4096 pixels per edge, 12,000,000 pixels total. Maximum candidates: 5, each polygon at most 64 points and closed; normalized top-left-origin coordinates in `[0, 1]`.
- Ranking: `min(area_fraction/largest_area_fraction, 1) * 0.50 + min(4*pi*pixel_area/perimeter_pixels^2, 1) * 0.30 + model_confidence * 0.20`. It is a visual-review ordering only. Never call it a safety probability/confidence or show a “safe” label.
- Model: `facebook/detr-resnet-50-panoptic`, immutable revision `d53b52a799403a8867920f82c869e40732b47037`; runtime must load local cached files only. Do not download weights in request handling or CI tests.
- API path `POST /api/v1/scene-analyses`; request `{ "image_base64": "...", "mime_type": "image/jpeg" }`; return the exact response fields in the spec. Add 413 (`scene_image_too_large`) to all applicable status/error docs.
- All user-facing states must retain the safety caveat: “Visual cues only—not a safety assessment. Verify conditions and follow official emergency guidance.” Indoor and outdoor scenes use the same model and algorithm.
- No database schema, migration, image history, gallery upload, model training, or external inference API.
- Verification before feature completion: backend pytest and Ruff; web `npm test` and `npm run build`; mobile `npm test` and TypeScript/native build where available; `python scripts/verify_structure.py`; `git diff --check`. Report camera hardware smoke checks separately if no camera-capable device is available.

## File Map

- `backend/app/services/scene_analysis.py`: bounded image decode, model adapter, candidate extraction, ranking, polygon/cue output.
- `backend/app/schemas/scene_analysis.py`: strict request and response types.
- `backend/app/api/v1/scene_analyses.py`, `backend/app/main.py`: streaming cap, route adapter and router registration.
- `backend/tests/unit/test_scene_analysis.py`, `backend/tests/integration/test_scene_analyses_api.py`: pure algorithm and route/error/privacy coverage with fakes.
- `backend/app/config.py`, `backend/pyproject.toml`, Dockerfiles and Compose files: pinned runtime/model provisioning only after resource measurement.
- `web/src/api/sceneAnalysis.ts`, `web/src/types/sceneAnalysis.ts`: exact typed JSON contract/client.
- `web/src/pages/SceneAnalysis.tsx` and CSS module, `web/src/App.tsx`, `web/src/types/views.ts`, `web/src/components/layout/TopNav.tsx`: capture/review/overlay/checklist UI, route and navigation entry.
- `web/tests/SceneAnalysis.test.tsx`: browser permission, state, cleanup, mapping, and rendering.
- `mobile/src/services/sceneAnalysis.ts`, `mobile/src/types/sceneAnalysis.ts`: camera result handling, upload and explicit API mapping.
- `mobile/src/screens/SceneAnalysisScreen.tsx`, `mobile/src/navigation/RootNavigator.tsx`, native permission config: mobile screen/navigation/permission setup.
- `mobile/tests/sceneAnalysis.test.ts`: pure service/state mapping tests with mocked picker/fetch.
- `docs/glossary.md`, `CODING_STANDARDS.md`, `docs/api-contracts.md`, `docs/error-handling-and-logging.md`, `docs/data-sources.md`, `docs/runbook.md`, `.env.example`, `README.md`, `docs/mobile-runtime-smoke-test.md`, `docs/project-status.md`: canonical contracts, model/provisioning assumptions, capture instructions, and final measured status.

---

### Task 1: Prove model/runtime packaging before wiring deployments

**Files:**
- Modify: `backend/pyproject.toml` only after checking the selected dependency versions and CPU wheel source.
- Modify: `backend/Dockerfile`, `backend/Dockerfile.prod`, `docker-compose.yml`, `docker-compose.prod.yml` only if a measured deployable packaging approach is available.
- Test/record: `docs/data-sources.md`, `docs/runbook.md`, and plan notes.

**Interfaces:**
- The model adapter loads `DetrImageProcessor` and `DetrForSegmentation` with the fixed model ID/revision and `local_files_only=True`. `PanopticSegmenter.segment(image: PIL.Image.Image) -> Sequence[PanopticSegment]` returns each `segments_info` entry as `class_name`, `mask: np.ndarray[bool]` (same height/width as the input), and `model_confidence` from its score. It maps `post_process_panoptic_segmentation` segment IDs to masks; it imports Transformers/Torch lazily and never accesses the network.
- The initial source revision is `d53b52a799403a8867920f82c869e40732b47037`; preserve it exactly unless the source is unavailable/license-invalid, in which case stop and revise the spec before changing model.

- [x] **Step 1: Inspect deployment and Python environments**

Run `Get-Content backend/Dockerfile`, `Get-Content backend/Dockerfile.prod`, `Get-Content docker-compose.yml`, `Get-Content docker-compose.prod.yml`, `Get-Content compose.staging.yml`, and inspect `.github/workflows/deploy-staging.yml`. Record the Python base versions, image targets, staging memory/architecture assumptions, and whether API and ingestion worker share one image. Confirm the current worktree is clean except for the plan file.

- [x] **Step 2: Verify model artifacts and license**

Use the exact Hugging Face repository revision in the model URL; verify model card license, config labels, and files needed by Transformers. Record the immutable revision, source/license, and selected surface labels in `docs/data-sources.md`. Do not fetch/store full weights in the repository.

- [ ] **Step 3: Measure CPU dependency and artifact cost — host results recorded; Python 3.12/deployment target remains unverified**

Resolve Python 3.12-compatible CPU-only Torch, Transformers and Pillow versions. Build a throwaway local Docker image or isolated package install and record compressed wheel size, installed image delta, model artifact size, cold load time, CPU inference time, and peak resident memory on a small image. Do not stage generated weights or the throwaway image. The isolated Windows CPython 3.11 host package measurements are recorded below, but this step stays open until Python 3.12/Linux dependency resolution and deployment-target image impact are verified.

- [ ] **Step 4: Gate deployment packaging on observed limits — deployment fit unverified**

If the existing API image and staging memory can support the measured package/model, pin exact versions and CPU wheel index and provision the pinned model as a build-time/local artifact without adding weights to Git. Keep model inference lazy and ensure the ingestion worker does not initialize the model. Otherwise, keep heavyweight dependencies out of the default API/worker image, document the measured constraint, and design an optional CPU scene-analysis deployment target that still serves the same `/api/v1/scene-analyses` contract through the existing API routing boundary; update the approved spec and ask for approval before implementing the changed hosting boundary.

- [ ] **Step 5: Verify artifact loading is offline — host cache load passed; typed unavailable handling pending adapter**

Run the packaged model loader with networking disabled and a pre-provisioned local revision. Expected: it loads only that cached commit, reports the pinned `model_version`, and raises the typed unavailable error when files are missing. Run a single small CPU inference and record elapsed time and peak RSS; do not claim safety or quality validation.

**Preflight evidence (2026-10-13):** Steps 1–2 are complete; host-only measurements for Step 3 are recorded, but the step remains open pending Python 3.12/Linux package resolution and deployment image impact. The isolated Windows x64 / CPython 3.11.9 run measured dependency pins, wheel/install sizes, model artifact size, cache-only load, CPU inference, and peak RSS; see `docs/data-sources.md`. The PyTorch CPU index lists the chosen Torch/torchvision pins for CPython 3.12 on both target Linux architectures, but those wheels were not installed. The offline load required `DetrConfig.use_pretrained_backbone=False` to avoid a separate timm checkpoint fetch; checkpoint load reported zero missing keys and four unused `num_batches_tracked` buffers. A socket guard and Hugging Face offline environment flags were active during inference; a missing local directory raised offline `OSError`. This does not verify CPython 3.12/Linux package resolution or inference, staging resource fit, or Docker image delta. Docker Desktop's Linux daemon is unavailable; staging publishes `linux/amd64` and `linux/arm64`, runs API/migration/worker from a shared image, sets no per-service memory/CPU limits, and documents a total 2 OCPU / 12 GB host allowance. Do not change `pyproject.toml` or deployment images until those deployment-target costs and resource headroom are measured. Step 5's conversion to the future typed unavailable error must be verified when the adapter exists; no adapter code is part of Task 1.

- [x] **Step 6: Record measured model preflight documentation**

Run `git diff --check`, inspect the staged file list, and commit only the Task 1 preflight documentation as `docs: record epic 7 model preflight`. Do not include dependency or deployment-image changes until the deployment-target gate is verified. The follow-up documentation commit is `058e625`; the earlier docs-only commit `d99ef9f` remains in history with its original subject.

### Task 2: Define and implement deterministic in-memory analysis

**Files:**
- Create: `backend/app/services/scene_analysis.py`
- Create: `backend/tests/unit/test_scene_analysis.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class PanopticSegment:
    class_name: str
    mask: np.ndarray  # bool [height, width]
    model_confidence: float

class PanopticSegmenter(Protocol):
    def segment(self, image: Image.Image) -> Sequence[PanopticSegment]: ...

def decode_scene_image(image_bytes: bytes, mime_type: str) -> Image.Image: ...
def analyze_scene(image: Image.Image, segmenter: PanopticSegmenter) -> SceneAnalysisResult: ...
```

Use frozen dataclasses: `ImagePoint(x: float, y: float)`, `CandidateRegion(rank: int, surface_class: str, polygon: tuple[ImagePoint, ...], area_fraction: float, compactness: float, model_confidence: float, ranking_score: float)`, `VisualCue(class_name: str, model_confidence: float)`, and `SceneAnalysisResult(result_status: Literal["candidates_found", "no_clear_candidate"], candidate_regions: tuple[CandidateRegion, ...], visual_cues: tuple[VisualCue, ...])`. The route adds `model_version` and the two fixed limitations from the response schema. Supported candidate labels are exactly `floor-other`, `floor-stone`, `floor-tile`, `floor-wood`, `ground-other`, `road`, `pavement`, `grass`, and `gravel` in the pinned config; do not use a generic `floor` label. Use deterministic 4-connected component labeling over the binary masks. Trace each component outer boundary from pixel-edge transitions and simplify it with a pure-Python Douglas–Peucker helper implemented in this module; do not add SciPy/OpenCV solely for contours.

- [x] **Step 1: Write failing image validation tests**

Create tests for strict JPEG only, invalid signature/decode, malformed dimensions, >4096 edge, >12,000,000 pixels, and EXIF orientation normalization. Keep all bytes in `io.BytesIO`; assert the decoded image is RGB with metadata removed. Run `cd backend && pytest -q tests/unit/test_scene_analysis.py`; expected: import/collection failure because the service module is absent.

- [x] **Step 2: Write failing candidate and scoring tests**

Use tiny synthetic masks injected as `PanopticSegment` values, independent of a model or network. Test unsupported labels and confidence `<0.50` excluded; connected components `<1%` excluded; each eligible candidate’s normalized closed polygon is in `[0,1]` and has ≤64 vertices; top five only; area/compactness/model-score formula exact within `1e-6`; score ties sorted by area then top-left; no candidates return `no_clear_candidate`; visual cues dedupe classes using max confidence and lexical order.

- [x] **Step 3: Run focused tests and verify expected failures**

Run `cd backend && pytest -q tests/unit/test_scene_analysis.py`; expected: failing import or missing functions, before implementation.

- [x] **Step 4: Implement bounded decode and pure mask processing**

Implement typed domain errors (`InvalidSceneImage`, `SceneAnalysisUnavailable`), image decode with header dimension checks before full pixel load, EXIF transpose and RGB re-encode in memory, class allow-list filtering, binary connected components, area/perimeter calculations, deterministic sort, contour simplification/closure, coordinate normalization, and cue aggregation. Keep all algorithm functions independent of FastAPI, config, network, and DB.

- [x] **Step 5: Run focused unit tests and commit**

Run `cd backend && pytest -q tests/unit/test_scene_analysis.py` and `cd backend && ruff check app/services/scene_analysis.py tests/unit/test_scene_analysis.py`. Expected: all unit tests pass without model weights or network. Commit `feat: add deterministic scene candidate analysis`.

**Task 2 verification and review:** Code review passed. Branch verification reported 17 focused scene-analysis tests and 100 backend unit tests passing; Ruff passed for changed files. Whole-package `ruff check app tests` still reports six pre-existing findings outside Epic 7 (risk-profile schema, dedup imports, source/event parser test imports, and a broad exception). These baseline findings were not changed in Task 2.

### Task 3: Add typed API contract, streaming body cap, errors, and contracts

**Files:**
- Create: `backend/app/schemas/scene_analysis.py`
- Create: `backend/app/api/v1/scene_analyses.py`
- Modify: `backend/app/main.py`, `backend/app/config.py`, `.env.example`
- Create: `backend/tests/unit/test_scene_analyses_api.py` (DB-free ASGI route contract tests)
- Modify: `docs/api-contracts.md`, `docs/error-handling-and-logging.md`, `CODING_STANDARDS.md`, `docs/glossary.md`

**Interfaces:**

```python
class SceneAnalysisRequest(BaseModel):
    image_base64: str
    mime_type: Literal["image/jpeg"]

class SceneAnalysisResponse(BaseModel):
    model_version: str
    result_status: Literal["candidates_found", "no_clear_candidate"]
    candidate_regions: list[CandidateRegion]
    visual_cues: list[VisualCue]
    limitations: list[str]

@router.post("", response_model=SceneAnalysisResponse)
async def post_scene_analysis(request: Request) -> SceneAnalysisResponse: ...
```

`CandidateRegion`: `rank:int`, `surface_class:str`, `polygon:list[ImagePoint]`, `area_fraction:float`, `compactness:float`, `model_confidence:float`, `ranking_score:float`. `ImagePoint`: `x:float`, `y:float`. `VisualCue`: `class_name:str`, `model_confidence:float`. JSON success is unwrapped. Request max is 5,593,000 bytes; decoded max 4 MiB. Error envelope codes/statuses: `invalid_scene_image`/422, `scene_image_too_large`/413, `scene_analysis_unavailable`/503.

- [x] **Step 1: Write failing schema and route tests**

Build a separate DB-free FastAPI app and inject a fake `PanopticSegmenter`; the existing integration `client` fixture starts migrated PostGIS and cannot run in this environment. Assert response schema and exact snake_case fields; bad JSON/base64/media/image return 422 envelope; missing model returns 503 envelope; bodies over cap return 413 envelope.

- [x] **Step 2: Test streaming limit and privacy behavior**

Add ASGI receive-stream tests for the exact cap, cap+1 with `Content-Length`, and cap+1 without it. Verify the route reads no more than cap+1 bytes before returning 413, body bytes never appear in captured logs/errors, and no file/cache/database writes occur. Never use the JSON test client's auto body logging or a real image fixture.

- [x] **Step 3: Run API tests to establish expected failures**

Run `cd backend && pytest -q tests/unit/test_scene_analyses_api.py`; expected: route/schema are missing and collection fails.

- [x] **Step 4: Implement schemas, streamed body reader, and route**

Create Pydantic output schemas and enforce normalized polygon bounds, closure, candidate limits, numeric `[0,1]` fields, and result-status consistency. In the route, require JSON content type; read `request.stream()` in chunks and stop immediately after aggregate size exceeds 5,593,000; decode JSON only after the bounded read; pass the image to the analysis service. Inject the segmenter through a dependency. Translate expected service errors to the standard envelope and do not catch unexpected errors locally. Register `scene_analyses.router` once in `backend/app/main.py`.

- [x] **Step 5: Add deployment settings and API contract docs**

Add the approved model ID/revision as code constants that cannot be overridden through environment settings, and `scene_analysis_model_cache_dir` as the documented local cache setting. Add 413 to the coding-standard HTTP table and document endpoint, caps, schemas, and error codes in `docs/api-contracts.md`. Document image/body exclusion from logs and trace payloads in `docs/error-handling-and-logging.md`; ensure `docs/glossary.md` uses the same endpoint and field definitions.

- [x] **Step 6: Verify and commit the API**

Run `cd backend && pytest -q tests/unit/test_scene_analyses_api.py tests/unit/test_scene_analysis.py` and Ruff on all changed Python files. The PostGIS integration suite remains separate and is not required for the DB-free route checks. Commit `feat: add scene analysis API`.

**Task 3 verification note:** API tests live under `tests/unit` because the shared autouse integration fixture requires local PostGIS. The route contract suite uses an isolated ASGI app and injected fake segmenter. Lightweight direct dependencies use exact Pillow 12.3.0 and NumPy 2.2.6 pins measured in the Task 1 CPython 3.11 preflight; both are compatible with Python >=3.11. Heavy model runtime packaging remains gated pending Linux/ARM64 and deployment-resource measurements.

The test-first run failed collection as expected because `app.api.v1.scene_analyses` did not exist. Before the runtime follow-up, focused API and service tests passed (34), and the full backend unit suite passed (117). The follow-up regression tests each failed against the original behavior, then passed after the fix: environment-like settings cannot change the model version, CPU analysis runs on a worker thread, concurrent calls serialize initialization and inference, and eight simultaneous FastAPI dependency resolutions construct exactly one shared segmenter. `get_segmenter` now protects explicit singleton initialization with a lock because `lru_cache` may execute its wrapped function multiple times on concurrent cache misses; the route-level analysis semaphore remains responsible for serializing bounded inference after dependency resolution. Current verification: API route tests 21 passed; full backend unit suite 121 passed (one existing Starlette/httpx deprecation warning); Ruff passes on changed Python files; structure verification reports all 140 scaffold paths present; and `git diff --check` passes. The PostGIS integration suite was not run for this follow-up; the earlier Task 3 attempt did not complete because PostgreSQL is stopped and Docker is unavailable. No integration pass is claimed.

### Task 4: Add the web capture and polygon/checklist experience

**Files:**
- Create: `web/src/api/sceneAnalysis.ts`, `web/src/types/sceneAnalysis.ts`, `web/src/pages/SceneAnalysis.tsx`, `web/src/pages/SceneAnalysis.module.css`, `web/tests/SceneAnalysis.test.tsx`
- Modify: `web/src/App.tsx`, `web/src/types/views.ts`, `web/src/components/layout/TopNav.tsx`, `web/src/pages/Dashboard.tsx`, `web/src/pages/Hero.tsx`.

**Interfaces:**

```typescript
export type SceneAnalysisRequest = { image_base64: string; mime_type: 'image/jpeg' };
export type ImagePoint = { x: number; y: number };
export type CandidateRegion = {
  rank: number; surface_class: string; polygon: ImagePoint[]; area_fraction: number;
  compactness: number; model_confidence: number; ranking_score: number;
};
export type VisualCue = { class_name: string; model_confidence: number };
export type SceneAnalysisResponse = {
  model_version: string; result_status: 'candidates_found' | 'no_clear_candidate';
  candidate_regions: CandidateRegion[]; visual_cues: VisualCue[]; limitations: string[];
};
export async function analyzeScene(
  apiBaseUrl: string, request: SceneAnalysisRequest, signal?: AbortSignal,
): Promise<SceneAnalysisResponse>;
```

The screen camera entry calls `navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'},audio:false})` only on user click, draws a captured frame to canvas, compresses a JPEG at ≤1600 px longest edge/≤4 MiB, encodes base64 without data URL prefix, stops every stream track after capture/unmount, and uses an absolutely positioned SVG/viewBox overlay with `preserveAspectRatio="none"` mapping `x*100%`,`y*100%` over the preview.

- [ ] **Step 1: Write failing web client tests**

Mock `fetch`; assert request path, JSON content type, and payload; parse exact response; map 413/422/503 envelopes to a typed safe error; verify body/request values are never sent to console logs. Run `cd web && npm test -- SceneAnalysis.test.tsx`; expected: module/test failure before client implementation.

- [ ] **Step 2: Write failing screen interaction tests**

Mock `getUserMedia`, video readiness, `canvas.toBlob`, and API client. Assert no permission request before camera action; denied and unsupported states render; capture shows preview; all tracks stop; Analyze shows loading and then polygons plus checklist/caveat; no-candidate and retry states render; retake/exit clears image/base64 and aborts pending requests. Test overlay coordinates from `(0,0)` to `(1,1)` align to preview bounds.

- [ ] **Step 3: Implement typed client and capture screen**

Add exact wire types, typed `SceneAnalysisApiError`, request/response validation, capture stream lifecycle, JPEG resize/compression, base64 encoding, preview, polygon selection, evidence checklist, permission/network/model/no-candidate states, and persistent disclaimer. Reuse project tokens and CSS Modules, preserve reduced-motion/accessibility conventions, and expose the entry in dashboard navigation and `/scene-analysis` route.

- [ ] **Step 4: Run web tests and production build**

Run `cd web && npm test -- SceneAnalysis.test.tsx`, then `cd web && npm test`, and `cd web && npm run build`. Expected: focused and full suites pass and TypeScript/Vite production build succeeds.

- [ ] **Step 5: Commit web feature**

Run `git diff --check`, inspect only web files are staged, then commit `feat: add web camera scene review`.

### Task 5: Add mobile capture, API mapping and screen

**Files:**
- Create: `mobile/src/services/sceneAnalysis.ts`, `mobile/src/types/sceneAnalysis.ts`, `mobile/src/screens/SceneAnalysisScreen.tsx`, `mobile/tests/sceneAnalysis.test.ts`
- Modify: `mobile/src/navigation/RootNavigator.tsx`, `mobile/package.json`, `mobile/package-lock.json`, `mobile/ios/GeoHazardPH/Info.plist` and `mobile/android/app/src/main/AndroidManifest.xml` only if required by the picker, `docs/mobile-runtime-smoke-test.md`

**Interfaces:**

```typescript
type SceneAnalysisWireResponse = {
  model_version: string;
  result_status: 'candidates_found' | 'no_clear_candidate';
  candidate_regions: {
    rank: number;
    surface_class: string;
    polygon: { x: number; y: number }[];
    area_fraction: number;
    compactness: number;
    model_confidence: number;
    ranking_score: number;
  }[];
  visual_cues: { class_name: string; model_confidence: number }[];
  limitations: string[];
};type SceneCandidate = {
  rank: number; surfaceClass: string; polygon: { x: number; y: number }[];
  areaFraction: number; compactness: number; modelConfidence: number; rankingScore: number;
};
type SceneAnalysisResult = {
  modelVersion: string; resultStatus: 'candidates_found' | 'no_clear_candidate';
  candidateRegions: SceneCandidate[];
  visualCues: { className: string; modelConfidence: number }[]; limitations: string[];
};
export function mapSceneAnalysisResponse(payload: unknown): SceneAnalysisResult;
```

Use `react-native-image-picker` `launchCamera({mediaType:'photo', includeBase64:true, maxWidth:1600, maxHeight:1600, quality:0.82})`; reject cancellation without an error message; require an `image/jpeg` result with base64 ≤4 MiB decoded; remove data from component state when retaking/leaving. `analyzeScene(baseUrl, imageBase64)` POSTs the shared JSON contract and maps snake_case only in the service.

- [ ] **Step 1: Write failing pure service/mapping tests**

Mock picker and `fetch`; assert permission/cancel/no-asset paths, correct resized JPEG request body/path, 413/422/503 error mapping, field-by-field snake_case mapping, normalized polygon point preservation, malformed response rejection, and no request-body logging. Run `cd mobile && npm test -- --runTestsByPath tests/sceneAnalysis.test.ts`; expected: missing module/tests fail before implementation.

- [ ] **Step 2: Implement capture service and response mapper**

Wrap `launchCamera`, return a typed discriminated outcome for cancelled/captured/error, validate MIME/base64 size, call the API, parse the existing standard error envelope, and map wire fields explicitly to mobile camelCase. Keep pure mapping exports directly testable.

- [ ] **Step 3: Implement mobile screen and navigation entry**

Build a thin screen for camera action, permission/cancel/loading/retry/error/empty/candidate states, local preview, rank selectors, normalized SVG polygon overlay, evidence checklist and persistent caveat. Add a “Scene review” entry to `RootNavigator` that does not interrupt nearby alerts or saved-location state. Add native camera permission description/config only where required by the current RN package; do not add gallery permissions.

- [ ] **Step 4: Run mobile tests and native checks**

Run `cd mobile && npm test -- --runTestsByPath tests/sceneAnalysis.test.ts`, then `cd mobile && npm test`. Run the project-supported Android debug build and iOS simulator build if their SDKs are installed; otherwise record each missing tool and leave hardware/native smoke status unverified.

- [ ] **Step 5: Commit mobile feature**

Run `git diff --check`, inspect staged paths for generated files/secrets, then commit `feat: add mobile camera scene review`.

### Task 6: Finish model provisioning, docs, and cross-platform verification

**Files:**
- Modify: `docs/data-sources.md`, `docs/runbook.md`, `README.md`, `.env.example`, `docs/mobile-runtime-smoke-test.md`, `docs/project-status.md`, `docs/geohazard-system-architecture.md`.
- Modify deployment/runtime files only if Task 1 measured the existing image and runtime as suitable.

- [ ] **Step 1: Write failing documentation-structure checks if available**

Inspect `python scripts/verify_structure.py` for repository requirements; do not create a new test framework for prose. Ensure existing structure checks expect the new API module and screen paths only if the script enforces them.

- [ ] **Step 2: Document the model, setup, and privacy contract**

Record exact model card URL, immutable revision, license, supported label list, dependencies, offline cache provisioning, image caps, API path/schema/errors, camera permissions, no logging/storage, runtime memory and latency measurements, and model-scene bias in data-source/runbook/README docs. Update the architecture diagram and epic status evidence. Add browser, Android, and iOS steps to `docs/mobile-runtime-smoke-test.md`; status must distinguish passed CI from unavailable hardware/deployed verification.

- [ ] **Step 3: Verify end-to-end package contracts**

Run `cd backend && pytest -v` and `ruff check app tests`; `cd web && npm test` and `npm run build`; `cd mobile && npm test`; `python scripts/verify_structure.py`; `git diff --check`. If actual model weights were provisioned, run one bounded local model inference offline and record model revision, cold load/inference time and peak RSS; do not claim classification accuracy or safety validation.

- [ ] **Step 4: Perform camera smoke checks where devices are available**

Run `docs/mobile-runtime-smoke-test.md` against browser localhost/HTTPS plus Android and iOS camera-capable runtimes: permission prompt only after action, capture, retake, analysis, overlay alignment, permission denial, network/API failure retry, camera track/preview/base64 cleanup. Record unavailable platforms as not run; do not mark them passed.

- [ ] **Step 5: Review feature diff and commit final documentation**

Review the complete branch diff, check each acceptance criterion in the spec against tests/evidence, run `git status --short` and `git diff --check`, stage only documentation and applicable runtime configuration, and commit `docs: document epic 7 scene review operations`.

## Self-review and execution choice

- Spec coverage: Task 1 measures and pins the model/runtime; Tasks 2–3 cover in-memory analysis and API/errors/privacy; Tasks 4–5 cover both camera clients, matching overlays and states; Task 6 covers model provenance, setup, operations, status and runtime smoke evidence. Non-goals remain explicit in the spec and product copy.
- Placeholder scan: no TBD/TODO or unspecified interface remains; the only environment-dependent decision is measured in Task 1 and requires a revised approved spec if it changes hosting boundaries.
- Type consistency: snake_case wire types, API response fields, mobile camelCase mapping, candidate geometry, and model revision agree with the approved spec.
- Execution choice: the user explicitly requested autonomous implementation, so execute this plan inline with verification checkpoints and no separate execution-mode prompt.
## Notes for the executor

- Tasks 1–3 are sequential: a missing revision/license or unacceptable deployment footprint requires revising the design and getting approval before proceeding with a different model/hosting boundary.
- Web and mobile depend on Task 3’s exact API contract. They can be developed independently after Task 3, but verify against the same fixtures and field names.
- Backend tests use injected fake masks and model adapter only. CI does not download weights or make network requests.
- `docs/testing-standards.md` requires mobile service/mapping tests rather than rendering native screen components; keep camera UI thin and push testable behavior into service/state functions.
- No database, PostGIS, Redis, Kaggle credentials, private source data, or API key is required for feature tests.
- The model is a scene-labeler only. COCO labels and the ranking heuristic have no emergency-safety validation; maintain the limitation copy across all states.
