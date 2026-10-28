# GeoHazard PH Project Status

This is the authoritative current status register. It separates implemented code
from data preparation, live deployment verification, and deferred product work.
Status is based on the repository and its recorded history, updated through
2026-10-28. Counts attached to earlier PRs are dated observations, not a
promise that a live advisory feed will return the same rows today.

| Epic or workstream | Current status | Evidence and remaining work |
| --- | --- | --- |
| Epic 1: Earthquake feed, API, and web map | Implemented | USGS ingestion and event API are in [backend ingestion](../backend/ingestion/sources/usgs.py), [event routes](../backend/app/api/v1/events.py), and the [web app](../web/src). The dashboard [interface refresh](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/22) and [map/feed event selection with a selected-event pulse](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/23) merged on 2026-10-10. Live operation still depends on reachable sources and a configured database. |
| Epic 2: PHIVOLCS, realtime, and deduplication | Implemented and merged | PHIVOLCS adapters, canonical event handling, and realtime publishing are present in [ingestion](../backend/app/services/ingest.py), [deduplication](../backend/app/services/dedup.py), and [realtime services](../backend/app/services/events_publisher.py). PHIVOLCS live fetch has a trusted-TLS/source availability caveat; see [runbook ingestion guidance](runbook.md#ingestion-failure), [PHIVOLCS bulletin notes](runbook.md#phivolcs-volcano-bulletins), and [data-source notes](data-sources.md). |
| Epic 3: Static hazard layers | GEM fault snapshot verified locally; coverage remains partial | The pinned GEM snapshot at `56816508ad92fd6846dad1163b1c8c01376a2cd1` was imported and verified through the faults API with 155 intersecting features. Dry runs now report source, accepted, excluded-out-of-bounds, and un-clipped accepted-bounds metrics. The raw source is not bundled. PHIVOLCS fault and volcano-zone service candidates are documented, but reuse clearance remains pending: attribution is required, permission for storage/display/redistribution is not established, and no PHIVOLCS vector geometry was imported. The documented PHIVOLCS Geomatics request/DUA-or-MOU path is an application process, not a reuse grant; no request has been submitted. Existing PHIVOLCS raster reference overlays are not local vector coverage. National completeness remains unresolved. See the [Epic 3 import runbook](runbook.md#import-static-layers-epic-3), [verified GEM source](data-sources.md#verified-gem-fault-snapshot), [fault source and clearance record](data-sources.md#phivolcs-active-fault-candidate-reuse-clearance-pending), [volcano-zone source and clearance record](data-sources.md#phivolcs-volcano-zone-candidate-services-reuse-clearance-pending), [fault clearance spec](superpowers/specs/2026-10-09-epic3-phivolcs-fault-geometry-design.md), and [volcano-zone coverage spec](superpowers/specs/2026-10-09-epic3-phivolcs-volcano-zone-coverage-design.md). |
| Epic 4: Mobile nearby alerts and offline cache | Foreground app and native CI builds implemented; physical Android foreground flow verified, with remaining device checks open | Saved locations, proximity matching, foreground alert list, and cached events are implemented in [mobile](../mobile/src). [PRs #46–49](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/49) fixed URL-scoped cache isolation, refresh ordering, cache-write ordering, and persistence warnings after five CI checks each. [PR #50](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/50) patched the critical transitive `shell-quote` finding; [PR #51](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/51) refreshed compatible lockfile entries; [PR #52](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/52) removed unused React Navigation, leaving 34 production-graph findings (six moderate, 28 high, zero critical). [PR #53](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/53) merged the reviewed migration assessment. [PR #54](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/54) merged after all five exact-head CI checks passed and generated non-published Android/iOS Release reports. The final reports list 25 source-map packages and 34 audit-chain findings on each platform; only `react-native` is listed among those findings, and every disposition remains undetermined. The iOS native list contains only the app and Hermes executables. [PR #55](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/55) merged after five exact-head CI checks and added installed versions, six direct advisory references across five packages, and inherited links to both reports; all 34 findings remain undetermined. [PR #56](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/56) merged after independent review and five exact-head checks; its dated path and precondition record leaves all 34 findings undetermined. [PR #57](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/57) merged after five exact-head checks; the pinned CLI consumers use XML parsing/validation rather than a direct XMLBuilder call, with other paths and input control unresolved. [PR #58](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/58) merged after five exact-head checks; Metro asset paths/buffers and byte-based image format dispatch are documented, with crafted-input provenance unresolved. [PR #59](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/59) merged the [node-forge consumer-call review](mobile-node-forge-callsites-2026-10-20.md) after five exact-head checks and both Release report inspections; the pinned middleware has no direct `selfsigned` call in published JavaScript, while `selfsigned.generate` verifies its new certificate. [PR #60](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/60) merged the [bounded braces consumer-call review](mobile-braces-callsites-2026-10-21.md) after five exact-head checks and both final Release-report inspections; all 34 dispositions remain undetermined. [PR #61](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/61) merged the [bounded sprintf-js consumer-call review](mobile-sprintf-js-callsites-2026-10-21.md) after five exact-head checks and both final Release-report inspections; all 34 dispositions remain undetermined. [PR #62](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/62) merged the [cross-advisory gate matrix](mobile-advisory-attack-path-gates-2026-10-21.md) after independent review, five exact-head checks, and both final Release-report comparisons; all 34 dispositions remain undetermined. [PR #63](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/63) merged the [asset provenance review](mobile-image-asset-provenance-2026-10-21.md) at `695e9ff8` after independent review, five exact-head CI checks, and final Android/iOS Release-report comparison with PR #62. Two local non-published Metro bundles copied no image asset, and current supported-suffix file signatures were PNG or SVG. Both CI reports retained 34 undetermined findings, 25 source-map packages, the same source-map hashes and native inventories; only the Android APK file hash differed. [PR #64](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/64) merged [Release build-process trace evidence](mobile-build-process-trace-2026-10-21.md) at `ecbe6173` after independent review and five exact-head checks on `2fe27ea8`. Both platforms observed Metro build activity and matching five-package summaries. Both final Release reports retain 34 undetermined findings, 25 source-map packages, and unchanged source-map hashes and native inventories against PR #63; only the Android APK hash differs. The tested head is on main, and its worktree and branch were removed after ignored files were preserved. Generated/external inputs, affected operation arguments, and device gates remain open; at that dated run, all 34 dispositions were undetermined. Remaining affected-API/attack-path review, New Architecture device flows, a supported framework migration, and post-migration Android/iOS device evidence remain. The [artifact evidence](mobile-artifact-evidence-2026-10-20.md), [audit record](mobile-dependency-audit-2026-10-19.md), [migration assessment](mobile-rn-migration-assessment-2026-10-20.md), and [current plan](../PLAN.md) separate these gates. The Android SDK 24/iOS 15.1 support-floor decision remains open. Use the [runtime smoke checklist](mobile-runtime-smoke-test.md); background push, store signing, and publishing remain deferred. |
| Epic 5: Regional seismic risk profiles | Validation and cutoff sensitivity evidence generated; export remains on quality hold | The [ML pipeline](../ml/src/ml/train.py), [risk-profile API](../backend/app/api/v1/risk_profile.py), and [web map layer](../web/src) use historical data. Offline training uses explicit PHIVOLCS/USGS files and the pinned 17-region boundary asset, with nearby offshore events assigned within 100 km. A local ignored bundle produced 17 schema-valid profiles on 2026-10-14. The offline [validation command](../ml/src/ml/validate_profiles.py) matched saved source and boundary hashes and assignment counts, then generated ignored JSON and Markdown reports. The [quality review](risk-profile-quality-review-2026-10-14.md) records three NCR events in the common window and 18 exploratory, data-derived count cutoffs. At threshold 4, NCR is excluded and 10 of 16 included labels change; no cutoff policy is selected. The user chose to hold this export from staging. [PR #30](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/30) merged with backend, ML, web, mobile, and iOS simulator CI checks passing; these checks do not resolve the data-quality hold. The [domain review decision record](epic5-domain-review-decision-record.md) is prepared, but no stakeholder review or policy decision is recorded. Kaggle versions are unknown; versioned source refresh, scheduled refresh, and live-event modeling remain. Labels are descriptive statistical profiles, not predictions. See [data-source assumptions](data-sources.md#kaggle-historical-earthquake-datasets) and [README training instructions](../README.md#regional-seismic-risk-profiles). |
| Epic 6: Landslide and InSAR stretch work | Part 1 implemented; Part 2 research-only | Part 1's NASA coarse, informational susceptibility overlay merged in [PR #37](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/37). Part 2 completed metadata screening and reproduction-design review at the Naga event-centroid point: 34 Sentinel-1B SLC records and 26 PROVISIONAL NISAR GUNW records. These do not establish source-scarp coverage, pixel quality, measured deformation, or validation. A georeferenced, reusable source-area footprint and a time-aligned independent reference were not found in the accessible sources reviewed. No images were downloaded and no processing ran. See the [screening report](epic6-insar-pilot-report.md) and [data sources](data-sources.md#static-layers). |
| Epic 7: Camera scene review | Merged demonstrator; image-quality calibration, deployment, and camera-device checks pending | Shared transient analysis API plus web and mobile camera review flows are implemented. Both clients display the same persistent visual cue demonstrator warning, including that results are not a safety assessment or production-ready emergency decision tool and do not give emergency instructions, identify official shelters, or predict earthquakes. API result limitations enumerate what a single image cannot verify, including structure, ground, glass/electrical hazards, egress, accessibility, routes, unseen areas, and changing conditions. A local Windows run loaded the pinned model and returned HTTP 200 for one synthetic image (`no_clear_candidate`, zero polygons, two model cues); this verifies model loading and the response path, not scene-recognition accuracy. Blur-threshold calibration and real-scene evaluation remain pending. The full backend suite passed (148 tests, including PostGIS and Redis integration), web tests passed (133) with production build, and mobile tests passed (46) with strict TypeScript checking. The 2026-10-13 local verification recorded API, Vite, PostGIS, and Redis running in an isolated Compose project; this is historical evidence, not a current health check. A browser check of `/dashboard` rendered 2,779 earthquake events after refresh; regional activity showed 2,753 events. Enabling Fault lines displayed 155 GEM reference features, and Volcano bulletins showed five PHIVOLCS entries retrieved on 2026-10-13. The recorded local polling-worker cycle fetched and processed 29 USGS events and 2,750 PHIVOLCS events. An earlier one-shot PHIVOLCS request failed Windows certificate-chain validation, but the continuous worker subsequently completed successfully. The checksum-verified pinned GEM source imported 155 local fault features into this isolated database; volcano-zone data remains unavailable pending reuse permission, and the alert-subscription API currently has no subscriptions. Android/iOS camera hardware checks and deployed Linux/ARM64 model packaging/resource fit remain unverified. The default API image omits the large model runtime and weights and can return typed 503 until deployment packaging is measured and provisioned. See the [Epic 7 plan](superpowers/plans/2026-10-13-epic7-scene-analysis.md), [image-quality follow-up plan](superpowers/plans/2026-10-13-epic7-image-quality.md), [model preflight and dataset limits](data-sources.md#scene-analysis-model-preflight), [runbook](runbook.md#epic-7-scene-review), and [camera smoke checklist](mobile-runtime-smoke-test.md). |
| Oracle Always Free staging | Held-export deployment path implemented; deployment unverified | The [2026-10-14 staging release run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/38516440460) published an earlier AMD64/ARM64 bundle for commit `5ada21049808c51f080da1e0080d3ee7577ec32b`; it predates the held-export mode. The base Compose configuration now omits the risk-profile bind mount and checks for an empty profile list. An explicit override and `--with-profile` deploy flag are reserved for a later validated and domain-approved export. The [Oracle runbook](runbook.md#oracle-cloud-infrastructure-always-free-a1) documents both modes. PR #71 verified the updated staging workflow on a feature branch with publication skipped; it did not publish a new bundle. There is no recorded OCI VM or DNS. A new bundle, host setup, and live checks remain; serving profiles additionally requires Epic 5 approval. |

The [PR #66 image-input slice](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/66)
merged at `c398d31c` after five exact-head checks on `a80ecd85` and final
Android/iOS Release-report comparison. Both traces recorded two pinned
`image-size` module loads and zero parser calls across covered Release Node
threads; the [dated trace record](mobile-image-input-trace-2026-10-24.md)
limits that observation to those builds. The live audit returned 12 rows on
each platform, all `undetermined`, rather than the 34 historical rows after
GitHub withdrew the `sprintf-js` and `braces` advisories. The lockfile,
source-map hashes, 25-package lists, native inventories, and five-package
process summaries are unchanged; only the Android APK hash differs. The
next merged Epic 4 evidence slice, [PR #68](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/68),
added the [direct XML-builder inventory](mobile-xml-builder-path-2026-10-25.md). It
finds no direct external builder token in the inspected installed JavaScript
and no named builder execution in the scoped Release trace. Dynamic/generated
callers, comment/CDATA input control, framework, and device gates remain.
The [bounded `node-forge` caller and key-path inventory](mobile-node-forge-path-2026-10-25.md)
found no external direct token in the inspected 7,540-file installed JavaScript
tree and no forge load in the scoped PR #68 Release processes. `selfsigned`
still contains a real certificate-verification call and an optional
caller-supplied-key path; dynamic callers and crafted-input provenance remain
unverified. All 12 rows at that checkpoint remained `undetermined`. [PR #69](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/69)
merged this bounded inventory at `d2fec772` after independent review and five
exact-head checks on `449b0d31`. Its Android Release report changed only the
APK hash against PR #68; iOS and all compact traces matched. No advisory
disposition changed. The automatic PR workflow refresh is scoped in the
[focused plan](superpowers/plans/2026-10-26-ci-action-runtime-pr-workflows.md);
the automatic workflow refresh merged in [PR #70](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/70)
at `fcf8c0b6` after five passing checks on `cf95281f` and independent review.
Android differed from PR #69 only in its APK hash; iOS and all compact traces
matched. Staging workflow maintenance was delivered by
[PR #71](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/71),
which merged at `271310fd` after five passing checks on `da7d3189`. The updated
workflow's branch-only run `40482711712` passed its PostGIS/Redis-backed
verification and skipped publication. Final Android/iOS Release reports showed
nine undetermined audit rows rather than PR #70's 12: three inherited chain rows
disappeared, and `react-native` inherited severity changed from high to moderate
with one removed CLI-plugin via link. The direct `node-forge` row remains high
and undetermined. The lockfile, source-map packages and hashes, native inventory,
and compact traces did not change; only the Android APK hash also differed.
This audit-feed change gives no safety or device clearance. Main-branch image
publication under the updated actions and a live staging host remain unverified.
This closeout updates the [focused plan](superpowers/plans/2026-10-27-staging-action-runtime.md)
with the final gate and cleanup evidence.
[PR #36](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/36)
is still open with conflicts against `main` and has not been merged.

## Session delivery plan

[PR #72](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/72) merged
the PR #71 tracking closeout at `e3bf201f` after five checks on `6d03f321`;
both Release reports and four compact traces matched PR #71 except the Android
APK hash. At that checkpoint, the audit had nine undetermined rows, including a high
direct `node-forge` row. At that checkpoint, the next Epic 4 slice was the
[New Architecture opt-in plan](superpowers/plans/2026-10-27-mobile-new-architecture-readiness.md);
native builds and device flows had not yet been verified.

[PR #73](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/73)
subsequently merged New Architecture build readiness at `fb283e6e`. All five
checks passed on `f98bd22f`; Android/iOS Debug and non-published Release builds
completed with opt-in flags. Android added 16 app/Codegen native entries across
four ABIs and changed its APK hash. Its audit rows, source-map packages/hash,
and compact traces matched PR #72; iOS's audited report and two compact traces
matched exactly. The iOS artifact hash covers the main JavaScript bundle, not
the native executable. At that checkpoint, nine rows remained undetermined, including
high direct `node-forge`. Real-device storage, camera, and SVG flows remain
unverified, as does the Android SDK 24/iOS 15.1 support-floor decision for the
later framework migration.

[PR #74](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/74)
merged the PR #73 tracking closeout at `771d529a` after five passing checks
on `fe7b35af`; it recorded no device-flow evidence. The subsequent
[main Mobile CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40618628164)
completed both native jobs and returned 11 undetermined rows on each platform.
Compared with PR #74, the new rows are direct `deepmerge`
[GHSA-gcqx-w48m-w2h4](https://github.com/advisories/GHSA-gcqx-w48m-w2h4)
and inherited `@react-native-community/cli-config`; the lockfile did not change.
Other Release-report fields matched except the Android APK hash.

The current maintenance decision is to keep React Native 0.75.5 and the existing
Android SDK 23/iOS 13.4 minimums while verifying the app before a supported
framework migration. The [maintenance design](superpowers/specs/2026-10-28-current-app-maintenance-design.md)
and [launch-gate plan](superpowers/plans/2026-10-28-current-app-launch-gate.md)
add Android/iOS simulator startup checks to Mobile CI. These checks establish
installation, launch, short process survival, and a screenshot only when their
exact-head runs pass. They do not replace the [device-flow checklist](mobile-runtime-smoke-test.md),
a live staging deployment, or the held Epic 5 domain-review decision. All 11
current mobile audit rows remain undetermined, including high direct `node-forge`.

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

## 2026-10-28 physical Android runtime update

At `4e130fb8`, a debug APK built locally from a short Windows path and ran on an
Android 14 phone. The [runtime checklist](mobile-runtime-smoke-test.md#record-results)
records passing Nearby, Saved locations, and Alerts checks for input validation,
a live 1 km PHIVOLCS match, offline cache, restart persistence, recovery, no-match
state, and test-location removal. This verifies those foreground flows on one
physical Android device. One PHIVOLCS place name contained `Â°` in both the
API response and app display. A 2026-10-28 source check found UTF-8 degree bytes
under `Content-Type: text/html` without a charset; Requests selected ISO-8859-1,
and the ingestion parser used `response.text`. The focused backend correction
and its local API verification are recorded below.
iOS physical-device behavior remains unverified.

Scene review opened the camera and displayed one indoor capture. The provisional
image-quality check warned on that capture; continuing returned the expected
HTTP 503 because the default local API image has no scene model. Leaving Scene
review cleared the preview and error. Candidate overlays, evidence checklist,
outdoor capture, camera-denial handling, model calibration, and production device
behavior remain open. The camera permission prompt appeared after Open camera;
the denial result was not verified. A transient Metro warning followed a USB
disconnect during testing and cleared after the debug overlay was dismissed.

## 2026-10-29 PHIVOLCS earthquake text correction

Commit `67963987` decodes the earthquake feed response bytes as strict UTF-8
before parsing. The observed missing-charset case failed before the fix and
passed afterward; invalid UTF-8 now raises the typed feed parsing error.
The full backend suite passed 151 tests and Ruff passed locally. A one-off
backend image from this branch fetched 1,678 live source rows and updated
1,676 unique events in the local development database without replacing the
running API. That API returned recent event `phivolcs-2026_1028_1942_B1` with
`024 km S 73° W of Claveria (Masbate)`. Twenty-seven older API rows still
contain `Â°`; none of their IDs was present in the current 1,676-ID feed.
No historical backfill was performed. The physical Android display and CI
on the fix commit remain to be checked.

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
