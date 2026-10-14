# Epic 7 Image Quality Gate — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Warn on likely blurry scene images consistently across web and mobile before model analysis, and document a reproducible external image evaluation protocol.

**Architecture:** The shared API computes a deterministic sharpness score after bounded decode and before model inference. A typed advisory error lets both clients offer retake or explicit continue. Evaluation uses held-out public annotations with source provenance; image files stay outside Git.

**Tech Stack:** Python 3.11, FastAPI, Pillow, NumPy, pytest, React/TypeScript/Vitest, React Native/Jest.

**Spec:** `docs/superpowers/specs/2026-10-13-epic7-image-quality-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`, `docs/api-contracts.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/glossary.md`.
- Add each behavior test first and confirm it fails before implementation.
- Do not log or persist image bytes, base64, decoded pixels, or user photos; do not use camera uploads for training.
- Do not commit dataset images, model weights, generated artifacts, caches, or secrets.
- User-facing results remain visual cues only, not a safety assessment.
- Use Conventional Commits. Run package tests, lint/build/type checks listed below, structure verifier, and `git diff --check`.
- Full backend integration tests need PostGIS; record if unavailable rather than claiming they passed.

### Task 1: Backend sharpness score and typed advisory

**Files:**
- Modify: `backend/app/services/scene_analysis.py`
- Modify: `backend/app/schemas/scene_analysis.py`
- Modify: `backend/app/api/v1/scene_analyses.py`
- Test: `backend/tests/unit/test_scene_analysis.py`
- Test: `backend/tests/unit/test_scene_analyses_api.py`

**Interfaces:**
- `estimate_sharpness(image: Image.Image) -> float` scales the longest edge to 512 pixels, then returns variance of a four-neighbor Laplacian over 8-bit grayscale pixels, computed in float32.
- `MIN_SHARPNESS_SCORE = 400.0` is a named provisional threshold; the real-image evaluation gate remains pending.
- Add request field `accept_quality_warning: bool = False`.
- Raise `SceneImageQualityWarning(sharpness_score: float)` below threshold before calling `segmenter.segment`, unless override is true.
- API maps it to HTTP 422 error code `scene_image_quality_warning` using only the standard `code`, `message`, and `status` envelope fields.

- [x] **Step 1: Write failing service tests** for a crisp synthetic edge image scoring above the threshold, a Gaussian-blurred version scoring below, and segmenter not called on warning.
- [x] **Step 2: Run** `pytest -v tests/unit/test_scene_analysis.py` from `backend/` and confirm the new tests fail because the metric and warning do not exist.
- [x] **Step 3: Implement** the metric with NumPy/Pillow only; add the domain warning exception; call it after decode and before segmenter invocation; ensure the explicit override bypasses only the warning.

```python
grayscale_image = image.convert("L")
grayscale_image.thumbnail((512, 512), Image.Resampling.BILINEAR)
grayscale = np.asarray(grayscale_image, dtype=np.float32)
laplacian = (
    grayscale[:-2, 1:-1] + grayscale[2:, 1:-1]
    + grayscale[1:-1, :-2] + grayscale[1:-1, 2:]
    - 4 * grayscale[1:-1, 1:-1]
)
score = float(np.var(laplacian, dtype=np.float64))
```

- [x] **Step 4: Write and run API tests** for warning envelope/code, override success, default warning, and absence of image/base64/pixels in captured logs; verify fail-before/pass-after.
- [x] **Step 5: Run** `pytest -v tests/unit/test_scene_analysis.py tests/unit/test_scene_analyses_api.py` and Ruff on the changed Python files. Full DB-free unit suite: 127 passed; changed-file Ruff passed.
- [x] **Step 6: Commit** `feat: warn on blurry scene images` (`8f6c2ab`).

### Task 2: Web retake and continue actions

**Files:**
- Modify: `web/src/api/sceneAnalysis.ts`
- Modify: `web/src/pages/SceneAnalysis.tsx`
- Modify: `web/tests/SceneAnalysis.test.tsx`

**Interfaces:**
- Extend the request mapping with optional `accept_quality_warning`.
- Parse API error code `scene_image_quality_warning` as the existing typed `SceneAnalysisApiError`.
- Present a visible retake recommendation with **Retake** and **Continue anyway** actions. The latter retries the same in-memory image with `accept_quality_warning: true`; retake clears image/result state and returns to capture.

