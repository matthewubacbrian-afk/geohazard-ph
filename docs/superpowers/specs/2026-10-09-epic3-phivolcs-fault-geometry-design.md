# Epic 3 PHIVOLCS Fault Geometry Clearance — Design

**Date:** 2026-10-09

## Problem

Epic 3 currently serves a locally verified GEM fault snapshot, but the project has not verified PHIVOLCS fault geometry reuse rights or national coverage. A current PHIVOLCS ArcGIS REST service exposes a polyline layer named `AF_2025_asofJanuary` with GeoJSON query support. PHIVOLCS's Maps Portal requires source acknowledgment and warns against unauthorized use and sale of its products or derivatives. Public access to the service alone does not establish permission for GeoHazard PH to copy, store, or redistribute that geometry.

The existing status and source documents correctly state that PHIVOLCS geometry and permission remain unresolved. This slice must determine what may be used, preserve required acknowledgment, and avoid an unauthorized import.

## Goals

- Record the PHIVOLCS fault service candidate, layer name, source URL, observed schema, stated date, and known coverage limits in project documentation.
- Compare a permitted sample or service metadata with the verified GEM snapshot to understand coverage and distinguish source differences without presenting either source as nationally complete.
- Establish a documented reuse basis before copying PHIVOLCS geometry into GeoHazard PH's database, web bundle, or any redistributed dataset.
- Require explicit PHIVOLCS acknowledgment and source linking anywhere PHIVOLCS-derived geometry is shown or documented, with version and retrieval/import dates kept distinct.
- If reuse permission is unavailable or unclear, retain the GEM layer, record PHIVOLCS geometry as blocked pending clearance, and make no PHIVOLCS geometry import.

## Non-goals

- Import, mirror, or redistribute PHIVOLCS geometry before acceptable reuse terms are documented.
- Treat public REST access, an attribution notice, or the label `PHIVOLCS` as a license.
- Contact PHIVOLCS on the user's behalf without separate authorization.
- Digitize PDFs or raster maps, infer fault traces, buffer faults, or synthesize missing features.
- Replace or remove the existing GEM snapshot.
- Change API schemas, database models, map UI, ingestion schedules, or production data.
- Claim national fault completeness.

## Context And Constraints

- `docs/project-status.md` is the current epic/status register. Epic 3 is partial: the pinned GEM snapshot was imported locally and verified through the faults API; PHIVOLCS geometry, volcano zones, and national completeness remain unresolved.
- `docs/data-sources.md` records the verified GEM source and license and notes that the previously checked PHIVOLCS ActiveFault service count query failed. The newer candidate is `https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/ActiveFaultGeneric/MapServer/0`, layer `AF_2025_asofJanuary`.
- The candidate layer reports WGS84 (EPSG:4326), polyline geometry, GeoJSON query format, a maximum record count of 1,000, pagination support, and attributes including `afcodepk`, `segname`, `fccode`, `ttcode`, `ltcode`, `datemapped`, `scale`, `publishdate`, `creator`, `editor`, and geometry. Its stated snapshot name is January 2025; this is not a claim that the service is current in 2026.
- The service extent shown in its metadata does not cover all of the project's Philippines bounding box. Any spatial comparison must report actual observed extents and accepted feature counts, not infer completeness from the layer name.
- The PHIVOLCS Maps Portal at `https://maps.phivolcs.dost.gov.ph/` asks users to acknowledge DOST-PHIVOLCS and states that unauthorized use, depiction, or sale of its products or derivatives is prohibited. It also says maps can change as new information becomes available. These terms do not state an open license for redistribution.
- Required acknowledgment for any permitted use: identify `DOST-PHIVOLCS` as the source, link directly to the actual service or map used, name the layer/product and its stated version/date, record retrieval/import time separately, and reproduce any additional terms PHIVOLCS confirms. Do not call the data openly licensed or redistribute a derivative until permission terms support that use.
- Reuse the existing static fault import, provenance, validation, and API path only after the reuse gate is satisfied. Read `docs/data-sources.md`, `docs/glossary.md`, `CODING_STANDARDS.md`, and the Epic 3 GEM import spec before implementation.

