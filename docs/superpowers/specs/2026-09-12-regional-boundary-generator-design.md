# Philippine Region Boundary Generator - Design

**Date:** 2026-09-12

## Problem

`web/src/data/philippine-regions.json` is a generated derivative of the
geoBoundaries Philippines ADM1 dataset, but the repository does not contain the
transformation that produced it. A future tolerance change or source refresh
would therefore require manually reconstructing the process and could silently
change the browser asset. The affected flow is the web risk overlay and the
source-data documentation in `docs/data-sources.md`.

## Goals

- Provide one command that fetches the pinned geoBoundaries ADM1 source,
  simplifies it, normalizes region names, and rewrites the web asset.
- Make simplification tolerance and source URL configurable without changing
  the script.
- Keep the generated asset as a WGS84 GeoJSON `FeatureCollection` with one
  `region_name` property per feature and the expected 17 regions.
- Target approximately 200 KB while emitting a warning, without failing, when
  the generated output exceeds 220 KiB.
- Write provenance containing the source identity, license, ready-to-use
  attribution string, generation settings, output size, feature count, and
  vertex count for every region.
- Verify that the same source and tolerance produce byte-for-byte identical
  output.

## Non-goals

- Do not change the map overlay's region matching behavior, including the
  existing `Palawan` to `Mimaropa` mapping.
- Do not add a runtime network dependency to the web application.
- Do not commit the raw geoBoundaries download.
- Do not implement general-purpose topology repair, reprojection, clipping, or
  administrative-boundary version discovery.
- Do not make the 220 KiB threshold a generation failure.

## Context And Constraints

- The source is geoBoundaries open ADM1 for the Philippines, boundary ID
  `PHL-ADM1-36201628`, representing 2020 and built July 5, 2023.
- The API metadata identifies the source as NAMRIA, PSA, and OCHA Philippines
  and licenses it under Creative Commons Attribution 3.0 Intergovernmental
  Organisations (CC BY 3.0 IGO).
- The pinned source GeoJSON URL is the media-backed GitHub URL for the commit
  referenced by the geoBoundaries API. The API endpoint remains the documented
  discovery/source URL, while the media URL avoids Git LFS pointer responses.
- The web package uses Node ESM and currently has no geometry simplification
  dependency. The generator should use only Node standard-library APIs so it
  can run after the existing web package install.
- Generated files must remain ASCII where practical, and source-data
  assumptions belong in `docs/data-sources.md`.
- Web tests use Vitest. Tests must not use live network access or depend on the
  process working directory.

## Alternatives Considered

### Use the geoBoundaries pre-simplified download

This avoids implementing simplification, but the tolerance and transformation
would be controlled outside the repository. It is rejected because the
requested reproducibility requires a configurable, checked-in simplification
step.

### Add a third-party GeoJSON simplification package

A package could provide a battle-tested implementation, but it adds dependency
and version-locking overhead for a small offline transformation. It is rejected
in favor of a focused standard-library implementation with direct tests.

### Implement simplification locally

The generator will implement Douglas-Peucker simplification for coordinate
rings, preserving each ring's closure and applying the same deterministic
numeric and JSON serialization rules on every run. This keeps the command
portable and makes tolerance behavior explicit, so it is the chosen approach.

## Design

### Architecture And Data Flow

```text
geoBoundaries API metadata
          |
          v
 pinned source GeoJSON -> validate FeatureCollection and 17 features
          |
          v
 normalize shapeName -> region_name
          |
          v
 simplify Polygon/MultiPolygon rings at tolerance
          |
          v
 count vertices + serialize deterministically
          |
          +--> web/src/data/philippine-regions.json
          +--> docs/data-sources.md provenance block
```

The default source URL is the pinned media-backed GeoJSON URL for
`PHL-ADM1-36201628`. The generator may accept a source URL override for
refreshes and local fixture testing. The default tolerance is `0.01` degrees
and coordinates are quantized to three decimal places, producing an output
under 500 KB while retaining small-region detail; the exact settings and
result are recorded in provenance.

### Components

- `web/scripts/generate-regions.mjs`: CLI entry point, network fetch, input
  validation, geometry transformation, deterministic serialization, output
  writing, warning logging, and provenance update.
- `web/scripts/generate-regions.test.mjs`: Vitest tests for pure geometry and
  serialization behavior, using local fixtures or in-memory source objects.
- `web/package.json`: `generate:regions` and any focused generator test command.
- `web/src/data/philippine-regions.json`: regenerated browser asset.
- `docs/data-sources.md`: generated provenance note and reusable attribution.

### Interfaces

The script will expose these testable functions from the ESM module:

```js
simplifyGeoJson(source, tolerance) -> FeatureCollection
countFeatureVertices(feature) -> number
serializeGeoJson(collection) -> string
buildProvenance({ sourceMetadata, sourceUrl, tolerance, outputBytes, features }) -> string
```

The CLI accepts:

```text
node scripts/generate-regions.mjs [--source=<URL>] [--tolerance=<number>]
```

Defaults are used when options are omitted. Invalid URLs, non-positive or
non-finite tolerances, malformed GeoJSON, missing `shapeName`, unsupported
geometry types, non-closed rings, or a feature count other than 17 cause a
non-zero exit with a concise error.

