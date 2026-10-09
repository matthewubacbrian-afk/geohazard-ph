# GeoHazard PH Web Interface Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh the GeoHazard PH web interface into a calm, accessible, map-centered geoscience instrument while preserving every existing data source, behavior, and honest state.

**Architecture:** Keep the existing React routes, component props, hooks, types, API clients, query-string state, and risk logic intact. Build the presentation in ordered layers: tokens and shared styles, shared navigation, dashboard shell and supporting panels, informational pages, then MapLibre-specific symbology and overlays. Finish with responsive screenshots, live-backend smoke checks, and a scoped diff review.

**Tech Stack:** React 18, TypeScript, Vite, CSS Modules, MapLibre GL, Vitest, Testing Library.

**Spec:** `docs/superpowers/specs/2026-10-09-web-interface-refresh-design.md`

---

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `REACT_BEST_PRACTICES.md`, `docs/glossary.md`, `docs/api-contracts.md`, `docs/testing-standards.md`, and the approved design spec.
- Change only `web/` and approved design documentation. Do not edit `backend/`, `ml/`, `mobile/`, `infra/`, API contracts, `web/src/api/client.ts`, any hook, any type, or `web/src/lib/risk.ts`.
- Preserve all existing props and data flow. Keep route paths, dashboard query parameters, event source selection, filters, websocket reconnect/reconciliation, retries, and map layer fetching unchanged.
- Keep honest empty, unavailable, loading, error, retry, stale-cache, and planned states. Never add fake numbers or imply that a risk profile is a prediction or official alert.
- Preserve USGS, PHIVOLCS, GVP, GEM, and Kaggle attribution, basemap provider attribution, static-layer provenance and coverage caveats, and the PHIVOLCS raster-reference disclaimer.
- Use CSS Modules and existing CSS variables. No Tailwind, new UI framework, dependency, icon emoji, fake Historical controls, or new tile source/vendor.
- Use CSS Modules and semantic tokens. Current proposal: pumice `#F3F0E9`, raised `#FAF8F3`, warm white `#FFFEFA`, ash container `#E8E4DA`, basalt `#292824`, secondary ash `#57554F`, faint text `#706E68`, border `#77736A`, hairline `#C9C4B8`, terracotta `#9B3F2E`, deep risk `#792D25`, ochre `#86600E`, mineral `#49655F`. Use the approved spec's system-serif heading stack, Inter UI and JetBrains Mono technical labels. Preserve tabular numerals.
- Validate WCAG AA contrast for text (4.5:1 normal, 3:1 large) and 3:1 for non-text indicators; use labels/shapes/patterns as well as color for risk.
- Honor `prefers-reduced-motion`; all controls remain keyboard-operable with visible focus. No horizontal overflow at desktop, tablet, or mobile widths.
- Follow TDD for behavior changes. For presentation-only changes, first inspect current user-visible behavior tests, keep them passing, and add/update assertions only when changed markup makes the accessible selector invalid while the interaction and copy remain the same. Test files live in `web/tests/` and follow `docs/testing-standards.md`.
- Each task ends with its listed verification and a small Conventional Commit. Do not claim visual, live-service, or test verification that was not actually performed.
- Required final verification: from `web/`, `npm test` and `npm run build`; from repository root, `python scripts/verify_structure.py` and `git diff --check`; before/after screenshots for each requested view at desktop and mobile; live-backend smoke checks; final `git diff` confirms scope.

## Current-State Summary

Epic 1 (earthquake feed/API/map) and Epic 2 (PHIVOLCS, realtime, deduplication) are implemented. Epic 3's code is implemented, but source coverage is partial: the GEM fault snapshot is locally verified, PHIVOLCS vector reuse clearance is unresolved, and national completeness is unclaimed. The web routes are Hero (`/`), Dashboard, About, Data Sources, and Historical. The Dashboard combines view/filter/layer controls, MapLibre map and summary, realtime status, event feed/detail, risk profiles, volcano bulletins, and static-layer status. Event data comes from `/events`; summary from `/events/summary`; profiles from `/risk-profile/clusters` and `/risk-profile/{region_name}`; static vectors from `/faults` and `/volcano-zones`; bulletins from `/volcanoes`; live updates from `/ws/events`. Historical remains a planned/unavailable page. Source-level wiring and exact field mappings are listed in the approved design spec and the checklist below.

