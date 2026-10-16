# Epic 6 NASA Landslide Susceptibility Overlay — Design

**Date:** 2026-10-16

## Problem

The dashboard map currently offers imported fault and volcano reference layers, but no landslide context. Existing placeholder modules in `backend/ingestion/sources/landslide_susceptibility.py` and `backend/app/models/landslide_zone.py` do not provide a complete, verified data path. Users need a clearly qualified broad-scale susceptibility reference on the map without implying a site assessment or live warning.

## Goals

- Add an optional landslide susceptibility overlay to the web dashboard map using NASA's published global image service directly.
- Let users toggle the overlay independently and identify NASA as its source.
- Present its published low-to-high value range and explain its coarse, static, planning-context limitations.
- Show loading and service-error states with a retry action while the layer is enabled.
- Keep the feature independent of backend storage, imports, APIs, and the later InSAR feasibility work.

## Non-goals

- Download, mirror, tile-cache, or persist NASA raster data in the project.
- Build or train a landslide model, derive local susceptibility classes, or interpret a pixel as an event probability.
- Present the layer as live, official warning, parcel-level/site-level assessment, or proof that an area is safe or hazardous.
- Add MGB polygons; reuse rights and national coverage for the candidate service have not been established.
- Add InSAR deformation data or feasibility conclusions.
- Change APIs, database models, ingestion, mobile, notifications, or alert logic.

## Context And Constraints

- The project uses React, TypeScript, Vite, MapLibre GL, and the existing dashboard/sidebar pattern for optional layers.
- `web/src/components/map/volcanoOverlays.ts` and `VolcanoOverlayStatus.tsx` provide examples for remote raster overlays, attribution, and status display. `DashboardSidebar.tsx`, `Dashboard.tsx`, and `MapView.tsx` own layer selection, state, and map rendering.
- NASA's [Global Landslide Susceptibility image service](https://gis.earthdata.nasa.gov/portal/rest/services/Landslides/Global_Landslide_Susceptibility/ImageServer) is a global one-band ImageServer in WGS84 with pixel size 0.0083333333 degrees (about 1 km) and values 0–5. The service metadata exposes only Low (0) and High (5) legend endpoints; the UI must not invent names for intermediate values.
- NASA describes the source as a heuristic global susceptibility product based on terrain and other contextual inputs. It is broad reference context with experimental/research-grade and availability limitations, not an operational warning product. Use NASA's [product guide](https://maps.disasters.nasa.gov/download/documents/NASA_Disasters_Mapping_Portal_Product_Guide_202109.pdf) and service metadata for attribution and these qualifications.
- The NASA portal item and service are publicly accessible. This design does not assume guaranteed availability, refresh cadence, or permission to redistribute a locally copied raster. The app will request display imagery from NASA at runtime.
- The NASA image service offers an ArcGIS REST export endpoint; MapLibre's raster source requires a tile URL template. The implementation must use the service's documented export/tile request behavior and validate the rendered layer in the existing MapLibre map. If that cannot be supported reliably without copying data, surface the error and revise the technical approach before implementation.
- No new domain API, schema, or glossary data fields are introduced. The glossary will define the UI term and its limits.

## Alternatives Considered

1. **Import raster tiles or polygons into project storage.** Rejected for this slice because it adds update, storage, provenance, and reuse obligations, and NASA already serves the global reference layer.
2. **Use MGB's detailed susceptibility polygons.** Rejected pending confirmation of reuse terms and national coverage; publicly accessible service metadata alone does not answer either question.
3. **Keep Epic 6 as an unimplemented placeholder until InSAR is ready.** Rejected because the NASA layer is an independently useful, bounded first deliverable and does not depend on InSAR.

## Design

### Architecture and data flow

1. A new dashboard toggle controls a boolean `landslideSusceptibility` layer state, defaulting to `false`.
2. `MapView` adds/removes one NASA-sourced raster layer when the toggle changes. The source remains remote; no browser or backend persistence is added.
3. A dedicated overlay-status component reports loading or failure and offers retry. On a successful map load, it exposes source attribution and the static-reference limitation alongside a legend from Low (0) to High (5).
4. When disabled, the raster source/layer and its status panel are removed/hidden. Existing fault and volcano layers retain their behavior.

### Components

- `web/src/components/map/landslideOverlays.ts`: service URL, source attribution, raster request construction and constants for the overlay.
- `web/src/components/map/LandslideOverlayStatus.tsx`: enabled-layer loading/error/retry presentation, low-to-high legend, NASA link, and limitation text. Reuse existing static-layer status styles where suitable.
- `web/src/components/dashboard/DashboardSidebar.tsx`: add the independent landslide susceptibility toggle.
- `web/src/pages/Dashboard.tsx`: own default-off state, wire toggle into map, and show status while enabled.
- `web/src/components/map/MapView.tsx`: typed visibility prop and lifecycle synchronization for the raster source/layer.
- `docs/glossary.md`: canonical term and limitation for the landslide susceptibility overlay.

### Interfaces

