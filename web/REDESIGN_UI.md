# GeoHazard PH — Web UI Redesign

This document is the implementation contract for the web-only visual redesign. It
changes presentation while keeping the current React, API, hooks, types, filters,
and map data flow intact. The “must keep working” inventory below records the
current state before implementation; it distinguishes active behavior from dormant
components and intentionally unavailable capabilities.

## Design principles

- **Map first:** keep the Philippines map as the dashboard's largest surface. Place
  navigation above it, controls in a dedicated left rail, and activity/details in a
  right panel on wide screens.
- **Operational clarity:** use restrained field-station materials—basalt ink, ash,
  sand, clay, and ochre. Every status has a readable label; color never carries a
  status by itself.
- **Dense, calm data:** align event rows and numeric columns, show units and source
  context, and reserve large display type for page or region headings.
- **Honest coverage:** keep imported vector layers, PHIVOLCS rendered reference
  overlays, and live bulletins distinct. Never imply national completeness or an
  official warning.
- **Reachable at every width:** no dashboard control may disappear at tablet or
  mobile widths. Avoid clipped panels and nested scroll traps; the sidebar itself
  must scroll when its contents exceed the available height.
- **One presentation system:** semantic CSS variables in `src/styles/tokens.css`,
  colocated CSS Modules, and SVG icons shared through small presentational
  components. No Tailwind or icon-font dependency.

## Must-keep-working inventory

| Existing capability | Current view/component | Data path and behavior that must remain |
| --- | --- | --- |
| Live event feed and event selection | Dashboard → `EventFeed`, `EventFeedItem`, `EventDetailPanel` | `useEvents` → `fetchEvents` → `GET /events`; filtered list and map use the same source/date/magnitude/category state; selection shows original event fields and units. |
| Map event markers | Dashboard → `DashboardMapArea` → `MapView` | Same filtered `HazardEvent[]`; longitude/latitude mapping, magnitude sizing, selected event, visibility, and four basemaps stay intact. |
| National event summary card | `DashboardMapArea` | `useEventSummary` → `fetchEventSummary` → `GET /events/summary`; server-backed count and average magnitude, loading/error/retry/empty states. Classification and dominant fault system currently say “Coming soon.” |
| Realtime updates and REST reconciliation | Dashboard → `RealtimeStatus`, `useRealtimeAlerts` | WebSocket `/ws/events`, reconnect/backoff, query-cache updates, REST invalidation on connect, and 30-second event and summary refresh remain unchanged. “LIVE” means transport connectivity only. |
| Volcano bulletins | Dashboard volcano view → `VolcanoPanel` | `useVolcanoes` → `GET /volcanoes`; retain alert level including valid zero, missing-level text, official links, bulletin/retrieval timestamps, stale-cache status, loading/error/retry/empty states. |
| Imported fault and local volcano-zone vectors | Sidebar toggles → `useStaticLayers` → `GET /faults`, `GET /volcano-zones` → `MapView`, `StaticLayerStatus` | Queries remain enabled only when selected; preserve geometry, visibility, source/version/license attribution, loading/error/retry and explicit “not imported yet” messages. |
| PHIVOLCS rendered volcano map overlays | `MapView`, `VolcanoOverlayStatus` | Used when local volcano-zone vectors are absent; preserve loading/error/retry and provider attribution. These raster references are not local vectors or current alert levels. |
| Regional risk overlay and profile cards | `DashboardMapArea`, `RiskProfilesPanel`, `RiskProfileCard` | `useRiskProfiles` → `GET /risk-profile/clusters`; preserve actual profile labels, confidence, drivers, model/dataset metadata, loading/error/retry/empty states and the descriptive-statistics disclaimer. |
| Region lookup | `RegionLookup`, dormant `RiskProfileExplorer` | A local filter over the already loaded cluster profiles exists but is not mounted by an active route. Make this existing lookup reachable from the risk panel without adding an endpoint call or changing data mapping. `fetchRiskProfile(regionName)` for `GET /risk-profile/{region_name}` exists in the client but has no active hook/view consumer. |
| About and Data Sources | `/about`, `/data-sources` | Static informational views; preserve USGS, PHIVOLCS, GVP, GEM and Kaggle provenance and links. |
| Historical view | `/historical` → `HistoricalBrowser` | Intentionally planned/unavailable; retain honest copy and do not add fake filters or sample data. |
| Hero / How It Works | `/` → `Hero` | Static content and navigation only. Remove prediction claims and decorative sample risk meters; explain the method in text without invented metrics. |
| Settings | `SettingsPanel` | Preserve the existing open/close and settings behavior; no new settings or persistence is implied. |