## Design System and Component Change Summary

The tokens task refines the existing primitive/semantic structure. Maintain a 4px base and 8px rhythm, compact data density, a type hierarchy of system-serif headings / Inter UI / JetBrains Mono technical labels, tabular numerals, 4px controls / 8px compact cards / 12px larger panels, flat bordered surfaces with low-elevation overlays, visible focus, reduced motion, and the existing responsive breakpoints. No new font or UI dependency is planned. The values and contrast thresholds are listed under Global Constraints and in the approved design spec.

| Component | Before | After | Preserved behavior/source |
| --- | --- | --- | --- |
| TopNav | Shared themed nav and settings entry | Compact responsive field-station header | Route destinations, active item, settings callback |
| Hero | Large atmospheric header, process cards, project copy and sample meters | Restrained specific introduction and editorial layout | Existing nav/actions; any sample remains labeled illustrative |
| Dashboard shell | Sidebar / map area / activity panel | Responsive desktop three-column workspace, intentional tablet/mobile stacking | Query-string state, view/filter/layer data and callbacks |
| DashboardSidebar | Controls grouped in current sidebar sections | Clear view, basemap, layer, category, date and magnitude groups | Same props/labels, including disabled and unavailable-layer labels |
| DashboardMapArea | Map with floating summary and overlays | Dominant map with compact summary, legend and controls | Same summary hook, values and loading/error/Retry/empty states |
| MapView and overlays | Current markers, vector layers, raster references and legend | Refined scale, contrast, boundaries and source-aware legend | Same basemaps, source attribution, layer behavior and empty states |
| EventFeed/detail | Activity rows, filters and detail panel | Dense scan-friendly rows and legible detail surface | Same event fields, category controls, selection and retries |
| RiskProfilesPanel | Profile cards and region lookup | Compact profiles with explicit descriptive framing | Same profiles, fields, lookup and loading/error/empty states |
| VolcanoPanel | Bulletin cards and status copy | Clear alert and timestamp hierarchy | Same values, null handling, links, stale/error/loading states |
| About/DataSources | Existing informational pages | Consistent editorial measure and source provenance | Existing facts, attribution and links |
| Historical | Planned capability page | Honest, visually intentional unavailable state | No fake data or nonfunctional controls |

## Data-Integrity Checklist

