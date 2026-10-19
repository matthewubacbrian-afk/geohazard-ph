# GeoHazard PH Project Status

This is the authoritative current status register. It separates implemented code
from data preparation, live deployment verification, and deferred product work.
Status is based on the repository and its recorded history, reviewed on
2026-10-18.

| Epic or workstream | Current status | Evidence and remaining work |
| --- | --- | --- |
| Epic 1: Earthquake feed, API, and web map | Implemented | USGS ingestion and event API are in [backend ingestion](../backend/ingestion/sources/usgs.py), [event routes](../backend/app/api/v1/events.py), and the [web app](../web/src). The dashboard [interface refresh](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/22) and [map/feed event selection with a selected-event pulse](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/23) merged on 2026-10-10. Live operation still depends on reachable sources and a configured database. |
| Epic 2: PHIVOLCS, realtime, and deduplication | Implemented and merged | PHIVOLCS adapters, canonical event handling, and realtime publishing are present in [ingestion](../backend/app/services/ingest.py), [deduplication](../backend/app/services/dedup.py), and [realtime services](../backend/app/services/events_publisher.py). PHIVOLCS live fetch has a trusted-TLS/source availability caveat; see [runbook ingestion guidance](runbook.md#ingestion-failure), [PHIVOLCS bulletin notes](runbook.md#phivolcs-volcano-bulletins), and [data-source notes](data-sources.md). |
| Epic 3: Static hazard layers | GEM fault snapshot verified locally; coverage remains partial | The pinned GEM snapshot at `56816508ad92fd6846dad1163b1c8c01376a2cd1` was imported and verified through the faults API with 155 intersecting features. Dry runs now report source, accepted, excluded-out-of-bounds, and un-clipped accepted-bounds metrics. The raw source is not bundled. PHIVOLCS fault and volcano-zone service candidates are documented, but reuse clearance remains pending: attribution is required, permission for storage/display/redistribution is not established, and no PHIVOLCS vector geometry was imported. The documented PHIVOLCS Geomatics request/DUA-or-MOU path is an application process, not a reuse grant; no request has been submitted. Existing PHIVOLCS raster reference overlays are not local vector coverage. National completeness remains unresolved. See the [Epic 3 import runbook](runbook.md#import-static-layers-epic-3), [verified GEM source](data-sources.md#verified-gem-fault-snapshot), [fault source and clearance record](data-sources.md#phivolcs-active-fault-candidate-reuse-clearance-pending), [volcano-zone source and clearance record](data-sources.md#phivolcs-volcano-zone-candidate-services-reuse-clearance-pending), [fault clearance spec](superpowers/specs/2026-10-09-epic3-phivolcs-fault-geometry-design.md), and [volcano-zone coverage spec](superpowers/specs/2026-10-09-epic3-phivolcs-volcano-zone-coverage-design.md). |
| Epic 4: Mobile nearby alerts and offline cache | Foreground app and native CI builds implemented; runtime flow checks remain | Saved locations, proximity matching, foreground alert list, and cached events are implemented in [mobile](../mobile/src). [PR #46](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/46) scoped event caching to the selected API URL; all five CI checks passed before merge. The [current plan](../PLAN.md) retains same-server refresh ordering and write-failure resilience as separate fixes. A 2026-10-18 production-dependency npm audit reported 42 findings; dependency reachability and compatible updates need triage. Android/iOS simulator or device user-flow checks remain unverified; use the [runtime smoke checklist](mobile-runtime-smoke-test.md) and [readiness plan](superpowers/plans/2026-10-09-mobile-runtime-readiness.md). Background push, store signing, and publishing remain deferred. See the [Epic 4 spec](superpowers/specs/2026-10-09-epic4-mobile-nearby-alerts-design.md), [mobile native runtime plan](superpowers/plans/2026-10-09-mobile-native-runtime.md), and [nearby-alert implementation plan](superpowers/plans/2026-10-09-epic4-mobile-nearby-alerts.md). |
| Epic 5: Regional seismic risk profiles | Validation and cutoff sensitivity evidence generated; export remains on quality hold | The [ML pipeline](../ml/src/ml/train.py), [risk-profile API](../backend/app/api/v1/risk_profile.py), and [web map layer](../web/src) use historical data. Offline training uses explicit PHIVOLCS/USGS files and the pinned 17-region boundary asset, with nearby offshore events assigned within 100 km. A local ignored bundle produced 17 schema-valid profiles on 2026-10-14. The offline [validation command](../ml/src/ml/validate_profiles.py) matched saved source and boundary hashes and assignment counts, then generated ignored JSON and Markdown reports. The [quality review](risk-profile-quality-review-2026-10-14.md) records three NCR events in the common window and 18 exploratory, data-derived count cutoffs. At threshold 4, NCR is excluded and 10 of 16 included labels change; no cutoff policy is selected. The user chose to hold this export from staging. [PR #30](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/30) merged with backend, ML, web, mobile, and iOS simulator CI checks passing; these checks do not resolve the data-quality hold. The [domain review decision record](epic5-domain-review-decision-record.md) is prepared, but no stakeholder review or policy decision is recorded. Kaggle versions are unknown; versioned source refresh, scheduled refresh, and live-event modeling remain. Labels are descriptive statistical profiles, not predictions. See [data-source assumptions](data-sources.md#kaggle-historical-earthquake-datasets) and [README training instructions](../README.md#regional-seismic-risk-profiles). |
| Epic 6: Landslide and InSAR stretch work | Part 1 implemented; Part 2 research-only | Part 1's NASA coarse, informational susceptibility overlay merged in [PR #37](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/37). Part 2 completed metadata screening and reproduction-design review at the Naga event-centroid point: 34 Sentinel-1B SLC records and 26 PROVISIONAL NISAR GUNW records. These do not establish source-scarp coverage, pixel quality, measured deformation, or validation. A georeferenced, reusable source-area footprint and a time-aligned independent reference were not found in the accessible sources reviewed. No images were downloaded and no processing ran. See the [screening report](epic6-insar-pilot-report.md) and [data sources](data-sources.md#static-layers). |
| Epic 7: Camera scene review | Merged demonstrator; image-quality calibration, deployment, and camera-device checks pending | Shared transient analysis API plus web and mobile camera review flows are implemented. Both clients display the same persistent visual cue demonstrator warning, including that results are not a safety assessment or production-ready emergency decision tool and do not give emergency instructions, identify official shelters, or predict earthquakes. API result limitations enumerate what a single image cannot verify, including structure, ground, glass/electrical hazards, egress, accessibility, routes, unseen areas, and changing conditions. A local Windows run loaded the pinned model and returned HTTP 200 for one synthetic image (`no_clear_candidate`, zero polygons, two model cues); this verifies model loading and the response path, not scene-recognition accuracy. Blur-threshold calibration and real-scene evaluation remain pending. The full backend suite passed (148 tests, including PostGIS and Redis integration), web tests passed (133) with production build, and mobile tests passed (46) with strict TypeScript checking. The 2026-10-13 local verification recorded API, Vite, PostGIS, and Redis running in an isolated Compose project; this is historical evidence, not a current health check. A browser check of `/dashboard` rendered 2,779 earthquake events after refresh; regional activity showed 2,753 events. Enabling Fault lines displayed 155 GEM reference features, and Volcano bulletins showed five PHIVOLCS entries retrieved on 2026-10-13. The recorded local polling-worker cycle fetched and processed 29 USGS events and 2,750 PHIVOLCS events. An earlier one-shot PHIVOLCS request failed Windows certificate-chain validation, but the continuous worker subsequently completed successfully. The checksum-verified pinned GEM source imported 155 local fault features into this isolated database; volcano-zone data remains unavailable pending reuse permission, and the alert-subscription API currently has no subscriptions. Android/iOS camera hardware checks and deployed Linux/ARM64 model packaging/resource fit remain unverified. The default API image omits the large model runtime and weights and can return typed 503 until deployment packaging is measured and provisioned. See the [Epic 7 plan](superpowers/plans/2026-10-13-epic7-scene-analysis.md), [image-quality follow-up plan](superpowers/plans/2026-10-13-epic7-image-quality.md), [model preflight and dataset limits](data-sources.md#scene-analysis-model-preflight), [runbook](runbook.md#epic-7-scene-review), and [camera smoke checklist](mobile-runtime-smoke-test.md). |
| Oracle Always Free staging | Held-export deployment path implemented; deployment unverified | The [2026-10-14 staging release run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/38516440460) published an earlier AMD64/ARM64 bundle for commit `5ada21049808c51f080da1e0080d3ee7577ec32b`; it predates the held-export mode. The base Compose configuration now omits the risk-profile bind mount and checks for an empty profile list. An explicit override and `--with-profile` deploy flag are reserved for a later validated and domain-approved export. The [Oracle runbook](runbook.md#oracle-cloud-infrastructure-always-free-a1) documents both modes. There is no recorded OCI VM or DNS. A new bundle, host setup, and live checks remain; serving profiles additionally requires Epic 5 approval. |

## Session delivery plan

The [project completion plan](../PLAN.md) records the 2026-10-17 audit, prioritized
engineering fixes, epic acceptance gates, and session verification evidence.

The [portable verification baseline slice](superpowers/plans/2026-10-17-verification-baseline.md)
merged in [PR #40](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/40)
after all five CI checks passed. Local backend tests passed (148, including
PostGIS and Redis), ML tests passed (65), both explicit package Ruff checks passed,
and mobile strict TypeScript checking passed. CI now requires Ruff and mobile
TypeScript checking. Applied migrations have only exact legacy style exceptions.
The [MapLibre security migration](superpowers/specs/2026-10-17-maplibre-security-design.md)
merged in [PR #41](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/41)
after the full web suite passed 175 tests, the production build succeeded, a
browser map smoke check rendered, `npm audit --omit=dev` reported zero findings,
and all five CI checks passed. The separate Vite/Vitest upgrade in the
[plan](../PLAN.md) merged in [PR #42](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/42)
after 175 web tests, a production build, a clean npm install, zero full and
production audit findings, independent review, and five green CI checks. These
engineering checks do not establish deployment health, device readiness, or
data-quality approval.

The Kaggle credential loader from
[PR #32](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/32) merged
through [PR #43](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/43).
The runbook now agrees with the downloader's repository-root `.env` support,
and downloader tests are isolated from a developer's real credentials. Local ML
tests passed 72/72 with Ruff, and all five CI checks passed. No Kaggle source
refresh or held risk-profile export was performed.

## Next integration milestone

1. Complete the [Epic 5 domain review decision record](epic5-domain-review-decision-record.md)
   with seismic-domain stakeholders, using the [reproducible validation
   evidence](risk-profile-quality-review-2026-10-14.md). Review the count-cutoff
   sensitivity and define a sparse-region policy before changing labels. Also
   review the 100 km assignment, source coverage, features, and category
   semantics. Keep the export on hold until review and validation criteria are
   documented for a new artifact version.
   Refresh both Kaggle sources with versioned downloads
   when credentials are available; preserve input hashes, boundary hash, source
   counts, and evaluation results. Follow the
   [training instructions](../README.md#regional-seismic-risk-profiles) and
   [data-source assumptions](data-sources.md#kaggle-historical-earthquake-datasets).
2. Prepare a new staging release from `main` when an OCI host, DNS, and staging
   configuration are available. Follow the
   [Oracle runbook](runbook.md#oracle-cloud-infrastructure-always-free-a1) to
   deploy and record live health and event-feed checks. Keep the risk-profile
   endpoint without the held export until a revised profile passes review, then
   record its own live check. CI does not establish those live checks.

## How to read project plans

Use this page for current status. Older specs and implementation plans are
historical records of their original scope and execution; unchecked boxes in
those records do not define the current backlog unless the work is reconfirmed
against current code and requirements. A code-complete row does not establish
that external data is loaded or that a hosted deployment is healthy.
