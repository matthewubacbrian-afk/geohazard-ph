# Web MVP Completion - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the web MVP so users can navigate shareable routes, inspect dashboard summaries and regional risk overlays, and read the supporting project pages.

**Architecture:** First add a versioned Philippine-region boundary asset and its attribution, then migrate the app shell from local view state to React Router. Add the informational pages and dashboard summary using existing APIs, then join risk profiles to boundary geometry through a pure transformation before wiring the MapLibre layer. Finish by serializing stable dashboard state into query parameters and running the full web verification suite.

**Tech Stack:** React 18, TypeScript, Vite, React Router, TanStack Query, MapLibre GL, Vitest, Testing Library, GeoJSON.

**Spec:** `docs/superpowers/specs/2026-09-12-web-mvp-completion-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/api-contracts.md`, and `docs/testing-standards.md`.
- Work only in the web package and related documentation/data attribution for this slice.
- Use `snake_case` for API fields and preserve the existing `RiskProfile` wire shape.
- Keep React components typed; do not introduce `any`.
- Keep network and MapLibre behavior mocked in tests.
- Do not fabricate region geometry from `region_name`; unmatched profiles must be omitted from the overlay.
- Do not commit credentials, generated `web/dist/`, caches, or large raw source files.
- Run `npm test` and `npm run build` from `web/` after web changes.
- Run `python scripts\verify_structure.py` when files are added or moved, and run `git diff --check` before each commit.
- Use Conventional Commits with imperative lowercase messages.

---

### Task 1: Add Region Boundary Data And Attribution

**Files:**
- Create: `web/src/data/philippine-regions.json`
- Create: `web/src/data/philippine-regions.ts`
- Modify: `docs/data-sources.md`
- Test: `web/tests/riskOverlay.test.ts`

**Interfaces:**
- `philippine-regions.ts` exports `PHILIPPINE_REGIONS` as a typed `FeatureCollection<Polygon | MultiPolygon>` loaded from the checked-in boundary asset.
- Each boundary feature has a normalized `region_name` property used to join the existing `RiskProfile.region_name` field.
- The asset metadata records its upstream source, dataset version/date, license, and download URL in `docs/data-sources.md`.

- [ ] **Step 1: Write the failing boundary-join test**

Add a fixture boundary collection in `web/tests/riskOverlay.test.ts` with two polygon features whose `region_name` values differ in case from two `RiskProfile` records. Assert that the intended helper returns two matched features and preserves each polygon geometry.

```ts
it('joins profiles to region boundaries case-insensitively', () => {
  const result = riskProfilesToFeatureCollection(profiles, boundaries);

  expect(result.features).toHaveLength(2);
  expect(result.features[0].properties).toMatchObject({
    region_name: 'Bicol Region',
    label: 'High',
  });
  expect(result.features[0].geometry).toEqual(boundaries.features[0].geometry);
});
```

- [ ] **Step 2: Run the focused test and verify it fails**

Run: `npm test -- --run web/tests/riskOverlay.test.ts` from the repository root, or `npm test -- riskOverlay.test.ts` from `web/`.

Expected: FAIL because the risk-overlay helper and boundary module do not exist.

- [ ] **Step 3: Obtain and normalize the boundary asset**

Use the GeoBoundaries open ADM1 Philippines dataset or another license-compatible source approved by the repository owner. Keep the checked-in JSON FeatureCollection limited to the Philippine region features required by the overlay, retain WGS84 coordinates, normalize the boundary name property to `region_name`, and record the exact upstream URL, release/version, license, and attribution in `docs/data-sources.md`. Do not commit the upstream archive or unrelated raw files.

- [ ] **Step 4: Export a typed boundary collection**

Create `web/src/data/philippine-regions.ts` with a typed import of the JSON GeoJSON FeatureCollection and a runtime-safe export:

```ts
import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson';
import regions from './philippine-regions.json';

export type RegionBoundary = FeatureCollection<Polygon | MultiPolygon>;

export const PHILIPPINE_REGIONS = regions as RegionBoundary;
```

If TypeScript needs a declaration for JSON/GeoJSON imports, add the smallest local declaration required by the current Vite configuration.

- [ ] **Step 5: Run the focused test and verify it passes**

Run: `npm test -- riskOverlay.test.ts` from `web/`.

