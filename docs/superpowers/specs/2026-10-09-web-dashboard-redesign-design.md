# GeoHazard PH Web Dashboard Redesign — Design

**Date:** 2026-10-09

## Problem

The current web UI has working event, summary, realtime, bulletin, static-layer, and
risk-profile flows, but the existing October refresh still uses Inter and does not
fully specify the requested four-level risk palette, separate magnitude colors, or
reachable responsive control layout. The dashboard's controls also need reliable
independent scrolling in a full browser. The redesign must make the map primary and
present every existing view clearly without changing API behavior or losing data
states, attribution, or honest unavailable messages.

## Goals

- Establish a restrained, tokenized basalt/ash/sand/clay/ochre system with a distinct
  four-level risk scale and neutral magnitude scale, both meeting WCAG AA on UI
  surfaces and never communicating status by color alone.
- Use self-hosted IBM Plex Serif, IBM Plex Sans, and IBM Plex Mono with tabular
  numerals; explain their roles and license/source in the web docs.
- Make the dashboard map the dominant desktop surface, with reachable controls and
  activity/detail panels; define tablet and mobile layouts without hidden controls,
  clipped scroll areas, or horizontal page overflow.
- Restyle every existing route, map, panel, and state with shared spacing, radius,
  icon, typography, and motion rules.
- Replace Hero's prediction-sounding claims and decorative sample risk meters with
  factual methodology copy; show both required non-prediction/non-official-advisory
  statements in the active risk panel and relevant About/dashboard context.
- Replace Hero's prediction-sounding claims and decorative sample risk meters with
  factual methodology copy; show both required non-prediction/non-official-advisory
  statements in the active risk panel and relevant About/dashboard context.
- Preserve the user-visible behavior and data source of every active feature in the
  inventory at `web/REDESIGN_UI.md`; expose the already-existing local region lookup
  in the active risk panel without introducing a new API request.
- Keep web CSS Modules, TypeScript strict mode, React/Vite/MapLibre, test framework,
  API client, hooks, types, endpoints, and data mappings.
- Verify web tests/build, repository structure, desktop/tablet/mobile rendering, and
  a live local API session where data prerequisites are available.

## Non-goals

- No changes to backend, ingestion, ML, mobile, infrastructure, API contracts,
  endpoint parameters, response mapping, hooks, shared hazard types, event filters,
  query-string semantics, risk calculations, or source-data assumptions.
- No new data source, map provider, geohazard claim, fake measurement, historical
  search control, prediction claim, or official-advisory implication.
- No Tailwind, dark mode, CSS-in-JS, gradient blobs, glassmorphism, emoji icons,
  remote icon fonts, runtime font CDN, or decorative metrics.
- Do not delete or weaken existing behavior assertions. Update assertions only for
  changed semantic markup while preserving the same interaction/data expectations.

## Context And Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `REACT_BEST_PRACTICES.md`,
  `docs/glossary.md`, `docs/api-contracts.md`, `docs/testing-standards.md`,
  `docs/runbook.md`, and the spec/plan templates.
- Stay in the current checkout and `docs/web-interface-refresh` branch. Preserve
  pre-existing uncommitted edits to `DashboardSidebar.module.css`,
  `Dashboard.module.css`, and `web/tests/DashboardLayout.test.mjs`; do not reset,
  overwrite, or stage them as part of unrelated commits.
- The current visual-refresh spec/plan is already in history. This new spec is the
  user's stricter second pass; the new requirements supersede conflicting prior
  choices such as Inter and the old single active risk token.
- Current routes are `/`, `/dashboard`, `/about`, `/data-sources`, `/historical`.
  The Hero page includes How It Works content; Historical is intentionally
  unavailable. About and Data Sources are static pages.
- Active event view: `useEvents` → `fetchEvents` → `GET /events`. The same filtered
  event set feeds map and list. Date, source, magnitude and category behavior and
  URL synchronization remain unchanged.
- Summary: `useEventSummary` → `GET /events/summary`; remains server-backed and
  reconciles every 30 seconds. “Classification” and “Dominant Fault System” remain
  honestly labeled “Coming soon.”
- Realtime: `useRealtimeAlerts` → `/ws/events`; preserve reconnect/backoff, query
  updates, reconnect reconciliation and 30-second REST refreshes. LIVE is transport
  connectivity only.
- Bulletins: `useVolcanoes` → `GET /volcanoes`; preserve alert-level null/zero
  handling, PHIVOLCS links, timestamps and stale-cache states.
- Static layers: `useStaticLayers` → `GET /faults` and `/volcano-zones`; preserve
  local geometry, independent toggles, provenance and explicit empty states.
  PHIVOLCS rendered raster reference overlays remain separate from local vectors and
  bulletins.
- Risk data: `useRiskProfiles` → `GET /risk-profile/clusters`. `RegionLookup` and
  `RiskProfileExplorer` exist but are not mounted by a route; make the existing
  loaded-list filter reachable in the active risk panel. `fetchRiskProfile` for
  `/risk-profile/{region_name}` exists but has no active hook consumer; do not add
  one for this redesign.
