# Epic 6 InSAR Feasibility — Design

**Date:** 2026-10-16

## Problem

Epic 6 includes landslide and InSAR work, but the project has no deformation product, Philippine coverage assessment, processing workflow, validation evidence, or operational service. Displaying an unvalidated displacement raster could be mistaken for a local hazard measurement or warning. Before proposing a public map layer, the project needs a source-backed decision about whether and how satellite InSAR can support a bounded, non-operational Philippine pilot.

## Goals

- Compare Sentinel-1 and NISAR for a small Philippine landslide-monitoring feasibility pilot using official mission and archive documentation.
- Define the acquisition, product-maturity, processing, coherence, validation, access, cost, and latency checks that the pilot must pass.
- Recommend a bounded next step and state clear stop/go criteria for any later implementation spec.
- Preserve the product framing: an InSAR result is a research/monitoring measurement, not an early-warning authority, event forecast, or assurance of slope safety.

## Non-goals

- Build an InSAR ingestion or processing pipeline, backend endpoint, database model, or user-facing deformation overlay.
- Claim verified Sentinel-1 or NISAR acquisition availability or coherent coverage at any Philippine landslide site; this spec does not run a site-specific archive search.
- Establish an alert threshold, predict a failure, validate national landslide coverage, or replace field monitoring and official advisories.
- Select MGB or PHIVOLCS geometry for a deformation pilot without provenance and reuse review.

## Context And Constraints

- Epic 6 is currently tracked as deferred/stretch work in `docs/project-status.md`; Part 1's NASA susceptibility overlay is separate from displacement monitoring.
- The product must follow `CODING_STANDARDS.md`, the canonical terminology in `docs/glossary.md`, and the provenance/licensing rules in `docs/data-sources.md`.
- Current ASF documentation says NISAR L-band PROVISIONAL products are calibrated and partially validated, with broader validation and reprocessing still underway. Product maturity and acquisition coverage must be checked per scene when a pilot runs.
- ASF HyP3 supports on-demand Sentinel-1 InSAR from SLC pairs. This requires selecting suitable repeated acquisitions and interpreting line-of-sight (LOS) displacement and coherence; outputs are not ground-motion vectors or a stand-alone landslide diagnosis.
- The Philippines' vegetated, humid, mountainous terrain is a material feasibility risk for C-band repeat-pass coherence. NISAR L-band is a more promising candidate to evaluate, but does not remove decorrelation, atmospheric, geometric, or validation limits.
- This spec records a desk feasibility assessment only. No satellite scenes, local landslide inventory, ground-control observations, or site-level products were downloaded or evaluated.

## Alternatives Considered

1. **NISAR-first bounded pilot (recommended).** Evaluate L-band mission products over a few independently documented Philippine slow-moving landslide sites. Its longer wavelength is a useful hypothesis for vegetated slopes, its public archive and analysis-ready products lower the processing barrier, and a site-level pilot can test actual coverage and coherence. It still requires data-maturity review and ground validation.
2. **Sentinel-1-only pilot.** Use ASF HyP3 on-demand InSAR products and established workflows. This is a mature processing route with an accessible archive, but C-band's shorter wavelength raises a stronger coherence risk in dense vegetation; actual Philippine pairs and costs still need testing.
3. **Build a nationwide operational layer now.** This would create broad map coverage quickly in appearance, but no validated national time series, confidence model, verified landslide inventory, or operational support exists. Rejected as unsupported by current evidence and incompatible with the project's awareness-tool framing.

## Design

### Feasibility finding and recommendation

Proceed only with a research pilot specification after this document is reviewed. Make NISAR L-band the primary candidate and Sentinel-1 the comparison/fallback. Do not commit to a production overlay until a pilot demonstrates suitable repeated acquisitions, spatial coherence, interpretable LOS time series, independent site validation, repeatable product access, and an affordable operating path.

