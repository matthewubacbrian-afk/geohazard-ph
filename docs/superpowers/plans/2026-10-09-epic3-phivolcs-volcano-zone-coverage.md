# Epic 3 PHIVOLCS Volcano-Zone Coverage — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record PHIVOLCS volcano-zone service metadata, coverage limits, attribution, and reuse status without downloading or importing geometry before permission is clear.

**Architecture:** Add an evidence-based vector service inventory to `docs/data-sources.md`, then update the Epic 3 status row to point to that record. Keep existing PHIVOLCS raster overlays unchanged and distinguish them from local `VolcanoZone` vectors and current alert levels.

**Tech Stack:** Markdown documentation; Git diff validation.

**Spec:** `docs/superpowers/specs/2026-10-09-epic3-phivolcs-volcano-zone-coverage-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`.
- Acknowledge the source as DOST-PHIVOLCS and link to the exact service layer or map product.
- Do not treat public service access or attribution as reuse permission or an open license.
- Treat the Geomatics form and DUA/MOU process as an application route only; no request has been submitted and no permission has been granted.
- Do not download geometry, query feature counts, import/bundle vector data, change API behavior, or alter the existing raster overlays.
- Keep hazard-zone classes distinct from `current_alert_level`; keep Epic 3 partial and Epic 4 runtime verification unverified.
- Run `git diff --check` before commit. No package tests apply to documentation-only changes.

## Files And Responsibilities

- `docs/data-sources.md` — inventory the official hazard polygon candidates, observed metadata extents and fields, source acknowledgment, and clearance blocker.
- `docs/project-status.md` — reflect that PHIVOLCS volcano vectors remain unimported pending terms; link the inventory and spec.

### Task 1: Add the PHIVOLCS volcano-zone source inventory

**Files:**
- Modify: `docs/data-sources.md`

**Interfaces:**
- Official source terms: `https://maps.phivolcs.dost.gov.ph/`.
- Project Philippines bounds: `(116, 4, 128, 22)`.
- Existing web overlays are source-rendered images and retain the existing DOST-PHIVOLCS attribution.

- [x] **Step 1: Add direct source references and metadata-only coverage table**

Add records for these official layer/service candidates:

| Layer or service | Hazard meaning | Geometry/CRS | Metadata extent (west, south, east, north) |
|---|---|---|---|
| `DangerZone/MapServer/0` | PDZ and EDZ | Polygon, EPSG:4326 | `120.8219, 10.2666, 124.2018, 14.1818` |
| `DangerZone_permanent/MapServer/0` | PDZ | Polygon, EPSG:4326 | `120.9660, 10.2675, 124.0992, 14.0431` |
| `DangerZone_extended/MapServer/0` | Extended danger zone | Polygon, EPSG:4326 | `120.9660, 10.2675, 124.0992, 14.0431` |
| `Pyroclastic_ohas/FeatureServer/0` | Pyroclastic density-current classes | Polygon, EPSG:4326 | `121.3494, 10.2473, 125.2667, 14.1944` |
| `Lava/MapServer/0` | Mapped lava-flow classes | Polygon, EPSG:4326 | `121.0088, 5.9622, 126.0874, 20.4895` |
| `VolcanoLahar_ohas/FeatureServer` | Lahar service; child layer metadata not verified | Geometry unknown at inspected service level; EPSG:4326 | `117.6710, 8.8235, 127.5621, 17.0364` |
| `BaseSurge_ohas/MapServer/0` | Base-surge zones | Polygon, EPSG:4326 | `120.8526, 13.8598, 121.1370, 14.1290` |

Link each exact service above. State that extents are metadata bounds, several are narrower than the project bounds, and they do not establish feature counts or complete mapped coverage. Record source date values as unobserved where feature-level values were not fetched.

- [x] **Step 2: Add classification, source acknowledgment, and reuse status**

Explain that danger-zone `PDZ`/`EDZ` classes and hazard-specific classes describe mapped geography, not current bulletin `current_alert_level`. State that the inventory used metadata only, so no feature geometry, service feature count, accepted-in-bounds count, or vector import is reported. Link the official Maps Portal and hazard-map instructions; record that they ask users to acknowledge DOST-PHIVOLCS and warn against unauthorized use, depiction, sale, or derivatives. State no open redistribution license was identified and reuse clearance is pending. Link the official Geomatics Services Request page and GGRDD Citizen's Charter; summarize the request form followed by applicable DUA/MOU and approval process for reference services, and state explicitly that this process has not been initiated and is not permission for storage/display/redistribution.

Confirm the documented clearance route is an application process, not a permission grant, and that no request or agreement is claimed. Mark the spec criterion for that addition complete.

Require every future permitted use to say `Source: DOST-PHIVOLCS`, link the exact layer/product, identify source-stated product dates separately from retrieval/import timestamps, and include any additional conditions. State existing remote raster overlays remain as rendered-map references and are distinct from local vectors; do not imply their attribution grants permission for new vector redistribution.

### Task 2: Reconcile Epic 3 project status

**Files:**
- Modify: `docs/project-status.md`

- [x] **Step 1: Update the Epic 3 row**

Record that official polygon candidates and their metadata extents are documented; no PHIVOLCS volcano vector has been imported; reuse permission remains unestablished; existing raster overlays are not local vector coverage; and the Epic remains partial. Link the new data-source subsection and this spec. Preserve the open Epic 4 runtime-flow check.

### Task 3: Review, validate, and commit

**Files:**
- Verify: `docs/data-sources.md`, `docs/project-status.md`

- [x] **Step 1: Review source links and terminology**

Confirm every service link is direct; all seven candidates are represented; unknown child-layer details remain explicitly unknown; source dates and feature counts are not inferred; acknowledgment and permissions remain separate; and no current alert status is inferred from zones.

- [x] **Step 2: Run whitespace validation**

Run:

```powershell
git diff --check
```

Expected: exit code 0 with no output.

- [x] **Step 3: Commit the documentation update**

```powershell
git add docs/data-sources.md docs/project-status.md docs/superpowers/plans/2026-10-09-epic3-phivolcs-volcano-zone-coverage.md
git commit -m "docs: record PHIVOLCS volcano zone coverage"
```

## Notes For The Executor

- This plan does not authorize or perform PHIVOLCS outreach.
- Any later vector import requires a separate plan after terms clearly cover the intended use.
- A future coverage analysis must distinguish service feature count, valid features accepted within project bounds, API-returned records, and displayed coverage.
- Mobile runtime checks remain an Epic 4 open item; this Epic 3 documentation work does not close them.
