# Epic 7 — Camera-Based Scene Review Design

**Date:** 2026-10-13

## Problem

GeoHazard PH has no camera-driven scene review feature. People indoors at home or in a mall and people outdoors need a quick way to inspect a captured earthquake-response scene for visible open floor or ground areas and nearby visual cues. The web and mobile clients should present the same evidence in a way that does not claim a photograph can establish a genuinely safe place.

## Goals

- Let a user explicitly open the camera, capture a still image, review it, retake it, and request analysis from both web and mobile.
- Analyze indoor and outdoor images through one Python backend path, using a pretrained panoptic-segmentation model and a deterministic, explainable ranking algorithm.
- Return zero or more normalized image polygons for visible open floor/ground candidates, ranked by documented visual features, plus recognized object cues and limitations.
- Present the same captured image with selectable/legible candidate polygons and an evidence checklist on web and mobile. Clearly describe results as visual candidates, never as safe locations.
- Process image content only in bounded backend memory; never log, persist, or train on uploaded image data. Keep the client preview transient and clear its URI/base64 references on retake, exit, or screen unmount. The native camera picker may stage a capture in app-specific temporary cache storage; do not save to the public photo library, and document that the picker/OS manages cache-file removal.
- Cover analysis, validation, privacy behavior, client states, and geometry mapping with deterministic tests that use an injected fake segmenter and do not download model weights.

## Non-goals

- Verifying structural integrity, earthquake resistance, ground conditions, falling-glass risk, electrical hazards, egress, accessibility, routes, unseen areas, or changing conditions.
- Giving emergency instructions, identifying an official shelter, predicting an earthquake, or asserting that a candidate is safe.
- Training or fine-tuning a scene-safety classifier, collecting photos, retaining analysis history, storing location metadata, or sending images to a third-party inference API.
- Video/continuous analysis, offline on-device inference, gallery selection, user accounts, and multi-image mapping.
- Claiming the feature is production-ready for emergency decision-making. It is a visual cue demonstrator and must say so in product copy.

## Context And Constraints

