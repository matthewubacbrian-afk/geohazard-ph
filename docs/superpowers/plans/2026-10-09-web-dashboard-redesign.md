# GeoHazard PH Web Dashboard Redesign — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign the web interface into a restrained, accessible, map-led field-station UI while preserving existing web data behavior and clearly documenting current gaps.

**Architecture:** Keep React pages/components, API clients, hooks, types, and MapLibre data flow in their current boundaries. Implement semantic tokens and local fonts first, then shared/page styles, responsive dashboard panels, and map symbology; finish with parity and live-app review. After user approval, execute one task at a time with a task brief/report and a fresh subagent, reviewing each result before the next task.

**Tech Stack:** React 18, TypeScript strict, Vite, CSS Modules, TanStack Query, React Router, MapLibre GL, Vitest, Testing Library, Fontsource.

**Spec:** `docs/superpowers/specs/2026-10-09-web-dashboard-redesign-design.md`

## Global Constraints

- Do not start implementation until the user approves this plan.
- Work in the current checkout and `docs/web-interface-refresh` branch. Do not create or switch branches/worktrees.
- Preserve current uncommitted changes in `web/src/components/dashboard/DashboardSidebar.module.css`, `web/src/pages/Dashboard.module.css`, and `web/tests/DashboardLayout.test.mjs`; inspect and integrate the scroll regression work only in its dashboard task. Never discard or accidentally include it in an unrelated commit.
- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `REACT_BEST_PRACTICES.md`, `docs/glossary.md`, `docs/api-contracts.md`, and `docs/testing-standards.md`.
- Keep CSS Modules; no Tailwind, CSS-in-JS, remote font CDN, or icon font. Use IBM Plex fonts self-hosted from Fontsource and retain package license notices.
- Do not change backend, ML, mobile, infrastructure, `web/src/api/`, `web/src/hooks/`, `web/src/types/`, `web/src/lib/risk.ts`, API parameters, or response mappings.
- Preserve every current behavior assertion. Add/adjust tests without deleting assertions to make a change pass. Use TDD for the reachable region lookup and any changed keyboard/accessibility behavior.
- Keep source attribution, empty-layer labels, stale/error/loading/retry states, risk disclaimer, and the statement that the site is not an official PHIVOLCS/NDRRMC advisory.
- Use semantic tokens from `web/src/styles/tokens.css`; do not put brand hex values in component styles.
- Every task produces `.superpowers/sdd/2026-10-09-web-redesign/task-NN-<slug>-brief.md` and `task-NN-<slug>-report.md`. The brief records acceptance and protected behavior; the report records files, commands/results, screenshots, review findings, and remaining limits.
- Make one focused Conventional Commit per completed task after its tests and review. Stage explicit task files only; never stage the unrelated dirty sidebar changes by accident.
- Final required commands: `npm test` and `npm run build` from `web/`; `python scripts\verify_structure.py` and `git diff --check` from repo root.

## File Structure

### Shared design foundation

- `web/src/styles/tokens.css` — semantic surfaces, text, four risk colors, separate four-step magnitude neutrals, spacing, shape, motion, breakpoints, focus, and z-index tokens.
- `web/src/styles/base.css`, `web/src/styles/utilities.css` — typography/reset/focus/reduced-motion and tiny shared helpers.
- `web/src/main.tsx` — self-hosted IBM Plex font imports before app render.
- `web/package.json`, `web/package-lock.json` — exact Fontsource runtime assets (Sans, Serif, Mono only).
- `web/tests/DesignTokens.test.ts` — token contrast checks against each light UI surface.

### Shared views and dashboard

- `web/src/components/layout/TopNav.tsx` and `TopNav.module.css` — responsive route navigation and accessible SVG actions.
- `web/src/components/common/` — current shared panel/control styles and SVG icon primitive if reuse is warranted.
- `web/src/pages/` — Hero, dashboard, About, Data Sources, Historical layouts and their CSS Modules.
- `web/src/components/dashboard/` — control rail, map area, realtime status and styles.
- `web/src/components/events/` — filter bar, feed rows, feed and details.
- `web/src/components/risk/` — panel, cards, existing lookup integration.
- `web/src/components/volcanoes/` — bulletin list/status presentation.
- `web/src/components/map/` — MapLibre paint/legend/status styling and `basemaps.ts` light style reference.
- `web/tests/` — preserve all current behavior assertions; add focused panel/layout coverage only where missing.

### Documentation and SDD artifacts