Expected: PASS for case-insensitive matching and geometry preservation.

- [ ] **Step 6: Commit**

```bash
git add web/src/data/philippine-regions.json web/src/data/philippine-regions.ts web/tests/riskOverlay.test.ts docs/data-sources.md
git commit -m "feat: add region boundaries for web risk overlay"
```

### Task 2: Migrate The App Shell To URL Routing

**Files:**
- Modify: `web/package.json`
- Modify: `web/src/App.tsx`
- Modify: `web/src/types/views.ts` if no longer used after migration
- Modify: existing shared navigation component files under `web/src/components/layout/`
- Create or modify: `web/tests/App.test.tsx`

**Interfaces:**
- Routes are `/`, `/dashboard`, `/about`, `/data-sources`, and `/historical`.
- Unknown paths redirect to `/`.
- Shared settings state remains owned by `App` and remains available to dashboard pages.
- Existing page components continue receiving only non-routing props they actually use.

- [ ] **Step 1: Write failing route tests**

Test each route with `MemoryRouter`, assert the page heading or unique page marker, assert an unknown route redirects to Hero, and assert a navigation link changes the rendered page.

```tsx
it('renders the dashboard for a direct route', () => {
  render(
    <MemoryRouter initialEntries={['/dashboard']}>
      <App />
    </MemoryRouter>,
  );

  expect(screen.getByRole('main', { name: /geospatial risk dashboard map/i })).toBeTruthy();
});
```

- [ ] **Step 2: Run route tests and verify they fail**

Run: `npm test -- App.test.tsx` from `web/`.

Expected: FAIL because `react-router-dom` is not installed and `App` ignores the URL.

- [ ] **Step 3: Install React Router**

Run from `web/`: `npm install react-router-dom`.

Confirm `web/package.json` and `web/package-lock.json` contain the dependency and no unrelated packages were changed.

- [ ] **Step 4: Replace local view switching with routes**

Wrap the app shell in `BrowserRouter`, define the five routes, add a wildcard redirect, and replace `onNavigate` callback usage in shared navigation with `Link` or `NavLink`. Keep the settings panel outside the route elements so it can be opened from dashboard navigation without duplicating state.

- [ ] **Step 5: Run route tests and verify they pass**

Run: `npm test -- App.test.tsx` from `web/`.

Expected: PASS for direct routes, fallback, and navigation.

- [ ] **Step 6: Commit**

```bash
git add web/package.json web/package-lock.json web/src/App.tsx web/src/types/views.ts web/src/components/layout web/tests/App.test.tsx
git commit -m "feat: add browser routes to web app"
```

### Task 3: Complete Informational Pages And Navigation Content

**Files:**
- Modify: `web/src/pages/About.tsx`
- Modify: `web/src/pages/DataSources.tsx`
- Modify: `web/src/pages/HistoricalBrowser.tsx`
- Modify: existing page module CSS files for those pages
- Modify: shared navigation/footer files under `web/src/components/layout/`
- Create or modify: `web/tests/InformationalPages.test.tsx`

**Interfaces:**
- About, Data Sources, and Historical Browser render without API access.
- Historical Browser has explanatory copy and a working link to `/dashboard`; it has no fake search, date, export, or disabled controls.
- Source copy uses the provider names and attribution rules in `docs/data-sources.md`.

- [ ] **Step 1: Write failing page-content tests**

Assert that About explains the project purpose and descriptive-risk limitation, Data Sources shows USGS and PHIVOLCS attribution, and Historical Browser shows future-feature language plus a dashboard link.

- [ ] **Step 2: Run the focused tests and verify the expected failures**

Run: `npm test -- InformationalPages.test.tsx` from `web/`.

Expected: FAIL for any missing or stale content/link.

- [ ] **Step 3: Implement page content using existing layout and CSS Modules**