| UI element | Data source and fields | UI owner | Rule to preserve |
| --- | --- | --- | --- |
| Event markers/feed/detail and event filters | `GET /events`; `HazardEvent`: `id`, `source`, `magnitude`, `depth_km`, `latitude`, `longitude`, `place_name`, `occurred_at`, `alert_level`, `is_primary` | `useEvents`, `Dashboard`, `DashboardMapArea`, `EventFeed`, `EventDetailPanel` | No invented values; preserve filters, selection and timestamps |
| Summary | `GET /events/summary`; `event_count`, `avg_magnitude`, `max_magnitude`, `latest_occurred_at`, optional `region_name` | `useEventSummary`, `DashboardMapArea` | Server values only; preserve null, loading, error, Retry and empty states |
| Realtime state | WebSocket `/ws/events`; `EventChange` fields and socket connectivity | `useRealtimeAlerts`, `RealtimeStatus` | Preserve reconnect/reconcile; LIVE indicates transport only |
| Fault/vector layer | `GET /faults`; `StaticLayer` geometry and source/version/license | `useStaticLayers`, `StaticLayerStatus`, `MapView` | Preserve provenance and explicit empty/error state; no coverage claim |
| Volcano-zone/vector layer | `GET /volcano-zones`; `StaticLayer` geometry and source/version/license | `useStaticLayers`, `StaticLayerStatus`, `MapView` | Preserve provenance and explicit empty/error state; no coverage claim |
| PHIVOLCS reference overlay | Existing PHIVOLCS MapServer raster exports and attribution | `volcanoOverlays`, `MapView`, overlay status | Raster reference only; not local polygons or live alert levels |
| Volcano bulletins | `GET /volcanoes`; alert level, source/bulletin URLs, bulletin/retrieval timestamps, `stale` | `useVolcanoes`, `VolcanoPanel` | Keep alert level zero distinct from null, source link and stale status |
| Risk profiles/lookup | `GET /risk-profile/clusters`; profile label, region, confidence, feature importances, version and snapshots; `GET /risk-profile/{region_name}` | `useRiskProfiles`, `RiskProfilesPanel`, `RegionLookup`, `RiskProfileCard` | Preserve real values; descriptive statistical profile, not prediction |
| Attribution | Existing source text/URLs for USGS, PHIVOLCS, GVP, GEM, Kaggle | DataSources, About, map/status/bulletin UI | Keep names and provenance; no implied endorsement |
| Historical | No implemented historical query endpoint | `HistoricalBrowser` | Keep planned/unavailable status; no fake controls/data |

## Risks and Open Questions

- **Fonts:** Verify Inter and JetBrains Mono are currently loaded with appropriate fallbacks. The heading stack uses system serif faces, so no new license/dependency is planned. If current font delivery requires a new external font, stop and revise the plan before adding it.
- **Basemaps:** Keep current OpenFreeMap/Esri providers and attribution. Tile terms, availability and future style/vendor changes are outside this task.
- **Dark mode:** Not included. Decide separately after the light palette passes contrast and map QA.
- **PHIVOLCS TLS/source availability:** Bulletin smoke checks can fail due to the existing external source/TLS caveat. Record the observed state; do not change backend or TLS behavior here.
- **Map contrast:** One marker/line/fill palette may not work over all four current basemaps. Validate per style and use outlines, backing surfaces and labels rather than changing providers.
- **Screenshots/backend:** A live backend and available source data are needed for realistic data screenshots. If unavailable, capture honest loading/empty/error states and report the unmet live prerequisite rather than substituting mock values.
## File Map

- `web/src/styles/tokens.css`: primitive and semantic color, typography, spacing, radius, elevation, breakpoint, and motion variables.
- `web/src/styles/base.css`, `web/src/styles/utilities.css`: global font application, base elements, visible focus, accessible utilities, and reduced-motion defaults.
- `web/src/components/layout/TopNav.tsx`, `TopNav.module.css`: shared app navigation presentation; retain callbacks and active item behavior.
- `web/src/pages/Dashboard.tsx`, `Dashboard.module.css`: current three-region dashboard composition only; preserve all state and callbacks.
- `web/src/components/dashboard/DashboardSidebar.tsx` and CSS: view, basemap, layer, category, date, and magnitude controls.
- `web/src/components/dashboard/DashboardMapArea.tsx` and CSS: MapView host, summary card, legend and map controls.
- `web/src/components/dashboard/RealtimeStatus.tsx` and CSS: transport state presentation.
- `web/src/components/events/EventFeed.tsx`, `EventFeedItem.tsx`, `EventDetailPanel.tsx` and their CSS Modules: event list, selection, and event detail presentation.
- `web/src/components/map/MapView.tsx`, `MapView.module.css`, `EventMarker.tsx`, `StaticLayerStatus.tsx`, `VolcanoOverlayStatus.tsx`, `volcanoOverlays.ts`: map-only visuals and overlay labels. Preserve `basemaps.ts` providers and attribution.
- `web/src/components/risk/RiskProfilesPanel.tsx`, `RegionLookup.tsx`, `RiskProfileCard.tsx` and CSS Modules: searchable descriptive profile presentation.
- `web/src/components/volcanoes/VolcanoPanel.tsx` and CSS: bulletin presentation.
- `web/src/pages/Hero.tsx`, `Hero.module.css`, `About.tsx`, `DataSources.tsx`, `HistoricalBrowser.tsx`, `InformationalPage.module.css`: informational route presentation and plain-language content.
- `web/DESIGN_NOTES.md`: refreshed design decisions after implementation. `web/WEB_STRUCTURE.md` only if its documented layout becomes inaccurate.
- Tests to inspect/update only as required: `web/tests/App.test.tsx`, `DashboardCard.test.tsx`, `DashboardSidebar.test.tsx`, `DashboardStates.test.tsx`, `DashboardSummary.test.tsx`, `EventFeed.test.tsx`, `EventListLive.test.tsx`, `EventSelection.test.tsx`, `InformationalPages.test.tsx`, `MapView.test.tsx`, `RiskProfile.test.tsx`, `StaticLayerStatus.test.tsx`, `VolcanoPanel.test.tsx`.

