# Philippine Region Boundary Generator - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Philippine region GeoJSON asset reproducible from the pinned geoBoundaries source with deterministic simplification, provenance, attribution, and size/vertex verification.

**Architecture:** Keep the generator self-contained in the web package. Pure GeoJSON transformation and serialization helpers will be exported for Vitest, while the CLI owns fetching, validation, file replacement, provenance updates, and advisory size logging. Regenerate the checked-in asset only after focused tests pass.

**Tech Stack:** Node.js ESM, standard-library `fetch` and filesystem APIs, GeoJSON, Vitest, TypeScript/Vite build.

**Spec:** `docs/superpowers/specs/2026-09-12-regional-boundary-generator-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, and `docs/testing-standards.md`.
- Keep the generator dependency-free and avoid live network access in tests.
- Preserve WGS84 coordinate order, closed rings, stable feature order, and sole `region_name` properties.
- Use `225280` bytes as the default advisory warning threshold; never fail solely for size.
- Do not commit raw source downloads, build output, credentials, or unrelated worktree changes.
- Run focused tests before regeneration, then `npm test`, `npm run build`, `python scripts\verify_structure.py`, and `git diff --check`.

### Task 1: Add deterministic geometry helpers and tests

**Files:**
- Create: `web/scripts/generate-regions.mjs`
- Create: `web/scripts/generate-regions.test.mjs`

**Interfaces:**
- `simplifyGeoJson(source, tolerance)` returns a normalized `FeatureCollection`.
- `countFeatureVertices(feature)` returns the number of coordinate pairs in a feature.
- `serializeGeoJson(collection)` returns stable compact JSON text ending in one newline.
- `buildProvenance({ sourceMetadata, sourceUrl, tolerance, outputBytes, features, generatedAt })` returns the Markdown provenance block.

- [ ] **Step 1: Write failing tests** for Polygon and MultiPolygon simplification, ring closure, `shapeName` normalization, vertex counts, stable serialization, byte-for-byte repeated output, and invalid tolerance/input.
- [ ] **Step 2: Run `npm test -- scripts/generate-regions.test.mjs`** from `web/` and confirm the tests fail because the generator module does not yet exist.
- [ ] **Step 3: Implement validation, Douglas-Peucker simplification, deterministic numeric serialization, and provenance formatting using only Node standard-library APIs.
- [ ] **Step 4: Run the focused test command again and verify it passes.

### Task 2: Add CLI, file generation, and package command

**Files:**
- Modify: `web/scripts/generate-regions.mjs`
- Modify: `web/package.json`
- Modify: `docs/data-sources.md`

**Interfaces:**
- CLI: `node scripts/generate-regions.mjs [--source=<URL>] [--tolerance=<number>]`.
- Package script: `npm run generate:regions`.
- Defaults use the pinned media-backed geoBoundaries GeoJSON URL, `0.01`-degree tolerance, three-decimal coordinate quantization, and `REGION_ASSET_WARNING_BYTES=225280`.

- [ ] **Step 1: Add tests for CLI argument parsing, non-OK fetch handling, advisory over-size warning, and provenance attribution text.
- [ ] **Step 2: Run the focused tests and verify the new cases fail before CLI implementation.
- [ ] **Step 3: Implement fetch/JSON validation, 17-feature validation, temporary-file writes, provenance replacement, and warning logging without replacing outputs after a failed validation.
- [ ] **Step 4: Add the `generate:regions` npm script and the generated provenance section in `docs/data-sources.md`.
- [ ] **Step 5: Run the focused tests and verify they pass.

### Task 3: Regenerate and verify the checked-in asset

**Files:**
- Modify: `web/src/data/philippine-regions.json`
- Modify: `docs/data-sources.md`

- [ ] **Step 1: Run `npm run generate:regions` from `web/` against the pinned source.
- [ ] **Step 2: Run the generator a second time with identical source and tolerance and compare asset hashes byte-for-byte.
- [ ] **Step 3: Inspect feature count, property keys, total bytes, and every region's vertex count; confirm output is near 200 KB and any warning is advisory.
- [ ] **Step 4: Run `npm test` and `npm run build` from `web/`.
- [ ] **Step 5: Run `python scripts\verify_structure.py` and `git diff --check` from the repository root.

## Notes for the executor

- The live media-backed source is permitted under CC BY 3.0 IGO; do not save its raw download in the repository.
- Use a fixed generation timestamp in unit tests so provenance tests remain deterministic; the real CLI may record the current UTC date in the checked-in provenance note.
- The ready-to-use attribution string is: `Philippine administrative boundaries © geoBoundaries, sourced from NAMRIA, PSA, and OCHA Philippines, licensed under CC BY 3.0 IGO.`
- Do not commit during execution unless explicitly requested by the user.