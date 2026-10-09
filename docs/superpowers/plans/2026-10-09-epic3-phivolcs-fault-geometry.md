# Epic 3 PHIVOLCS Fault Geometry Clearance — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the PHIVOLCS fault geometry candidate, source acknowledgment, reuse terms, observed coverage limits, and clearance status without importing geometry before permission is clear.

**Architecture:** Make a source record in `docs/data-sources.md`, then reconcile the Epic 3 row in `docs/project-status.md` against that record. Keep the existing GEM source and import unchanged; this plan has no application-code, database, or dataset changes.

**Tech Stack:** Markdown documentation; Git diff validation.

**Spec:** `docs/superpowers/specs/2026-10-09-epic3-phivolcs-fault-geometry-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`.
- Preserve explicit PHIVOLCS source acknowledgment and direct source links.
- Attribution is required but does not establish permission to download, store, display, or redistribute geometry.
- Do not contact PHIVOLCS, download geometry, import data, commit source files, or describe the candidate as openly licensed.
- Keep Epic 3 partial; do not imply national fault-layer completeness.
- Do not mark Epic 4 mobile runtime verification complete without actual emulator/device or iOS simulator evidence.
- Run `git diff --check` before commit. No package tests apply because only Markdown changes are in scope.

## Files And Responsibilities

- `docs/data-sources.md` — record the official candidate service, observed metadata and extent, source acknowledgment, portal terms, clearance decision, and current limitations.
- `docs/project-status.md` — show Epic 3's PHIVOLCS source state and keep remaining Epic 4 runtime verification visible.

### Task 1: Record PHIVOLCS source and reuse terms

**Files:**
- Modify: `docs/data-sources.md`

**Interfaces:**
- Source candidate: `https://gisweb.phivolcs.dost.gov.ph/arcgis/rest/services/PHIVOLCS/ActiveFaultGeneric/MapServer/0`, layer `AF_2025_asofJanuary`.
- Official source terms: `https://maps.phivolcs.dost.gov.ph/`.
- Do not add a local license name unless an explicit license or written authorization establishes one.

- [x] **Step 1: Add the source record**

Document that metadata identifies the layer as polylines in EPSG:4326 with GeoJSON query format, max record count 1,000, pagination support, and the listed layer attributes. Record its metadata extent `(119.5151, 5.3655, 126.7414, 19.8674)` and the inspection date `2026-10-09`. State that this extent does not span the configured Philippines bounds `(116, 4, 128, 22)`.

- [x] **Step 2: State the attribution and clearance gate**

Require `Source: DOST-PHIVOLCS`, a direct link to the exact layer or map used, the layer/product name and source-stated date, and separate retrieval/import timestamps for every future permitted use. Summarize the Maps Portal's acknowledgment request and warning against improper depiction, unauthorized use, or sale of its products or derivatives. State that no open redistribution license was identified and that public REST access or attribution alone does not authorize import or redistribution.

- [x] **Step 3: Record current comparison limits**

Identify GEM as the current local reference with its existing recorded 155 intersecting features. Explain that this source review used metadata only: no PHIVOLCS geometry, service feature count, or accepted feature count was retrieved. Keep these measures distinct; any later permitted comparison must record source count, accepted count within project bounds, and display count separately.

### Task 2: Update the Epic 3 status record

**Files:**
- Modify: `docs/project-status.md`

**Interfaces:**
- Preserve the Epic 3 state as partial.
- Link to the PHIVOLCS source record and this clearance spec.
- Keep the PR #20 Epic 4 runtime check listed as open and unverified.

- [x] **Step 1: Reconcile the Epic 3 row**

Add that the official PHIVOLCS fault-layer candidate has been identified, its source is acknowledged, and reuse remains blocked pending terms that cover storage, display, and redistribution. State that no PHIVOLCS geometry has been imported and the existing GEM layer remains the local reference.

- [x] **Step 2: Preserve epic status boundaries**

Keep national completeness and volcano-zone data unresolved. Keep Android/iOS mobile runtime user-flow verification open under Epic 4; do not call a CI build a runtime-flow pass.

### Task 3: Validate and commit the documentation update

**Files:**
- Verify: `docs/data-sources.md`, `docs/project-status.md`

- [x] **Step 1: Review the complete documentation diff**

Confirm the exact source URLs and metadata, the DOST-PHIVOLCS acknowledgment requirement, the reuse restriction, the absence of any claimed open license, and the unchanged GEM/Epic 4 limitations.

- [x] **Step 2: Run whitespace validation**

Run from the repository root:

```powershell
git diff --check
```

Expected: exit code 0 with no output.

- [x] **Step 3: Commit the documentation record**

```powershell
git add docs/data-sources.md docs/project-status.md
git commit -m "docs: record PHIVOLCS fault source clearance"
```

## Notes For The Executor

- The task is a source-governance record, not a PHIVOLCS geometry import.
- Do not email or otherwise contact PHIVOLCS without separate user authorization.
- If PHIVOLCS later provides terms covering the intended reuse, create a separate import plan and retain the exact attribution and provenance requirements.
- Volcano-zone coverage remains the next distinct Epic 3 slice after this fault-geometry clearance record; do not combine it here.
