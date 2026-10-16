# Scene Review Camera Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Restyle Scene Review to match GeoHazard PH and add working front/rear, preview mirror, and camera zoom controls.

**Architecture:** Keep the existing SceneAnalysis page and API intact. Extend its camera lifecycle so the live stream exposes facing and zoom settings; native zoom is preferred, with a centered digital crop used for both preview and capture as fallback. Restyle the same route as a responsive two-column capture workspace using existing tokens.

**Tech Stack:** React, TypeScript, CSS Modules, Vitest, Testing Library, MediaDevices and MediaStreamTrack browser APIs.

**Spec:** `docs/superpowers/specs/2026-10-14-scene-review-camera-workspace-design.md`

## Global Constraints

- Follow `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, and the design spec.
- Use TDD: add a failing behavior test, run it, implement only that behavior, then rerun it.
- Preserve `SceneCapture`, JPEG size/quality bounds, `/scene-analyses` payload, disclaimers, and analysis result/error flows.
- Never mirror captured pixels; mirroring is a CSS transform on the preview only.
- Zoom must match in preview and captured pixels. Prefer native zoom; fall back to centered digital crop.
- Stop all tracks when switching, closing, capturing, exiting, or unmounting.
- Web verification: `npm test`, `npm run build` from `web/`; `python scripts\verify_structure.py`; `git diff --check`.
- Commit with Conventional Commit messages and do not include generated artifacts or secrets.

---

### Task 1: Camera state, facing selection, and lifecycle

**Files:**
- Modify: `web/src/pages/SceneAnalysis.tsx`
- Test: `web/tests/SceneAnalysis.test.tsx`

**Interfaces:**
- Add local facing state with values `'environment' | 'user'`, default `'environment'`.
- Camera start requests `getUserMedia({ video: { facingMode }, audio: false })`.
- Camera switch stops prior stream tracks before requesting the other facing mode; failed requests leave no active stream and show the existing alert.

- [x] **Step 1: Add failing tests** for default rear-facing constraints, switching to front-facing, stopping old tracks, and failed switch cleanup.
- [x] **Step 2: Run focused tests** with `npm test -- --run tests/SceneAnalysis.test.tsx`; confirm failures concern facing selection or cleanup.
- [x] **Step 3: Implement lifecycle** in `SceneAnalysis.tsx`; keep the selector disabled while the camera is opening, show current facing accessibly, stop all tracks before switching, and preserve unmount cleanup.
- [x] **Step 4: Rerun focused tests** and confirm switching and cleanup pass without breaking existing capture tests.
- [x] **Step 5: Commit** as `feat: add camera facing selection to scene review`.

### Task 2: Preview mirror and capture-safe zoom

**Files:**
- Modify: `web/src/pages/SceneAnalysis.tsx`
- Modify: `web/src/pages/SceneAnalysis.module.css`
- Test: `web/tests/SceneAnalysis.test.tsx`

**Interfaces:**
- Add a boolean mirror toggle that controls only a preview class.
- Add zoom state and an accessible 1×–maximum range input. Native maximum comes from the active track capabilities; when unavailable, use 1×–3× digital zoom.
- For software zoom `z >= 1`, derive the center source rectangle as `sw = videoWidth / z`, `sh = videoHeight / z`, `sx = (videoWidth - sw) / 2`, and `sy = (videoHeight - sh) / 2`; use it in preview styling and `drawImage(video, sx, sy, sw, sh, 0, 0, canvasWidth, canvasHeight)`.
- For native zoom, apply the requested value to the active video track with `applyConstraints`; if unsupported or rejected, set software-zoom mode and retain the chosen amount within its range.

- [x] **Step 1: Add failing tests** for preview-only mirroring, native zoom constraints, software zoom fallback, and the same digital crop being used by capture.
- [x] **Step 2: Run the focused tests** and confirm each new assertion fails for the expected missing behavior.
- [x] **Step 3: Implement mirror and zoom** with labeled switch/range controls; keep mirror CSS separate from the canvas path and share the crop calculation between preview and capture.
- [x] **Step 4: Rerun focused tests** and confirm hardware and software paths pass; include a rejected `applyConstraints` case.
- [x] **Step 5: Commit** as `feat: add mirror and zoom camera controls`.

### Task 3: Responsive field capture workspace

**Files:**
- Modify: `web/src/pages/SceneAnalysis.tsx`
- Modify: `web/src/pages/SceneAnalysis.module.css`
- Test: `web/tests/SceneAnalysisStyles.test.tsx`
- Test: `web/tests/SceneAnalysis.test.tsx`

**Interfaces:**
- Keep the existing route, Back callback, API function, page copy, privacy note, disclaimer, and all result-state controls.
- Add semantic stage and settings regions; desktop uses a larger preview column plus a settings card, narrow view stacks preview then settings.

- [x] **Step 1: Add failing assertions** for desktop workspace layout, narrow stacked layout, labeled camera settings, and existing captured-result actions.
- [x] **Step 2: Run the focused page/style tests** and confirm new layout/control assertions fail before implementation.
- [x] **Step 3: Implement the workspace** with existing design tokens, shared button styling, visible focus, explanatory unsupported-camera errors, and mobile reflow; do not add a new dependency.
- [x] **Step 4: Rerun focused tests** and confirm existing quality-warning, analysis, and cleanup behaviors still pass.
- [x] **Step 5: Commit** as `style: align scene review with field dashboard`.

### Task 4: Full verification and manual browser review

**Files:**
- Verify: all files listed above.

- [x] **Step 1: Run the full web suite** with `npm test` from `web/`; expected: all test files pass.
- [x] **Step 2: Run the production build** with `npm run build` from `web/`; expected: exit code 0.
- [x] **Step 3: Run repository checks** with `python scripts\verify_structure.py` from the repo root and `git diff --check`; expected: no structural or whitespace errors.
- [x] **Step 4: Walk the UI** at `/scene-analysis` at desktop and narrow widths; verify idle, camera mock/permission-denied, switched-facing, mirror-preview, zoom, captured, analysis, and retry states. Do not accept camera permission automatically; use mocked tracks for automated tests.
- [x] **Step 5: Commit any verified test-only corrections** with their appropriate Conventional Commit type; do not claim device hardware behavior was tested unless a real camera was available.

---

## Notes for the executor

- Tasks 1 and 2 modify the same page and must be implemented in order. Task 3 follows after camera behavior stabilizes. Task 4 is final verification.
- Browser API camera access requires a secure context and explicit user permission; localhost qualifies, but automated tests should mock `getUserMedia` and tracks.
- Physical front/rear switching and native lens zoom depend on device support; digital zoom is the deterministic fallback for zoom, while unavailable camera directions should produce a retryable message.