- `web/REDESIGN_UI.md`, `web/DESIGN_NOTES.md`, `web/WEB_STRUCTURE.md` — approved visual contract, contributor summary, and code/data ownership.
- `docs/superpowers/specs/2026-10-09-web-dashboard-redesign-design.md` — approved design and feature inventory.
- `docs/superpowers/plans/2026-10-09-web-dashboard-redesign.md` — this approved task sequence.
- `.superpowers/sdd/2026-10-09-web-redesign/` — one brief and report per implementation task.

---

### Task 1: Add self-hosted type and semantic design tokens

**Files:**
- Modify: `web/package.json`, `web/package-lock.json`, `web/src/main.tsx`
- Modify: `web/src/styles/tokens.css`, `web/src/styles/base.css`, `web/src/styles/utilities.css`
- Create: `web/tests/DesignTokens.test.ts`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-01-foundation-brief.md`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-01-foundation-report.md`

**Interfaces:**
- Produces semantic variables listed in `web/REDESIGN_UI.md`, IBM Plex Sans/Serif/Mono font-family tokens, `--radius-*`, `--space-*`, reduced-motion and breakpoints.
- Adds self-hosted `@fontsource/ibm-plex-sans`, `@fontsource/ibm-plex-serif`, and `@fontsource/ibm-plex-mono` dependencies; imports only weights used by the UI from `main.tsx`.
- Does not change any component/API signature.

Use these font imports (trim weights only if a UI audit proves a weight unused):

```typescript
import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/ibm-plex-serif/400.css';
import '@fontsource/ibm-plex-serif/600.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
```

The four risk tokens and four magnitude tokens must use the exact values in
`web/REDESIGN_UI.md`; set `--radius-square: 0px`, `--radius-control: 4px`,
`--radius-panel: 10px`, and `--radius-pill: 999px` in `tokens.css`.

- [ ] **Step 1: Write a contrast regression test** in `web/tests/DesignTokens.test.ts`. Import `src/styles/tokens.css`, read the exact risk, magnitude, and surface variables, compute WCAG relative luminance, and assert every foreground pair is ≥4.5:1. Assert the risk and magnitude token sets are distinct. Use only test-local parsing/math; do not add a runtime dependency.
- [ ] **Step 2: Run `npm test -- --run tests/DesignTokens.test.ts` from `web/`.** Confirm it fails because the required four-step semantic token set is not yet present.
- [ ] **Step 3: Install the three Fontsource packages** with `npm install @fontsource/ibm-plex-sans @fontsource/ibm-plex-serif @fontsource/ibm-plex-mono` from `web/`; verify `package-lock.json` contains the three packages and no unrelated dependency additions.
- [ ] **Step 4: Define tokens and font loading.** Add the exact values and roles in `web/REDESIGN_UI.md`; use only needed font weights, set tabular numerals for measurement classes, and preserve the established 4px spacing base while replacing one-radius-everywhere usage with `0/4/10/999px` roles.
- [ ] **Step 5: Run the focused token test** and `npm run build` from `web/`. Expected: contrast and distinct-palette assertions pass; TypeScript/Vite build succeeds.
- [ ] **Step 6: Review and commit** as `style: add geohazard design tokens and fonts`. Record measured ratios, exact font package weights/source, and any license files in the SDD report.

### Task 2: Restyle shared navigation and informational pages

**Files:**
- Modify: `web/src/components/layout/TopNav.tsx`, `TopNav.module.css`
- Modify: `web/src/components/common/SettingsPanel.tsx`, `SettingsPanel.module.css`, `ComingSoon.module.css`, `RiskMeter.module.css`, `SectionHeader.module.css`, `Skeleton.module.css`
- Modify: `web/src/pages/Hero.tsx`, `Hero.module.css`, `InformationalPage.module.css`, `About.tsx`, `DataSources.tsx`, `HistoricalBrowser.tsx`
- Modify: affected tests under `web/tests/` (`App.test.tsx`, `InformationalPages.test.tsx`, `SettingsPanel.test.tsx`)
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-02-shared-pages-brief.md`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-02-shared-pages-report.md`

**Interfaces:** Preserve `TopNav` props, route targets, settings open/close callbacks, page content/source links, and all test-asserted behavior. Use accessible SVG icon components or inline SVG; icon-only actions need `aria-label`.

