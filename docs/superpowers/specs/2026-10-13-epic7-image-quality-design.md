# Epic 7 Image Quality Gate — Design

**Date:** 2026-10-13

## Problem

`POST /api/v1/scene-analyses` validates JPEG encoding and resource bounds, but it does not assess blur. Web and mobile can therefore display ranked regions from an image whose detail is too poor for useful segmentation. The pinned model is pretrained on COCO; it has not been fine-tuned or validated for Philippine interiors, obstruction, or disaster response.

## Goals

- Estimate image sharpness in the shared Python service before model inference.
- Warn the user when an image is likely blurred, with explicit **Retake** and **Continue anyway** options on web and mobile.
- Keep the warning advisory and report that image quality and view obstruction can reduce result reliability.
- Define a reproducible, licensed, labeled public-image evaluation workflow; do not put images or model weights in Git.
- Keep user camera images transient and excluded from training.

## Non-goals

- Claim to detect every obstruction, verify view coverage, or prove an image is usable.
- Train or fine-tune a replacement model in this change.
- Use user-captured photos for training or retain them for quality review.
- Claim safety, structural condition, or emergency readiness.

## Context And Constraints

The service decodes bounded JPEGs in `backend/app/services/scene_analysis.py`; the API and both clients share `POST /api/v1/scene-analyses`. API errors use the standard stable error envelope. The pinned DETR model is loaded locally and inference is CPU-bound. Backend, API, web, and mobile requirements follow `BACKEND_STANDARDS.md`, `docs/api-contracts.md`, `docs/testing-standards.md`, and `docs/error-handling-and-logging.md`.

The current model card documents COCO 2017 training. COCO images are not owned by the dataset consortium and use is subject to source-image terms. Use only the held-out validation partition for evaluation, preserve per-image provenance, and do not redistribute those images. ADE20K requires registration and agreement to its own terms, so it is not an automatic download source. Dataset permissions and coverage must be reviewed before any publication or training use.

## Alternatives Considered

1. **Shared backend advisory gate (chosen).** One luminance Laplacian-variance metric is computed after decode and before segmentation. A low score returns a typed warning; a client can request retake or explicitly continue. It keeps platform behavior consistent and avoids duplicating image processing.
2. **Separate web/mobile client blur checks.** This could avoid an extra API round trip, but browser canvas and native image decoding would produce different metrics and maintenance paths. Rejected for inconsistent results.
3. **Hard reject all images below a fixed threshold.** A low-texture, dark, or naturally smooth scene may score low despite being usable. Rejected because an uncalibrated hard block could prevent valid analysis.

## Design

### Architecture and data flow

```text
captured JPEG -> bounded decode -> sharpness score -> (warning? retake / explicit continue) -> model segmentation
```

The service reduces the image's longest edge to 512 pixels, computes variance of a 4-neighbor Laplacian on 8-bit grayscale pixels, and applies `MIN_SHARPNESS_SCORE = 400.0`. The threshold is a provisional heuristic and must be calibrated against held-out labeled images and controlled blur variants before release. The quality check runs before loading/invoking the segmenter.

If the score is below threshold and `accept_quality_warning` is false (default), return HTTP 422 with `error.code: "scene_image_quality_warning"` and a safe message using the existing error envelope. The client shows **Retake** and **Continue anyway**. Continue resubmits the same transient image with `accept_quality_warning: true`; the server recomputes quality and proceeds. The override bypasses only this advisory gate and does not change inference, ranking, or limitations. Never log the image, sharpness score, request body, or pixel data.

The successful response includes a fixed limitation explaining that blur, obstruction, lighting, and viewpoint can hide or distort visual cues. If no candidate is detected, retain the existing `no_clear_candidate` state. Do not present an obstruction detector as implemented.

### Components and interfaces

- `backend/app/services/scene_analysis.py`: pure `estimate_sharpness(image: Image.Image) -> float` helper, provisional `MIN_SHARPNESS_SCORE = 400.0` constant, and a typed `SceneImageQualityWarning` raised before segmentation.
- `backend/app/schemas/scene_analysis.py`: optional request field `accept_quality_warning: bool = False`.
- `backend/app/api/v1/scene_analyses.py`: map the warning to the existing project error envelope; no image or pixel data in the response.
- `web/src/api/sceneAnalysis.ts`, `web/src/pages/SceneAnalysis.tsx`, and `web/tests/SceneAnalysis.test.tsx`: parse the stable warning code; offer retake and explicit continue.
- `mobile/src/services/sceneAnalysis.ts`, `mobile/src/screens/SceneAnalysisScreen.tsx`, and `mobile/tests/sceneAnalysis.test.ts`: same behavior through explicit wire mapping.
- `docs/data-sources.md`: source/license provenance and reproducible held-out evaluation protocol. The protocol records split, image IDs, annotations, perturbation settings, metric, threshold selection, and limitations; dataset files remain external.
- `docs/mobile-runtime-smoke-test.md`, `docs/runbook.md`, `docs/api-contracts.md`, `docs/glossary.md`, and `docs/project-status.md`: user flow, error contract, terminology, caveat, and verification status.

### Evaluation protocol

