# Epic 6 InSAR Pilot — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete a bounded, source-documented Philippine InSAR feasibility pilot and deliver a go/no-go recommendation without adding an operational hazard layer.

**Architecture:** This is a research workflow, not an application feature. First establish reproducible candidate sites and independent validation evidence, then query public NISAR and Sentinel-1 archive metadata, and only then assess whether a small no-cost processing trial is justified. Publish a report with scene provenance, quality gaps, validation limits, access/cost findings, and a recommendation; keep raw satellite products outside Git.

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

- [ ] **Step 1: Review Antipolo reference evidence.** Read the full UP Diliman Philippine Engineering Journal article and record its site footprint, Sentinel-1 acquisition dates/orbits, processing method, reported 0.83 LOS correlation, GNSS receiver location and time interval, and availability/reuse terms. Treat abstract-only details as unverified.
- [ ] **Step 2: Review two comparator candidates.** Read the ISPRS Naga retrospective study and the Toledo City mining-site study. Record the same fields, explicitly mark absent GNSS/field validation or reuse evidence as unavailable, and do not treat a published claim of precursory motion as a validated warning signal.
- [ ] **Step 3: Select the bounded pilot sites.** Choose Antipolo as the primary candidate only if its footprint and independent comparison can be reconstructed. Select no more than two additional sites from the reviewed studies only when geometry, source provenance, and a relevant independent reference are sufficient. Record rejected candidates and reasons.
- [ ] **Step 4: Confirm report provenance.** Add stable article links, full citations, access date `2026-10-16`, and a note that the report is an independent feasibility review, not a replication of the papers.

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

- [ ] **Step 1: Query Sentinel-1 history.** Search the Sentinel-1 IW SLC archive for each site's study interval and available historical/current dates. Record ascending and descending separately, exact scene IDs, dates, relative orbit, polarization, footprint overlap, and candidate repeat-pair temporal/spatial baselines.
- [ ] **Step 2: Query NISAR current coverage.** Search ASF for L-band products intersecting each site from 2026-06-17 onward. Record product type, maturity, track/frame, direction, dates, full/partial coverage, processing release, and whether the product is a mission-generated unwrapped interferogram or an input image product.
- [ ] **Step 3: Distinguish observation cadence from product availability.** Calculate observed gaps only from returned acquisitions. Report nominal mission cadence separately and note scenes that are absent, partial, provisional, or not usable for the intended time-series comparison.
- [ ] **Step 4: Record catalog evidence.** Include the query date, search geometry, date filters, product filters, scene count, and direct archive links in the report so a reviewer can repeat the search.

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

- [ ] **Step 1: Identify one Sentinel-1 comparison pair or stack.** Prefer the exact published Antipolo observation window if its scene IDs and comparison period are public. Otherwise choose one pair only when the paper's temporal window, orbit, and independent reference can be aligned; record why the selected pair is scientifically comparable.
- [ ] **Step 2: Identify NISAR analysis-ready products.** Prefer a documented GUNW or other appropriate product only after its product guide confirms that it supports the intended LOS displacement comparison and its maturity is recorded. Do not combine BETA and PROVISIONAL data in one time series without explicitly accounting for processing-version changes.
- [ ] **Step 3: Estimate processing cost and access.** Confirm HyP3 Basic credit requirements from the current official credit table before submitting any job. If Earthdata authentication, user-specific account state, or any paid credits are required, stop and document the requirement; do not request credentials or submit paid processing.
- [ ] **Step 4: Gate the processing trial.** Process no more than one site and one bounded Sentinel-1 stack through an already authorized no-cost service path. If no eligible public/no-cost path is available, stop after catalog feasibility and state that clearly. Keep downloaded source products in ignored local storage and record checksums and provider metadata, not the files, in the report.

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

- [ ] **Step 1: Report quality evidence.** For each actual product, report valid-pixel fraction, coherence/quality mask behavior, spatial coverage, temporal gaps, layover/shadow, atmospheric/unwrapping issues, LOS viewing geometry, processing version, and known limitations. If no products were processed, mark every metric `not evaluated`.
- [ ] **Step 2: Compare only time-aligned references.** Compare LOS trends with the Antipolo GNSS or cited Sentinel-1 outputs only when the exact intervals, LOS projection, and reference time series are accessible. Keep published claims distinct from measurements independently reproduced in this pilot.
- [ ] **Step 3: Issue the bounded recommendation.** Choose `go to a second research validation site`, `remain research-only`, or `stop`. A go decision requires reproducible data access and independent validation at more than one site, matching the approved spec. No single-site result authorizes an operational map layer.
- [ ] **Step 4: Update source and project records.** Record the source maturity, reuse/citation requirements, measured access/cost limits, and the report link in `docs/data-sources.md`; update Epic 6 status in `docs/project-status.md` only to the level supported by the completed evidence.

**Commit:** `docs: report epic 6 insar pilot findings`

---

### Task 5: Verify and hand off the pilot decision

**Files:**
- Verify: all files created or modified above.

- [ ] **Step 1: Check the source statements.** Reopen every cited primary source and verify dates, product maturity, sensor, reference period, access, and licensing statements against the report.
- [ ] **Step 2: Check the documentation diff.** Run `git diff --check` and `python scripts/verify_structure.py`; expected output is no whitespace errors and `All 140 expected scaffold paths exist.`
- [ ] **Step 3: Check artifact hygiene.** Run `git status --short`; ensure no product rasters, source scenes, credentials, local caches, or generated processing outputs are staged.
- [ ] **Step 4: Summarize the decision.** Report which sites were evaluated, the archive evidence, whether processing ran, what validation was possible, and the exact reasons for go/defer/stop. Do not recommend UI work unless the multi-site validation gate is satisfied.

## Notes for the executor

- Task 1 precedes archive searches because AOIs and comparison periods must come from source-documented evidence. Task 2 precedes all processing.
- The Antipolo journal abstract reports 184,253 persistent-scatterer points and LOS correlation of 0.83 with a stationary GNSS receiver, but this plan requires the full paper and source time series to be checked before treating that as a reproducible validation benchmark.
- NISAR launched after the 2023 Antipolo study; its current products cannot reproduce that historical time period. A direct NISAR comparison requires independent observations over its own acquisition period.
- Do not invent geometry from susceptibility products. Do not import MGB or PHIVOLCS landslide boundaries absent verified reuse permission.
- NISAR's data maturity and ASF processing terms can change. Recheck official sources on the execution date and record the date accessed.
- This research plan does not authorize credit purchases, requests to agencies/authors, account creation, or user-facing publication of any displacement result.
