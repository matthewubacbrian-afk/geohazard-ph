# Epic 3 PHIVOLCS Volcano-Zone Coverage — Design

**Date:** 2026-10-09

## Problem

Epic 3 already has a `VolcanoZone` vector import, PostGIS storage, and read endpoint, but the current project status says no PHIVOLCS volcano-zone vector data has been imported. The web map separately displays PHIVOLCS-rendered raster overlays for lahar, lava flows, pyroclastic density currents, and base surge. Those rendered map images are not locally stored `VolcanoZone` polygons and do not establish nationwide polygon coverage.

PHIVOLCS publishes multiple ArcGIS polygon services with different hazard meanings and metadata extents. Its Maps Portal asks for source acknowledgment and warns against unauthorized use, depiction, sale, and derivatives. Publicly queryable service metadata alone does not establish permission for GeoHazard PH to copy, store, display, or redistribute vector geometry. The project needs an evidence-based coverage inventory and reuse decision without conflating hazard zones with current volcano alert levels.

## Goals

- Inventory the official PHIVOLCS polygon-layer candidates relevant to Epic 3: permanent/extended danger zones and hazard-specific layers such as pyroclastic density currents, lahar, lava, and base surge.
- Record each inspected service/layer URL, official product name, geometry type, CRS, metadata extent, relevant classification/provenance fields, and source-stated date where present.
- Compare each metadata extent with the configured project bounds `(116, 4, 128, 22)` and state that extents are bounding metadata, not proof of complete coverage or feature counts.
- Preserve the existing source-rendered raster overlays and their DOST-PHIVOLCS attribution. Keep those overlays distinct from imported local vectors and from current `alert_level` reports.
- Establish terms that cover the planned storage, display, and redistribution before importing or bundling PHIVOLCS vector geometry.
- If reuse terms remain unclear, record the source and attribution requirements, leave local vector import blocked, and keep Epic 3 partial.

## Non-goals

- Import, mirror, bundle, or redistribute PHIVOLCS geometry before reuse terms are clear.
- Change existing MapLibre raster overlays, their service URLs, or their behavior in this slice.
- Treat public ArcGIS service access or source acknowledgment as a license.
- Contact PHIVOLCS on the user's behalf without separate authorization.
- Treat permanent/extended danger-zone classes as live alert levels or official real-time warnings.
- Digitize map PDFs/KMZs, infer hazard polygons, generate buffers, or fill gaps with arbitrary geometry.
- Change API schemas, database models, migrations, map styles, or production data.
- Claim all Philippine volcano hazard areas are mapped or represented.

## Context And Constraints

- `docs/project-status.md` is the current status register. Epic 3 is partial: the GEM fault snapshot is verified locally, while PHIVOLCS fault reuse, volcano-zone data, and national completeness remain unresolved.
- `README.md` describes the existing Epic 3 validated vector import and API path. `backend/app/schemas/volcano_zone.py` and `backend/app/api/v1/volcano_zones.py` define the current generic `VolcanoZone` response and `/volcano-zones` endpoint.
- `web/src/components/map/volcanoOverlays.ts` uses PHIVOLCS MapServer `export` images as raster map sources and includes the attribution link `DOST-PHIVOLCS volcano hazard maps`. `web/src/components/map/VolcanoOverlayStatus.tsx` labels them as official reference overlays and says they do not indicate current alert levels. This design preserves those behaviors.
- Official PHIVOLCS vector candidates observed in ArcGIS REST metadata include:
  - `DangerZone/MapServer/0`: polygon features classified as `PDZ` or `EDZ`; metadata extent `(120.8219, 10.2666, 124.2018, 14.1818)`; WGS84; fields include `volcanoname`, `distance`, `datasource`, `datemapped`, `scale`, `publishdate`, and `dzc`.
  - `DangerZone_permanent/MapServer/0`: polygon features labeled `PDZ`; metadata extent `(120.9660, 10.2675, 124.0992, 14.0431)`; WGS84.
  - `DangerZone_extended/MapServer/0`: polygon features for extended danger zones; metadata extent `(120.9660, 10.2675, 124.0992, 14.0431)`; WGS84.
  - `Pyroclastic_ohas/FeatureServer/0`: polygon features for pyroclastic density currents with classes including `ModLow`, `Moderate`, `High`, and buffer classes; metadata extent `(121.3494, 10.2473, 125.2667, 14.1944)`; WGS84; source metadata fields include `volcanoname`, `datasource`, `datemapped`, `scale`, and `publishdate`.
  - `Lava/MapServer/0`: polygon features for mapped lava flows; metadata extent `(121.0088, 5.9622, 126.0874, 20.4895)`; WGS84; source classification field `lavaclass` and provenance fields include `volcanoname`, `datasource`, `datemapped`, `scale`, and `publishdate`.
  - `VolcanoLahar_ohas/FeatureServer`: service metadata reports WGS84 and full extent `(117.6710, 8.8235, 127.5621, 17.0364)`. Inspect the specific child layer before any future use.
  - `BaseSurge_ohas/MapServer/0`: polygon layer extent `(120.8526, 13.8598, 121.1370, 14.1290)`; metadata describes base-surge zones around a limited area.
