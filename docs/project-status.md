# GeoHazard PH Project Status

This is the authoritative current status register. It separates implemented code
from data preparation, live deployment verification, and deferred product work.
Status is based on the repository and its recorded history as of 2026-10-09.

| Epic or workstream | Current status | Evidence and remaining work |
| --- | --- | --- |
| Epic 1: Earthquake feed, API, and web map | Implemented | USGS ingestion and event API are in [backend ingestion](../backend/ingestion/sources/usgs.py), [event routes](../backend/app/api/v1/events.py), and the [web app](../web/src). Live operation still depends on reachable sources and a configured database. |
| Epic 2: PHIVOLCS, realtime, and deduplication | Implemented and merged | PHIVOLCS adapters, canonical event handling, and realtime publishing are present in [ingestion](../backend/app/services/ingest.py), [deduplication](../backend/app/services/dedup.py), and [realtime services](../backend/app/services/events_publisher.py). PHIVOLCS live fetch has a trusted-TLS/source availability caveat; see [runbook ingestion guidance](runbook.md#ingestion-failure), [PHIVOLCS bulletin notes](runbook.md#phivolcs-volcano-bulletins), and [data-source notes](data-sources.md). |
| Epic 3: Static hazard layers | GEM fault snapshot verified locally; coverage remains partial | The pinned GEM snapshot at `56816508ad92fd6846dad1163b1c8c01376a2cd1` was imported and verified through the faults API with 155 intersecting features. The raw source is not bundled. PHIVOLCS geometry, volcano-zone data, and national completeness remain unresolved. See the [Epic 3 import runbook](runbook.md#import-static-layers-epic-3) and [verified source record](data-sources.md#verified-gem-fault-snapshot). |
| Epic 4: Mobile nearby alerts and offline cache | Foreground app and native scaffolding implemented; runtime verification in progress | Saved locations, proximity matching, foreground alert list, and cached events are implemented in [mobile](../mobile/src). Android/iOS native projects and Android debug CI are present. An iOS simulator build job and [runtime smoke checklist](mobile-runtime-smoke-test.md) are added on this branch; hosted iOS build and Android/iOS runtime user-flow results remain unverified. See the [mobile runtime readiness plan](superpowers/plans/2026-10-09-mobile-runtime-readiness.md). Background push, store signing, and publishing remain deferred. See the [Epic 4 spec](superpowers/specs/2026-10-09-epic4-mobile-nearby-alerts-design.md), [mobile native runtime plan](superpowers/plans/2026-10-09-mobile-native-runtime.md), and [nearby-alert implementation plan](superpowers/plans/2026-10-09-epic4-mobile-nearby-alerts.md). |
| Epic 5: Regional seismic risk profiles | Historical-data pipeline and product path implemented | The [ML pipeline](../ml/src/ml/train.py), [risk-profile API](../backend/app/api/v1/risk_profile.py), and [web map layer](../web/src) use historical Kaggle data. A trained model/export must be prepared manually for deployment; scheduled refresh and live-event modeling are not implemented. Labels are descriptive statistical profiles, not predictions. See [data-source assumptions](data-sources.md#kaggle-historical-earthquake-datasets) and [README training instructions](../README.md#regional-seismic-risk-profiles). |
| Epic 6: Landslide and InSAR stretch work | Deferred | No product-ready landslide or InSAR feature is claimed. Source validation, licensing, ingestion, and user-facing work remain future scope. See [data sources](data-sources.md#static-layers). |
| Oracle Always Free staging | Multi-architecture release and operator guide implemented on this branch; deployment unverified | The [staging workflow](../.github/workflows/deploy-staging.yml) builds AMD64 and ARM64 images, and the [Oracle runbook](runbook.md#oracle-cloud-infrastructure-always-free-a1) documents operator setup and deployment. OCI account/VM/network/DNS setup, required model export, and deployed-state verification are operator tasks and are not verified by repository CI. |

## How to read project plans

Use this page for current status. Older specs and implementation plans are
historical records of their original scope and execution; unchecked boxes in
those records do not define the current backlog unless the work is reconfirmed
against current code and requirements. A code-complete row does not establish
that external data is loaded or that a hosted deployment is healthy.