NASA/JPL describes NISAR as observing land and ice frequently, with planned 12-day interferometric observations; the ASF NISAR guide currently lists public L-band PROVISIONAL products beginning with acquisitions on 2026-06-17, calibrated and partially validated, and notes that broader validated reprocessing is still in progress. The mission's global observation plan makes Philippines coverage plausible but does not prove coverage for a particular slope, orbit, or date. The ASF Vertex archive must be queried for every pilot area and data maturity.

Sentinel-1 provides a comparison dataset with six-day nominal equatorial revisit for the two-satellite constellation. Actual local revisit and usable repeat-pair availability must be queried, rather than inferred from the nominal cadence. ASF HyP3 supports on-demand processing from Sentinel-1 IW SLC pairs and exposes products via Vertex/API/SDK. Basic processing has a monthly credit limit, Earthdata authentication, queue/service constraints, and temporary output retention; a pilot must measure its actual resource and access requirements before recurring use.

### Pilot protocol required by a later implementation plan

1. Select at most three Philippine slow-moving landslide sites with published or agency-documented location, dates, and independent evidence suitable for comparison. Record the source and reuse terms for each site. Do not invent a site boundary from a susceptibility raster.
2. Search ASF Vertex/DAAC for NISAR ascending/descending L-band products and Sentinel-1 IW SLC pairs covering each site. Record track/frame or relative orbit, acquisition dates, product type, maturity, processing version, geographic coverage, and observed/nominal revisit. Confirm products overlap the site and span a useful monitoring interval.
3. For NISAR, prioritize mission-provided geocoded unwrapped interferogram/time-series-relevant products where the archive documentation and available acquisitions support the intended calculation. For Sentinel-1, prototype a reproducible HyP3 burst or full-scene pair/stack. Record processing parameters, DEM, software/service versions, output resolution, credits, queue time, download expiry, and authentication requirements.
4. Evaluate valid-pixel fraction, coherence/quality masks, temporal gaps, layover/shadow, atmospheric artifacts, unwrapping failures, and LOS geometry. Preserve a `no usable measurement` result where coverage or quality fails; never interpolate it into apparent continuous coverage.
5. Compare candidate displacement trends with independent field or published measurements and source dates. Report LOS displacement and its observation interval, not slope-parallel motion unless a justified multi-geometry decomposition is available. Document uncertainty and disagreements.
6. A later go decision requires repeatable processing, successful independent validation at more than one site, a declared minimum quality gate, operationally acceptable archive latency/access/cost, source attribution and reuse terms, and domain review. Otherwise retain the work as research-only or stop.

### Product and user-facing constraints for any future UI spec

- Label any future product **Research-grade ground-motion estimate (LOS)** and name the satellite, source, acquisition interval, product maturity, and last data timestamp.
- Explain that the measurement is coarse relative to local slope conditions, only samples radar line-of-sight motion, can be unavailable or unreliable under vegetation/surface change and atmospheric or geometric effects, and is not a forecast, alert, or site safety assessment.
- Show quality/coverage gaps as unavailable; do not render no-data as zero motion.
- Credit NASA/ISRO and ASF for NISAR-derived data; credit ESA/Copernicus Sentinel-1 and ASF for Sentinel-1-derived products. Follow the exact citation and license terms for the products used.
- Keep the NASA landslide susceptibility overlay distinct: it is a coarse, informational susceptibility reference, not measured deformation.

### Interfaces, configuration, and errors

N/A for this feasibility spec: it adds no executable interface, endpoint, configuration setting, storage, or runtime error path. Those contracts require a separate implementation design after the pilot decision.

### Source-backed assessment