Every generated feature has exactly this property shape:

```json
{"region_name":"<source shapeName>"}
```

The attribution string emitted into the provenance note will be:

```text
Philippine administrative boundaries © geoBoundaries, sourced from NAMRIA, PSA, and OCHA Philippines, licensed under CC BY 3.0 IGO.
```

The provenance note will record, at minimum:

- boundary ID, represented year, build date, source URL, and API URL;
- license name and the ready-to-use attribution string;
- generation UTC date, simplification tolerance, and generator path;
- output byte size, feature count, total vertex count, and a table of region
  names with per-region vertex counts.

### Configuration

- `--source`: optional source GeoJSON URL; defaults to the pinned source URL.
- `--tolerance`: optional coordinate-space Douglas-Peucker tolerance; defaults
  to `0.01` degrees, documented in provenance.
- Coordinates are quantized to three decimal places after simplification,
  approximately 111 meters at the equator and finer than one kilometer at
  Philippine latitudes.
- `REGION_ASSET_WARNING_BYTES`: optional environment override for the warning
  threshold, defaulting to `225280` bytes (220 KiB). This is a diagnostic
  threshold only and never changes the exit status.

No web runtime environment variable or API setting is added.

### Error Handling

Network failures, non-OK responses, invalid JSON, failed GeoJSON validation,
and invalid CLI configuration terminate generation before replacing either
output file. Output is written through temporary files and renamed only after
all validation and serialization completes. A size warning is written to
stderr when output exceeds the threshold, while the command still exits zero.

### Data Considerations

Coordinates remain WGS84 longitude/latitude pairs. Douglas-Peucker operates in
the source coordinate space and never reprojects or clips geometries. Rings
remain closed after simplification, and each ring retains enough coordinates
to represent a valid polygon ring. Feature order, region-name order, numeric
formatting, and JSON key order are stable so identical source bytes and
tolerance produce identical output bytes.

## Rollout

1. Add and test the generator's pure transformation and serialization logic.
2. Run the generator against the pinned geoBoundaries source to regenerate the
   asset and provenance note.
3. Run the focused generator tests, web test suite, web build, and repository
   structure verification.

This change has no database migration, API rollout, feature flag, or runtime
network behavior.

## Files

- `web/scripts/generate-regions.mjs` - generator CLI and pure transformation
  helpers.
- `web/scripts/generate-regions.test.mjs` - deterministic generator tests.
- `web/package.json` - generator command and test wiring.
- `web/src/data/philippine-regions.json` - regenerated simplified asset.
- `docs/data-sources.md` - source provenance, attribution, settings, and
  measured output statistics.

## Testing Strategy

### Web generator tests

- Simplification reduces vertices at a known tolerance while preserving ring
  closure and geometry type.
- `shapeName` is normalized to the sole `region_name` property.
- Vertex counts are correct for Polygon and MultiPolygon features.
- Serialization is stable for repeated calls with the same source and
  tolerance.
- The determinism/idempotency test compares the complete serialized output
  strings byte-for-byte for two identical source+tolerance runs.
- Invalid source shape, unsupported geometry, and invalid tolerance are
  rejected.

### Package verification

- Run `npm test` from `web/`.
- Run `npm run build` from `web/`.
- Run `node scripts/generate-regions.mjs` from `web/` and confirm the warning
  behavior, output size, 17 features, and per-region vertex counts.
- Run `python scripts\\verify_structure.py` from the repository root.

## Acceptance Criteria

- [ ] `npm run generate:regions` fetches the pinned geoBoundaries source and
  rewrites the asset and provenance note in one command.
- [ ] `--tolerance` and `--source` override their documented defaults.
- [ ] The generated asset has 17 WGS84 features and only `region_name` in each
  feature's properties.
- [ ] The default output is approximately 200 KB and provenance records the
  actual byte size.
- [ ] Output above 220 KiB logs a warning but exits successfully.
- [ ] Provenance records every region's vertex count and total vertex count.
- [ ] Provenance contains the exact ready-to-use CC BY 3.0 IGO attribution
  string.
- [ ] Two runs with identical source and tolerance produce identical output
  bytes.
- [ ] Focused tests, `npm test`, `npm run build`, and structure verification
  pass.

## Out Of Scope (backlog)

- Automatic polling for new geoBoundaries dataset versions.
- A general geometry validation/repair library.
- Visual regression testing of the map overlay at every tolerance.
- Runtime display changes for attribution beyond the documented provenance
  string and the existing source-data documentation.

---

## Spec self-review

- No `TBD`, `TODO`, or unfinished sections remain.
- The target-size warning is explicitly advisory and does not conflict with
  the acceptance criteria.
- The attribution requirement is represented in both the design interface and
  acceptance criteria.
- The determinism requirement specifies byte-for-byte output and appears in
  the interfaces, testing strategy, and acceptance criteria.
- The scope fits one web implementation plan without database or API changes.

## Related documents

- Implementation plan: to be created as `docs/superpowers/plans/2026-09-12-regional-boundary-generator.md`.
- `docs/data-sources.md`
- `docs/testing-standards.md`
- `docs/glossary.md`
- `CODING_STANDARDS.md`