- [ ] **Step 1: Read existing page/component tests** and write any missing keyboard-navigation/focus assertions before markup changes. Keep current headings, required legal/data wording, and active navigation meaning.
- [ ] **Step 2: Run `npm test -- --run tests/App.test.tsx tests/InformationalPages.test.tsx tests/SettingsPanel.test.tsx`.** Confirm any new assertion fails for the missing accessible/visual behavior it covers.
- [ ] **Step 3: Implement the shared/page treatment** with IBM Plex tokens, clear editorial reading widths, compact accessible navigation, restrained SVG controls, and no hero blobs or fake metrics. Replace prediction-sounding Hero copy and sample risk meters with factual methodology text. Add “Risk profiles are descriptive statistics, not earthquake predictions” to the risk/About contexts and “GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory” to About and dashboard data/status context; keep Historical honest.
- [ ] **Step 4: Run the same focused tests and build.** Expected: existing route/navigation/settings/source assertions remain passing and new keyboard checks pass.
- [ ] **Step 5: Review desktop and 390px route screenshots** for `/`, `/about`, `/data-sources`, and `/historical`; record any backend-independent limitation in the report.
- [ ] **Step 6: Commit** as `style: refresh shared navigation and information pages`.

### Task 3: Make dashboard layout and all controls responsive/scrollable

**Files:**
- Modify: `web/src/pages/Dashboard.module.css`
- Modify: `web/src/components/dashboard/DashboardSidebar.tsx`, `DashboardSidebar.module.css`
- Modify: `web/tests/DashboardSidebar.test.tsx`, `web/tests/DashboardLayout.test.mjs`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-03-dashboard-layout-brief.md`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-03-dashboard-layout-report.md`

**Interfaces:** Keep every current sidebar prop/callback and dashboard query-state behavior. Keep the view, basemap, event/layer/category toggles, start/end dates, and magnitude slider present at all viewport widths. Preserve and inspect the pre-existing uncommitted scroll changes before editing.

- [ ] **Step 1: Audit the existing uncommitted sidebar layout work and write/retain a regression assertion** that the dashboard grid has a bounded row and the sidebar body is the vertical scroll container with `min-height: 0`. Add behavior assertions that the accessible names for date range, magnitude, and all toggles remain present.
- [ ] **Step 2: Run `npm test -- --run tests/DashboardSidebar.test.tsx tests/DashboardLayout.test.mjs`.** Confirm the regression test fails on the old overflowing layout and passes on the current partial fix only where the behavior is actually correct.
- [ ] **Step 3: Implement the desktop/tablet/mobile composition.** Desktop uses controls/map/activity columns; tablet uses controls beside map with activity below; mobile puts all visible controls before the map and activity in one document column. Set `min-height: 0` through every constraining grid/flex parent and `overflow-y: auto` only on bounded rail/panel bodies.

The dashboard grid's bounded-row pattern is:

```css
.main {
  display: grid;
  grid-template-columns: minmax(240px, 280px) minmax(0, 1fr) minmax(300px, 360px);
  grid-template-rows: minmax(0, 1fr);
  min-height: 0;
}

.sidebarBody {
  min-height: 0;
  overflow-y: auto;
}
```
- [ ] **Step 4: Run the focused dashboard tests and inspect 1440px, 900px, and 390px in a full browser.** Verify sidebar can scroll to date/magnitude, the feed is reachable, and no horizontal overflow appears. Record current dirty changes explicitly in the report.
- [ ] **Step 5: Run build and commit** as `style: make dashboard controls responsive and scrollable`; stage only reviewed dashboard files and the layout regression test.

### Task 4: Restyle feed, filter, summary, realtime, and event details

**Files:**
- Modify CSS Modules under `web/src/components/events/` and `web/src/components/dashboard/` for `DashboardMapArea` and `RealtimeStatus`
- Modify: `web/src/pages/Dashboard.module.css` only for panel alignment as needed
- Modify: `web/tests/EventFeed.test.tsx`, `EventListLive.test.tsx`, `EventSelection.test.tsx`, `DashboardSummary.test.tsx`, `DashboardStates.test.tsx`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-04-event-panels-brief.md`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-04-event-panels-report.md`

**Interfaces:** Do not modify `useEvents`, `useEventSummary`, `useRealtimeAlerts`, `api/client.ts`, `api/realtime.ts`, event types, query parameters, filtering, reconciliation, or 30-second intervals.

