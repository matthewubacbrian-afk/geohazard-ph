# GeoHazard PH Project Status

This is the authoritative current status register. It separates implemented code,
deployed acceptance, data permission, scientific validation and deferred scope.
Reviewed through **2026-11-06 (Asia/Manila)** against `main` at `392a936f`
(PR #92). Counts and test totals below are dated observations, not live guarantees.

## Current assessment

The project is a deployed public-awareness monitoring demonstrator. The core web
feed/map and foreground mobile code are substantially implemented; full operational,
scientific and device acceptance is incomplete. There is no evidence-based single
completion percentage across these independent gates.

Use [the active deployment record](free-split-deployment.md) for Render + Supabase +
Upstash + GitHub Actions operations, [the fresh acceptance record](staging-acceptance-2026-11-06.md)
for bounded live results, and [the completion plan](../PLAN.md) for the ordered queue.
Oracle/colocated Compose is an alternative, not the active staging topology.

## Epic completion and remaining gates

| Epic or workstream | Current status | Evidence and remaining work |
| --- | --- | --- |
| Epic 1: Earthquake feed, API, and web map | Implemented; hosted feed and map observed | Public API, browser map and source records verified on November 6. Sustained freshness, automatic ingestion and recovery acceptance remain; a healthy API alone does not prove a fresh feed. |
| Epic 2: PHIVOLCS, realtime, and deduplication | Implemented; hosted ingestion-to-browser delivery observed | PR #83 restored verified PHIVOLCS TLS. Canonical ingestion and post-commit Redis/WSS publishing are implemented. November 6 acceptance observed a real ingestion-generated USGS message and browser notifications. First automatic schedule evidence, sleep/restart reconnection and source-outage acceptance remain open. |
| Epic 3: Static hazard layers | GEM faults available locally and on staging; coverage partial | Pinned GEM snapshot `56816508ad92fd6846dad1163b1c8c01376a2cd1` supplies 155 staging faults. PHIVOLCS vector storage/display/redistribution permission is not established; no request or permission grant is recorded. Raster overlays do not establish local vector coverage or national completeness. See [source/clearance evidence](data-sources.md#static-layers) and [import runbook](runbook.md#import-static-layers-epic-3). |
| Epic 4: Mobile nearby alerts and offline cache | Foreground Android flow verified on dated builds; release acceptance incomplete | Saved locations, radius matching, ordered URL-scoped cache and native CI are implemented. October 31 standalone QA passed foreground/cache/restart/recovery checks against the local API. PR #82 merged the Retake repair with 71 mobile tests; a fresh binary's physical Retake acceptance remains open. Current-build staging, physical iOS, unresolved advisory/framework decisions and post-migration evidence remain. Background push, signing and store publishing are deferred. See [QA evidence](android-qa-acceptance-2026-10-31.md), [device checklist](mobile-runtime-smoke-test.md), and [advisory evidence](mobile-advisory-attack-path-gates-2026-10-21.md). Historical audit totals are not fresh security clearance. |
| Epic 5: Regional seismic risk profiles | Pipeline/validation implemented; scientific export held | A local bundle produced 17 schema-valid profiles, but sparse-region sensitivity remains material: excluding NCR at count threshold 4 changed 10 of 16 included labels. No cutoff or export approval is selected. [Domain review](epic5-domain-review-decision-record.md), versioned inputs, policy and a newly validated/approved artifact remain required. [Recorded activity shading](data-sources.md#recorded-regional-earthquake-activity-web) counts events and does not complete this epic or lift the hold. |
| Epic 6: Landslide and InSAR stretch work | NASA reference overlay implemented; InSAR research-only | PR #37 delivered the coarse informational overlay. InSAR screening found candidate metadata, but no reusable source-area footprint, independent time-aligned validation, download, processing or displacement result. Keep InSAR outside the core monitoring acceptance milestone; see [screening report](epic6-insar-pilot-report.md). |
| Epic 7: Camera scene review | Browser demonstrator deployed and exercised; mobile/server inference unprovisioned | PR #89 delivered local quantized browser inference; November 5 public staging tests displayed a grass candidate, about 25 seconds cold / 11 seconds warm, with zero photo uploads. These are fixture-path checks, not accuracy evidence. Physical phone/browser performance, representative-scene evaluation and blur calibration remain. Mobile still uses the separate Python endpoint whose default image lacks runtime/weights. The offline training pipeline is under review in PR #36. See [browser architecture/evidence](browser-scene-analysis.md), [model preflight](runbook.md#epic-7-model-packaging-preflight-2026-10-13), and [device checklist](mobile-runtime-smoke-test.md). |
| Free split staging | Public API/web and manual ingestion live; operational acceptance incomplete | Worker image `5c33057841dd9ae1a2df91926b626b94a78bed0a` published successfully. November 6 health, read endpoints and exact allowed-origin CORS passed; ingestion-generated browser notifications were observed. Six-hour schedule is configured and enabled, but no automatic run was returned at the initial inspection. Sleep/restart recovery, mobile staging, managed backup/restore, repeatable migrations and fresh provider usage evidence remain open. Risk clusters remain empty under the quality hold. |

## Epic 7 offline training branch

The [training PR](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/36)
includes dataset and rights validation, source-group splits, offline training,
held-out evaluation, and versioned artifact export. Synthetic fixtures exercise
the pipeline and export checks. The evaluation command currently produces a
candidate-only report. Export requires a passing comparison with the pinned
baseline on the identical held-out images. The CLI still needs a mapping from
baseline outputs to the Scene Review label set and a comparison step.

Inspection of the local pinned DETR configuration at `d53b52a7` found floor
and ground categories used by the current candidate detector. Its taxonomy has
no direct glass-facade, overhead-line, or visible-building-damage class. The
comparison needs to report which target labels the baseline can evaluate.

The existing source-rights review has not cleared images for training. Real-scene
evaluation and any artifact release also require approved inputs and thresholds.
See the [vision-training plan](superpowers/plans/2026-10-15-scene-review-vision-training.md)
and the [rights and annotation guide](superpowers/scene-review-annotation-guide.md).

## Latest development and evidence boundaries

- PR #83 restored PHIVOLCS ingestion; PR #84 selected six-hour staging cadence.
- PR #86 delivered event-count regional activity shading; PR #88 repaired its panel layout.
- PR #89 delivered browser scene inference; PR #90 recorded deployed verification.
- PRs #91–92 refreshed About and project guides. Main `392a936f` passed Backend,
  ML, Web and Mobile CI, including both mobile/iOS simulator jobs. PR #92 records
  198 web tests plus build and desktop/tablet/phone page checks. These checks do
  not prove physical-device, scientific or sustained deployment readiness.
- The [November 6 acceptance record](staging-acceptance-2026-11-06.md) distinguishes
  a manual refresh from automatic scheduling and event occurrence from receipt time.
- No newer approval supersedes the Epic 5 hold. No new permission, domain-review,
  physical-device or InSAR processing result is inferred by this documentation update.

## Historical implementation and acceptance evidence

The entries below retain their original dates and commit-specific scope. Present-tense
statements within an older checkpoint describe that checkpoint; the table above and
linked current acceptance record govern current status.

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
## Historical delivery checkpoints (October 2026)

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
No historical backfill was performed. On an Android 14 Infinix X6532 running
the existing debug app `4e130fb8`, a fresh 1 km `EncodingCheck` location at
`12.84, 123.03` showed `024 km S 73° W of Claveria (Masbate)` in both Nearby
and Alerts. The test location was removed afterward. This verifies one corrected
mobile display path through the local API. [PR #77](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/77)
merged with all five checks passing. The corrected text has not been verified
on a physical iOS device.

## 2026-10-30 local readiness checkpoint

Main `18b9a0ac` passed [Backend CI](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40942275878),
[Web CI](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40942275883),
[ML CI](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40942275854),
and [Mobile CI](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/40942275873).
[PR #78](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/78) merged the
iOS root safe-area fix. Its simulator screenshot evidence covers startup layout;
see the dated rows in the [runtime checklist](mobile-runtime-smoke-test.md#record-results).
Physical iOS API/camera flows remain open.

At this 2026-10-30 checkpoint, staging was deferred. The later free split
deployment supersedes that decision. Local API and device acceptance were ordered in
[PLAN.md](../PLAN.md#historical-local-readiness-checkpoint-2026-10-30). At this local
inspection Docker Desktop was unavailable and Android SDK tooling reported no
connected devices. These prerequisites prevent fresh local runtime evidence;
they do not change prior recorded results or clear any release gate.

## Current integration milestone

The current queue is in [PLAN.md](../PLAN.md#current-delivery-queue-2026-11-06).
Complete automatic ingestion and recovery acceptance, current-build mobile staging
checks, and managed-database backup/restore evidence. Epic 5 domain decisions,
Epic 3 reuse permission/coverage, and Epic 7 real-scene evaluation remain separate
gates. Keep the held export absent; count-based activity shading does not release it.

## How to read project plans

Use this page for current status. Older specs and implementation plans are
historical records of their original scope and execution; unchecked boxes in
those records do not define the current backlog unless the work is reconfirmed
against current code and requirements. A code-complete row does not establish
that external data is loaded or that a hosted deployment is healthy.

## 2026-10-30 local API and physical Android follow-up

The [dated acceptance record](local-api-acceptance-2026-10-30.md) verifies local
API health and ingestion from `18b9a0ac`: 39 USGS events fetched/processed and
1,768 PHIVOLCS rows fetched, with 1,766 unique events processed. The API returned
1,864 events and an empty held-profile list. Redis connectivity and a WebSocket
connection passed. A second bounded cycle delivered an ingestion-generated USGS
update over the WebSocket; its October 1 occurrence time identifies it as a
historical-event update, not a newly occurring earthquake.

On Android 14 Infinix X6532, the October 28 native debug binary with current
`18b9a0ac` JavaScript passed foreground validation, nearby matching, offline cache,
process restart persistence, recovery, no-match state, and temporary-location
removal. Camera opening/canceling and permission denial/recovery also passed.
This mixed build does not replace a fresh native release acceptance run. No new
photos were captured; scene capture/retake, model evaluation, and physical iOS
remain open. All 61 mobile tests and strict TypeScript checking passed locally.
See the [runtime checklist](mobile-runtime-smoke-test.md#2026-10-30-foreground-and-permission-follow-up).

## 2026-10-31 standalone Android QA build

The dedicated Android QA workflow builds an independently installable APK with
bundled JavaScript, a separate application ID, commit/checksum metadata, and
QA-only local HTTP access. Its final-artifact verifier also requires an explicit
Release HTTP denial. [Build and physical acceptance evidence](android-qa-acceptance-2026-10-31.md)
records the exact downloaded binary, passing foreground/cache/restart/recovery
checks without Metro, and user-assisted capture preview/cleanup.

Testing exposed missing initial-preview Retake. The repair merged in PR #82
on 2026-10-31; physical acceptance of a fresh APK containing it remains open.
Scientific model evaluation, remaining camera cases, physical iOS, and store
release remain open. These results do not establish deployment or
scientific readiness.


## Regional Activity Shading (2026-11-05)

The web activity view summarizes filtered earthquake records with count-based
regional shading, UTC observed dates, per-region source totals, and explicit
unassigned/invalid counts. It replaces the dashboard's empty ML-profile view,
while the risk-profile API/export remains on hold. Uses existing source records
and pinned boundaries with no new provider cost. See
[method and limitations](data-sources.md#recorded-regional-earthquake-activity-web).
Deployment verification must confirm the new web bundle; the previous API-only
PHIVOLCS verification does not establish that the updated frontend is live.


Regional activity deployment evidence: PR #86 merged; web CI passed 182 tests
and build. The Render public bundle now contains the activity feature. The
live-record aggregation assigned 82 of 339 events to 14 regions and left 257
outside/offshore on 2026-11-05. Full browser visual acceptance remains open;
see the deployment record for the evidence boundary.


## Browser Scene Review (2026-11-05)

The web analysis default now uses a local module worker, pinned quantized ONNX
model, bounded device inference, provisional blur choices, component contours,
and existing evidence/caveats. It uploads no picture and invokes no paid inference
API. Actual Edge production-build checks recognized sample-photo cues and a grass
candidate; warm analysis reused weights without network writes. See
[browser architecture, model provenance, cost boundary and checks](browser-scene-analysis.md).
The separate default Python endpoint/mobile prototype remains unavailable until
its own model provisioning. This browser path is still an uncalibrated visual
cue demonstrator; physical phone testing and real-world accuracy remain open.


Browser Scene Review deployment: PR #89 merged; web CI passed 193 tests and
build. The public staging browser test completed local inference and displayed a
grass candidate (about 25 seconds cold / 11 seconds warm), with zero photo uploads
and no additional weight requests on repeat. See the browser-scene-analysis
record for the fixture, immutable model/runtime identifiers, and remaining limits.