- Direct PHIVOLCS service references: [`DangerZone`](https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/DangerZone/MapServer/0), [`DangerZone_permanent`](https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/DangerZone_permanent/MapServer/0), [`DangerZone_extended`](https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/DangerZone_extended/MapServer/0), [`Pyroclastic_ohas`](https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/Pyroclastic_ohas/FeatureServer/0), [`Lava`](https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/Lava/MapServer/0), [`VolcanoLahar_ohas`](https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/VolcanoLahar_ohas/FeatureServer), and [`BaseSurge_ohas`](https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/BaseSurge_ohas/MapServer/0).
- These metadata extents are not feature counts and do not prove that all hazards or volcanoes in those rectangles are represented. Several are visibly narrower than the project's Philippines bounds. No service feature count or feature geometry was retrieved for this design.
- The official [PHIVOLCS Maps Portal](https://maps.phivolcs.dost.gov.ph/) asks users to acknowledge DOST-PHIVOLCS and warns against improper depiction, unauthorized use, sale, or derivatives. It says hazard maps may be revised as information improves. The [hazard-map download instructions](https://www.phivolcs.dost.gov.ph/gisweb-download-hazard-maps-instruction/) describe downloadable KMZs and note that map availability can vary by municipality, province, or region. No open redistribution license was identified in the reviewed materials.
- For every permitted PHIVOLCS-derived use, acknowledge **DOST-PHIVOLCS**, link to the exact service or map product, identify the layer/product and its source-stated date/version, distinguish source date from retrieval/import timestamps, and include all additional attribution/restrictions in the applicable permission terms.
- Existing static vector imports require source provenance and validated WGS84 geometry. Read `docs/data-sources.md`, `docs/glossary.md`, `CODING_STANDARDS.md`, and `docs/api-contracts.md` before any future implementation that changes API or data behavior.

## Alternatives Considered

1. **Import every public polygon service immediately and attribute it.** Rejected because public access and attribution do not resolve PHIVOLCS's published reuse restrictions; the service extents also demonstrate partial coverage.
2. **Keep only the existing source-rendered raster overlays and do no coverage review.** Rejected for this slice because the project status and Epic 3 vector path need an evidence-based account of what each official service represents and where it applies. Existing overlays remain unchanged as the current map reference.
3. **Download and digitize the portal's KMZ/PDF map packages.** Rejected because the portal itself notes availability varies by location, digitization creates a derivative, and the same permission/attribution requirements still apply.

## Design

### Architecture and data flow

This is a source inventory and reuse-clearance slice, not a polygon import:

1. Review official PHIVOLCS service and portal metadata for each candidate. Record only layer metadata and published terms; do not fetch feature geometry or count results while redistribution permission is unclear.
2. Build a per-layer coverage inventory using published metadata extent, geometry type, hazard/classification fields, source-stated mapping/publication date, and direct source links. Mark unknown counts and unknown coverage explicitly.
3. Compare each metadata extent to the configured project bounds. Do not infer that the rectangle contains mapped geometry throughout, that an absent service layer means no hazard, or that one hazard type represents another.
4. Preserve the existing PHIVOLCS-rendered raster overlays and their source links. Document that these images are remote reference map renders and are not imported local `VolcanoZone` polygons.
5. Apply the reuse gate before any future vector download/import or bundling:
   - If official terms or written authorization cover storage, display, and redistribution, create a separate implementation plan for reviewed imports through the existing static-layer path. Preserve source attribution, provenance, original classifications, stated dataset date/version, and separate retrieval/import timestamps.
   - If the terms are absent, denied, ambiguous, or narrower than the planned use, keep the import blocked, retain current overlays, and record the limitation in project status.
6. Maintain separate concepts for `current_alert_level` (a PHIVOLCS bulletin value) and mapped spatial zones such as `PDZ`, `EDZ`, lava, lahar, pyroclastic, or base-surge classifications. A mapped zone is not a current alert status.

### Components and interfaces

- `docs/data-sources.md`: add the PHIVOLCS volcano-zone service inventory, exact source links, observed extents and fields, source terms, attribution rules, and clearance outcome. Distinguish remote raster overlays from local vectors.
- `docs/project-status.md`: keep Epic 3 partial and link the inventory/spec; keep volcano vector import blocked until terms and coverage are reviewed.
- `docs/superpowers/specs/2026-10-09-epic3-phivolcs-volcano-zone-coverage-design.md`: this design and its acceptance criteria.
- Existing raster display remains in `web/src/components/map/volcanoOverlays.ts`; no code change is in this slice.
- Future import, only after clearance: use the existing static-layer parser/service and `GET /api/v1/volcano-zones`. No volcano-zone import CLI currently exists; select whether to extend the existing fault importer or add a dedicated command in the follow-up implementation plan. No new endpoint or schema is designed here.

### Source acknowledgment requirements

Every future permitted PHIVOLCS volcano-zone display or dataset record must:

- Identify the source as **DOST-PHIVOLCS**.
- Link directly to the exact PHIVOLCS service layer or map product used.
- Identify the volcano and hazard-layer product and its source-stated date/version when available.
- Distinguish mapping/publication date, retrieval time, and `imported_at`.
- Preserve the original PHIVOLCS hazard classification and all additional terms/attribution conditions.

The existing raster overlays already link to the PHIVOLCS map service. This spec does not claim that raster attribution alone establishes a broader reuse license. No local vector is to be imported while permission remains unclear.

### Configuration

No new environment variables, settings, or dependencies.

### Error handling

- If metadata pages disagree, fail to load, omit a child-layer extent, or do not identify a source date, record that value as unknown and do not infer it.
- If an official map or metadata service cannot be reached with verified TLS, stop inspection and record the retrieval limitation; do not bypass TLS checks for runtime use.
- If reuse terms do not clearly cover the intended storage/display/redistribution, stop before geometry download, local storage, database import, or bundling.
- Keep the existing map overlays and locally loaded layers intact if a candidate source is incomplete or permission is unresolved.

### Data considerations

- Treat `PDZ`, `EDZ`, and hazard-specific classification fields as source classifications, not user-defined risk scores or alert levels.
- Retain original source attributes for any future authorized import; do not rename or reinterpret source fields in the data source record.
- Record source-layer extent, source feature count, valid accepted features within project bounds, API-returned features, and rendered coverage as distinct measures.
- No source feature count, geometry sample, or local PHIVOLCS vector import is included in this clearance-first slice.
- Do not call the candidate services nationally complete; their reported extents are partial and the metadata is not a completeness guarantee.

## Rollout

Use a dedicated Epic 3 branch after the PHIVOLCS fault-geometry source record. Land the layer inventory and clearance result before considering vector imports. Keep this as a separate plan from the PHIVOLCS fault-geometry work. The outstanding Epic 4 mobile runtime checks remain unverified and must not be marked complete by this documentation work.

## Files

- `docs/superpowers/specs/2026-10-09-epic3-phivolcs-volcano-zone-coverage-design.md` — define source inventory, attribution, and reuse gates.
- `docs/data-sources.md` — record observed candidate-layer metadata and terms after implementation.
- `docs/project-status.md` — track volcano-zone clearance and coverage status under Epic 3.
- `web/src/components/map/volcanoOverlays.ts` — reference only; existing attribution and map behavior remain unchanged.

## Testing Strategy

- No application code or source data is changed by the source-inventory/clearance slice.
- Review every source link, layer name, extent, and field against official PHIVOLCS REST metadata and portal instructions.
- Confirm the data-source record requires DOST-PHIVOLCS acknowledgment, exact source links, separate source/retrieval/import dates, and explicit reuse terms.
- Run `git diff --check`; run `python scripts\verify_structure.py` only if repository structure changes (not expected).
- Any later import requires importer unit tests, a permitted dry run, local database/API verification, and the relevant package checks from `CODING_STANDARDS.md`.

## Acceptance Criteria

- [ ] The reviewed vector candidates are documented by exact service/layer URL, hazard product, geometry type, metadata extent, and source-stated date when published.
- [ ] Extents are described as metadata bounds and are not used to claim full volcano, hazard, or national coverage.
- [ ] Danger-zone classes, hazard-specific mapped zones, remote raster renders, and current bulletin alert levels are clearly distinguished.
- [ ] Every future permitted PHIVOLCS data/display use requires explicit DOST-PHIVOLCS acknowledgment and a direct link to the actual product/layer.
- [ ] The source record states that attribution and public service access alone do not establish reuse permission.
- [ ] Terms covering storage, display, and redistribution are recorded, or vector import is explicitly marked blocked; no PHIVOLCS vector geometry is imported in this slice.
- [ ] Existing raster overlay links and behavior are unchanged.
- [ ] Epic 3 remains partial; Epic 4 runtime-flow status remains accurate.

## Out Of Scope (backlog)

- PHIVOLCS volcano-zone geometry import, pending reuse clearance.
- National polygon coverage and quality assessment beyond the metadata inventory.
- Changes to existing MapLibre raster overlays, visual styles, or per-layer map bounds.
- Any current alert-level, eruption bulletin, warning, or notification behavior.
- Landslide/InSAR work (Epic 6).

## Spec self-review

- No placeholders or incomplete sections remain.
- Every goal maps to an acceptance criterion.
- No source geometry, vector import, or map behavior change is permitted by this slice.
- Hazard zones and current alert levels remain distinct, and attribution does not substitute for permission.
- The source inventory is one bounded Epic 3 slice; implementation requiring reuse permission is a separate follow-up.

## Related documents

- Implementation plan: to be created after user review at `docs/superpowers/plans/2026-10-09-epic3-phivolcs-volcano-zone-coverage.md`.
- Prior fault-geometry source clearance: `docs/superpowers/specs/2026-10-09-epic3-phivolcs-fault-geometry-design.md`.
- Project status: `docs/project-status.md`.
- Data sources: `docs/data-sources.md`.
- Terminology: `docs/glossary.md`.
