# Epic 6 InSAR Pilot — Archive Screening Record

**Screening date:** 2026-10-16
**Scope:** Public metadata only. No SAR image or interferogram was downloaded, no displacement was calculated, and no processing job was submitted.

## Decision summary

ASF's public catalog has repeat Sentinel-1B IW SLC scenes for a point at the 2018 Naga landslide event centroid, and it has NISAR L2 GUNW products intersecting that same point in 2026. This establishes catalog-level data availability at the event centroid only. It does not establish coverage or quality at the landslide source scarp, a valid time series, or an operational monitoring capability.

The candidate is not ready for processing. The 2026 Naga PS-InSAR paper is a retrospective study with reported field comparisons, but its stated time windows and displacement totals are internally inconsistent, and its plotted PS point is not accompanied by a retrievable coordinate. The Antipolo study's abstract reports a GNSS comparison, but the full article endpoint returned 404 during this review, so its acquisition details and reference series could not be checked. No current GNSS series was identified for comparison with 2026 NISAR products. No displacement layer or alert should be built from this evidence.

## Candidate site evidence

### Naga City, Cebu

The open-access ISPRS paper [PS-InSAR Analysis of Precursory Deformation Before the September 2018 Naga Landslide](https://isprs-archives.copernicus.org/articles/XLVIII-5-W4-2025/213/2026/isprs-archives-XLVIII-5-W4-2025-213-2026.html) is published under CC BY 4.0. Its full text describes 35 descending Sentinel-1B IW SLC scenes in VV polarization from August 2017 to early September 2018 and reports a PS time series near the quarry slope. It compares that LOS result to field-mapped cracks described in Catane et al. (2019).

The paper is suitable as a retrospective research candidate, not as evidence of warning performance. The text alternates between July and August 2017 for the start of the observation period. It describes the field comparison as a 12-day interval while listing August 29 to September 18 (20 days) in its table. It also gives different LOS totals in separate sections. The named persistent-scatterer point is shown in figures but its coordinate and source-scene identifiers are not published in the readable text. Reproduction must resolve these differences rather than select whichever figure is convenient.

The International Consortium on Landslides event record gives the event centroid as **10.208494 N, 123.759047 E** (converted from its published DMS coordinate). This point identifies the catalog query location; it is not the source-scarp boundary. The [MGB Region VII incident brief](https://r7.mgb.gov.ph/briefer-of-the-landslide-incident-in-barangay-tinaan-city-of-naga-cebu/) places the crown area in Sitio Tagaytay and the toe area in Sitio Sindulan, Barangay Tinaan. No MGB polygon was downloaded or reused.

## Reproduction-design review

The [UNOOSA presentation on Philippine space activities](https://www.unoosa.org/documents/pdf/copuos/2019/copuos2019tech21E.pdf) includes a Naga landslide outline identified as having been delineated from Planet imagery acquired on 2018-09-21. It credits building footprints to the UP Cebu Center for Environmental Informatics. The presentation supplies a map figure, but not a georeferenced outline or reuse terms for the Planet-derived delineation. The figure is evidence that a post-event mapped outline exists; it is not a redistributable source-area geometry suitable for this reproduction. No Planet imagery was accessed or digitized.

The [MGB Region VII incident brief](https://r7.mgb.gov.ph/briefer-of-the-landslide-incident-in-barangay-tinaan-city-of-naga-cebu/) identifies crown and toe localities and documents pre-event crack investigations. The Naga PS-InSAR paper compares its reported result with field-mapped cracks, but the available materials do not provide a georeferenced crack dataset or an independent, time-aligned GNSS displacement series. Those sources support the event chronology and localities, not quantitative validation of a reproduced LOS time series.

**Design-review outcome:** the source-area geometry and independent validation target are not sufficiently reproducible from the accessible, reusable materials reviewed. Keep the Naga case as a literature-screened candidate and stop before image download or processing. Reconsider only if a georeferenced source-area outline with usable terms and a suitable independent reference become accessible. This review did not contact agencies or authors, request restricted data, or create a digitized boundary.

### Antipolo, Rizal

The [UP Diliman Philippine Engineering Journal abstract](https://www.journals.upd.edu.ph/index.php/pej/article/view/9482) reports 184,253 persistent-scatterer points and a LOS correlation of 0.83 against a stationary GNSS receiver. The journal page is currently inaccessible from the project environment: the article and PDF routes returned HTTP 404 on 2026-10-16. The abstract does not expose the exact study footprint, scene IDs, dates, or GNSS series. Treat this as promising published context, not a reproducible validation benchmark. Antipolo was not searched in the satellite archive.

## ASF catalog queries

Queries used the public [ASF Search API](https://docs.asf.alaska.edu/api/keywords/) with `intersectsWith=point(123.759047 10.208494)`. The public catalog query is reproducible from the direct links below. Search results were inspected as metadata only.

### Sentinel-1B

Query filters: dataset `SENTINEL-1`, platform `Sentinel-1B`, processing level `SLC`, beam mode `IW`, flight direction `DESCENDING`, 2017-08-01 through 2018-09-13 UTC.

- **34** SLC records intersected the event-centroid point.
- All returned records were on relative orbit / track **61**, descending.
- Acquisition range: **2017-08-12 through 2018-09-12 UTC**.
- ASF metadata `sizeMB` summed to approximately **67.8 GiB** for the returned scenes. No scene data were downloaded.
- The paper says it used 35 images. The one-scene count difference and the paper's conflicting start dates need resolution before any reproduction.

[Repeat the Sentinel-1B catalog query](https://api.daac.asf.alaska.edu/services/search/param?dataset=SENTINEL-1&platform=Sentinel-1B&processingLevel=SLC&beamMode=IW&flightDirection=DESCENDING&intersectsWith=point%28123.759047+10.208494%29&start=2017-08-01T00%3A00%3A00&end=2018-09-13T23%3A59%3A59&output=json)

### NISAR L2 GUNW

Query filters: dataset `NISAR`, processing level `GUNW`, 2026-06-17 through 2026-10-16 UTC.

- **26** geocoded unwrapped-interferogram records intersected the event-centroid point.
- Orbit groups: descending relative orbit 3 (**12** records), descending relative orbit 104 (**7**), and ascending relative orbit 39 (**7**).
- The returned products were PROVISIONAL (`PR`) collection products with processor version `R05.02.3`.
- Acquisition intervals in the returned records began on **2026-06-26**; the newest pair began **2026-09-30** and ended **2026-10-12**, and its processing date was **2026-10-14**.
- This is current archive availability at one point. It cannot reproduce the 2017–2018 Naga event, and the review found no time-aligned 2026 field/GNSS series.

[Repeat the NISAR GUNW catalog query](https://api.daac.asf.alaska.edu/services/search/param?dataset=NISAR&processingLevel=GUNW&intersectsWith=point%28123.759047+10.208494%29&start=2026-06-17T00%3A00%3A00&end=2026-10-16T23%3A59%3A59&output=json)

## Quality, processing, and validation status

| Check | Result |
| --- | --- |
| Exact landslide source-scarp geometry intersects each scene | Not evaluated; query used the event centroid only. |
| Reproducible Sentinel-1 scene list matches the published 35 inputs | Not resolved; catalog returned 34 point-intersecting scenes under the stated query. |
| NISAR maturity and product identifier recorded | PROVISIONAL collection, `P05023`, processor `R05.02.3` in returned metadata. |
| Pixel quality, coherence, valid-data masks, layover/shadow, and unwrapping quality | Not evaluated; no products downloaded. |
| LOS time series independently reproduced | No. |
| Comparison with current GNSS or field measurements | Not available for the 2026 NISAR interval. |
| Processing access, credits, queue time, and retention | Not tested. No Earthdata/HyP3 job was submitted. |

## Recommendation

**Remain at reproduction-design review; do not proceed to processing or map implementation.** The accessible evidence does not resolve the paper's scene-count and time-window mismatch, provide a reusable source-area footprint, or provide a time-aligned independent reference. Reconsider processing only after those prerequisites are met. Review the Antipolo full paper through an accessible copy if it is to be considered as the GNSS-validated site. Require a current, time-aligned independent reference before evaluating NISAR as a validation candidate.

Do not download the full 67.8 GiB Sentinel-1 candidate stack or submit a HyP3 job until the paper inputs, source-area AOI, validation target, and no-cost processing allowance are confirmed. Do not pay for credits. Product quality and displacement remain unevaluated; no go decision for a user-facing layer has been reached.

## Sources

- Ricofuerto, J. B. E. and Veracruz, N. A. S. (2026), [ISPRS Archives paper and full text](https://doi.org/10.5194/isprs-archives-XLVIII-5-W4-2025-213-2026), CC BY 4.0.
- Mabaquiao, L. C. and Reyes, R. (2023), [Philippine Engineering Journal abstract](https://www.journals.upd.edu.ph/index.php/pej/article/view/9482); full text was not retrievable for this review.
- [International Consortium on Landslides Naga event record](https://www.landslides.org/report/naga-landslide/), event centroid.
- [MGB Region VII Naga incident brief](https://r7.mgb.gov.ph/briefer-of-the-landslide-incident-in-barangay-tinaan-city-of-naga-cebu/), source/toe locality and incident chronology.
- [ASF Search API documentation](https://docs.asf.alaska.edu/api/keywords/).
- [ASF NISAR data availability](https://nisar-docs.asf.alaska.edu/data-availability/availability-overview/), product-maturity definitions.