---

### Task 1: Establish the shared design tokens

**Files:**
- Modify: `web/src/styles/tokens.css`
- Modify: `web/src/styles/base.css`
- Modify: `web/src/styles/utilities.css`
- Test/inspect: existing `web/tests/App.test.tsx`, `web/tests/InformationalPages.test.tsx`

- [ ] **Step 1: Capture the existing visual baseline** for Hero, Dashboard, About, Data Sources, Historical at 1440px desktop and 390px mobile. Save screenshots outside tracked build output and note current light-theme behavior.
- [ ] **Step 2: Inspect existing styles and tests** for hard-coded colors, font loading, focus styles, reduced-motion styles, and selectors that assert visible text or accessible roles. No component changes in this task.
- [ ] **Step 3: Replace primitive and semantic tokens** with the approved spec palette while keeping existing variable names where components consume them. Add `--mineral` and a distinct `--risk-moderate` only if the existing four risk tokens cannot represent four ordered labels. Use exact initial values: `--cream-0: #F3F0E9`, `--cream-50: #FAF8F3`, `--cream-100: #FFFEFA`, `--cream-150: #E8E4DA`, `--ink: #292824`, `--ink-soft: #57554F`, `--ink-faint: #706E68`, `--outline: #77736A`, `--outline-variant: #C9C4B8`, `--accent: #9B3F2E`, `--risk-very-high: #792D25`, `--risk-medium: #86600E`, `--risk-low: #49655F`. Set the heading family to `"Iowan Old Style", "Palatino Linotype", "Book Antiqua", Georgia, serif`; retain Inter and JetBrains Mono stacks and current type/spacing/radius/motion scales, adjusting only where the spec requires.
- [ ] **Step 4: Add a separate token for semantic focus and overlay contrast if necessary**, then use it in existing global `:focus-visible` rules. Keep reduced-motion overrides and map z-index tokens intact.
- [ ] **Step 5: Check contrast for the exact proposed foreground/surface and risk swatches** with a reproducible contrast calculation and record results in the plan execution notes. Adjust token values until AA/3:1 thresholds pass; never compensate by removing text or labels.
- [ ] **Step 6: Run focused existing web checks** with `cd web; npm test -- tests/App.test.tsx tests/InformationalPages.test.tsx`, then `npm run build`. Expected: existing assertions pass and the app compiles with no missing token references.
- [ ] **Step 7: Review token diff and commit** `style: refresh web design tokens`.

### Task 2: Restyle shared navigation and common controls

**Files:**
- Modify: `web/src/components/layout/TopNav.tsx`, `TopNav.module.css`
- Modify: scoped styles in `web/src/components/common/SectionHeader.module.css`, `RiskMeter.module.css`, `Skeleton.module.css`, `SettingsPanel.module.css`, `ComingSoon.module.css` (only those found to be used on included routes)
- Test: `web/tests/App.test.tsx`, `web/tests/SettingsPanel.test.tsx`