## Alternatives Considered

1. **Import the public GeoJSON service immediately with attribution.** Rejected because source acknowledgment does not resolve the portal's restrictions on unauthorized use or derivatives.
2. **Continue using GEM and leave the PHIVOLCS question unexamined.** Rejected for this slice because it does not answer whether the official local source can be used; GEM remains the fallback if clearance is denied or unavailable.
3. **Digitize PHIVOLCS map PDFs to fill apparent gaps.** Rejected because digitization creates a derived dataset and would not avoid the same reuse question; it also risks interpreting cartographic traces without the source's GIS context.

## Design

### Architecture and data flow

This is a source-governance and documentation slice before it is an import feature:

1. Inspect the official ArcGIS REST metadata and, where terms permit, a small GeoJSON sample. Record the exact service/layer URL, response date, snapshot label, CRS, geometry type, fields, query/pagination behavior, feature count, and extent.
2. Compare the candidate's observed coverage and attributes with the pinned GEM snapshot. Report the result as a source comparison; do not treat differences as omissions or correctness findings without PHIVOLCS context.
3. Obtain a clear reuse basis from official published terms or written authorization that covers the planned storage, display, and redistribution of the geometry and derivatives. Keep the evidence and any conditions in the project source record. Do not send an inquiry on the user's behalf without separate authorization.
4. Apply the reuse gate:
   - If permission covers the planned use, define a follow-up import task that preserves source attribution, URL, source version, actual license/permission terms, retrieval time, and imported time, and uses the existing validated static-layer import path.
   - If permission is absent, denied, ambiguous, or does not cover redistribution, do not download/store/import geometry for project use. Record the blocker and continue serving GEM with its known coverage limitation.
5. Keep Epic 3 project status partial until source coverage and data stewardship are separately verified. This source clearance does not complete Epic 3 or imply national completeness.

### Components and interfaces

- `docs/data-sources.md`: record the official PHIVOLCS candidate endpoint and layer, the portal's acknowledgment/reuse terms, observed metadata, and the clearance outcome. Keep GEM's license and source record separate.
- `docs/project-status.md`: track this as the next Epic 3 source-clearance item after the remaining Epic 4 mobile runtime verification; maintain partial status until the fault-layer coverage claim is supported.
- `docs/superpowers/specs/2026-10-09-epic3-phivolcs-fault-geometry-design.md`: this spec and its acceptance record.
- Future implementation (only after clearance): reuse `scripts/import_fault_lines.py`, `backend/ingestion/sources/static_layers.py`, `backend/app/services/static_layers.py`, and `GET /api/v1/faults`. No new endpoint or data model is designed here.

### Source acknowledgment requirements

Every GeoHazard PH view or documentation entry that uses an authorized PHIVOLCS-derived geometry must:

- Say `Source: DOST-PHIVOLCS`.
- Link to the exact PHIVOLCS service or map product used.
- Identify `AF_2025_asofJanuary` (or the exact later layer/version actually imported).
- Show the dataset's stated version/date separately from the retrieval/import timestamp.
- Include any additional attribution or restrictions supplied in the written permission or official license.

If reuse permission is not established, documentation may identify the candidate source and quote/link its terms for research purposes, but must state that no PHIVOLCS geometry has been imported or redistributed. Acknowledgment is required but is not a substitute for permission.

### Configuration

No new environment variables, settings, or dependencies.

### Error handling

- Stop the source comparison if TLS validation fails, the endpoint returns malformed/incomplete data, pagination cannot be completed, or counts/extent cannot be verified. Report the exact limitation; do not bypass TLS verification for runtime use.
- Stop before any geometry download for project redistribution when terms are unclear. Do not infer permission from successful REST queries.
- Preserve the current GEM snapshot if the candidate fails validation or clearance.

