# Epic 6 InSAR Pilot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete a bounded, source-documented Philippine InSAR feasibility pilot and deliver a go/no-go recommendation without adding an operational hazard layer.

**Architecture:** This is a research workflow, not an application feature. The initial execution reviewed published candidate evidence and queried public NISAR and Sentinel-1 archive metadata at the Naga event centroid. It stopped before image access or processing because exact source-area geometry, reconciled study inputs, and a current independent reference were not established. The report records this bounded result and gates any later processing trial; raw satellite products remain outside Git.

**Tech Stack:** ASF Vertex / DAAC catalog, ASF HyP3 only if eligible under its no-cost Basic allowance, NISAR data products, Sentinel-1 IW SLC, published Philippine Engineering Journal and other cited studies, Markdown.

**Spec:** `docs/superpowers/specs/2026-10-16-epic6-insar-feasibility-design.md`

## Global Constraints

- Follow `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/data-sources.md`, `docs/git-workflow.md`, and the approved Epic 6 feasibility spec.
- Conventional Commits; imperative, lowercase after type.
- Keep original satellite products, study datasets, GNSS data, and derived rasters outside Git; never add large source files to the repository.
- Do not send data-access requests to agencies or authors, sign up for accounts, expose credentials, buy credits, or submit paid jobs.
- Catalog searches must record query date and parameters, product maturity, acquisition and processing dates, coverage, orbit, and a stable source identifier/URL.
- Do not imply acquisition availability until the catalog returns matching scenes; do not interpret missing data as zero displacement.
- Any InSAR measurement is LOS displacement with research-grade and quality caveats. It is not an alert, forecast, slope-safety evaluation, or official advisory.
- Verification: source/link review, `git diff --check`, and `python scripts/verify_structure.py`. No application test suite applies unless executable pilot code is added under a separately reviewed scope.

---

### Task 1: Verify Philippine reference sites and validation provenance

**Files:**
- Create: `docs/epic6-insar-pilot-report.md`
- Reference: `https://www.journals.upd.edu.ph/index.php/pej/article/view/9482`
- Reference: `https://isprs-archives.copernicus.org/articles/XLVIII-5-W4-2025/213/2026/isprs-archives-XLVIII-5-W4-2025-213-2026.html`
- Reference: `https://pure.kaist.ac.kr/en/publications/satellite-based-monitoring-of-an-open-pit-mining-site-using-senti/`

**Interfaces:**
- Consumes: published case-study methods, locations, observation intervals, GNSS/field references, and reuse conditions.
- Produces: a report table with candidate site, evidence source, reported period, sensor/method, independent reference, reference availability, reuse status, and selection decision.

- [x] **Step 1: Review Antipolo reference evidence.** The abstract and reported 0.83 LOS correlation were recorded; full text, footprint, acquisitions, GNSS series, and reuse terms remain unavailable. Do not treat this as a reproducible benchmark.
- [x] **Step 2: Review the Naga comparator.** The ISPRS Naga retrospective study was reviewed and its reported field-crack comparison, scene count, dates, inconsistencies, and missing point coordinate were recorded. Toledo was not selected for this bounded screen.
- [x] **Step 3: Select the bounded screen site.** Naga was selected for metadata screening from the published study. The event centroid was used only as a reproducible catalog point, not as source-area geometry or a validated pilot AOI.
- [x] **Step 4: Confirm report provenance.** Stable links, citations, access date `2026-10-16`, and the independent-review limitation are in the report.

**Commit:** `docs: document epic 6 insar pilot sites`

---

### Task 2: Search ASF archives for site acquisition coverage

**Files:**
- Modify: `docs/epic6-insar-pilot-report.md`
- Reference: `https://nisar-docs.asf.alaska.edu/vertex/`
- Reference: `https://search.asf.alaska.edu/`

**Interfaces:**
- Consumes: site polygons or documented study-area bounds approved in Task 1.
- Produces: one scene-inventory table per selected site, with mission, product, maturity, relative orbit/track/frame, acquisition interval, processing version, spatial intersection, nominal/observed revisit, and archive URL.

- [x] **Step 1: Query Sentinel-1 history.** The public metadata query returned 34 descending Sentinel-1B IW SLC records on relative orbit 61 at the event centroid from 2017-08-12 through 2018-09-12. Exact record details are in the repeatable API query. Source-scarp overlap, scene-pair baselines, and quality were not evaluated; the paper reports 35 scenes, which remains unresolved.
- [x] **Step 2: Query NISAR current coverage.** The public query returned 26 PROVISIONAL GUNW records in three orbit groups, with collection and processor maturity recorded in the report. Search geometry was the event centroid only.
- [x] **Step 3: Distinguish observation cadence from product availability.** Product acquisition intervals were recorded; the records are not evidence of usable cadence or a validated time series. No pixel-level usability was inferred.
- [x] **Step 4: Record catalog evidence.** Query date, parameters, point geometry, counts, and direct API links are in the report.