- [ ] **Step 1: Inspect existing assertions and route callback behavior** for active navigation, page links, settings open/close, and keyboard access. Keep route labels and accessible names stable.
- [ ] **Step 2: Define before changing markup any required accessible behavior** for narrow navigation: all existing destinations remain reachable, active route stays discernible, settings remains operable, and focus is visible. Prefer CSS reflow over new menu state.
- [ ] **Step 3: Restyle `TopNav`** as a compact field-station header with pumice surface, subtle edge, clear active route, legible brand, responsive wrapping/stacking, and no icon-only unlabeled control. Retain `items`, `activeItem`, `theme`, `onNavigate`, and `onSettings` behavior.
- [ ] **Step 4: Align common section headers, meters, skeletons, settings and unavailable affordances** to the token system. Keep sample meter wording explicit; do not reuse sample values as live data. Avoid adding decorative orbs, gradients, or identical card treatments.
- [ ] **Step 5: Run `cd web; npm test -- tests/App.test.tsx tests/SettingsPanel.test.tsx` and `npm run build`.** Expected: navigation/settings tests pass; no new horizontal overflow is visible at mobile width.
- [ ] **Step 6: Commit** `style: refine shared navigation and controls`.

### Task 3: Recompose the dashboard shell and sidebar responsively

**Files:**
- Modify: `web/src/pages/Dashboard.module.css`
- Modify: `web/src/components/dashboard/DashboardSidebar.module.css`
- Modify: `web/src/components/dashboard/DashboardSidebar.tsx` only if semantic markup needs adjustment; no prop/data-flow changes.
- Test: `web/tests/DashboardSidebar.test.tsx`, `web/tests/DashboardStates.test.tsx`, `web/tests/App.test.tsx`

- [ ] **Step 1: Preserve the baseline behavior in tests**: Map, Filters, Historical data, Risk, Volcanoes views; all basemap choices; event, risk, fault and volcano layer controls; event category filters; date range; magnitude slider; URL query restoration. Update only selectors invalidated by semantic markup, keeping visible text and state assertions.
- [ ] **Step 2: Define responsive layout breakpoints** using existing `--bp-md: 900px` and `--bp-sm: 640px`: desktop sidebar / map / activity columns; tablet a dominant map with sidebar/activity panels below or in a clear stacked sequence; mobile single-column with controls and activity reachable without horizontal scrolling. Do not hide controls or data.
- [ ] **Step 3: Restyle the desktop dashboard grid** with explicit min-width/overflow handling, aligned outer padding, map-led proportions, and a restrained surface hierarchy. No data state or React state changes.
- [ ] **Step 4: Restyle sidebar sections** so selected view, selected basemap, active layers, disabled availability tags, event category states, date fields and magnitude range read clearly. Keep all labels including explicit empty-layer labels.
- [ ] **Step 5: Implement mobile/tablet reflow** and verify controls remain keyboard operable, labels do not clip, date inputs remain usable, and no page-level horizontal scroll occurs.
- [ ] **Step 6: Run `cd web; npm test -- tests/DashboardSidebar.test.tsx tests/DashboardStates.test.tsx tests/App.test.tsx` and `npm run build`.** Expected: current view/query/filter behavior is unchanged and responsive CSS compiles.
- [ ] **Step 7: Commit** `style: make dashboard shell responsive`.

### Task 4: Restyle dashboard summary, realtime status, feed and detail

**Files:**
- Modify: `web/src/components/dashboard/DashboardMapArea.module.css`
- Modify: `web/src/components/dashboard/RealtimeStatus.module.css`
- Modify: `web/src/components/events/EventFeed.tsx`, `EventFeed.module.css`, `EventFeedItem.module.css`, `EventDetailPanel.module.css` (JSX only for necessary semantic/accessibility markup)
- Test: `web/tests/DashboardCard.test.tsx`, `DashboardSummary.test.tsx`, `DashboardStates.test.tsx`, `EventFeed.test.tsx`, `EventListLive.test.tsx`, `EventSelection.test.tsx`