Use the current design tokens and page layout patterns. Keep the Historical page informational rather than rendering controls that imply a working backend feature. Replace stale navigation labels and update the footer year without introducing hard-coded dead routes.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `npm test -- InformationalPages.test.tsx` from `web/`.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/pages web/src/components/layout web/tests/InformationalPages.test.tsx
git commit -m "feat: complete web informational pages"
```

### Task 4: Add The Dashboard Summary Card

**Files:**
- Modify: `web/src/components/dashboard/DashboardMapArea.tsx` or extract the summary region if the file already owns the card
- Create or modify: summary card component and CSS Module under `web/src/components/dashboard/`
- Modify: `web/src/hooks/useEventSummary.ts` only if the existing hook lacks the required state contract
- Create or modify: `web/tests/DashboardSummary.test.tsx`

**Interfaces:**
- Summary consumes `EventSummary | undefined` plus query loading/error state.
- It displays `event_count`, `avg_magnitude`, `max_magnitude`, and `latest_occurred_at` when available.
- It renders explicit loading, empty, and error states without blocking the event map.

- [ ] **Step 1: Write failing summary tests**

Cover loading skeleton/status, successful values, empty/null summary values, error text with retry action, and preservation of the event-map landmark when summary data fails.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `npm test -- DashboardSummary.test.tsx` from `web/`.

Expected: FAIL because the current region card does not expose the complete tested summary states.

- [ ] **Step 3: Implement the smallest summary component**

Render API values with existing formatting helpers/styles. Keep null magnitude/timestamp values as an explicit unavailable state; do not derive official alert status or risk labels from magnitude.

- [ ] **Step 4: Run the focused tests and verify they pass**

Run: `npm test -- DashboardSummary.test.tsx` from `web/`.

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/dashboard web/src/hooks/useEventSummary.ts web/tests/DashboardSummary.test.tsx
git commit -m "feat: add dashboard activity summary"
```

### Task 5: Render The Regional Risk Overlay

**Files:**
- Create or modify: `web/src/components/map/riskOverlay.ts`
- Modify: `web/src/components/map/MapView.tsx`
- Modify: `web/src/components/dashboard/DashboardMapArea.tsx`
- Modify: `web/src/pages/Dashboard.tsx`
- Modify: `web/src/components/dashboard/DashboardSidebar.tsx` if risk-layer controls need explicit synchronization
- Modify: `web/src/styles/tokens.css` only if a missing semantic overlay color is required
- Modify: `web/tests/riskOverlay.test.ts`
- Create or modify: `web/tests/MapView.test.tsx`

**Interfaces:**
- `riskProfilesToFeatureCollection(profiles, boundaries)` returns a GeoJSON `FeatureCollection<Polygon | MultiPolygon>`.
- Profile joins are case-insensitive on `region_name`.
- Matched feature properties include `region_name`, `label`, `confidence`, and `model_version`.
- Missing profiles or unmatched boundaries produce no fabricated geometry and do not prevent event rendering.

- [ ] **Step 1: Extend failing pure-helper tests**

Assert matched geometry, canonical labels, confidence properties, unmatched-region omission, empty inputs, and no inferred polygon output.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `npm test -- riskOverlay.test.ts` from `web/`.

Expected: FAIL until the helper exists and performs the join.

- [ ] **Step 3: Implement the pure join helper**

Index boundaries by normalized `region_name`, iterate profiles, and create features by copying matched boundary geometry and attaching profile properties. Keep the helper independent of React and MapLibre.

- [ ] **Step 4: Add MapLibre source/layer synchronization**

Add a `risk-regions` GeoJSON source and fill/outline layers in `MapView`. Update source data when profiles or the active risk-level filter changes, set visibility from the dashboard risk-layer state, and remove/recreate custom layers after basemap style changes using the same lifecycle approach as existing event/static layers.

- [ ] **Step 5: Pass profiles and boundary data through the dashboard**

Use `useRiskProfiles()` at the dashboard/map ownership boundary, keep loading/error local to the risk layer, and leave events, faults, and volcano zones functional if the risk query fails.

- [ ] **Step 6: Add map behavior tests**

Mock MapLibre and assert the risk source/layer is configured only with converted valid features, visibility follows the risk toggle, and risk-query failure does not remove the event source.

- [ ] **Step 7: Run focused tests and verify they pass**