- `DashboardSidebar` active-layer map gains `landslideSusceptibility: boolean`; its change callback uses the same key and boolean contract as the existing toggles.
- `MapViewProps` gains `showLandslideSusceptibility?: boolean`, default `false`.
- Overlay module exports a stable layer ID and a function that builds the remote raster source configuration from the NASA ImageServer. It must not expose an API response type or imply a locally stored dataset.
- `LandslideOverlayStatus` props: `loading: boolean`, `error: string | null`, `onRetry: () => void`; status text and attribution are fixed UI copy, not caller-supplied hazard classifications.
- Legend endpoints are exactly `Low · 0` and `High · 5`; no intermediate classes are named unless NASA metadata supplies them in a later reviewed change.
- Toggle label: `Landslide susceptibility`; status title/attribution names NASA Global Landslide Susceptibility Map and links to the exact ImageServer/item source.

### Configuration

No new environment variables, settings fields, packages, or user configuration.

### Error handling

- If the map style is not yet ready, defer source/layer registration until the existing MapLibre load lifecycle allows it.
- If the NASA service request fails, keep the rest of the map usable, show a concise unavailable message, retain source attribution, and provide a retry action.
- Do not silently substitute a blank/zero overlay or present missing pixels as low susceptibility.
- Follow `docs/error-handling-and-logging.md`; do not log per-tile failures as application errors or add noisy console output.

### Data considerations

- No data is imported, transformed, retained, or exposed through the backend. Geographic coordinates and raster values remain controlled by the NASA service.
- The layer is static source context and has no observation timestamp in this UI. Do not show a retrieval timestamp as if it were a source update date.
- Source service availability, pixel coverage, and rendering are external dependencies. Missing or transparent pixels must not be interpreted as low risk.

## Rollout

Web-only, default-off feature on `feat/epic6-landslide`. Implement the map source and toggle, then status/legend and failure handling, followed by focused web tests and package verification. No migration, backfill, deployment setting, or data import is required. InSAR remains a later separate feasibility spec.

## Files

### Web

- `web/src/components/map/landslideOverlays.ts` — NASA remote raster source configuration and attribution.
- `web/src/components/map/LandslideOverlayStatus.tsx` — status, retry, legend, and caveat UI.
- `web/src/components/map/MapView.tsx` — raster source/layer lifecycle and visibility.
- `web/src/components/dashboard/DashboardSidebar.tsx` — user toggle.
- `web/src/pages/Dashboard.tsx` — dashboard state and status wiring.
- `web/src/components/map/*.test.tsx` or established adjacent test locations — component/layer behavior tests, selected to match repository conventions in the implementation plan.

### Documentation

- `docs/glossary.md` — canonical terminology for the overlay.
- `docs/superpowers/specs/2026-10-16-epic6-nasa-landslide-overlay-design.md` — approved scope and design.

## Testing Strategy

- Web unit tests verify the default-off toggle, callback key, raster source/layer visibility lifecycle, error/retry state, legend endpoints, attribution link, and limitation copy.
- Tests mock MapLibre and NASA requests; they do not depend on NASA availability.
- Run the web package's required tests and build/type-check from `CODING_STANDARDS.md` and `docs/testing-standards.md` during implementation. A manual browser check should confirm enable/disable behavior and visible attribution when the source is reachable.
- No backend, mobile, database, or ingestion tests are needed because those packages are unchanged.

## Acceptance Criteria

- [ ] Dashboard includes a default-off `Landslide susceptibility` map toggle.
- [ ] Enabling the toggle requests and displays the NASA global raster as a distinct layer; disabling it removes the layer.
- [ ] Existing fault, volcano-zone, and PHIVOLCS overlays continue to work.
- [ ] The enabled overlay shows NASA attribution, a Low (0) to High (5) legend, and text identifying the layer as coarse, static reference context rather than a live warning or site assessment.
- [ ] Loading, service failure, and retry are represented without treating absent pixels as low susceptibility.
- [ ] No server-side raster copy, backend endpoint/model, or new environment setting is introduced.
- [ ] Focused tests and required web package verification pass; external-service browser check is reported separately if NASA is unavailable.

## Out Of Scope (backlog)

- InSAR feasibility: investigate suitable SAR datasets, coverage, revisit cadence, processing, validation, costs, and operational limits in a separate Epic 6 part-two spec before implementation.
- MGB detailed susceptibility polygons: establish reuse rights, source coverage, and update expectations before considering display or import.
- Site-specific or event-driven landslide assessment, rainfall thresholds, alerts, and prediction.
- Caching, downloading, or bundling NASA raster data.

---

## Spec self-review

- No TBD/TODO markers or unfinished sections remain.
- Goals map to acceptance criteria; the scope is one web-only implementation plan.
- Remote imagery, legend endpoints, loading/error behavior, attribution, and limitations are specified without inventing intermediate classes.
- The design explicitly excludes backend persistence, MGB data pending clearance, and InSAR implementation.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-16-epic6-nasa-landslide-overlay.md` (to be created after spec approval; see plan template).
- Terminology: `docs/glossary.md`.
- Source assumptions: `docs/data-sources.md`.