- [ ] **Step 1: Run the existing focused event/summary/state tests and add assertions only for currently uncovered accessible selection, source-filter, or retry behavior before changing markup.** The map/list must continue receiving the same `visibleEvents` collection.
- [ ] **Step 2: Run the focused tests** with `npm test -- --run tests/EventFeed.test.tsx tests/EventListLive.test.tsx tests/EventSelection.test.tsx tests/DashboardSummary.test.tsx tests/DashboardStates.test.tsx` and confirm any new assertions fail first.
- [ ] **Step 3: Restyle rows/details and summary** for dense scanning, aligned tabular magnitude/depth/time fields, explicit units/source, visible selected/focus states, contextual skeleton/error/empty states, and true server-sourced summary values. Leave “Coming soon” fields honest.
- [ ] **Step 4: Verify focused tests and build.** Expected: the same list order, selection, filters, WebSocket-facing status, retry, summary mapping, and empty/loading/error assertions pass.
- [ ] **Step 5: Commit** as `style: clarify live event and summary panels`.

### Task 5: Align basemaps, overlays, event markers, and legends

**Files:**
- Modify: `web/src/components/map/basemaps.ts`, `MapView.tsx`, `MapView.module.css`, `EventMarker.tsx`, `StaticLayerStatus.module.css`
- Modify: `web/src/components/dashboard/DashboardMapArea.module.css`
- Modify tests: `web/tests/MapView.test.tsx`, `basemaps.test.ts`, `riskOverlay.test.ts`, `StaticLayerStatus.test.tsx`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-05-map-brief.md`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-05-map-report.md`

**Interfaces:** Keep all four basemap choices and provider attribution. Switch Streets to `https://tiles.openfreemap.org/styles/positron`; retain Esri raster templates for Satellite/Hybrid/Terrain. Keep camera lifecycle, GeoJSON geometry, visibility, layer IDs, and current event/risk data mapping stable.

- [ ] **Step 1: Inspect map tests and write/retain assertions** for all basemap options/attributions, event magnitude sizing, risk labels, vector/raster distinction, visibility restoration after style load, and empty/error statuses.
- [ ] **Step 2: Run focused map tests** with `npm test -- --run tests/MapView.test.tsx tests/basemaps.test.ts tests/riskOverlay.test.ts tests/StaticLayerStatus.test.tsx`; verify any new color/symbol expectation fails before the style change.
- [ ] **Step 3: Apply palette-compatible map paint.** Use a distinct neutral magnitude ramp and bounded radii; keep a contrasting outlined/halo marker; use separately labeled risk colors plus pattern/shape cues; keep fault lines and volcano-zone polygons distinct; style controls and attribution on a legible pumice backing.
- [ ] **Step 4: Run focused map tests and build;** inspect all four basemaps at desktop and mobile map dimensions. Ensure tiles, attribution, labels, and overlays remain legible and no overlay implies a current PHIVOLCS alert.
- [ ] **Step 5: Commit** as `style: align map layers with hazard palette`.

### Task 6: Restyle risk and volcano panels; surface the existing region lookup

**Files:**
- Modify: `web/src/components/risk/RiskProfilesPanel.tsx`, `RiskProfilesPanel.module.css`, `RiskProfileCard.tsx`, `RiskProfileCard.module.css`, `RegionLookup.tsx`, `RegionLookup.module.css`
- Modify: `web/src/components/volcanoes/VolcanoPanel.module.css`
- Create/update tests: `web/tests/RiskProfilesPanel.test.tsx`, `RiskProfile.test.tsx`, `VolcanoPanel.test.tsx`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-06-risk-volcano-brief.md`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-06-risk-volcano-report.md`

**Interfaces:** Retain `useRiskProfiles` and `useVolcanoes`. Add only local search state to `RiskProfilesPanel`; reuse `RegionLookup` to filter the loaded profile list. Do not call `fetchRiskProfile`, add a hook, or change the API client. Preserve numeric values, model/dataset metadata, volcano alert level zero/null distinctions, source links, stale cache, and error/retry/empty behavior.

- [ ] **Step 1: Add a failing integration test** rendering `RiskProfilesPanel` with mocked profiles and `useRiskProfiles`; assert a labeled region input filters both lookup rows and visible profile cards. Keep existing component-level lookup and risk card assertions.
- [ ] **Step 2: Run `npm test -- --run tests/RiskProfilesPanel.test.tsx tests/RiskProfile.test.tsx`** and confirm the active panel lookup assertion fails before integration.
- [ ] **Step 3: Integrate the input and existing `RegionLookup`** into the active risk panel, filtering the same already-loaded profile list; add clear-results/empty-query behavior and show the required descriptive-statistics disclaimer. Restyle risk tokens without relying on color alone.

Keep lookup local to the cached profile list:

```typescript
const { data: profiles = [] } = useRiskProfiles();
const [query, setQuery] = useState('');
const filtered = profiles.filter((profile) =>
  profile.region_name.toLowerCase().includes(query.trim().toLowerCase()),
);
```

