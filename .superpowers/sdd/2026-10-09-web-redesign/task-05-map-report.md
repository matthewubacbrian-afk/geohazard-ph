# Task 5 Report — Map layers and basemaps

## Implemented
- Switched Streets to OpenFreeMap Positron while retaining Satellite, Hybrid, Terrain and their existing Esri raster services and attribution metadata.
- Kept MapLibre lifecycle, GeoJSON, source/layer IDs, event/risk mapping, visibility, and style-load restoration intact.
- Applied the semantic neutral magnitude scale to event markers, reduced bounded marker radii, and added a light outline for contrast. Added a visible four-band magnitude legend with numeric-only ranges and color/size cues, without units or risk-like classification terms.
- Exposed the rendered map as a labeled region whose accessible description states how many events are shown, or that the event layer is hidden.
- Applied separate risk tokens, label-dependent opacity and dashed/solid region boundary cues. Added a light boundary casing for mixed basemaps.
- Kept fault lines and volcano-zone polygons visually distinct; changed map controls, attribution, and static-layer status backing to warm neutral surfaces.
- Preserved the existing explicit loading, empty, error, retry, and source attribution UI.

## TDD and verification
- Added assertions for Streets Positron URL, all four basemap choices, exact provider credits for each Esri raster source, OpenFreeMap Streets style URL, magnitude colors/radii/halo, all four risk pattern cues and their visibility toggles, rendered numeric-only magnitude legend labels and map event summary, layer visibility and restoration, and static-layer empty/error/retry states.
- The initial map legend/accessibility assertion failed because MapView had neither a labeled region nor a magnitude legend. A follow-up wording assertion failed on the previous unit and classification labels before the legend copy was corrected. After adding them, the focused suite passes: 4 files, 30 tests.
- `npm run build` passed. Vite reports the existing large JavaScript chunk advisory (>500 kB).
- `git diff --check` passed after the follow-up assertions.
- Did not start services; desktop/mobile inspection of all four basemaps is reserved for Task 7.

## Files
- `web/src/components/map/basemaps.ts`
- `web/src/components/map/MapView.tsx`
- `web/src/components/map/MapView.module.css`
- `web/src/components/map/StaticLayerStatus.module.css`
- `web/src/components/dashboard/DashboardMapArea.module.css`
- `web/tests/MapView.test.tsx`
- `web/tests/basemaps.test.ts`
- `.superpowers/sdd/2026-10-09-web-redesign/task-05-map-brief.md`
- `.superpowers/sdd/2026-10-09-web-redesign/task-05-map-report.md`
