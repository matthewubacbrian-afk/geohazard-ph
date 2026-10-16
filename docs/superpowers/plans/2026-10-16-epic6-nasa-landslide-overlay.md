# Epic 6 NASA Landslide Susceptibility Overlay Implementation Plan

> **For agentic workers:** Execute this plan inline using the executing-plans skill; track each checkbox and keep the test-first order.

**Goal:** Add an optional NASA global landslide susceptibility raster reference to the dashboard map with clear attribution, limitations, loading/error feedback, and retry.

**Architecture:** A small MapLibre helper will construct and synchronize the remote ArcGIS ImageServer raster layer. `MapView` reports source status to dashboard state; the dashboard routes a default-off toggle and displays a dedicated status/legend panel. No NASA raster is downloaded or persisted.

**Tech Stack:** React 18, TypeScript, MapLibre GL, CSS Modules, Vitest, React Testing Library.

---

## File Structure

- Create `web/src/components/map/landslideOverlays.ts` for source/layer ID, NASA attribution, state type, and add/remove helpers.
- Create `web/tests/landslideOverlays.test.ts` for URL/source and synchronization behavior.
- Create `web/src/components/map/LandslideOverlayStatus.tsx` and colocated CSS module for state, legend, attribution, retry, and the reviewed caveat copy.
- Create `web/tests/LandslideOverlayStatus.test.tsx` for loading, error/retry, and ready state rendering.
- Modify `web/src/components/map/MapView.tsx` and `web/src/components/dashboard/DashboardMapArea.tsx` to wire layer visibility and map status.
- Modify `web/src/pages/Dashboard.tsx` and `web/src/components/dashboard/DashboardSidebar.tsx` to own default-off state, toggle callback, retry, and status display.
- Update `web/tests/MapView.test.tsx`, `web/tests/DashboardSidebar.test.tsx`, and `web/tests/DashboardActivity.test.tsx` where needed for integration behavior.
- Keep the approved wording and source record in `docs/superpowers/specs/2026-10-16-epic6-nasa-landslide-overlay-design.md`, `docs/glossary.md`, and `docs/data-sources.md` unchanged unless implementation reveals a factual mismatch.

## Task 1: Define and test NASA raster source synchronization

**Files:** Create `web/tests/landslideOverlays.test.ts`; create `web/src/components/map/landslideOverlays.ts`.

- [x] **Step 1: Write failing tests** for the NASA export tile template, NASA attribution, default layer addition with opacity, visibility changes, and removing the source/layer.
- [x] **Step 2: Run** `npm test -- tests/landslideOverlays.test.ts` from `web/`; confirm failure because the module does not exist.
- [x] **Step 3: Implement** `LANDSLIDE_LAYER_ID`, `LANDSLIDE_IMAGE_SERVICE`, `LANDSLIDE_ATTRIBUTION`, `LandslideOverlayState`, `syncLandslideOverlay(map, enabled)`, and `removeLandslideOverlay(map)`. Use the ImageServer `exportImage` operation with `{bbox-epsg-3857}`, EPSG:3857 bbox/image spatial references, 256×256 PNG, transparency, and NASA attribution link. Never infer raster data locally.
- [x] **Step 4: Re-run** the focused test and confirm all source/lifecycle expectations pass.

## Task 2: Build status, legend, and caveat UI

**Files:** Create `web/tests/LandslideOverlayStatus.test.tsx`; create `web/src/components/map/LandslideOverlayStatus.tsx`; create `web/src/components/map/LandslideOverlayStatus.module.css`.

- [x] **Step 1: Write failing tests** for loading, error with retry, and ready copy. Ready state must show NASA credit/link, `Low · 0`, `High · 5`, and `Coarse, informational susceptibility reference for awareness; not an early-warning authority or site-level assessment.`
- [x] **Step 2: Run** `npm test -- tests/LandslideOverlayStatus.test.tsx` from `web/`; confirm the component is missing.
- [x] **Step 3: Implement** a typed component with props `{ state: LandslideOverlayState; onRetry: () => void }`, semantic `role=status`/`role=alert`, a button retry, and existing design tokens/static-layer styling conventions.
- [x] **Step 4: Re-run** the focused test and confirm it passes.

## Task 3: Wire the default-off map toggle and status lifecycle

**Files:** Modify `web/src/components/map/MapView.tsx`, `web/src/components/dashboard/DashboardMapArea.tsx`, `web/src/pages/Dashboard.tsx`, and `web/src/components/dashboard/DashboardSidebar.tsx`; modify the existing tests listed above.

- [x] **Step 1: Add failing tests** asserting the sidebar exposes `Landslide susceptibility` and emits key `landslideSusceptibility`, the map adds the remote source only when enabled, and the dashboard starts with the layer disabled.
- [x] **Step 2: Run** `npm test -- tests/DashboardSidebar.test.tsx tests/MapView.test.tsx tests/DashboardActivity.test.tsx` from `web/`; confirm failures match missing toggle/prop/layer behavior.
- [x] **Step 3: Implement** `showLandslideSusceptibility?: boolean` and `onLandslideOverlayState?: (state: LandslideOverlayState) => void` on `MapView`, defaulting visibility to false. Keep the latest prop/callback in refs, synchronize the overlay after style load and when visibility changes, recognize only the landslide source in MapLibre `error`, `idle`, and `sourcedataloading` events, and remove listeners/resources safely on teardown/style replacement. Thread props through `DashboardMapArea`; initialize `activeLayers.landslideSusceptibility` to false; add the sidebar checkbox; show `LandslideOverlayStatus` when enabled; retry by incrementing an overlay revision and recreating the source.
- [x] **Step 4: Re-run** focused tests and fix any regressions.

## Task 4: Full verification and review

**Files:** All files from Tasks 1–3.

- [x] **Step 1: Run** `npm test` from `web/`.
- [x] **Step 2: Run** `npm run build` from `web/`.
- [x] **Step 3: Run** `python scripts/verify_structure.py` from repository root and `git diff --check`.
- [x] **Step 4: Inspect** the dashboard in a browser with the NASA service reachable; verify toggle on/off, source attribution, layer ordering, and retry/error behavior. If external NASA tiles are unavailable, report that limitation separately from automated verification.
- [x] **Step 5: Review** the final diff for compliance with the approved design and ensure no raster data, credentials, generated artifacts, or backend changes were introduced.

## Plan self-review

- All approved feature goals map to Tasks 1–4 and the spec acceptance criteria.
- UI copy and attribution are explicit; intermediate classes are not invented.
- NASA requests remain remote; MGB remains a possible future complementary layer after rights and coverage review; InSAR is untouched.
- MapLibre's existing error and idle event lifecycle is reused, with source filtering to avoid reporting unrelated map errors as NASA failures.
