# GeoHazard PH Web Interface Refresh — Design

**Date:** 2026-10-09

## Problem

The current web experience contains a live hazard dashboard and several informational pages, but its established warm-cream/red visual language and component layouts do not fully express the requested calm, field-station feel. The dashboard must remain a working geoscience instrument: event data, source filters, URL state, realtime updates, summary states, volcano bulletins, static-layer availability, and descriptive regional profiles must retain their existing behavior and source attribution throughout a presentation-only redesign.

## Goals

- Establish a restrained, accessible design system with basalt/ash neutrals, pumice surfaces, terracotta, ochre, and a cool mineral accent.
- Clarify hierarchy across Hero, Dashboard, About, Data Sources, and Historical pages, with the map as the dashboard's primary surface and supporting panels at appropriate density.
- Restyle map controls, event markers, fault and volcano-zone layers, overlays, and legend without changing the current basemap/data behavior.
- Preserve all existing copy and accessible names asserted by tests, all data states, attribution, and component props/data flow unless a narrowly justified markup-only change is needed.
- Keep the stack unchanged: React, Vite, TypeScript, CSS Modules, and MapLibre GL; add no framework and no dependency unless specifically justified.

## Non-goals

- No changes to `backend/`, `ml/`, `mobile/`, `infra/`, API contracts, event/risk logic, endpoint behavior, hooks, `types/`, `web/src/api/client.ts`, or `web/src/lib/risk.ts`.
- No new user-facing feature, made-up metric, prediction claim, data source, or static hazard coverage claim.
- No change to source selection, URL query synchronization, filters, retry behavior, realtime reconnection, risk calculations, or map-layer fetching.
- No new UI framework, Tailwind, gradient-heavy hero, glassmorphism, glowing shadows, emoji icons, decorative blobs, or filler statistics.
- Dark mode is not included in the initial redesign; revisit only if implementation scope and contrast validation support it without risking the light theme.

## Context And Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `REACT_BEST_PRACTICES.md`, `docs/glossary.md`, `docs/api-contracts.md`, and `docs/testing-standards.md` when implementing. Use CSS Modules and shared variables from `web/src/styles/tokens.css`.
- `web/DESIGN_NOTES.md` and `web/WEB_STRUCTURE.md` document the earlier Aug 31 visual system and layout. The current code has since gained React Router routes, a dashboard summary state, realtime status, volcano bulletin content, static layer status, and coverage caveats; implementation should follow current code and `docs/project-status.md`, not treat historical plans as current backlog.
- Current product state: Epics 1 and 2 are implemented; Epic 3 code exists, but coverage is partial. A GEM fault snapshot is locally verified; PHIVOLCS vector reuse clearance and national completeness are unresolved. PHIVOLCS rendered raster overlays are not local vector coverage. Risk profiles remain descriptive statistical profiles, not predictions.
- Routes: Hero `/`, Dashboard `/dashboard`, About `/about`, Data Sources `/data-sources`, Historical `/historical`. Historical is explicitly unavailable/planned and must remain honest.
- Keep current API, data hooks, types, query/URL state, props, and data flow stable. Existing tests assert visible copy and interaction behavior; inspect them before markup edits and update only when semantics/behavior are preserved.

## Alternatives Considered

1. **Shared tokens followed by focused component/page passes (chosen).** Establish semantic palette, typography, spacing, and surfaces first, then restyle navigation/shared controls, dashboard shell, supporting panels, informational pages, and map. This yields coherent visual rules while keeping changes reviewable and data wiring stable.
2. **Dashboard-first, then shared styles and other pages.** Could deliver the central map experience sooner, but creates temporary divergence and encourages duplicated values before shared tokens settle.
3. **Full visual-system replacement plus dark mode.** Could make the broader theme change more dramatic, but expands scope, raises accessibility/verification risk, and is not necessary to achieve the brief.

## Design

### Architecture and data flow

The refresh is CSS and markup presentation work around the existing components and hooks. Preserve the current data path and responsibilities:

- `Dashboard` owns the selected source, date/magnitude filters, basemap, active dashboard view/layers/categories, selected event, and query-string synchronization.
- `DashboardMapArea` renders the MapView and map overlays and uses `useEventSummary` for its summary card.
- `EventFeed` and `EventDetailPanel` display the selected event list and event fields; `RealtimeStatus` reflects `useRealtimeAlerts` transport state.
- `DashboardSidebar` continues to control views, filters, event categories, and static-layer toggles.
- `RiskProfilesPanel`, `RegionLookup`, and `RiskProfileCard` retain `useRiskProfiles` and region lookup behavior; wording continues to describe statistical profiles and not predictions.
- `VolcanoPanel` retains `useVolcanoes`, alert-level null handling, source links, observation/retrieval timestamps, and stale-cache status.
- `StaticLayerStatus`, `VolcanoOverlayStatus`, and `MapView` retain current feature/empty states, retries, source/license/version provenance, remote overlay caveats, and attribution.
- About, Data Sources, and Historical remain informational routes; preserve honest "Not available"/planned labels.

No endpoint or API client changes are proposed. Existing sources are `GET /events`, `GET /events/summary`, `GET /risk-profile/clusters`, `GET /risk-profile/{region_name}`, `GET /faults`, `GET /volcano-zones`, `GET /volcanoes`, and WebSocket `/ws/events`.

### Proposed design tokens

Retain the existing primitive/semantic layering in `web/src/styles/tokens.css`; replace or revise values only through tokens. These values are a starting design decision to validate for contrast and map legibility during implementation.

| Role | Proposed token/value |
| --- | --- |
| Basalt text | `--ink: #292824` |
| Secondary ash text | `--ink-soft: #57554F` |
| Faint text | `--ink-faint: #706E68` |
| Pumice app background | `--cream-0: #F3F0E9` |
| Raised surface | `--cream-50: #FAF8F3` |
| Warm white card | `--cream-100: #FFFEFA` |
| Ash container | `--cream-150: #E8E4DA` |
| Border | `--outline: #77736A` |
| Hairline | `--outline-variant: #C9C4B8` |
| Terracotta primary action | `--accent: #9B3F2E` |
| Deep risk accent | `--risk-very-high: #792D25` |
| Ochre secondary | `--risk-medium: #86600E` |
| Mineral slate/cool balance | `--mineral: #49655F` |
| Low risk | `--risk-low: #49655F` |
| Elevation | Keep ink-tinted low-opacity shadow tokens; use borders and flat surfaces as the default.

Use an explicit muted risk scale (Low, Moderate, High, Very High) with adjacent luminance/shape differences; always show text labels and retain existing event risk names where they are user-visible. Do not rely on hue alone. Validate text contrast to WCAG AA (4.5:1 normal text, 3:1 large text) and non-text/map controls to 3:1 against adjacent colors. If the initial values miss, adjust the tokens and record final values in the implementation plan/results.

- **Type:** use a restrained system serif heading stack (`Iowan Old Style`, `Palatino Linotype`, `Book Antiqua`, `Georgia`, serif) with the existing Inter UI face and JetBrains Mono technical labels. Use tabular numerals for magnitude/count/time-series figures. This avoids adding a font dependency; verify the current UI/data fonts' local or bundled availability and fallbacks during implementation.
- **Spacing:** retain a 4 px base / 8 px rhythm, with compact data spacing and more generous landing-page spacing.
- **Radius:** controls 4 px; compact cards 8 px; larger page/panel surfaces 12 px; avoid applying one radius/padding pattern to every surface.
- **Elevation:** subtle warm borders and flat surfaces; low elevation only where overlays need separation.
- **Motion:** purposeful feedback only; honor `prefers-reduced-motion` and keep existing map navigation and loading behavior.

### Affected component before/after