**Commit:** `docs: record epic 6 insar archive coverage`

---

### Task 3: Decide whether a bounded processing trial can proceed

**Files:**
- Modify: `docs/epic6-insar-pilot-report.md`
- Reference: `https://hyp3-docs.asf.alaska.edu/guides/insar_product_guide/`
- Reference: `https://hyp3-docs.asf.alaska.edu/guides/burst_insar_product_guide/`
- Reference: `https://hyp3-docs.asf.alaska.edu/using/authentication/`

**Interfaces:**
- Consumes: verified candidate pairs, NISAR product metadata, the reference data availability findings, and ASF service terms.
- Produces: a processing decision record with input IDs, pair rationale, method/product type, expected resolution, free-credit estimate, credentials requirement, expected queue/retention constraints, and a `proceed`, `defer`, or `stop` result.

- [ ] **Step 1: Identify one Sentinel-1 comparison pair or stack.** Deferred: resolve the paper's inputs and establish a source-area AOI and independent reference first.
- [ ] **Step 2: Identify NISAR analysis-ready products.** Prefer a documented GUNW or other appropriate product only after its product guide confirms that it supports the intended LOS displacement comparison and its maturity is recorded. Do not combine BETA and PROVISIONAL data in one time series without explicitly accounting for processing-version changes.
- [ ] **Step 3: Estimate processing cost and access.** Confirm HyP3 Basic credit requirements from the current official credit table before submitting any job. If Earthdata authentication, user-specific account state, or any paid credits are required, stop and document the requirement; do not request credentials or submit paid processing.
- [x] **Step 4: Gate the processing trial.** Stopped at metadata feasibility. No source scenes were downloaded and no HyP3 job was submitted because the study inputs, source-area AOI, validation target, and no-cost account allowance were not confirmed. No paid credits were used.

**Commit:** `docs: record epic 6 insar processing feasibility`

---

### Task 4: Assess quality and compare with independent observations

**Files:**
- Modify: `docs/epic6-insar-pilot-report.md`
- Modify: `docs/data-sources.md`
- Modify: `docs/project-status.md`

**Interfaces:**
- Consumes: candidate processing outputs or a documented no-processing stop, plus published/field/GNSS references whose access and time interval are verified.
- Produces: quality/validation results, a per-site go/no-go decision, updated source notes, and an accurate Epic 6 status entry.

- [x] **Step 1: Report quality evidence.** No image products were processed; pixel quality, coherence, masks, layover/shadow, atmospheric and unwrapping behavior, and displacement are marked not evaluated in the report.
- [ ] **Step 2: Compare only time-aligned references.** Compare LOS trends with the Antipolo GNSS or cited Sentinel-1 outputs only when the exact intervals, LOS projection, and reference time series are accessible. Keep published claims distinct from measurements independently reproduced in this pilot.
- [x] **Step 3: Issue the bounded recommendation.** Remain research-only and proceed only to a reproduction-design review; no go decision for processing or a user-facing layer was reached.
- [x] **Step 4: Update source and project records.** Data-source notes and project status now link to and accurately summarize the metadata-only result.

**Commit:** `docs: report epic 6 insar pilot findings`

---

### Task 5: Verify and hand off the pilot decision

**Files:**
- Verify: all files created or modified above.

- [ ] **Step 1: Check the source statements.** Reopen every cited primary source and verify dates, product maturity, sensor, reference period, access, and licensing statements against the report.
- [ ] **Step 2: Check the documentation diff.** Run `git diff --check` and `python scripts/verify_structure.py` before handoff.
- [ ] **Step 3: Check artifact hygiene.** Run `git status --short`; ensure no product rasters, source scenes, credentials, local caches, or generated processing outputs are staged.
- [ ] **Step 4: Summarize the decision.** Report which sites were evaluated, the archive evidence, whether processing ran, what validation was possible, and the exact reasons for go/defer/stop. Do not recommend UI work unless the multi-site validation gate is satisfied.

## Notes for the executor

- Task 1 precedes archive searches because AOIs and comparison periods must come from source-documented evidence. Task 2 precedes all processing.
- The Antipolo journal abstract reports 184,253 persistent-scatterer points and LOS correlation of 0.83 with a stationary GNSS receiver, but this plan requires the full paper and source time series to be checked before treating that as a reproducible validation benchmark.
- NISAR launched after the 2023 Antipolo study; its current products cannot reproduce that historical time period. A direct NISAR comparison requires independent observations over its own acquisition period.
- Do not invent geometry from susceptibility products. Do not import MGB or PHIVOLCS landslide boundaries absent verified reuse permission.
- NISAR's data maturity and ASF processing terms can change. Recheck official sources on the execution date and record the date accessed.
- This research plan does not authorize credit purchases, requests to agencies/authors, account creation, or user-facing publication of any displacement result.