- [x] **Step 1: Add failing UI tests** for warning actions, retake cleanup, and continue retry body.
- [x] **Step 2: Run** `npm test -- --run SceneAnalysis.test.tsx` from `web/` and confirm failure is the absent warning state.
- [x] **Step 3: Implement** typed error handling and the accessible warning interaction without changing unrelated screen states.
- [x] **Step 4: Run** the focused test and confirm it passes.
- [x] **Step 5: Run** `npm test` and `npm run build` from `web/`. Full suite: 133 passed; build exited 0 with the existing large-chunk warning.
- [x] **Step 6: Commit** `feat: add web scene quality warning` (`5bf1b8f`).

### Task 3: Mobile retake and continue actions

**Files:**
- Modify: `mobile/src/services/sceneAnalysis.ts`
- Modify: `mobile/src/screens/SceneAnalysisScreen.tsx`
- Modify: `mobile/tests/sceneAnalysis.test.ts`

**Interfaces:**
- Map the same stable API error code through the existing mobile `SceneAnalysisError` type.
- Show equivalent **Retake** and **Continue anyway** actions. Continue resubmits the current image with explicit override; retake clears image/result state.

- [x] **Step 1: Add failing tests** for warning code mapping and override retry.
- [x] **Step 2: Run** `npm test -- --runInBand tests/sceneAnalysis.test.ts` from `mobile/` and confirm failure because the warning is not mapped.
- [x] **Step 3: Implement** typed mobile warning state and actions.
- [x] **Step 4: Run** focused mobile tests and confirm pass.
- [x] **Step 5: Run** `npm test -- --runInBand` and the strict TypeScript check from `mobile/`. Full suite: 45 passed; explicit source type-check exited 0.
- [x] **Step 6: Commit** `feat: add mobile scene quality warning` (`a952257`).

### Task 4: Public-image evaluation protocol and product documentation

**Files:**
- Modify: `docs/api-contracts.md`
- Modify: `docs/glossary.md`
- Modify: `docs/data-sources.md`
- Modify: `docs/runbook.md`
- Modify: `docs/mobile-runtime-smoke-test.md`
- Modify: `docs/project-status.md`

**Interfaces:**
- Document request override, warning response code, provisional threshold, and persistent quality limitation.
- Record public dataset source, license/terms, held-out split, no-training-on-validation rule, image ID provenance, deterministic blur settings, supported-surface IoU/coverage metrics, threshold calibration/holdout split, and no image redistribution.

- [x] **Step 1: Inspect** `docs/api-contracts.md`, `docs/glossary.md`, `docs/data-sources.md`, `docs/runbook.md`, `docs/mobile-runtime-smoke-test.md`, and `docs/project-status.md` for existing Epic 7 terminology and camera flow.
- [x] **Step 2: Record** official COCO terms and ADE20K access terms as source references; do not download or redistribute any dataset file in this documentation task.
- [x] **Step 3: Document** the exact external data requirements: COCO 2017 validation images and panoptic annotations, image IDs, split, deterministic Gaussian blur radii, supported-surface IoU and candidate coverage, calibration/holdout split, and threshold report fields. Mark measured evaluation pending until a provisioned model and licensed dataset are available.
- [x] **Step 4: Update** camera smoke flow for blur warning, retake, continue, and obstruction caveat on browser, Android, and iOS.
- [x] **Step 5: Reconcile** project status with actual test counts and distinguish synthetic tests from real-image evaluation.
- [x] **Step 6: Review** documentation links and verify `git diff --check`.
- [x] **Step 7: Commit** `docs: document scene image quality limits`.

## Notes for the executor

- The project model runtime and weights are not present in the default API image. Do not infer threshold validity from synthetic tests or attempt hidden network downloads in unit tests.
- COCO image source rights remain subject to image-provider terms; the dataset consortium does not own all image copyrights. Use only the held-out validation partition for evaluation; do not redistribute it. If license/terms, data access, or compute are unresolved, keep empirical calibration explicitly pending.
- The metric can flag blur but cannot reliably detect obstruction, low texture, poor framing, or scene-domain mismatch. Explicit continue remains available.
- Preserve existing uncommitted changes in the worktree; stage only task-owned files in every commit.