| Area | Current | Proposed | Data/behavior retained |
| --- | --- | --- | --- |
| Shared tokens/base/utilities | Warm cream, red, Inter/JetBrains Mono; extensive existing scales | Refined semantic palette, clear type hierarchy, tokenized focus/spacing/surface rules | CSS variable consumers and reduced-motion behavior |
| TopNav | Shared nav with page themes and settings entry | Clear compact field-station header, visible active route, responsive navigation and focus states | Same `items`, active item, route navigation and settings callback |
| Hero | Large atmospheric hero, methodology, project copy, sample meters | Specific plain-language introduction, restrained visual field, clearer calls to action and relaxed editorial sections | Existing navigation and text/test assertions; any sample display must remain clearly illustrative |
| Dashboard shell | Sidebar + map area + activity panel | Responsive three-column desktop workspace; at narrower widths controls/panels stack or become usable compact sections without horizontal scroll | Same dashboard view/filter/layer state and URL synchronization |
| DashboardSidebar | View controls, basemap, layers, event categories, date and magnitude filters | Grouped compact controls with clear selected/disabled states and responsive behavior | Same controls/props and explicit unavailable-layer labels |
| DashboardMapArea | Map, summary, map controls/overlays | Map receives strongest area; summary and controls align with instrument hierarchy | `useEventSummary`, `events`, `isLoading`, error and retry; all summary values remain source-backed |
| MapView/overlays/legend | MapLibre basemaps, event markers, static vectors and PHIVOLCS raster overlays | Refined contrast and symbol hierarchy; labels and legend clarify layer meaning and source limitations | Same MapLibre sources, basemaps, features, attribution and empty-layer messaging |
| EventFeed/detail | Live activity list and detail surface | Compact scan-friendly rows, stable selected/focus states, tabular magnitude/time | Same filtered events, source, timestamps, coordinates, selection and retry |
| RiskProfilesPanel/lookup/cards | Region search and descriptive cluster cards | Compact searchable panel with clear descriptive framing and non-color risk labels | Same hook, lookup inputs, profile fields, loading/error/empty states |
| VolcanoPanel | PHIVOLCS bulletin list and state labels | Readable alert hierarchy and source/timestamp grouping | Same null alert level, links, stale status, retrieval and observation values |
| About/DataSources | Informational page layouts | Consistent editorial layout, clear source/provenance details | Same USGS, PHIVOLCS, GVP, GEM, Kaggle attributions and copy assertions |
| Historical | Planned/unavailable information page | Clear, intentional unavailable page consistent with refresh | No fake controls, data, or claim of implemented functionality |

### Per-view implementation intent

- **TopNav:** preserve active-item meaning, settings action, and current route map. At mobile widths provide a keyboard-operable compact layout, retaining visible destinations and focus.
- **Hero:** establish the product as a current hazard observation/reference tool; remove prediction-sounding marketing wording where it conflicts with project truth. Retain methodology content but avoid vague accuracy claims. If sample risk meters remain, label them unmistakably as samples and ensure they cannot be confused with live data; otherwise use a text-only explanatory representation without changing data behavior.
- **Dashboard:** desktop uses sidebar / dominant map / activity panel, with aligned edges and practical minimum widths. Tablet/mobile collapse to a deliberate vertical/compact arrangement with reachable controls and no horizontal scrolling. Do not remove dashboard features to achieve fit.
- **DashboardSidebar:** distinct sections for view, basemap, active layers, event categories and date/magnitude filters. Keep disabled labels such as "Soon" and explicit empty-layer labels where currently present.
- **DashboardMapArea:** preserve summary loading, error and Retry states, no-data state, map legend, realtime/status overlays, and report action. Summary card never uses placeholder numbers.
- **MapView and legend:** retain all basemap choices and attribution. Keep event markers discernible at map scales; style their size by existing magnitude data when currently supported, and keep a non-color cue (outline/shape) and magnitude label/legend. Fault vectors remain lines; volcano-zone vectors remain shaded polygons; PHIVOLCS rendered overlays remain explicitly raster reference layers and never imply current alert levels. Empty/failed layer status remains explicit.
- **EventFeed/detail:** retain REST list, selected event details, category filters and retry/loading/empty messages; style for dense scanning and keyboard selection.
- **Risk panel:** retain region lookup, profile cards, meter and current fields; display "descriptive, not a prediction" framing prominently and avoid turning a cluster into an official hazard warning.
- **Volcano view:** retain alert levels including valid zero and missing-level text, PHIVOLCS link, stale-cache notice, bulletin observation date, retrieval time, and unavailable/error states.
- **About/Data Sources:** use a relaxed text measure and source-specific provenance; keep USGS, PHIVOLCS, GVP, GEM and Kaggle attribution.

### MapLibre styling

