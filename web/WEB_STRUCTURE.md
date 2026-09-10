# GeoHazard PH Web Application Structure

The web application uses React 18, TypeScript, Vite, TanStack Query and MapLibre GL.
Components use colocated CSS Modules and tokens from `src/styles/tokens.css`; see
[DESIGN_NOTES.md](DESIGN_NOTES.md) for palette, spacing and motion conventions.

## Composition

`src/main.tsx` mounts the application. `App.tsx` supplies the QueryClient and switches
views between Hero, Dashboard, About, DataSources and HistoricalBrowser. The informational
pages retain explicit placeholders for unfinished capabilities.

`pages/Dashboard.tsx` owns selected event, source/date/magnitude filters, active view,
basemap and overlay toggles. `DashboardSidebar` renders controls; `DashboardMapArea`
composes the map, live loading/error status and the national summary card.
`EventFeed` renders activity and event details. The side panel switches between
activity, `VolcanoPanel` and `RiskProfilesPanel`. `TopNav` provides navigation.

## Data access

| Module | Responsibility |
| --- | --- |
| `api/client.ts` | Events, event summary, risk profiles; configurable `VITE_API_BASE_URL` |
| `api/errors.ts` | Named `ApiError` carrying HTTP status and stable code |
| `api/staticLayers.ts` | Imported fault and volcano-zone reads |
| `hooks/useEvents.ts` | Event cache and browser filtering |
| `hooks/useEventSummary.ts` | National bounding-box event aggregate |
| `hooks/useRiskProfiles.ts` | Historical statistical profiles |
| `hooks/useRealtimeAlerts.ts` | Active reconnecting WebSocket subscriber and REST reconciliation |
| `hooks/useStaticLayers.ts` | Optional reference queries, enabled per toggle, one-hour freshness |
| `hooks/useFaultLines.ts` | Legacy scaffold; use `useStaticLayers` for the active flow |

The API base defaults to `http://localhost:8000/api/v1`. Wire fields remain snake_case.
`types/hazard.ts` defines `HazardEvent`, `EventSummary` and `RiskProfile`;
`types/staticLayer.ts` defines imported geometry and provenance. Mobile mappings are
owned by the mobile package, not reused as wire types here.

## Map lifecycle

`components/map/MapView.tsx` retains its camera and map instance while switching among
Streets, Satellite, Hybrid and Terrain basemaps. It restores live-event circles, fault
lines and volcano polygons after `style.load` using current data and toggle values.
Reference data arriving after map load updates existing sources without moving the camera.
Source geometry preserves polygon holes. All map paint colors resolve from design tokens.

`StaticLayerStatus` renders loading, empty, error/retry and attributed loaded states.
Missing optional overlays do not block earthquake data. Faults use solid lines;
volcano hazard zones use shaded polygons. These are static references, not live alerts.

## Backend endpoints consumed

- `GET /api/v1/events` and `/api/v1/events/summary`
- `GET /api/v1/risk-profile/clusters` and `/api/v1/risk-profile/{region_name}`
- `GET /api/v1/volcanoes`
- `GET /api/v1/faults` and `/api/v1/volcano-zones`
- `WS /ws/events` (unversioned)

See [API contracts](../docs/api-contracts.md) for errors, source filtering and response fields.

## Verification

```bash
cd web
npm install
npm test
npm run build
```

Tests live in `tests/`. Vitest uses jsdom with shared jest-dom registration and cleanup
in `tests/setup.ts`. Component tests use Testing Library; MapLibre is mocked for
deterministic geometry, visibility, style lifecycle and camera checks.
