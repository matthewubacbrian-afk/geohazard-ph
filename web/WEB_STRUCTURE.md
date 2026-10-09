# GeoHazard PH Web Application Structure

The web app uses React 18, TypeScript, Vite, TanStack Query, React Router, and
MapLibre GL. Keep the API boundary and data hooks separate from presentation.
CSS Modules are colocated with components; shared style values come from
`src/styles/tokens.css`. The design contract and current feature inventory are in
[REDESIGN_UI.md](REDESIGN_UI.md); the concise contributor rules are in
[DESIGN_NOTES.md](DESIGN_NOTES.md).

## Composition and routes

- `src/main.tsx` loads the app-wide fonts, styles, and providers.
- `src/App.tsx` supplies route composition and settings state.
- `/` renders `pages/Hero.tsx` (How It Works content).
- `/dashboard` renders `pages/Dashboard.tsx` and its control rail, map, and activity
  panel.
- `/about` and `/data-sources` render static informational pages.
- `/historical` renders an intentionally unavailable/planned state; it has no live
  historical query or fake controls.

The dashboard owner keeps filters, selected event, active dashboard view, basemap,
layer/category toggles, and URL query synchronization. Reusable presentation lives
under `components/`; asynchronous reads stay under `hooks/` and `api/`.

## Dashboard view and data flow

| UI | Component | Data source |
| --- | --- | --- |
| Event feed and selected event | `EventFeed`, `EventFeedItem`, `EventDetailPanel` | `useEvents` → `fetchEvents` → `GET /api/v1/events`; source/time/magnitude/category filtering applies to the shared map/list event set. |
| Event markers and map | `DashboardMapArea`, `MapView` | Filtered events, current basemap and toggles; preserve camera, event selection, fault/vector geometry and source attribution. |
| National summary card | `DashboardMapArea` | `useEventSummary` → `GET /api/v1/events/summary`; server values and loading/error/retry/empty states. “Classification” and “Dominant Fault System” are still Coming soon. |
| Realtime connection | `RealtimeStatus`, `useRealtimeAlerts` | WebSocket `/ws/events`; reconnects with backoff and reconciles with REST on open. Events and summary refresh every 30 seconds. LIVE describes connection state only. |
| Fault and volcano-zone vectors | `useStaticLayers`, `StaticLayerStatus`, `MapView` | Toggle-gated `GET /api/v1/faults` and `/api/v1/volcano-zones`; retain imported/empty/error/retry/provenance states. |
| PHIVOLCS volcano reference overlays | `volcanoOverlays.ts`, `VolcanoOverlayStatus`, `MapView` | Remote rendered raster layers when local volcano-zone vectors are absent; distinct from local polygons and alert bulletins. |
| Volcano bulletin view | `VolcanoPanel` | `useVolcanoes` → `GET /api/v1/volcanoes`; alert level, source, bulletin/retrieval time, stale-cache, loading/error/retry/empty. |
| Regional risk overlay and cards | `useRiskProfiles`, `RiskProfilesPanel`, `RiskProfileCard` | `GET /api/v1/risk-profile/clusters`; descriptive profile values and disclaimer. `RegionLookup` is currently dormant and should be surfaced using the already loaded profile list. |
| Individual risk profile client function | `api/client.ts` | `fetchRiskProfile` targets `/api/v1/risk-profile/{region_name}` but no current hook or route consumes it. Do not add an API call as part of the UI redesign. |

`api/client.ts`, `api/staticLayers.ts`, `api/volcanoes.ts`, and `api/realtime.ts`
remain the request/mapping boundary. `types/hazard.ts`, `types/staticLayer.ts`,
`types/volcano.ts`, and hooks remain stable. The default base is
`http://localhost:8000/api/v1`, overridable with `VITE_API_BASE_URL`.

## Map lifecycle and styling

`components/map/basemaps.ts` defines Streets (OpenFreeMap Positron), Satellite,
Hybrid, and Terrain. The raster providers and attribution remain visible. `MapView`
keeps the map instance/camera while styles change, then restores event circles,
risk regions, local fault/volcano vectors, and remote volcano overlays. Map paint
colors resolve from semantic tokens. Event magnitude uses a neutral size/color scale;
risk uses its separate labeled four-step scale. Faults remain lines and local
volcano zones remain shaded polygons.

## Responsive/accessibility rules

At wide widths, the left controls and right activity panel scroll independently
beside the primary map. At tablet widths, use a controls/map row and place the feed
below. At mobile widths, use a single column with visible controls, map, then feed.
The sidebar needs `min-height: 0` through grid/flex ancestors and its own vertical
overflow; browser zoom and narrow viewports must not clip the bottom controls.

All routes use semantic landmarks, labels, keyboard-visible focus, accessible SVG
icons, readable contrast, non-color risk/magnitude cues, and reduced-motion support.
See `REDESIGN_UI.md` for dimensions, tokens, states, and implementation checklist.

## Tests and verification

Web tests are in `tests/` and use Vitest, jsdom, and Testing Library. Mock MapLibre
and network boundaries; assert user-visible behavior rather than implementation
class names. Run from `web/`:

```powershell
npm test
npm run build
```

Also run `python scripts\verify_structure.py` and `git diff --check` from the repo
root. The redesign's desktop/tablet/mobile and live-data verification steps are in
`docs/superpowers/plans/2026-10-09-web-dashboard-redesign.md`.