Run: `npm test -- riskOverlay.test.ts MapView.test.tsx` from `web/`.

Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add web/src/data web/src/components/map web/src/components/dashboard web/src/pages/Dashboard.tsx web/src/styles/tokens.css web/tests/riskOverlay.test.ts web/tests/MapView.test.tsx
git commit -m "feat: render regional risk overlay"
```

### Task 6: Persist Stable Dashboard State In The URL

**Files:**
- Modify: `web/src/pages/Dashboard.tsx`
- Create: `web/src/lib/dashboardQueryState.ts`
- Modify: `web/src/components/dashboard/DashboardSidebar.tsx` only if controlled values need URL-backed defaults
- Create or modify: `web/tests/dashboardQueryState.test.ts`
- Modify: `web/tests/App.test.tsx` or create `web/tests/DashboardRouting.test.tsx`

**Interfaces:**
- `parseDashboardQuery(search: string): DashboardQueryState` returns validated defaults for `view`, `source`, `startDate`, `endDate`, `minMagnitude`, `basemap`, and `region`.
- `serializeDashboardQuery(state: DashboardQueryState): string` omits default/empty values and emits stable URLSearchParams.
- Invalid enum/date/numeric values fall back to defaults and never throw.

- [ ] **Step 1: Write failing query-state tests**

Test default parsing, valid round trips, omitted defaults, invalid values, and copied-URL restoration through a dashboard route rendered with `MemoryRouter`.

- [ ] **Step 2: Run the focused tests and verify they fail**

Run: `npm test -- dashboardQueryState.test.ts DashboardRouting.test.tsx` from `web/`.

Expected: FAIL because Dashboard state is currently local-only.

- [ ] **Step 3: Implement pure parse/serialize helpers**

Use `URLSearchParams`; validate values against the existing `DashboardView`, `BasemapId`, risk-level, date, and magnitude constraints. Keep parsing independent of React.

- [ ] **Step 4: Connect dashboard controls to router search params**

Initialize state from `useSearchParams`, update search params on stable control changes, and preserve unrelated query values while changing one control. Avoid writing transient map selection or settings-panel state to the URL.

- [ ] **Step 5: Run focused tests and verify they pass**

Run: `npm test -- dashboardQueryState.test.ts DashboardRouting.test.tsx` from `web/`.

Expected: PASS, including copied-URL restoration.

- [ ] **Step 6: Commit**

```bash
git add web/src/pages/Dashboard.tsx web/src/lib/dashboardQueryState.ts web/src/components/dashboard/DashboardSidebar.tsx web/tests/dashboardQueryState.test.ts web/tests/DashboardRouting.test.tsx
git commit -m "feat: persist dashboard state in URLs"
```

### Task 7: Final Cleanup And Verification

**Files:**
- Modify: affected web files from Tasks 1-6 only
- Modify: `docs/superpowers/specs/2026-09-12-web-mvp-completion-design.md` only if implementation decisions require a documented correction

**Interfaces:**
- No new public API; this task verifies the completed web slice and removes only cleanup made necessary by the migration.

- [ ] **Step 1: Run the complete web test suite**

Run from `web/`: `npm test`.

Expected: all existing and new web tests pass.

- [ ] **Step 2: Run the production build**

Run from `web/`: `npm run build`.

Expected: TypeScript compilation and Vite build complete successfully.

- [ ] **Step 3: Run repository structure verification**

Run from the repository root: `python scripts\verify_structure.py`.

Expected: structure validation passes with the new web data and test files.

- [ ] **Step 4: Check the diff**

Run: `git diff --check` and `git status --short`.

Expected: no whitespace/conflict errors, no `web/dist/`, and only intended files are present.

- [ ] **Step 5: Commit verification and cleanup**

```bash
git add docs/superpowers/specs/2026-09-12-web-mvp-completion-design.md docs/superpowers/plans/2026-09-12-web-mvp-completion.md
git commit -m "docs: add web mvp implementation plan"
```

## Notes for the executor

- Tasks are sequential because routing affects page tests, page composition affects dashboard integration, and the risk overlay depends on the boundary asset.
- The boundary asset must be reviewed for license and region-name compatibility before it is committed. The checked-in FeatureCollection is simplified/quantized for browser delivery. If the upstream source does not provide the project’s canonical region names, normalize the asset property and maintain explicit province-to-region aliases in the overlay adapter; do not change the backend `RiskProfile` contract.
- The web test suite should not require a running backend, Postgres, Redis, or live MapLibre style/network access.
- Browser-level visual verification is useful after Task 5, but the required automated checks are the Vitest suite and TypeScript/Vite build.
- The existing `RiskProfileExplorer.tsx` is not automatically routed by this plan; either remove it only if confirmed unused after route migration or leave it untouched and record it as follow-up cleanup.
- Do not implement functional historical browsing in the Historical page.