- Keep current selectable basemaps (Streets, Satellite, Hybrid, Terrain) and their provider attribution; do not silently change tile vendors, URLs, or terms in a presentation pass.
- Use warm light map controls and a subtle opaque/near-opaque pumice backing for legends/overlays; preserve readable labels over satellite/terrain.
- Event marker size should map monotonically to magnitude with bounded, restrained steps and clear legend labels. Use terracotta for stronger event emphasis and mineral/ochre distinctions only where they encode risk; preserve a visible outline so markers remain legible over both bright and dark tiles.
- Fault lines use a muted terracotta stroke with contrast outline where required; volcano-zone polygons use translucent muted ochre fill plus defined boundary. Rendered PHIVOLCS hazard references retain their own layer distinctions and source attribution.
- Legend labels distinguish event risk buckets, magnitude scaling, fault lines, local volcano zones, and PHIVOLCS raster reference overlays. Provide text/symbol distinction so information is not color-only. Confirm colors and minimum marker sizes against each existing basemap during visual review.

### Data-integrity checklist

| UI element | Source and fields | Existing source path | Integrity rule |
| --- | --- | --- | --- |
| Event markers, event list, filters, detail panel | `/events`; `HazardEvent` fields `id`, `source`, `magnitude`, `depth_km`, `latitude`, `longitude`, `place_name`, `occurred_at`, `alert_level`, `is_primary` | `useEvents` → `fetchEvents`; `Dashboard`, `DashboardMapArea`, `EventFeed`, `EventDetailPanel` | No invented events/values; keep source/date/magnitude filters and selected event behavior |
| Event summary | `/events/summary`; `event_count`, `avg_magnitude`, `max_magnitude`, `latest_occurred_at`, optional `region_name` | `useEventSummary` → `DashboardMapArea` | Preserve loading/error/retry/empty states; nulls remain missing; never fabricate a count or magnitude |
| Realtime badge/feed refresh | `/ws/events`; `EventChange` canonical fields and connectivity state | `useRealtimeAlerts` → `RealtimeStatus` and query cache | Keep reconnect/reconcile behavior and source selection; LIVE describes transport connectivity only |
| Basemap and layer controls | Current static configuration; user-selected dashboard state | `basemaps.ts`, `DashboardSidebar`, `Dashboard` | Do not alter providers, attribution, query state, or defaults as a visual-only change |
| Fault and volcano-zone layer rows/status | `/faults`, `/volcano-zones`; `StaticLayer` source/version/license/properties/geometry | `useStaticLayers` → `StaticLayerStatus`, `MapView` | Preserve empty state and provenance; imported rows do not mean national completeness |
| PHIVOLCS raster overlays | MapServer raster tile exports and source attribution | `volcanoOverlays.ts`, MapView/status components | Label as reference imagery; never present as local vectors or current alert levels |
| Volcano bulletins | `/volcanoes`; `current_alert_level`, `source_url`, `bulletin_url`, `bulletin_at`, `retrieved_at`, `stale` | `useVolcanoes` → `VolcanoPanel` | Preserve null/missing distinctions, valid zero, stale cache state and official links |
| Risk profile cards and region lookup | `/risk-profile/clusters`; `RiskProfile` region, cluster, label, confidence, feature importances, model version, generated time, dataset snapshot; `/risk-profile/{region_name}` lookup | `useRiskProfiles`, `RiskProfileCard`, `RegionLookup` | Keep actual values and descriptive disclaimer; no prediction/official warning framing |
| Source attribution | Existing source/provenance copy and URLs | About, DataSources, static status, bulletin rows | Preserve USGS, PHIVOLCS, GVP, GEM, Kaggle names and links; do not imply endorsement |
| Historical route | No implemented historical query source | `HistoricalBrowser` | Keep the explicit planned/unavailable state; do not add nonfunctional/fake data controls |

### Error handling and accessibility

Keep existing loading, error, retry, empty, stale and unavailable states and their semantics. Preserve user-visible text and accessible names that tests rely on. Use semantic headings/controls, keyboard focus-visible indication, readable labels, non-color cues, contrast-checked text and map symbols, and reduced-motion behavior. Markup changes are allowed only when they preserve the underlying interaction and asserted text; tests may be updated only to reflect the markup change, never to weaken behavior coverage.

## Rollout

One web-only implementation stream, ordered from low to high risk: design-token foundation; shared navigation/common primitives; dashboard shell and responsive layout; dashboard panels and informational pages; MapLibre layers/markers/legend; final accessibility, responsive, data-integrity, and visual verification. Each task is a small Conventional Commit. No backend, ML, mobile, infrastructure, or API work is part of rollout. No commit is made until its intended implementation work and package verification are complete.