- Preserve the required messaging: profiles are descriptive statistics, not
  earthquake predictions, and the app is not an official PHIVOLCS/NDRRMC advisory.
- Project verification commands: `npm test` and `npm run build` from `web/`,
  `python scripts\verify_structure.py` and `git diff --check` from repo root.

## Alternatives Considered

1. **Map-led three-column desktop, stacked tablet/mobile (chosen).** It preserves
   the established view model, gives the map most desktop space, keeps controls
   adjacent to the map, and keeps every control in document flow on narrow screens.
2. **Card-grid dashboard with a smaller map.** It would fit the data into familiar
   cards but would demote the geographic context and duplicate panel chrome.
3. **Full-bleed map with floating drawers.** It maximizes map pixels but hides
   filters and feed context, adds open/close state, and makes the existing sidebar
   scrolling issue harder to avoid. No new drawer interaction is needed.

## Design

### Architecture and data flow

Restyle existing React components and preserve ownership boundaries. `Dashboard`
retains filter, selection, view, layer, basemap and URL state. `DashboardSidebar`
retains control callbacks. `DashboardMapArea` uses the existing summary/profile
hooks and passes data to `MapView`. `EventFeed`, `VolcanoPanel`, and
`RiskProfilesPanel` keep their existing data hooks. The only behavior made
reachable is local filtering through the existing `RegionLookup`, using profiles
already loaded by `useRiskProfiles`.

No request parameters, endpoints, response mapping, hook signatures, or domain types
change. The detailed feature-to-view and API-to-hook inventory is in
`web/REDESIGN_UI.md` and must be checked during implementation.

### Visual system and tokens

Use `web/REDESIGN_UI.md` as the authoritative design specification. Its tokens are:

- Surfaces: `#F3F0E9`, `#FAF8F3`, `#FFFEFA`, `#E8E4DA`.
- Main/muted/faint text: `#292824`, `#57554F`, `#68665F`.
- Border/accent/focus: `#645F55`, `#9B3F2E`, `#74402E`.
- Risk Low/Moderate/High/Very High: `#315B4C`, `#75500E`, `#99422F`, `#702820`.
- Magnitude Low/Moderate/High/Very High: neutral ramp `#69645A`, `#58544D`,
  `#413D37`, `#292824`.

Risk and magnitude palettes remain separate. Show a written label and symbol/size
cue wherever either scale appears. Risk text and magnitude swatches must meet 4.5:1
against each light token surface; non-text indicators meet 3:1 against adjacent UI
surfaces. Map markers require a visible contrasting outline/halo and visual checks
against streets, satellite, hybrid, and terrain tiles.

Use self-hosted Fontsource IBM Plex packages: Serif for editorial headings, Sans for
UI/body, Mono with tabular numerals for measurement/time fields. Retain system
fallbacks. This single open family is chosen for cohesive serif/sans/mono character,
clear numeric forms, and an OFL-licensed self-hosted delivery path rather than
remote requests. Record source/license in the design docs. Use 4px spacing, 0/4/10/999px
shape radii for map/table edges, inputs, rounded-square panels and filter pills
respectively. Motion stays minimal and honors reduced-motion.

### Layout and basemaps

- Desktop ≥1200px: header; 240–280px scrollable control rail; flexible dominant
  map; 300–360px scrollable feed/detail panel.
- Tablet 640–1199px: compact controls beside the map and full-width feed below;
  reduce panel widths before collapsing at 900px.
- Mobile <640px: normal-flow header/navigation, visible controls, map, then
  activity/detail. All fields stay in the document flow; no hidden drawer-only
  controls and no horizontal page scrolling.
- Grid/flex ancestors use `min-height: 0`; scroll containers have constrained
  available height and `overflow-y: auto` so browser viewport clipping cannot hide
  the date or magnitude controls.
- Streets uses OpenFreeMap Positron; Satellite, Hybrid, and Terrain retain the
  existing Esri raster services. Keep provider attribution. Tune only style choice
  and GeoHazard overlays; do not change hazard data sources.

Wireframes, component inventory, interaction states, accessibility rules and
contrast matrix are defined in `web/REDESIGN_UI.md`.

### Error handling and states

Preserve loading skeletons, retry actions, `role="status"`/`role="alert"`, empty
layer/feed/profile/bulletin messages, volcano stale-cache labeling, source links,
license/version attribution, unavailable Historical copy, and the summary's
unavailable fields. Never substitute invented values. Risk disclosures remain
visible in Hero/About and in the risk view.

### Files

#### Web documentation (this planning stage)

- Create `web/REDESIGN_UI.md` — full design contract, inventory, wireframes and
  accessibility rules.