Use COCO 2017 validation images/annotations as a held-out public benchmark, subject to the dataset's image-source terms. Keep the official train/validation separation. Evaluate the current model on original images and deterministic Gaussian-blur variants across recorded radii. Report supported-surface segmentation IoU and candidate-region coverage by blur level, plus sharpness-score distributions for originals and variants. Choose a warning threshold on a calibration subset, then report results on a disjoint subset. Record the exact source revision, image IDs, annotation version, script version, environment, and metrics. Do not call this local Philippine-domain validation. Do not train on the validation partition. If source terms or the pinned runtime are unavailable, keep the threshold explicitly provisional and the evaluation gate open.

Obstruction remains a limitation. A future obstruction model requires separately licensed images with annotated visible/occluded regions and independent testing; low segmentation coverage alone cannot distinguish obstruction from an unsupported scene, unusual viewpoint, lighting, or model failure.

### Configuration and errors

No new environment variable. The warning threshold is a named, tested constant so it can be reviewed and later calibrated. Invalid image content remains `422 invalid_scene_image`; the advisory is `422 scene_image_quality_warning`; model unavailability remains 503. Use only the existing stable error envelope fields (`code`, `message`, `status`). No image is persisted, cached, or sent to analytics.

## Rollout

Implement backend metric and warning contract first, then web/mobile choice states, then evaluation/runbook and smoke documentation. Use test-first changes in each package. Keep model training and deployment provisioning out of this patch. The gate ships as an advisory with override; release status must call out provisional threshold until the held-out evaluation is run on a provisioned model runtime.

## Files

- `backend/app/services/scene_analysis.py` — sharpness metric and pre-inference warning.
- `backend/app/schemas/scene_analysis.py` — explicit client override request flag.
- `backend/app/api/v1/scene_analyses.py` — stable quality warning error mapping.
- `backend/tests/unit/test_scene_analysis.py` and `backend/tests/unit/test_scene_analyses_api.py` — synthetic sharp/blurred fixtures, override, ordering, and safe error contract.
- `web/src/api/sceneAnalysis.ts`, `web/src/pages/SceneAnalysis.tsx`, `web/tests/SceneAnalysis.test.tsx` — warning parse and retake/continue interaction.
- `mobile/src/services/sceneAnalysis.ts`, `mobile/src/screens/SceneAnalysisScreen.tsx`, `mobile/tests/sceneAnalysis.test.tsx` — shared warning behavior.
- `docs/api-contracts.md`, `docs/glossary.md`, `docs/data-sources.md`, `docs/runbook.md`, `docs/mobile-runtime-smoke-test.md`, and `docs/project-status.md` — contract, provenance, operations, smoke flow, and status.
- `docs/superpowers/plans/2026-10-13-epic7-image-quality.md` — implementation sequence and verification checklist.

## Testing Strategy

- Backend unit tests: sharp synthetic edge scores above threshold; deterministic blur lowers the score; image dimensions do not alter constant score behavior; warning is raised before segmentation; explicit override proceeds.
- Backend API tests: warning error envelope/code, override success, and no image/body data in logs.
- Web tests: typed warning exposes retake and continue; retake clears capture; continue retries with explicit override.
- Mobile Jest tests: warning code maps to a safe message and continue sends the explicit override. Strict source type-check covers the screen wiring; native warning/retake interaction remains in the device smoke checklist.
- Data evaluation: held-out report is reproducible and records threshold-selection and untouched evaluation partitions. No internet is used by normal test suites.
- Run backend DB-free unit suite and Ruff, web tests/build, mobile tests/type check, structure verifier, and `git diff --check`. PostGIS tests remain separately service-dependent.

## Acceptance Criteria

- [ ] Blur scoring runs after bounded decode and before any model inference.
- [ ] Below-threshold images receive the stable warning unless the user explicitly continues.
- [ ] Web and mobile offer retake and continue, and continue sends the explicit override.
- [ ] Limitation copy explains that blur, obstruction, lighting, and viewpoint can reduce reliability.
- [ ] Automated tests cover sharp/blurred synthetic cases, gate ordering, override, API contract, web choice actions, and mobile error/override mapping. Native device smoke checks remain pending.
- [ ] Dataset source terms, split, annotations, blur perturbations, metrics, and threshold selection are documented; data is not committed.
- [ ] Provisional threshold and unverified obstruction/local-domain performance are visible in project status.
- [ ] User images remain transient and are not used for training.

## Out Of Scope (backlog)

- Training or fine-tuning on internet-sourced images. Requires a reviewed license/source manifest, task-compatible annotations, split strategy, and independent evaluation.
- Philippine-specific indoor/outdoor/disaster-scene validation.
- Reliable obstruction/occlusion classification.
- Camera hardware checks on physical devices.

---

## Spec self-review

- Each goal maps to acceptance criteria. The API error contract, opt-in override, and test behavior are defined.
- Blur threshold calibration is a release gate; a synthetic test is not treated as real-world quality validation.
- Dataset images remain external; no user capture or held-out validation image enters training.
- Obstruction detection is explicitly not claimed.

## Related documents

- Epic 7 design: `docs/superpowers/specs/2026-10-13-epic7-scene-analysis-design.md`
- Implementation plan: `docs/superpowers/plans/2026-10-13-epic7-image-quality.md`
- Terminology: `docs/glossary.md`