## Files

### Web design system and layouts
- Modify: `web/src/styles/tokens.css` — primitive and semantic palette/type/spacing/radius/elevation tokens.
- Modify: `web/src/styles/base.css`, `web/src/styles/utilities.css` — global type, focus, common responsive/accessibility treatment.
- Modify: `web/src/components/layout/TopNav.tsx` and `TopNav.module.css` — shared navigation presentation.
- Modify: `web/src/pages/Hero.tsx`, `Hero.module.css`, `Dashboard.tsx`, `Dashboard.module.css`, `InformationalPage.module.css`, `About.tsx`, `DataSources.tsx`, `HistoricalBrowser.tsx` — page presentation only.
- Modify component CSS Modules under `web/src/components/common`, `dashboard`, `events`, `risk`, `volcanoes`, and `map` — scoped presentation.
- Modify: `web/DESIGN_NOTES.md` — document the refreshed web design decisions after implementation.
- Modify conditionally: `web/WEB_STRUCTURE.md` only if its existing documented tree/layout becomes inaccurate due to the visual implementation.
- Modify conditionally: focused component tests in `web/tests/` only where markup changes require updated semantic selectors while preserving behavior assertions.

### Protected files
- No changes: `web/src/api/client.ts`, all of `web/src/hooks/`, `web/src/types/`, `web/src/lib/risk.ts`, and all files under `backend/`, `ml/`, `mobile/`, `infra/`.
- No API contract edits. Any unexpected need for a protected-file change is a scope issue requiring a revised plan.

## Testing Strategy

- For each changed component, preserve or add behavior-focused Vitest/Testing Library assertions for loaded, empty, error/retry, stale, and keyboard interactions relevant to it. Inspect existing tests first; no behavior change is allowed.
- `cd web && npm test` — complete web suite.
- `cd web && npm run build` — TypeScript/Vite production build.
- `python scripts/verify_structure.py` — repository structure check.
- Review `git diff --check` and confirm only `web/` plus approved design documentation changed.
- Capture before/after screenshots at desktop and mobile widths for Hero, Dashboard map/feed, Dashboard risk view, Dashboard volcano view, About, Data Sources, and Historical. Check tablet layout during the same review.
- Manually run against a live backend: events/map, summary card, stop API to check error/Retry, volcano bulletins, both layer toggles and explicit empty labels, region lookup/risk meter, source selection, and `/ws/events` connection/reconnect. Do not mark a manual scenario complete unless it was run and observed.

## Acceptance Criteria

- [ ] All routes listed in `App.tsx` remain reachable and present their same information and honest availability.
- [ ] Event, summary, realtime, volcano, static-layer, and risk-profile behavior/data sources remain unchanged.
- [ ] All specified source attribution, stale/error/loading/retry/empty states, and "Not available" labels remain present as applicable.
- [ ] New palette tokens and risk colors pass WCAG AA text contrast and 3:1 non-text contrast at UI/map usage sizes; risk is communicated by labels/symbols as well as color.
- [ ] No new fabricated/placeholder values, prediction claims, unsupported coverage claims, or fake historical controls appear.
- [ ] Layout remains usable without horizontal scrolling at desktop, tablet, and mobile widths; keyboard focus and reduced-motion behavior remain usable.
- [ ] Web tests, web build, structure verification, screenshots, live-backend smoke checks, and final scoped diff review are recorded with actual results.

## Out Of Scope (backlog)

- A true dark theme and persisted theme selection.
- Font dependency changes (pending license, self-hosting, loading-performance, and fallback review).
- Basemap vendor/style changes (pending tile terms, attribution, availability, and visual QA review).
- New API metrics, map layers, data sources, historical browsing behavior, official-warning behavior, or expansion/claims about static data coverage.
- Fixes to unrelated copy or existing domain/data behavior.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-09-web-interface-refresh.md` (to follow after this design review).
- Current project status: `docs/project-status.md`.
- Previous web design reference: `docs/superpowers/specs/2026-08-31-web-ui-elevation-design.md`.
- Previous web completion work: `docs/superpowers/specs/2026-09-12-web-mvp-completion-design.md` and `docs/superpowers/plans/2026-09-12-web-mvp-completion.md`.
- Terminology: `docs/glossary.md`.