- Follow `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/api-contracts.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/glossary.md`.
- The backend is FastAPI/Python 3.11+, web is React 18/TypeScript/Vite, and mobile is React Native CLI. The mobile package currently has no camera package; the web package has no camera implementation.
- `facebook/detr-resnet-50-panoptic` is the chosen initial pretrained model candidate. Its model card reports COCO panoptic training and an Apache-2.0 model license; its label configuration includes floor/ground and common indoor/outdoor object classes. Pin an immutable model revision and record the upstream model/code license and source revision before shipping weights. The upstream class set and COCO scene distribution are imperfect for Philippine homes, malls, and disaster scenes; this is not a locally validated safety model. References: [model card](https://huggingface.co/facebook/detr-resnet-50-panoptic) and [label configuration](https://huggingface.co/facebook/detr-resnet-50-panoptic/raw/main/config.json).
- The inference model is hosted by the existing Python API so web and mobile share behavior. PyTorch/Transformers can materially increase image size, cold start, CPU, and memory use. The implementation plan must explicitly inspect Docker targets and runtime resource limits, pin CPU-compatible dependencies, and measure/test loading before adding the model to default deployment images. The model is loaded once per process from the pinned local cache; requests must not trigger network downloads. If unavailable, return a safe 503 instead of switching to another model.
- Browser camera access requires a secure context and user permission. Mobile camera access requires native runtime permission. Camera capture is an explicit user action. Web stops camera tracks immediately after capture or leaving the capture view; mobile clears its local image URI/base64 when the capture view closes.
- The sample screenshot is a presentation reference only. Green “SAFE” labels, traffic-light safety colors, and implied engineering/material judgments are excluded; candidate highlights use a neutral selection treatment.

## Alternatives Considered

1. **Shared backend panoptic model with deterministic visual-cue ranking (chosen).** One analysis implementation serves both clients, has testable deterministic scoring, and requires no locally labeled safety dataset. Trade-off: server model packaging and runtime resources are heavier, and visual cues cannot establish real-world safety.
2. **Train a project-specific image classifier.** Could target local settings and hazards, but there is no consented, labeled, representative Philippine dataset or validated safety ground truth. Reject for this release because it would create unsupported safety claims.
3. **Separate on-device models for web and mobile.** Could reduce image transfer, but would duplicate model packaging, inference behavior, and platform testing and would not fit the currently agreed shared Python analysis flow. Reject for this release.

## Design

### Architecture and data flow

```text
Web camera ─┐
             ├─> bounded JSON image request ─> FastAPI scene-analysis service
Mobile camera┘                                ├─> pinned panoptic model (in process)
                                               ├─> candidate extraction + ranking
                                               └─> response: polygons + evidence + caveat
                                                        ├─> web photo overlay/checklist
                                                        └─> mobile photo overlay/checklist
```

The client requests camera permission only after the user activates the camera action. It captures one JPEG, scales the longest edge to at most 1600 pixels, compresses to JPEG quality 0.82 or lower as needed to remain within 4 MiB decoded, and shows a local preview with capture/retake/Analyze controls. The client sends a JSON body with `image_base64` (standard base64, no data-URL prefix) and `mime_type: "image/jpeg"` to `POST /api/v1/scene-analyses`. The JSON request is capped at 5,593,000 bytes (base64 expansion of 4 MiB plus small JSON overhead); the backend incrementally reads `request.stream()`, stops and returns 413 as soon as the cap is crossed (including when `Content-Length` is absent), buffers at most the cap, then parses JSON. It validates strict base64, decodes into bounded memory, checks JPEG signature, dimensions no greater than 4096 per edge and 12,000,000 pixels total before full decode, normalizes orientation and re-encodes pixels in memory to strip metadata, and never writes the image to disk. It rejects other media types, invalid bytes, and images with either dimension above 4096 pixels or more than 12,000,000 total pixels. Resizing/normalization for inference occurs in memory. Both clients use the same wire contract. The image is not included in any response.

The client retains its local preview only until retake, navigation away, or component unmount. The API does not retain the input or output image. Request bodies, base64 values, and image-derived paths are excluded from logs, tracing, analytics, and error detail. No database, cache, event, or model-training write is introduced.

The backend runs the pinned `facebook/detr-resnet-50-panoptic` model on CPU. Only exact configured surface labels `floor-other`, `floor-stone`, `floor-tile`, `floor-wood`, `ground-other`, `pavement`, `road`, `grass`, and `gravel` are eligible for candidate regions; the config has no label named exactly `floor`. A candidate is a connected component of eligible surface pixels with model confidence at least 0.50 and at least 1% of image pixels. Extract one external contour per component; simplify it while retaining a closed polygon of at most 64 normalized points. Coordinates use `x = pixel_x / image_width`, `y = pixel_y / image_height`, origin at top-left, values in `[0, 1]`. Return at most five candidates.

Rank candidates deterministically with a visual-review score (not a safety probability):

```text
area_term = min(candidate_area_fraction / largest_candidate_area_fraction, 1)
compactness = min(4 * pi * component_pixel_area / component_perimeter_pixels^2, 1)
ranking_score = 0.50 * area_term + 0.30 * compactness + 0.20 * model_segment_confidence
```

Sort descending by `ranking_score`, then descending `area_fraction`, then ascending polygon top-left `(y, x)` for stable ties; assign one-based ranks. Do not subtract a hazard penalty or infer material/stability. The checklist reports detected model labels, their model confidence, candidate surface names, visible area fraction, compactness, and the ranking-score components. Recognized objects are descriptive “nearby visual cues to review” only and are not labeled hazards by the system. When there is no eligible candidate, return `result_status: "no_clear_candidate"`; do not fabricate a polygon or fallback recommendation.

### Components and interfaces

- `POST /api/v1/scene-analyses` accepts a JSON object:

  ```json
  {"image_base64":"...","mime_type":"image/jpeg"}
  ```

  Success returns the direct response object, without an envelope:

  ```json
  {
    "model_version":"facebook/detr-resnet-50-panoptic@d53b52a799403a8867920f82c869e40732b47037",
    "result_status":"candidates_found",
    "candidate_regions":[{
      "rank":1,
      "surface_class":"floor-wood",
      "polygon":[{"x":0.12,"y":0.58},{"x":0.82,"y":0.58},{"x":0.82,"y":0.94},{"x":0.12,"y":0.94}],
      "area_fraction":0.21,
      "compactness":0.71,
      "model_confidence":0.88,
      "ranking_score":0.81
    }],
    "visual_cues":[{"class_name":"chair","model_confidence":0.76}],
    "limitations":["Visual scene cues only; this result does not determine whether any area is safe.","Blur, obstruction, lighting, or viewpoint can hide visual cues; one image cannot assess structural stability, hidden hazards, or route access."]
  }
  ```

  `result_status` is `candidates_found` or `no_clear_candidate`. Candidate polygons are closed, normalized, and clockwise in image coordinates, with at least four distinct vertices plus the repeated closing point. `visual_cues` are deduplicated recognized model classes (maximum confidence retained for repeated classes), sorted by class name. `model_version` includes the exact immutable upstream revision. `ranking_score` is only a sort aid and is not called confidence or probability.
- Invalid JSON/base64, unsupported media, undecodable images, and invalid dimensions return the standard error envelope with HTTP 422 and stable code `invalid_scene_image`. Bodies exceeding the cap return 413 and `scene_image_too_large`. A missing/unloadable pinned model returns 503 and `scene_analysis_unavailable`. Unexpected errors use the existing safe 500 envelope; logs contain request ID and stage, never image/body bytes. Add 413 to the project status-code contract if it is not already listed in the current standards.
- `backend/app/api/v1/scene_analyses.py` owns HTTP validation/error mapping; `backend/app/schemas/scene_analysis.py` defines request/response contracts; `backend/app/services/scene_analysis.py` owns in-memory decode, inference adapter, candidate extraction, ranking, and polygon normalization. The model adapter is injected so tests do not load/download weights.
- The web route-level camera/review page uses `getUserMedia` after an explicit tap, stops tracks promptly, calls a typed API client, and draws returned polygons over the captured preview using normalized coordinates. It provides permission-denied, unsupported/insecure browser, capture failure, invalid-image, too-large, model-unavailable, loading, no-candidate, retry, and retake states.
- Mobile uses `react-native-image-picker` `launchCamera` for a still capture, requests permission on tap, obtains a client-resized/compressed JPEG/base64 representation, and maps the snake_case wire response through an explicit service mapping. It renders the same preview, polygon, evidence, caveat, loading, and error states. No gallery fallback is included.
- Both interfaces include persistent copy: “Visual cues only—not a safety assessment. Verify conditions and follow official emergency guidance.” Do not use “safe spot,” “safe zone,” or green safety-confidence styling.

### Configuration

- `SCENE_ANALYSIS_MODEL_ID` is `facebook/detr-resnet-50-panoptic`; `SCENE_ANALYSIS_MODEL_REVISION` is pinned to `d53b52a799403a8867920f82c869e40732b47037`. Both identify a local cached artifact. Startup fails clearly or the endpoint returns unavailable if the configured revision is not present. Production image builds must provision that exact artifact only after license/source and image/resource impact review; request handling never downloads weights.
- Fixed caps and ranking weights are constants with unit tests: decoded image 4 MiB, JSON body 5,593,000 bytes, dimensions 4096, total pixels 12,000,000, client longest edge 1600, min component area 1%, min segment score 0.50, max candidates 5, max vertices 64, and ranking weights 0.50/0.30/0.20.

### Error handling

Use the existing API error envelope. Invalid client content is a 422 `invalid_scene_image`; oversized request body is 413 `scene_image_too_large`; unavailable model is a 503 `scene_analysis_unavailable`; unexpected errors are sanitized 500 responses with a request ID. The service does not silently fall back to a different checkpoint or heuristics if model loading fails. Client permission denial is an explicit actionable capture state; API/network failures retain the local preview for retry or retake, and leaving the feature clears it.

### Data considerations

No ORM model, database migration, user identifier, location, history, public photo-library copy, or durable server-side image artifact is added. All API fields use snake_case and image polygon points use normalized `x`/`y` pixel fractions (not map coordinates or GeoJSON). Inference outputs are visual model labels and image-space metrics only. The feature adds glossary terms for scene analysis, candidate region, visual cue, and ranking score.

## Rollout

Implement as a separate `feat/epic7-scene-analysis` branch/worktree based on current `main`, in backend → contract/client types → web → mobile dependency order. Add deterministic backend tests before backend behavior, then web and mobile state/overlay mapping tests. Keep inference test fixtures independent of network and weights. Verify package test/build commands and Docker image constraints before enabling the endpoint in default service startup. Add an explicit hardware smoke checklist for browser/mobile camera permission, capture, retake, API result, and cleanup. No deployment or emergency-use readiness is implied by merge.

## Files

- `docs/glossary.md` — canonical vocabulary and wire field names.
- `docs/api-contracts.md` and `CODING_STANDARDS.md` — endpoint, success payload, 413 status, validation and unavailable error codes.
- `docs/error-handling-and-logging.md` — image/body privacy and safe failure handling.
- `docs/data-sources.md` — model source, license, pinned revision, class coverage, and limitations.
- `docs/runbook.md`, `README.md`, and `.env.example` — model provisioning/cache, new settings, and local verification, after image/resource decision.
- `docs/project-status.md` — Epic 7 status and evidence once implementation exists.
- `backend/app/config.py` — pinned model and local cache settings.
- `backend/app/api/v1/scene_analyses.py` — bounded JSON body request and typed endpoint.
- `backend/app/schemas/scene_analysis.py` — Pydantic request and response schemas.
- `backend/app/services/scene_analysis.py` — decode, model adapter, mask-to-region algorithm, ranking, and response assembly.
- `backend/pyproject.toml`, `backend/Dockerfile`, `backend/Dockerfile.prod`, and Compose/deployment files — pinned CPU runtime dependencies and model artifact provisioning, if default image impact is acceptable.
- `backend/tests/test_scene_analysis_service.py` — deterministic validation, extraction, scoring, ordering, and geometry tests with injected masks.
- `backend/tests/test_scene_analyses_api.py` — body limit, standard errors, schema, and non-persistence/no-log behavior.
- `web/src/pages/SceneAnalysis.tsx` and colocated CSS module — camera capture and shared result experience.
- `web/src/App.tsx`, `web/src/types/views.ts`, and the relevant navigation control — register the feature route and entry point.
- `web/src/api/sceneAnalysis.ts`, `web/src/types/sceneAnalysis.ts` — typed endpoint client and wire contract.
- `web/tests/SceneAnalysis.test.tsx` — permissions/states, capture cleanup, polygon overlay, and checklist.
- `mobile/src/screens/SceneAnalysisScreen.tsx` and colocated styles — camera and result experience.
- `mobile/src/navigation/RootNavigator.tsx` and the relevant navigation entry point — register feature navigation.
- `mobile/src/services/sceneAnalysis.ts`, `mobile/src/types/sceneAnalysis.ts` — capture/API mapping and typed mobile result.
- `mobile/tests/sceneAnalysis.test.tsx` — permission, capture/retake, wire mapping, polygon alignment, cleanup, and failure states.
- `mobile/package.json` and lockfile — pinned camera dependency if the current native APIs require it.
- `docs/mobile-runtime-smoke-test.md` — browser + Android + iOS camera permission and end-to-end checklist, updating the existing checklist.

## Testing Strategy

- Backend service tests use small synthetic masks and a fake model: invalid/oversize/unsupported input; indoor floor and outdoor road/grass regions; connected components and minimum thresholds; exact score formula and deterministic tie order; normalized closed polygons bounded in `[0,1]`; at most five candidates/64 vertices; no-candidate output; class evidence; image bytes not persisted or logged.
- Backend API tests cover bounded streaming with and without `Content-Length`, valid request/response schema, malformed JSON/base64, invalid image, dimension/pixel caps, 413 cap, 422 envelope, 503 envelope, no model download, and no image/body in captured logs. No network or model weights in CI.
- Web tests cover explicit camera permission request, denied/unsupported states, capture and track cleanup, retake and preview cleanup, request/loading/retry, result/no-candidate, normalized polygon-to-preview alignment, accessible evidence checklist, and persistent limitation copy.
- Mobile tests cover permission denied/granted, capture cancellation, base64/JPEG sizing contract, explicit snake_case mapping, retake/exit reference cleanup, relative-area evidence, neutral candidate highlight styling, API errors and retry, polygon alignment, checklist, and limitation copy. Device smoke checks confirm no public photo-library save; picker-created cache files follow the platform temporary-cache lifecycle.
- Run backend pytest and Ruff; web Vitest and production build; mobile Jest and available TypeScript/native build checks; `python scripts/verify_structure.py`; and `git diff --check`. Hardware smoke tests require a physical device or a camera-capable emulator and are recorded separately from CI.

## Acceptance Criteria

- [ ] Web and mobile can capture a still photo after user action and show preview, retake, and analysis states.
- [ ] Indoor and outdoor test scenes produce only visible floor/ground candidates from supported model labels; unsupported or empty scenes return no candidate.
- [ ] The same Python endpoint/model/algorithm serves both clients and returns deterministic top-five polygons, score evidence, visual cues, model revision, and limitations.
- [ ] Polygon coordinates are closed, normalized, bounded, and align with the captured preview on both clients.
- [ ] Ranking uses the documented area/compactness/model-score formula and is never described as safety confidence.
- [ ] Images are capped, processed in memory, absent from logs/responses/storage, and cleared from client view state on retake or exit.
- [ ] API validation/413/model-unavailable errors follow documented error envelopes and client states.
- [ ] Camera, permission, loading, retry, no-candidate, and failure states are accessible and documented on web and mobile.
- [ ] Model source/license/revision, dependency/resource impact, provisioning, and known class/scene limitations are documented before default deployment.
- [ ] Backend, web, mobile, structure, and diff checks pass; camera hardware smoke checks are recorded as passed or explicitly unavailable.
- [ ] Project status calls Epic 7 implemented only after all applicable checks and records any hardware/deployment verification that remains.

## Out Of Scope (backlog)

- A locally labeled and independently validated Philippine indoor/outdoor disaster-scene dataset and classifier.
- Depth sensing, multi-frame mapping, route or exit accessibility, geolocation, shared incident reporting, and photo history.
- Live/hosted model latency, load, security, and emergency-service validation beyond local and CI checks.

---

## Spec self-review

- The model revision in configuration and the response example is the immutable upstream HEAD captured during spec authoring; the implementation must use this exact revision.
- Goals map to acceptance criteria, and backend/web/mobile responsibilities and error contracts are defined.
- Candidate rank is explicitly a heuristic visual-review ordering and cannot become a safety confidence claim.
- The single-image and model-label limitations apply equally indoors and outdoors; no unsupported material/structural inference is specified.
- The feature fits one plan, with model packaging/resource assessment called out before default deployment.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-13-epic7-scene-analysis.md`
- Terminology: `docs/glossary.md`