- [ ] **Step 1: Confirm tests cover summary loading, populated values, unavailable/null fields, error and Retry; event feed loading/error/retry/empty, source labels, category selection, event selection/details; and realtime connected/disconnected semantics. Add a failing behavior assertion first only for any uncovered interaction that markup work could break.**
- [ ] **Step 2: Restyle summary** as a compact map-supporting instrument panel. Continue rendering values exclusively from `useEventSummary` fields `event_count`, `avg_magnitude`, `max_magnitude`, `latest_occurred_at`; retain `DashboardMapArea` loading, error, Retry, and no-summary content. Do not add defaults that display fake metrics.
- [ ] **Step 3: Restyle realtime status** with labeled LIVE/disconnected state and accessible status semantics. Preserve the hook as connectivity-only and do not imply ingest health or an official alert.
- [ ] **Step 4: Restyle event feed rows and filter pills** for compact scanability, tabular magnitude/time, source clarity, visible selection, hover/focus/pressed states, and responsive overflow behavior. Keep categories and event totals derived from existing filtered rows.
- [ ] **Step 5: Restyle event detail** with readable definition list, source, coordinates, timestamps, units, and keyboard-accessible close action; render optional magnitude/depth only when present.
- [ ] **Step 6: Run `cd web; npm test -- tests/DashboardCard.test.tsx tests/DashboardSummary.test.tsx tests/DashboardStates.test.tsx tests/EventFeed.test.tsx tests/EventListLive.test.tsx tests/EventSelection.test.tsx` and `npm run build`.** Expected: all current data/state and selection assertions pass.
- [ ] **Step 7: Commit** `style: refine dashboard activity panels`.

### Task 5: Restyle risk and volcano panels without changing their meaning

**Files:**
- Modify: `web/src/components/risk/RiskProfilesPanel.module.css`, `RiskProfileCard.module.css`, `RegionLookup.module.css`
- Modify: `web/src/components/volcanoes/VolcanoPanel.module.css`
- Modify JSX in those components only if an existing role/label needs preservation or improvement; no hooks or types.
- Test: `web/tests/RiskProfile.test.tsx`, `web/tests/VolcanoPanel.test.tsx`

- [ ] **Step 1: Inspect risk tests and current fields**: region name, label, confidence, feature importances, model version, generated time and dataset snapshot; lookup behavior; loading/error/retry/empty. Verify exact phrase "descriptive, not a prediction" remains visible (add a failing assertion if absent).
- [ ] **Step 2: Restyle lookup and risk cards** as compact, readable profiles. Show label text and non-color marker/shape, keep tabular numerical values, do not present raw cluster index as severity, forecast or official warning.
- [ ] **Step 3: Inspect volcano tests** for alert level `0`, missing alert level, source URL, bulletin URL, bulletin time, retrieval time, stale cache, error/Retry, empty and loading.
- [ ] **Step 4: Restyle volcano bulletins** with alert level and timestamp grouping; maintain `Alert level not supplied`, valid `Alert Level 0`, stale-cache wording, source link, and all empty/error states.
- [ ] **Step 5: Run `cd web; npm test -- tests/RiskProfile.test.tsx tests/VolcanoPanel.test.tsx` and `npm run build`.** Expected: unchanged profile/bulletin values and source states.
- [ ] **Step 6: Commit** `style: refine risk and volcano panels`.

### Task 6: Restyle Hero and informational routes

**Files:**
- Modify: `web/src/pages/Hero.tsx`, `Hero.module.css`
- Modify: `web/src/pages/InformationalPage.module.css`, `About.tsx`, `DataSources.tsx`, `HistoricalBrowser.tsx` only where styling/accessible structure requires.
- Modify: `web/DESIGN_NOTES.md`; modify `web/WEB_STRUCTURE.md` only if documentation is inaccurate after CSS/layout changes.
- Test: `web/tests/InformationalPages.test.tsx`, `web/tests/App.test.tsx`

