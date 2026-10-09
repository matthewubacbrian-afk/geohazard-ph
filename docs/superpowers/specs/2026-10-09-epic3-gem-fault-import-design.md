# Epic 3 GEM Fault Import — Design

**Date:** 2026-10-09

## Problem

Epic 3's static-layer parser, database models, API, map layer, and import command
are implemented. The main branch does not include the ignored local GEM source
snapshot used by an earlier development session, so a clean checkout cannot
reproduce that import. Project status correctly avoids claiming nationally
complete fault coverage. No PHIVOLCS fault vectors or reuse permission are
available for this work.

## Goals

- Reproduce a GEM active-fault import from a pinned upstream commit using the
  existing importer.
- Preserve source URL, CC BY-SA 4.0 license, immutable dataset version, and input
  SHA-256 in a local import receipt.
- Validate the source in dry-run mode before replacing the local GEM fault snapshot.
- Verify the imported records through the existing faults API and document observed
  counts, version, and coverage limits.
- Keep raw source data and import receipts out of Git.

## Non-goals

- Claim that GEM provides nationally complete Philippine fault coverage.
- Import PHIVOLCS geometry without reviewed vector files and permission terms.
- Infer fault lines, create buffers, digitize PDFs, or add volcano-zone geometry.
- Change backend schemas, database migrations, API contracts, or map UI.
- Schedule automatic downloads or production refreshes.

## Context And Constraints

- `scripts/import_fault_lines.py` already accepts GeoJSON and shapefiles, validates
  provenance, supports `--dry-run`, and replaces one source snapshot through
  `backend/app/services/static_layers.py`.
- Import replacement is transactional and serialized per layer/source. Invalid or
  empty input is rejected before replacement.
- `docs/data-sources.md` identifies the GEM Global Active Faults database and its
  CC-BY-SA-4.0 license. Its repository has a public harmonized GeoJSON at
  `geojson/gem_active_faults_harmonized.geojson`.
- Pin the inspected upstream commit
  `56816508ad92fd6846dad1163b1c8c01376a2cd1` and record the full immutable raw URL:
  `https://raw.githubusercontent.com/GEMScienceTools/gem-global-active-faults/56816508ad92fd6846dad1163b1c8c01376a2cd1/geojson/gem_active_faults_harmonized.geojson`.
- The repository ignores `data/fault_lines/local/`; use that directory for the
  downloaded source and local receipt. Do not commit the 10 MB source file.
- The source license is described in the [GEM repository](https://github.com/GEMScienceTools/gem-global-active-faults).

## Alternatives Considered

1. **Wait for PHIVOLCS vectors before loading anything.** Rejected for this slice
   because an open-licensed source can exercise the implemented import path now;
   PHIVOLCS source coverage remains a separately gated follow-up.
2. **Import a moving `master` snapshot.** Rejected because it is not reproducible.
   Use the inspected immutable commit and file hash.
3. **Add new geometry or synthesize missing traces.** Rejected because the project
   requires reviewed source geometry and does not permit inferred hazard boundaries.

## Design

### Architecture and data flow

Download the pinned GeoJSON to the ignored local data directory. Calculate and save
its SHA-256 alongside source name, URL, license, commit, download date, and validation
results. Run the existing importer in dry-run mode first. After reviewing the result,
run the same import without `--dry-run`; the existing service replaces only the GEM
fault source in one database transaction. Query `/api/v1/faults` and compare returned
GEM record count, source provenance, geometry, and bounds with the validated input.

### Components and interfaces

- `scripts/import_fault_lines.py`: existing CLI; retain its argument contract.
- `backend/ingestion/sources/static_layers.py`: existing WGS84 geometry validation,
  Philippines-bounds filtering, identity selection, and provenance mapping.
- `backend/app/services/static_layers.py`: existing atomic source replacement.
- `data/fault_lines/local/gem-ph.metadata.json`: ignored local receipt containing
  `source`, `source_url`, `license_name`, `dataset_version`, `sha256`,
  `downloaded_at`, `source_feature_count`, `accepted_feature_count`, and
  `validation_status`.
- `docs/data-sources.md`, `docs/runbook.md`, and `docs/project-status.md`: record the
  verified snapshot and clearly state that it does not establish national coverage.
- No public API or response shape changes.

### Configuration

No new environment variables or dependencies. The importer uses the existing
PostGIS development database and backend virtual environment.

### Error handling

Stop before applying the import if download, checksum calculation, dry-run parsing,
geometry validation, or source-count review fails. Do not remove or replace the
existing GEM snapshot after any failed validation. Keep failures visible in the
terminal and do not suppress parser errors.

### Data considerations

The dataset version is the full pinned Git commit SHA. Compute SHA-256 from the
downloaded bytes. Report the actual source and accepted feature counts; do not
hard-code the count from an older snapshot. Existing WGS84/bounds and geometry
validation remain authoritative. The API's returned count and record provenance
must match the accepted dry-run snapshot. No raw or derived dataset is committed.

## Rollout

Use a dedicated Epic 3 feature branch. Download and validate the pinned source,
review the receipt, then apply it to a running local PostGIS database. Only after
the API verification succeeds, update the data-source, runbook, and status records.
This is a local development import and does not publish data to staging or production.

## Files

- `scripts/import_fault_lines.py` — reuse; modify only if the pinned GeoJSON reveals
  a concrete importer defect.
- `data/fault_lines/local/gem_active_faults_harmonized.geojson` — ignored local input.
- `data/fault_lines/local/gem-ph.metadata.json` — ignored local import receipt.
- `docs/data-sources.md` — record verified source commit, license, hash, and observed
  feature counts.
- `docs/runbook.md` — replace the generic Epic 3 example with reproducible pinned
  GEM commands and receipt verification.
- `docs/project-status.md` — record the verified GEM local-import state without
  marking the wider Epic nationally complete.

## Testing Strategy

- Run the existing static-layer importer unit tests from `backend/`.
- Run the dry-run import against the pinned source and retain its actual count and
  validation result in the local receipt.
- With local PostGIS available, run the apply import and query
  `GET /api/v1/faults`; confirm count, source, source URL, license, dataset version,
  imported timestamp, geometry type, and WGS84 coordinate bounds.
- Run the full backend test suite if importer code changes; run documentation and
  Git whitespace checks for docs-only changes.

## Acceptance Criteria

- [ ] The source is downloaded from the immutable URL at the pinned commit.
- [ ] The local receipt records the actual SHA-256 and source/accepted counts.
- [ ] Dry-run validation succeeds with at least one accepted fault and no invalid
  geometries.
- [ ] The applied local GEM snapshot matches the accepted dry-run count.
- [ ] The API returns records with the expected source, version, license, and valid
  WGS84 fault geometry.
- [ ] The source GeoJSON and receipt remain ignored by Git.
- [ ] Documentation records the snapshot and explicitly avoids a national
  completeness claim.

## Out Of Scope (backlog)

- PHIVOLCS fault vectors pending source files and reviewed permissions.
- Volcano hazard-zone vector selection and import.
- Production database import and deployment verification.
- UI updates and Epic 6 landslide/InSAR work.

## Related documents

- Implementation plan: to be created after review at
  `docs/superpowers/plans/2026-10-09-epic3-gem-fault-import.md`.
