# Scene Review Camera Workspace — Design

**Date:** 2026-10-14

## Problem

`web/src/pages/SceneAnalysis.tsx` renders Scene Review as a narrow, plain page and opens only the rear camera. That page no longer feels like the GeoHazard PH field-station interface, and users cannot choose the front camera, mirror the live preview, or frame a subject with zoom.

## Goals

- Restyle Scene Review with the app’s shared field-station tokens, button language, clear status treatment, and responsive layout.
- Provide working front/rear camera selection, preview-only mirroring, and zoom while the camera is active.
- Keep zoom reflected in both the preview and captured image, including on devices without native camera zoom.
- Preserve capture compression, transient API submission, result overlays/checklist, error and quality-warning flows, privacy copy, and camera cleanup.
- Keep all controls keyboard-accessible and operable at mobile and desktop widths.

## Non-goals

- Add image upload, video recording, camera preference persistence, new API fields, model behavior, or backend endpoints.
- Present visual cues as safety guidance or change the existing disclaimer.
- Add torch, focus, exposure, or camera-device enumeration controls.

## Context And Constraints

- The active route is `/scene-analysis`, registered in `web/src/App.tsx`; `TopNav` maps the “Scene Review” button to it.
- Scene analysis uses `navigator.mediaDevices.getUserMedia`, a transient `SceneCapture`, and `POST /scene-analyses`. The photo is not persisted by this UI.
- Dashboard appearance uses shared variables from `web/src/styles/tokens.css`, CSS modules, and compact operational controls.
- Browser camera permissions and hardware capabilities vary. Camera access remains a user action, and zoom must still work digitally where `MediaTrackCapabilities.zoom` is unavailable.
- Read `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/testing-standards.md`; this is a web-only behavior and presentation change with no API contract change.

## Alternatives Considered

1. **Field capture workspace (chosen):** A prominent camera stage paired with a compact settings and guidance card, stacking on small screens. It matches the app’s map-plus-control hierarchy while keeping camera framing primary.
2. **Full-screen camera with a bottom drawer:** Gives the feed maximum space, but makes guidance and camera options less discoverable and does not fit the app’s page navigation as well.
3. **Dashboard-style three-panel view:** Reuses the dashboard structure, but adds unnecessary density to a single-image capture task.

## Design

### Layout and states

- Use a page header with the existing Back action, a small operational eyebrow, the “Camera scene review” heading, and concise purpose copy.
- Keep the existing safety disclaimer and privacy note visible before camera use.
- On desktop, use a two-column workspace: the larger camera/preview stage on the left and a settings/instructions card on the right. On narrow screens, stack the stage, settings, and captured results in that order.
- The idle stage explains the camera action and has a clear primary “Open camera” button. The live stage keeps the preview dominant and places settings in a labeled Camera controls card. The captured stage retains Analyze, Retake, loading, error, quality-warning, and evidence-result behaviors.
- Use shared surfaces, spacing, typography, focus, borders, and semantic colors. Camera readiness and errors always include text and accessible status semantics.

### Camera controls and behavior

- **Camera:** Rear is the initial choice. A labeled Rear/Front selector requests `facingMode: "environment"` or `facingMode: "user"`. Switching stops the active stream before opening the selected facing mode. If access fails, stop any stream, keep the page responsive, and show an actionable error.
- **Mirror:** A labeled toggle applies `scaleX(-1)` to the live preview only. The capture canvas continues drawing the untransformed video, so the analyzed image keeps camera orientation.
- **Zoom:** A labeled range input defaults to 1×. Read the active track’s native zoom range when available and update it through `applyConstraints`. If native zoom is unavailable or applying it fails, use digital zoom from 1× to 3×: crop the centered source rectangle in the preview and use the same crop when drawing the captured canvas. The displayed value includes an accessible numeric label. Zoom resets to 1× after a camera switch; mirror setting remains as currently selected.
- **Lifecycle:** Camera access starts only after “Open camera”; closing, capturing, switching, leaving, or unmounting stops every old track. Camera selection, mirror, and zoom remain in component memory only and reset when leaving Scene Review.
- **Errors:** Unsupported media access and permission/device failures use the existing camera error alert pattern. A camera-switch failure leaves the camera closed and gives the user a way to retry. No browser permission prompt is requested before the user chooses to open the camera.

### Data flow

```text
Open camera → getUserMedia(facingMode) → live stream
Settings → native track zoom OR digital preview crop
Capture → same digital crop (when active) → existing JPEG compression → SceneCapture
Analyze → existing /scene-analyses request → existing results and limitations
```

The mirror transform is visual-only and is never applied to the captured canvas. No backend/API changes are needed.

## Rollout

Ship as a web feature branch. No migration, feature flag, server configuration, or mobile change is required. Camera controls are hidden until the user opens the camera; unsupported native zoom falls back to digital zoom.

## Files

- `web/src/pages/SceneAnalysis.tsx` — camera facing, preview mirroring, hardware/software zoom, and workspace states.
- `web/src/pages/SceneAnalysis.module.css` — responsive field-workspace layout and camera control styling.
- `web/tests/SceneAnalysis.test.tsx` — camera constraints, switching and cleanup, mirror-only preview behavior, zoom and capture crop, and existing analysis states.
- `web/tests/SceneAnalysisStyles.test.tsx` — responsive and control styling acceptance assertions.

## Testing Strategy

- In `SceneAnalysis.test.tsx`, test rear/front `getUserMedia` constraints, track cleanup on switch/close/unmount, mirror preview CSS while preserving original capture pixels, native zoom `applyConstraints`, digital zoom crop for preview and canvas, and camera failure states.
- Keep existing analysis, quality-warning, retry, result selection, and cleanup tests passing.
- In `SceneAnalysisStyles.test.tsx`, assert desktop two-column and narrow-screen stacked layout and visible focus/accessibility affordances.
- Run `npm test` and `npm run build` from `web/`; run `git diff --check` and the repository structure verifier.
- Manually open `/scene-analysis`, check the page at desktop and narrow widths, verify button and settings states, and check browser console. Physical camera testing is environment-dependent; do not grant camera permission without the user's action.

## Acceptance Criteria

- [ ] The Scene Review page uses shared GeoHazard PH surfaces, type, spacing, and controls.
- [ ] A user can open and close the camera, switch front/rear, mirror the live preview only, and change zoom.
- [ ] Digital zoom matches the photo sent for analysis when native zoom is unavailable.
- [ ] Camera tracks stop on switch, close, capture, exit, and unmount.
- [ ] Existing transient analysis, disclaimer, quality warning, errors, results, and retry flows remain intact.
- [ ] Web tests and production build pass; no new browser console errors appear.

## Out Of Scope (backlog)

- Persistent camera preferences, torch/focus/exposure controls, selectable enumerated device names, and image upload.
- Physical-device camera coverage on a matrix of browsers and hardware.
- Backend packaging/calibration and scene-analysis safety claims.

---

## Spec self-review

- No placeholders remain; goals map to acceptance criteria.
- Mirror semantics are explicit: preview only.
- Zoom behavior is explicit for both native and unsupported hardware, including capture parity.
- Scope is a single web-only implementation plan.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-14-scene-review-camera-workspace.md`.
- Terminology: `docs/glossary.md`.