- [ ] **Step 1: Capture/inspect assertions** for Hero copy and navigation, About and Data Sources route content, all attribution names and links, and Historical planned/unavailable copy. Keep all current tested text unless a specific prediction/accuracy statement is factually misleading; if copy must change, preserve behavior and update only the corresponding copy assertion with a clear reason.
- [ ] **Step 2: Restyle Hero** with a calm pumice/ash field, no gradient-heavy effect or decorative blobs, concise typographic hierarchy and existing navigation actions. Remove/replace only unsupported prediction or model-accuracy claims with specific, truthful descriptions; do not add new statistics. If sample meters remain, label them explicitly as illustrative and non-live.
- [ ] **Step 3: Restyle About and Data Sources** with a constrained editorial measure, clear section headings, source provenance and links, and responsive spacing; retain USGS, PHIVOLCS, GVP, GEM and Kaggle attribution.
- [ ] **Step 4: Restyle Historical** to present its current planned/unavailable status intentionally. Keep no fake search controls and no claim that historical queries are implemented.
- [ ] **Step 5: Update `web/DESIGN_NOTES.md`** with final tokens, typography, spacing, responsive rules, contrast checks, icon treatment and motion. Update `WEB_STRUCTURE.md` only where its page/layout descriptions become inaccurate.
- [ ] **Step 6: Run `cd web; npm test -- tests/InformationalPages.test.tsx tests/App.test.tsx` and `npm run build`.** Expected: route navigation and source attribution assertions pass.
- [ ] **Step 7: Commit** `style: refresh informational pages`.

### Task 7: Apply MapLibre palette and legend styling

**Files:**
- Modify: `web/src/components/map/MapView.tsx`, `MapView.module.css`, `EventMarker.tsx`, `StaticLayerStatus.module.css`, `VolcanoOverlayStatus.module.css`, `volcanoOverlays.ts` only for presentation/labels.
- Modify: `web/src/components/dashboard/DashboardMapArea.module.css` for map controls/legend.
- Do not modify: `web/src/components/map/basemaps.ts` provider URLs/attribution or `riskOverlay.ts` risk computation/geometry behavior.
- Test: `web/tests/MapView.test.tsx`, `web/tests/StaticLayerStatus.test.tsx`, `web/tests/basemaps.test.ts`, `web/tests/riskOverlay.test.ts`

- [ ] **Step 1: Inspect map tests and current MapLibre layer IDs/paint expressions.** Record existing event visibility, selected event behavior, map style swap behavior, static-layer fetch/empty state, raster-overlay attribution, and basemap attribution. Add a focused failing assertion before any required markup/behavior adjustment.
- [ ] **Step 2: Restyle built-in map controls, status badges and legend backing** using pumice surfaces, semantic borders, legible text, visible focus and reduced-motion-compatible feedback. Maintain legibility on streets, satellite, hybrid and terrain.
- [ ] **Step 3: Set marker scale by existing magnitude only** with a restrained bounded size range and a clear non-color cue (outline/shape). Use the existing data and risk bucket classification; do not introduce event values or change `lib/risk.ts`. If current marker size is static, introduce a visual-only MapLibre paint expression based on the existing `magnitude` property and document its bounded stops in the legend.
- [ ] **Step 4: Style fault lines and local volcano-zone polygons** with distinct terracotta line / muted ochre fill and boundaries that remain visible over all current basemaps. Use a casing or outline where needed; preserve existing layer IDs and click/visibility behavior.
- [ ] **Step 5: Distinguish PHIVOLCS raster reference overlays from local vector zones** in the legend and status. Keep existing attribution and the explicit note that remote reference imagery is not an alert level or imported vector data. Preserve all explicit empty/error/retry labels.
- [ ] **Step 6: Verify color and minimum size contrast** on all four existing basemaps and at desktop/mobile screen sizes. Keep risk labels and symbols so the map does not encode meaning by hue alone.
- [ ] **Step 7: Run `cd web; npm test -- tests/MapView.test.tsx tests/StaticLayerStatus.test.tsx tests/basemaps.test.ts tests/riskOverlay.test.ts` and `npm run build`.** Expected: map behavior, attribution, basemaps, and data geometry assertions pass.
- [ ] **Step 8: Commit** `style: refine map hazard symbology`.