- ESA describes Sentinel-1's two-satellite constellation and six-day nominal equatorial revisit; the actual Philippine acquisition schedule still needs an archive search: [Sentinel-1 facts and figures](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Facts_and_figures).
- ASF documents the Sentinel-1 HyP3 InSAR workflow, SLC-pair selection, atmospheric and DEM error considerations, and its caution against drawing conclusions from one interferogram: [HyP3 InSAR product guide](https://hyp3-docs.asf.alaska.edu/guides/insar_product_guide/).
- ASF lists Burst InSAR processing options and output resolution (40–160 m depending on looks), and explains that C-band's 5.6 cm wavelength is more prone to decorrelation from surface changes than longer wavelengths: [Burst InSAR product guide](https://hyp3-docs.asf.alaska.edu/guides/burst_insar_product_guide/).
- ASF states HyP3 Basic's 8,000 monthly credits, Earthdata authentication requirement, service details, and the separate paid HyP3+ option: [HyP3 overview](https://hyp3-docs.asf.alaska.edu/) and [authentication](https://hyp3-docs.asf.alaska.edu/using/authentication/).
- NASA/JPL describes NISAR's planned 12-day interferometric observation interval, its use for landslide motion, and the need to compensate phase contributions before interpreting ground motion: [NISAR interferometry](https://science.nasa.gov/mission/nisar/interferometry/).
- The live ASF user guide identifies PROVISIONAL products as calibrated but partially validated, beginning 2026-06-17, and documents product availability and validation/reprocessing status: [NISAR data availability](https://nisar-docs.asf.alaska.edu/data-availability/availability-overview/) and [product overview](https://nisar-docs.asf.alaska.edu/products-overview/).
- NASA describes the NISAR L-band instrument and openly available ASF archive: [NISAR mission](https://science.nasa.gov/mission/nisar/). Open data availability does not by itself define reuse of any third-party site inventory used for validation.

## Rollout

This change is documentation-only. First review this feasibility recommendation. If approved, create a separate bounded pilot implementation plan/spec that runs archive searches and validates data for selected sites; only a successful pilot can justify a separate user-facing overlay design. No live layer is enabled by this document.

## Files

- `docs/superpowers/specs/2026-10-16-epic6-insar-feasibility-design.md` — feasibility decision, evidence, pilot protocol, constraints, and acceptance gates.
- `docs/data-sources.md` — current source maturity, access, and operational caveats.
- `docs/glossary.md` — canonical InSAR and LOS terminology.

## Testing Strategy

- Documentation review confirms all sections are complete, claims link to official mission/archive guidance, and the spec contains no implied validated Philippine coverage.
- `git diff --check` confirms clean Markdown edits.
- `python scripts/verify_structure.py` confirms repository structure remains valid.
- No application tests apply because no executable files or behavior change.

## Acceptance Criteria

- [x] The recommendation compares NISAR, Sentinel-1, and immediate nationwide implementation and explains the trade-offs.
- [x] The next-step pilot protocol identifies product discovery, site provenance, quality evaluation, validation, access/cost, and stop/go requirements.
- [x] The spec distinguishes LOS displacement from full ground motion and distinguishes measured deformation from the NASA susceptibility reference.
- [x] The user-facing constraints preserve the research-grade, informational, non-warning framing and source credit.
- [x] Current provisional/partial validation and actual site coverage uncertainty are explicit.
- [x] The document does not add code, runtime behavior, or assert that a Philippine pilot has been executed.

## Out Of Scope (backlog)

- Site selection, archive queries, scene downloads, and pilot processing.
- Independent field validation and domain review.
- MGB or PHIVOLCS landslide inventory licensing and geometry assessment.
- A production ingestion/processing pipeline, web layer, alerts, thresholding, or operational monitoring.

## Spec self-review

- No placeholders remain; all template sections apply or explicitly state why they do not.
- Every goal has a corresponding acceptance criterion.
- The recommended scope is one documentation-only feasibility decision; pilot execution is explicitly deferred.
- Product maturity, spatial coverage, latency, and quality are not overstated.

## Related documents

- Implementation plan: to be created only after this feasibility spec is reviewed and the pilot scope is approved.
- Terminology: `docs/glossary.md`.