### Data considerations

- Treat `AF_2025_asofJanuary` as the source's stated layer/version string, not a retrieval date or proof of freshness.
- Preserve source identifiers and original source properties if later authorized. Use the existing fallback content hash only when the source has no stable feature identifier.
- Retain WGS84 coordinate order and source geometry type. Do not clip, simplify, or edit traces unless permission explicitly covers that derivative and the transformation is documented.
- Keep service feature counts, Philippine-bounds accepted counts, and rendered counts distinct.
- Do not record a license name until an actual license or permission instrument identifies it.

## Rollout

Use a dedicated Epic 3 feature branch. Land the source and permissions record first. A later import change requires this clearance outcome and its own reviewed implementation plan; it must not be combined with unrelated volcano-zone work. The Epic 4 runtime smoke remains the preceding verification item in the project sequence and may only be marked complete with actual runtime evidence.

## Files

- `docs/superpowers/specs/2026-10-09-epic3-phivolcs-fault-geometry-design.md` — define the clearance-first scope and mandatory source acknowledgment.
- `docs/data-sources.md` — add observed official source metadata and the permission decision when established.
- `docs/project-status.md` — track the Epic 3 source-clearance state and its dependency on Epic 4 runtime verification.
- Future import files are intentionally not changed by this clearance spec.

## Testing Strategy

- No application code or data import is part of this source-clearance slice.
- Review links and metadata against official PHIVOLCS pages and the exact service layer.
- Verify the documentation states both that PHIVOLCS is acknowledged as the source and that acknowledgment alone does not grant reuse permission.
- Run `git diff --check`; run `python scripts\verify_structure.py` if repository structure changes (not expected).
- Any future import implementation must run the backend static-layer tests, importer dry run, local database/API verification, and full relevant package checks defined in `CODING_STANDARDS.md` and `docs/testing-standards.md`.

## Acceptance Criteria

- [ ] The official source record identifies DOST-PHIVOLCS, the exact REST layer URL, `AF_2025_asofJanuary`, observed metadata, and the date of inspection.
- [ ] The comparison plan distinguishes layer extent, source feature count, accepted Philippines-bounds count, and map display count.
- [ ] The PHIVOLCS acknowledgment wording and direct source link are explicitly required for every permitted use.
- [ ] The project record states that attribution does not substitute for reuse permission and that no PHIVOLCS geometry may be redistributed before clearance.
- [ ] Permission terms covering storage, display, and redistribution are recorded, or the work is explicitly marked blocked and no PHIVOLCS geometry is imported.
- [ ] GEM remains available as the current fault reference layer and Epic 3 remains partial absent verified coverage evidence.
- [ ] No PHIVOLCS raw or derived geometry is committed as part of this clearance-first spec.

## Out Of Scope (backlog)

- Volcano-zone source clearance and coverage review, to follow this PHIVOLCS fault-geometry slice.
- PHIVOLCS geometry import, pending reuse clearance.
- National completeness analysis across fault datasets.
- Mobile runtime verification in an Android emulator/device or iOS simulator; already tracked under Epic 4 and requires suitable runtimes.
- Epic 6 landslide and InSAR work.

## Spec self-review

- No placeholders or incomplete sections remain.
- Each goal maps to an acceptance criterion.
- No service import is allowed before permissions are clarified; acknowledgments are explicitly required but not treated as authorization.
- The spec is a single source-clearance slice and defers implementation requiring a later authorized reuse decision.

## Related documents

- Implementation plan: to be created only after user review and clearance-scope approval at `docs/superpowers/plans/2026-10-09-epic3-phivolcs-fault-geometry.md`.
- Prior Epic 3 import: `docs/superpowers/specs/2026-10-09-epic3-gem-fault-import-design.md`.
- Project status: `docs/project-status.md`.
- Data sources: `docs/data-sources.md`.
- Terminology: `docs/glossary.md`.