### Active API and hook map

| View/data | Hook | API client | Contract |
| --- | --- | --- | --- |
| Event feed and markers | `useEvents` | `fetchEvents` in `api/client.ts` | `GET /events`; source and time bounds are requested or applied client-side as currently implemented; source, date, magnitude and category selections continue to affect both list and map. |
| Summary card | `useEventSummary` | `fetchEventSummary` in `api/client.ts` | `GET /events/summary`; 30-second reconciliation. |
| Realtime status and updates | `useRealtimeAlerts` | `realtimeUrl`, `parseEventChange`, `applyEventChange` in `api/realtime.ts` | `WS /ws/events`; REST cache refresh remains in the existing hook/query intervals. |
| Risk overlay and cards | `useRiskProfiles` | `fetchRiskProfiles` in `api/client.ts` | `GET /risk-profile/clusters`. |
| Individual risk lookup function | No active hook | `fetchRiskProfile` in `api/client.ts` | `GET /risk-profile/{region_name}` exists but is not called by current routes. No request-parameter or response-mapping changes are planned. |
| Volcano bulletins | `useVolcanoes` | `fetchVolcanoes` in `api/volcanoes.ts` | `GET /volcanoes`; retain 60-second refresh and stale/error behavior. |
| Imported static layers | `useStaticLayers` | `fetchStaticLayers` in `api/staticLayers.ts` | `GET /faults`, `GET /volcano-zones`; toggle-gated, one-hour freshness. |
| About, Data Sources, Historical, Hero | None | None | Static page content and navigation. |

The API base remains `VITE_API_BASE_URL` or `http://localhost:8000/api/v1`.
No backend, ML, mobile, endpoint, request-parameter, hook, type, or response-mapping
changes are in scope.

## Visual system

### Palette and semantic tokens

Add primitive and semantic aliases in `src/styles/tokens.css`; component styles must
consume semantic names rather than copy hex values. These foreground colors exceed
4.5:1 against each listed light dashboard surface. The last column is the minimum
ratio against the three dashboard surfaces; recheck and record final values.

| Role | Token | Value | Minimum contrast |
| --- | --- | --- | --- |
| Basalt text | `--text` | `#292824` | 11.62:1 |
| Secondary text | `--text-muted` | `#57554F` | 5.87:1 |
| Fine print | `--text-faint` | `#68665F` | 4.53:1 |
| App surface | `--surface` | `#F3F0E9` | — |
| Raised surface | `--surface-raised` | `#FAF8F3` | — |
| Warm card surface | `--surface-card` | `#FFFEFA` | — |
| Ash container | `--surface-container` | `#E8E4DA` | — |
| Strong border | `--border` | `#645F55` | 5.00:1 |
| Soft divider | `--border-subtle` | `#C9C4B8` | 1.65:1 |
| Clay action | `--accent` | `#9B3F2E` | 5.26:1 |
| Focus indicator | `--focus-ring` | `#74402E` | 6.58:1 |
| Low risk | `--risk-low` | `#315B4C` | 6.06:1 |
| Moderate risk | `--risk-moderate` | `#75500E` | 5.68:1 |
| High risk | `--risk-high` | `#99422F` | 5.21:1 |
| Very high risk | `--risk-very-high` | `#702820` | 8.22:1 |
| Low magnitude marker | `--magnitude-low` | `#69645A` | 4.63:1 |
| Moderate magnitude marker | `--magnitude-moderate` | `#58544D` | 5.93:1 |
| High magnitude marker | `--magnitude-high` | `#413D37` | 8.49:1 |
| Very high magnitude marker | `--magnitude-very-high` | `#292824` | 11.62:1 |

