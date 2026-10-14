# Regional Risk Profile Export: Technical Quality Review

**Reviewed:** 2026-10-14  
**Export:** local ignored `ml/model_artifacts/snapshots/2026-10-14/v1`  
**Disposition:** hold the export from staging and user-facing risk guidance pending further validation.

## Evidence reviewed

- The export contains 17 profiles matching the checked-in regional boundary names. Both saved source files and the boundary asset match their recorded SHA-256 hashes. All profiles parse through the backend `RiskProfile` schema.
- Parsing accepted 142,493 PHIVOLCS and 26,483 USGS rows. After deduplication and the 100 km regional assignment rule, 134,335 PHIVOLCS and 21,402 USGS rows were assigned; 7,123 and 5,004 were excluded from regional assignment, respectively. Parser rejection and regional exclusion are separate counts.
- The assigned PHIVOLCS records span 2015–2026; assigned USGS records span 1905–2026. The two sources have unequal observation periods and reporting thresholds, so aggregate counts cannot be read as comparable regional rates.
- NCR has five assigned records: two PHIVOLCS and three USGS. The export labels NCR `Low` with classifier confidence `1.0`. That is an in-sample classification of a sparse regional summary, not evidence of low seismic hazard or calibrated confidence.
- K-Means selected three clusters with sizes 1, 14, and 2 and silhouette score 0.4651. Fourteen regions share `Moderate`; two are `High`; NCR alone is `Low`. The Random Forest's 17/17 accuracy is measured on its training rows and has no holdout or temporal validation.
- In a limited sensitivity check using the saved regional features, changing K-Means seeds from 0 through 19 changed the labels of ARMM and Calabarzon once each. Removing NCR and refitting with the default seed changed 14 of the remaining 16 labels. This check shows that the category scale depends strongly on the included regional summaries; it does not measure future-event prediction.
- `event_density` is an event-count divided by a latitude/longitude span product. It is a coordinate-spread proxy, not events per square kilometer, and the clustering severity order also uses raw event counts. Neither feature adjusts for source coverage, observation period, exposure, or population.
- The saved CSVs have no verified Kaggle version identifiers. Metadata records their exact hashes, and offline dataset versions correctly remain `null`.

## Reproducible validation report

The offline `ml.validate_profiles` command re-read the held bundle and both saved
CSVs, matched their SHA-256 values and the pinned regional boundary SHA-256,
and reproduced parser and assignment totals. It wrote ignored local
`validation-report.json` and `validation-report.md` under
`ml/model_artifacts/validation/2026-10-14/v1`. All 17 region names are present.
The report state is `requires_domain_review`.

- Assigned PHIVOLCS events span 2015-12-31 16:40 UTC to 2026-10-07 10:26 UTC;
  assigned USGS events span 1905-06-01 02:23 UTC to 2026-10-02 23:10 UTC.
- Their inclusive shared observation window is 2015-12-31 16:40 UTC to
  2026-10-02 23:10 UTC. Within it, 134,053 PHIVOLCS and 6,929 USGS assigned
  events remain. Matching dates does not equalize reporting thresholds or
  catalog completeness.
- NCR contributes two PHIVOLCS and one USGS event in that shared window.
  A refit on all represented regions in the shared window changes 11 of the
  17 saved labels. This is a sensitivity comparison, not a corrected label set.
- Of 20 seed fits (0-19) on saved regional features, seed 12 changes ARMM and
  Calabarzon; the other seeds reproduce the saved categories. Seventeen
  leave-one-region-out fits were recorded. Omitting NCR changes labels for
  14 of the remaining 16 regions.

The report makes the sparse-region and catalog-coverage issues reproducible.
It does not establish reliable categories or calibrated classifier confidence.

## Release decision

The artifact is reproducible and structurally valid, but its labels and displayed confidence are not sufficiently supported for publication as regional risk guidance. Do not transfer `risk_profiles.json` to a staging host or configure the staging API to serve it. The project can prepare code and container images independently of this export.

Before reconsidering the export, define a sparse-region policy, harmonize observation windows and source coverage, review the feature and label semantics with a seismic-domain stakeholder, and assess stability using a documented validation design. Present any revised labels as descriptive historical summaries, never forecasts or official warnings. A new export needs a distinct version and recorded source hashes and review outcome.

No OCI staging host or DNS name was available at this review. Live deployment and endpoint checks remain unverified.