Render a labeled controlled search input (`aria-label="Filter regions"`), pass
`profiles` and `query` to `RegionLookup`, and render cards from `filtered`. Do not
call `fetchRiskProfile`.
- [ ] **Step 4: Restyle volcano bulletin hierarchy** while retaining PHIVOLCS links, observation/retrieval timestamps, alert level zero/null, stale status, and all status states. Do not change hook options.
- [ ] **Step 5: Run risk/volcano tests and build.** Expected: lookup, values, disclaimer, bulletins, stale, Retry, loading, and empty states pass.
- [ ] **Step 6: Commit** as `feat: expose region lookup in risk panel`. The commit type is `feat` because a previously dormant existing lookup becomes reachable; data behavior and requests stay the same.

### Task 7: Complete parity review, responsive verification, and live-app check

**Files:**
- Update: `web/REDESIGN_UI.md` with a checked before/after parity checklist and final contrast/font/viewport evidence
- Update: `web/DESIGN_NOTES.md`, `web/WEB_STRUCTURE.md` only if final file ownership/layout differs from the approved documents
- Update relevant `web/tests/` assertions only where approved semantic markup changed, without removing behavior coverage
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-07-verification-brief.md`
- Create: `.superpowers/sdd/2026-10-09-web-redesign/task-07-verification-report.md`

- [ ] **Step 1: Run the complete web suite** from `web/` with `npm test`; resolve failures without relaxing behavior assertions.
- [ ] **Step 2: Run the production build** from `web/` with `npm run build`; resolve strict TypeScript or Vite errors.
- [ ] **Step 3: Run repository checks** from the root with `python scripts\verify_structure.py` and `git diff --check`. Expected: both succeed; no generated `web/dist`, credentials, or local datasets are staged.
- [ ] **Step 4: Start local data services and app for visual review** using the README/Runbook procedures: `docker compose up -d postgres redis`, apply migrations, start the API, then start the web app; start the ingestion worker only if live event freshness is needed. Keep all services in visible/manageable sessions and record unavailable external sources honestly.
- [ ] **Step 5: Inspect every route** at 1440px, 900px, and 390px. Capture screenshots for Hero, Dashboard event/risk/volcano views, About, Data Sources, and Historical. Check sidebar scroll to date/magnitude in full browser, panel/feed reachability, keyboard focus, zoom/reflow, contrast, reduced motion, and no horizontal clipping.
- [ ] **Step 6: Exercise live data when reachable:** event source/date/magnitude/category filters affect list and map; summary values come from API; `/ws/events` connects and reconnect/reconcile remains; volcano bulletins expose source/time/stale fields; fault/volcano switches show loaded or explicit empty state; risk overlay and active region lookup use actual cluster data; stop/retry UI remains covered by tests. Do not mark a failed/unavailable prerequisite passed.
- [ ] **Step 7: Fill the parity checklist** in `web/REDESIGN_UI.md`, review complete diff and current working tree, and confirm no protected backend/API/hook/type/mobile/ML file changed.
- [ ] **Step 8: Commit verification-driven changes only** with a focused Conventional Commit and rerun the affected checks. Write actual results and remaining external-data limitations in the SDD report.

## Notes for the executor

- **Approval gate:** This plan is the approval artifact. Do not execute Tasks 1–7 until the user approves it.
- **Subagent workflow:** After approval, read `C:\Users\matth\.codex\skills\subagent-driven-development\SKILL.md`. Create each task brief before dispatching one fresh implementer subagent; review the diff and test evidence before accepting its report. Use a separate reviewer subagent for each completed task. Keep tasks sequential because they share token and CSS files; do not parallel-edit the same component tree.
- **SDD artifacts:** The user requested one brief and report per task under `.superpowers/sdd/2026-10-09-web-redesign/`. Commit each completed pair with its task changes after verification.
- **Current checkout state:** The project services were explicitly stopped earlier; starting them is reserved for approved implementation verification. Existing database volumes should be retained. Do not run `docker compose down --volumes`.
- **Live prerequisites:** PostGIS/Redis, `backend/.venv`, migrated schema, external USGS/PHIVOLCS access, and imported local static data may be unavailable. Distinguish API response empty states from missing data imports and network failures.
- **Branch and dirty files:** Stay on `docs/web-interface-refresh`. Do not rebase, create a worktree, or commit the current uncommitted sidebar work until its ownership and task scope are verified.
- **Parity evidence:** Compare each row in `web/REDESIGN_UI.md` before and after. A visual refresh is incomplete if any filter, layer toggle, data field, source, error/empty/retry/stale state, or required disclaimer has disappeared.