Risk colors use four distinct semantic hues and always pair with the written risk
label plus a shape/pattern cue. Magnitude markers use a neutral basalt intensity
scale, bounded size steps, and a labeled magnitude legend; do not reuse risk swatches
for magnitude. Keep a contrasting marker outline/halo on every basemap. Do not use
these surface contrast numbers as a substitute for checking symbols against map tiles.

### Typography

- **Display and section headings:** IBM Plex Serif, with Georgia as the system fallback.
- **UI and reading text:** IBM Plex Sans, with Arial/system sans fallbacks.
- **Magnitude, depth, timestamps, coordinates, and counts:** IBM Plex Mono with
  `font-variant-numeric: tabular-nums`.
- Self-host the WOFF2 files through the `@fontsource/ibm-plex-serif`,
  `@fontsource/ibm-plex-sans`, and `@fontsource/ibm-plex-mono` packages. Import only
  the weights used by the UI. IBM publishes Plex as an open-source family under the
  SIL Open Font License; record the package/source and license in `web/README.md`
  or `web/DESIGN_NOTES.md` and retain the license notices required by the packages.

This coordinated family keeps headings characterful, body copy neutral and readable,
and numeric columns easy to compare. It is not Inter, Roboto, or Space Grotesk and it
does not require third-party font requests at runtime.

### Shape, spacing, and motion

Use a 4px base spacing scale (`4, 8, 12, 16, 24, 32, 48, 64px`) with compact data
rows and larger page gutters. Use a purposeful radius scale: `0px` for map controls
and dense table edges, `4px` for inputs, `10px` for rounded-square panels, and `999px`
for filter chips/toggles only. Avoid giving every element the same rounded card
shape. Keep borders visible and shadows limited to overlays above the map.

Motion is limited to short state transitions; disable nonessential transitions and
reveals under `prefers-reduced-motion: reduce`. Do not animate map data to imply a
forecast.

### Iconography

Use small, consistent, inline or shared React SVG icons with `currentColor`, explicit
accessible names for icon-only buttons, and `aria-hidden="true"` for decorative
icons. Remove reliance on emoji or the Material Symbols font for functional icons.

## Layouts