### Task 8: Full visual, responsive, and data-integrity verification

**Files:**
- Inspect/update only tests and documentation within the approved web-only scope.
- No changes to protected files.

- [ ] **Step 1: Run the full web suite** from `web/`: `npm test`. Expected: Vitest exits successfully with all assertions passing.
- [ ] **Step 2: Run production build** from `web/`: `npm run build`. Expected: TypeScript and Vite build complete successfully.
- [ ] **Step 3: Run structure and whitespace checks** from repository root: `python scripts/verify_structure.py` and `git diff --check`. Expected: structure verifier exits successfully; no whitespace errors.
- [ ] **Step 4: Capture after screenshots** at 1440px desktop and 390px mobile for Hero, Dashboard Map/feed, Dashboard risk panel, Dashboard volcano bulletins, About, Data Sources, and Historical. Compare with Task 1 baseline; inspect a tablet width; record any unavailable backend state honestly. Confirm no horizontal scroll, clipping, inaccessible action, low-contrast text, or map legend obscuring controls.
- [ ] **Step 5: Run live-backend smoke checks** with a reachable configured API: map events load; source/date/magnitude filters still change displayed events; summary uses server values; stop API and verify error plus Retry then restart; volcano bulletins show alert levels, source links and stale state when available; toggle faults and volcano zones and observe imported/empty labels; region lookup and risk meter use actual profile data; realtime connects at `/ws/events` and reconnects/refetches after disconnect. Record any unavailable prerequisite and do not mark that scenario passed.
- [ ] **Step 6: Verify source mappings** against `docs/api-contracts.md` and actual UI: `/events`, `/events/summary`, `/risk-profile/clusters`, `/risk-profile/{region_name}`, `/faults`, `/volcano-zones`, `/volcanoes`, `/ws/events`; verify every visible field is backed by a response field or existing static explanatory copy.
- [ ] **Step 7: Inspect `git diff --stat`, `git status --short`, and the complete diff.** Expected: only `web/` and the approved design docs are changed; no API client, hook, types, risk logic, backend/ML/mobile/infra files, secrets, build output, local caches, or large raw datasets.
- [ ] **Step 8: Commit any verification-driven corrections** separately with an appropriate Conventional Commit, rerun the affected package verification and repeat the relevant screenshot/smoke check.

---

## Notes for the executor

- The dashboard summary lives in `DashboardMapArea`; it is not a separate `DashboardSummary` source component.
- The Historical route is a planned/unavailable information page and must remain so.
- Epic 3 code is implemented but source coverage remains partial. Do not imply national completeness or PHIVOLCS vector clearance. Current PHIVOLCS raster map overlays are reference imagery, not local polygons and not live alert levels.
- Current PHIVOLCS bulletin fetch has a trusted-TLS/source-availability caveat documented in `docs/project-status.md` and `docs/runbook.md`. A smoke failure may reflect that external condition; record what was observed and do not modify backend TLS behavior in this web redesign.
- Basemaps currently use OpenFreeMap streets and Esri satellite/hybrid/terrain layers. Keep current vendor configuration and attribution; this plan does not settle future tile terms or dark mode.
- Fonts: the plan adds no font package. Verify the existing Inter/JetBrains Mono loading path and system-serif heading fallback before implementation; change font delivery only if separately approved and license/performance impact is understood.
- Task order is intentional: token foundation → shared components → dashboard shell → data panels → informational pages → MapLibre styling → final verification. Each task produces a testable visual increment and has a Conventional Commit.


