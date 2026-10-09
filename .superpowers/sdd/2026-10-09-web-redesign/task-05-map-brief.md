# Task 5 Brief — Map layers and basemaps

## Objective
Align GeoHazard PH map tiles, event symbols, risk fills, static overlays, legends, controls, and layer status panels with the approved basalt/ash/sand/clay palette while preserving the existing map data flow and lifecycle.

## Constraints
- Keep all four basemaps and their source attribution; Streets uses OpenFreeMap Positron, and Satellite/Hybrid/Terrain retain their Esri raster templates.
- Preserve MapLibre camera lifecycle, source/layer IDs, geometry conversion, event/risk mappings, visibility state, and style-load restoration.
- Do not imply current PHIVOLCS alerts. Do not change APIs, hooks, types, backend, mobile, or ML.
- Event magnitude colors remain distinct from risk colors; symbols remain legible on all basemaps and include non-color meaning.

## Acceptance
- Focused tests cover all basemap IDs, style URL/provider attribution, raster/vector distinction, bounded magnitude sizing and halo, canonical risk label colors and cues, layer visibility restoration after style loads, and loading/empty/error/retry statuses.
- Map controls/status backing and attribution use readable warm neutral surfaces.
- Focused map tests and web build pass. No services are started in this task.
- Commit as `style: align map layers with hazard palette`.
