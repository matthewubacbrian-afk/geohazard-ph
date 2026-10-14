# GeoHazard PH Project Status

This is the authoritative current status register. It separates implemented code
from data preparation, live deployment verification, and deferred product work.
Status is based on the repository and its recorded history, reviewed on
2026-10-14.

| Epic or workstream | Current status | Evidence and remaining work |
| --- | --- | --- |
| Epic 1: Earthquake feed, API, and web map | Implemented | USGS ingestion and event API are in [backend ingestion](../backend/ingestion/sources/usgs.py), [event routes](../backend/app/api/v1/events.py), and the [web app](../web/src). The dashboard [interface refresh](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/22) and [map/feed event selection with a selected-event pulse](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/23) merged on 2026-10-10. Live operation still depends on reachable sources and a configured database. |
| Epic 2: PHIVOLCS, realtime, and deduplication | Implemented and merged | PHIVOLCS adapters, canonical event handling, and realtime publishing are present in [ingestion](../backend/app/services/ingest.py), [deduplication](../backend/app/services/dedup.py), and [realtime services](../backend/app/services/events_publisher.py). PHIVOLCS live fetch has a trusted-TLS/source availability caveat; see [runbook ingestion guidance](runbook.md#ingestion-failure), [PHIVOLCS bulletin notes](runbook.md#phivolcs-volcano-bulletins), and [data-source notes](data-sources.md). |
| Epic 3: Static hazard layers | GEM fault snapshot verified locally; coverage remains partial | The pinned GEM snapshot at `56816508ad92fd6846dad1163b1c8c01376a2cd1` was imported and verified through the faults API with 155 intersecting features. Dry runs now report source, accepted, excluded-out-of-bounds, and un-clipped accepted-bounds metrics. The raw source is not bundled. PHIVOLCS fault and volcano-zone service candidates are documented, but reuse clearance remains pending: attribution is required, permission for storage/display/redistribution is not established, and no PHIVOLCS vector geometry was imported. The documented PHIVOLCS Geomatics request/DUA-or-MOU path is an application process, not a reuse grant; no request has been submitted. Existing PHIVOLCS raster reference overlays are not local vector coverage. National completeness remains unresolved. See the [Epic 3 import runbook](runbook.md#import-static-layers-epic-3), [verified GEM source](data-sources.md#verified-gem-fault-snapshot), [fault source and clearance record](data-sources.md#phivolcs-active-fault-candidate-reuse-clearance-pending), [volcano-zone source and clearance record](data-sources.md#phivolcs-volcano-zone-candidate-services-reuse-clearance-pending), [fault clearance spec](superpowers/specs/2026-10-09-epic3-phivolcs-fault-geometry-design.md), and [volcano-zone coverage spec](superpowers/specs/2026-10-09-epic3-phivolcs-volcano-zone-coverage-design.md). |
| Epic 4: Mobile nearby alerts and offline cache | Foreground app and native CI builds implemented; runtime flow checks remain | Saved locations, proximity matching, foreground alert list, and cached events are implemented in [mobile](../mobile/src). Android/iOS native projects are present, and both Android debug and iOS simulator builds passed in [PR #20 CI](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/20). Android/iOS simulator or device user-flow checks remain unverified; use the [runtime smoke checklist](mobile-runtime-smoke-test.md) and [readiness plan](superpowers/plans/2026-10-09-mobile-runtime-readiness.md). Background push, store signing, and publishing remain deferred. See the [Epic 4 spec](superpowers/specs/2026-10-09-epic4-mobile-nearby-alerts-design.md), [mobile native runtime plan](superpowers/plans/2026-10-09-mobile-native-runtime.md), and [nearby-alert implementation plan](superpowers/plans/2026-10-09-epic4-mobile-nearby-alerts.md). |
| Epic 5: Regional seismic risk profiles | Export structurally validated; quality hold before deployment | The [ML pipeline](../ml/src/ml/train.py), [risk-profile API](../backend/app/api/v1/risk_profile.py), and [web map layer](../web/src) use historical data. Offline training uses explicit PHIVOLCS/USGS files and the pinned 17-region boundary asset, with nearby offshore events assigned within 100 km. A local ignored bundle produced 17 schema-valid profiles on 2026-10-14 with matching source and boundary hashes. The [technical quality review](risk-profile-quality-review-2026-10-14.md) found only five assigned NCR records, unequal source time spans, in-sample classifier accuracy, and unstable category assignments when NCR is excluded. The user chose to hold this export from staging until further validation. Kaggle versions are unknown; scientific review, scheduled refresh, and live-event modeling remain. Labels are descriptive statistical profiles, not predictions. See [data-source assumptions](data-sources.md#kaggle-historical-earthquake-datasets) and [README training instructions](../README.md#regional-seismic-risk-profiles). |
| Epic 6: Landslide and InSAR stretch work | Deferred | No product-ready landslide or InSAR feature is claimed. Source validation, licensing, ingestion, and user-facing work remain future scope. See [data sources](data-sources.md#static-layers). |
| Oracle Always Free staging | Multi-architecture release and operator guide implemented; deployment unverified | The [staging workflow](../.github/workflows/deploy-staging.yml) builds AMD64 and ARM64 images, and the [Oracle runbook](runbook.md#oracle-cloud-infrastructure-always-free-a1) documents operator setup and deployment. The user confirmed there is no OCI VM or DNS yet. The current model export is on quality hold and must not be transferred. Host setup, a reviewed export, and deployed-state verification remain. |

## Next integration milestone

1. Resolve the [technical quality hold](risk-profile-quality-review-2026-10-14.md)
   before presenting Epic 5 labels as meaningful risk guidance. Review the 100 km
   assignment, sparse regions, source coverage, features, and category semantics
   with domain stakeholders. Refresh both Kaggle sources with versioned downloads
   when credentials are available; preserve input hashes, boundary hash, source
   counts, and evaluation results. Follow the
   [training instructions](../README.md#regional-seismic-risk-profiles) and
   [data-source assumptions](data-sources.md#kaggle-historical-earthquake-datasets).
2. Prepare release images and the deployment bundle without the held model export.
   Once an OCI host, DNS, staging configuration, and reviewed export are available,
   follow the [Oracle runbook](runbook.md#oracle-cloud-infrastructure-always-free-a1)
   to deploy and record live health, event-feed, and risk-profile checks. CI does
   not establish those live checks.

## How to read project plans

Use this page for current status. Older specs and implementation plans are
historical records of their original scope and execution; unchecked boxes in
those records do not define the current backlog unless the work is reconfirmed
against current code and requirements. A code-complete row does not establish
that external data is loaded or that a hosted deployment is healthy.