- Rewrite `web/DESIGN_NOTES.md` — concise design-system handoff.
- Rewrite `web/WEB_STRUCTURE.md` — current component/data ownership and layout.
- Create `docs/superpowers/specs/2026-10-09-web-dashboard-redesign-design.md` —
  this specification.
- Create `docs/superpowers/plans/2026-10-09-web-dashboard-redesign.md` —
  task-by-task implementation steps.

#### Web implementation (after approval)

- Modify `web/src/styles/tokens.css`, `base.css`, `utilities.css`, and `main.tsx`;
  add the self-hosted IBM Plex Fontsource packages to `web/package.json` and
  `web/package-lock.json`.
- Modify shared navigation/settings and page components/styles under
  `web/src/components/layout`, `web/src/components/common`, and `web/src/pages`.
- Modify dashboard/event/risk/volcano/map component presentation and CSS Modules
  under `web/src/components/dashboard`, `events`, `risk`, `volcanoes`, `map`, and
  `web/src/pages`.
- Modify `web/src/components/map/basemaps.ts` for the selected light style and
  palette-compatible map treatment; update `MapView` paint/legend only.
- Add/update user-visible behavior and accessibility assertions under `web/tests/`;
  specifically cover sidebar scrolling layout and the active region lookup.
- Do not modify `web/src/api/`, `web/src/hooks/`, `web/src/types/`,
  `web/src/lib/risk.ts`, `backend/`, `ml/`, `mobile/`, or `infra/`.

## Rollout

1. Complete reorientation and the requested documentation first. Review the spec
   and plan with the user; no implementation starts until approval.
2. After approval, execute the plan in the current checkout/branch using
   subagent-driven development, sequential task briefs/reports, and TDD wherever
   behavior or accessibility semantics are touched.
3. Verify tests/build/structure, run the app with local API data where available,
   and inspect desktop/tablet/mobile routes before reporting completion.

## Testing Strategy

- Preserve every existing `web/tests` behavior assertion. Add coverage for active
  risk-panel lookup filtering and responsive/scroll semantics where not already
  covered; do not assert class names unless the test is specifically checking the
  stylesheet's constrained scroll contract.
- For changed components, retain loaded, empty, error/retry, stale, keyboard and
  source/selection behavior cases relevant to those components.
- Run `npm test` and `npm run build` from `web/`.
- Run `python scripts\verify_structure.py` and `git diff --check` from repo root.
- Manually inspect 1440px desktop, 900px tablet, and 390px mobile for `/`,
  `/dashboard` in event/risk/volcano views, `/about`, `/data-sources`, and
  `/historical`. Capture screenshots and verify no clipping or horizontal overflow.
- With local PostGIS/Redis/API available, verify live event map+feed, source/date/
  magnitude/category filters, summary, WebSocket and 30-second reconcile, bulletin
  links/staleness, fault/volcano toggles with loaded/empty status, risk overlay,
  region filtering and Retry states. Record unavailable prerequisites without
  marking those scenarios passed.
- Review the before/after parity checklist against this spec and the full scoped diff.

## Acceptance Criteria

- [ ] `web/REDESIGN_UI.md`, `web/DESIGN_NOTES.md`, and `web/WEB_STRUCTURE.md` match
  the approved design and contain the current-state inventory.
- [ ] Desktop/tablet/mobile layouts have no clipped controls or horizontal page
  overflow; date and magnitude remain reachable in the browser.
- [ ] All routes and active feature behavior/data paths in `REDESIGN_UI.md` remain
  present; current gaps stay explicitly identified and honest.
- [ ] Existing API client, hooks, types, endpoints, filter request/mapping behavior,
  and backend/mobile/ML code are unchanged.
- [ ] The four risk levels have distinct labels and non-color cues; risk and
  magnitude palettes are distinct and pass WCAG AA on each listed UI surface.
- [ ] IBM Plex typefaces are self-hosted with source/license documented; no remote
  runtime font or icon-font dependency is added.
- [ ] `npm test`, `npm run build`, structure verification, and `git diff --check`
  pass; behavior assertions are not removed or weakened.
- [ ] Desktop/tablet/mobile screenshots and available live-API smoke scenarios are
  recorded; the before/after parity checklist is complete.
- [ ] Task briefs/reports exist under `.superpowers/sdd/2026-10-09-web-redesign/`.

## Out Of Scope (backlog)

- Implementing historical event queries or region-specific server lookup behavior.
- Importing new hazard datasets, changing map providers, or claiming complete
  national static-layer coverage.
- Changing endpoint contracts or making risk profiles predictive.
- Creating a dark theme or adding motion beyond small accessible state transitions.

## Related documents

- Design rules and feature inventory: `web/REDESIGN_UI.md`.
- Implementation plan: `docs/superpowers/plans/2026-10-09-web-dashboard-redesign.md`.
- Templates: `docs/superpowers/templates/spec-template.md` and
  `docs/superpowers/templates/plan-template.md`.
- API fields and terminology: `docs/api-contracts.md` and `docs/glossary.md`.