### Desktop — 1200px and wider

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ GeoHazard PH   Dashboard  How it works  About  Sources  Historical  Settings│
├───────────────────┬────────────────────────────────┬───────────────────────┤
│ Controls           │                                │ Realtime / source     │
│ views               │                                │ Event feed / details  │
│ basemap             │        PRIMARY MAP             │ or Volcano / Risk     │
│ layers + categories │                                │ profile panel         │
│ date + magnitude    │  legend and summary overlay   │                       │
│ independently       │                                │ independently         │
│ scrollable rail     │                                │ scrollable panel      │
└───────────────────┴────────────────────────────────┴───────────────────────┘
```

Keep a compact global header, a 240–280px control rail, a flexible map, and a
300–360px activity panel. The map receives the largest share of width and the
available viewport height. Left controls and right activity scroll independently;
neither body may be clipped by a grid/flex ancestor.

### Tablet — 640px through 1199px

Keep the header readable. Use a controls column and map as the first row; put the
activity panel below the map at full width. Controls may use two compact columns
inside their rail, but labels and all inputs remain visible and operable. Avoid
three cramped side-by-side columns.

### Mobile — below 640px

Use one document column: header/navigation, controls, map, then activity/details.
Controls are expanded in normal document flow so date, magnitude, categories, and
layer toggles are immediately reachable; no hover-only controls, horizontal page
scroll, or hidden drawer-only functionality. Give the map a useful fixed/clamped
height and place map controls within its bounds. Event/detail content follows the map
and remains scrollable as part of the page.

Breakpoints are `--bp-md: 900px` for the desktop/tablet composition and
`--bp-sm: 640px` for mobile. At 640–900px, use the tablet composition with compact
controls. At 900–1200px, reduce the desktop rail/panel widths before using tablet
stacking.

## Component inventory

- **Global:** `TopNav`, `SettingsPanel`, `Reveal`, shared SVG icon primitives,
  typography/surface/focus tokens.
- **Dashboard layout:** `Dashboard`, `DashboardSidebar`, `DashboardMapArea`,
  `RealtimeStatus`.
- **Map:** `MapView`, `EventMarker`, `StaticLayerStatus`, `VolcanoOverlayStatus`,
  `basemaps.ts`, risk legend, magnitude legend, event selection/details.
- **Events:** `EventFilterBar`, `EventFeed`, `EventFeedItem`, `EventDetailPanel`.
- **Risk:** `RiskProfilesPanel`, `RiskProfileCard`, existing `RegionLookup` filtering
  profiles already fetched by `useRiskProfiles`.
- **Volcano:** `VolcanoPanel` and bulletin status/provenance.
- **Pages:** `Hero`, `About`, `DataSources`, `HistoricalBrowser`.
- **Styles:** shared tokens/base/utilities plus colocated CSS Modules. Do not introduce
  Tailwind or move API behavior into presentation components.

## States and copy

- **Loading:** keep existing skeletons and contextual `role="status"` text. Optional
  data never blocks the event/map view.
- **Error:** preserve `role="alert"`, clear failure wording, and the existing Retry
  action at the same data boundary.
- **Empty:** say what is empty (no events, no profiles, no imported features, no
  bulletins); do not imply there is no hazard where there is only no imported data.
- **Unavailable / coming soon:** retain the intentionally unavailable Historical
  state and honestly label unimplemented summary metrics. Never display fake controls
  or sample values as current data.
- **Stale:** keep the volcano cache-stale indicator distinct from current/live state.
- **Attribution:** retain source names, links, licenses, dataset versions, and map
  attribution alongside the data or layer they describe.
- **Required disclaimer:** risk profiles are descriptive statistics, not earthquake
  predictions. Show that statement in the active risk panel and About page. Show
  “GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory” in About and near the
  live dashboard's data/status context.

## Accessibility and visual acceptance

- Body text contrast is at least 4.5:1; large text and meaningful non-text UI
  indicators are at least 3:1 against their adjacent surface. Verify every semantic
  foreground against `--surface`, `--surface-raised`, and `--surface-container`.
- Risk/magnitude legends include textual labels and shape/size distinctions; users
  never need to infer meaning from color alone.
- All navigation and controls work by keyboard, have visible focus, associated
  labels, and practical touch targets. Icon-only controls expose an accessible name.
- Preserve semantic landmarks and heading order; do not encode selection only by color.
- Respect reduced motion and browser zoom/reflow. At desktop, tablet, and mobile
  screenshots there must be no clipped controls or page-level horizontal overflow.
- Verify all view states with mocked data in Vitest and inspect the running app with
  the real local API where its data is available.

## Basemap treatment

Keep the Streets, Satellite, Hybrid, and Terrain choices and provider attribution.
Use OpenFreeMap's Positron light style for Streets; retain the existing Esri
imagery/topographic raster services for the other choices. Tune only the
presentation/style references and GeoHazard overlays in `components/map/basemaps.ts`
and `MapView`; do not remove attribution or make a remote raster claim to be locally
styled. Test hazard symbols, labels, and legend on all four basemaps.

## Reference sources

- IBM Plex family and typeface rationale: <https://www.ibm.com/design/language/typography/typeface/>
- IBM Plex source and SIL Open Font License: <https://github.com/IBM/plex>
- Self-hosted web font packages: <https://fontsource.org/fonts/ibm-plex-sans>,
  <https://fontsource.org/fonts/ibm-plex-serif>, and
  <https://fontsource.org/fonts/ibm-plex-mono>
- OpenFreeMap MapLibre styles and custom-style guidance:
  <https://openfreemap.org/quick_start/>
