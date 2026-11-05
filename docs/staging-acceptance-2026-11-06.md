# Staging Acceptance — 2026-11-06

All local times are Asia/Manila (UTC+8). This is a bounded acceptance record,
not a service-availability, national-coverage, scientific-accuracy or release-readiness guarantee.

## Release and configuration identity

- Reviewed repository baseline: `main` at `392a936f432d1e550b70e0d9bb3ed248b63d8689`
  ([PR #92](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/92)). Its Backend,
  ML, Web and Mobile workflows passed, including mobile and iOS-simulator jobs.
  PR #92 reports 198 web tests and a production build; these are CI/PR observations,
  not a new local package-suite run in this documentation slice.
- Published/selected worker image: `5c33057841dd9ae1a2df91926b626b94a78bed0a`.
  [Publication run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/41995260585)
  succeeded. Newer frontend commits do not require a different ingestion image.
- GitHub metadata confirmed the ingestion workflow is active,
  `STAGING_INGEST_ENABLED=true`, the selected staging image SHA above, and the
  presence of both staging connection-secret names. Secret values were not read.
- Cron remains `17 */6 * * *` UTC: 02:17, 08:17, 14:17 and 20:17 Manila time.
  At initial inspection and the post-run check, GitHub returned manual runs only.
  **No successful automatic `schedule` run is evidenced.** Root cause is not
  established by these checks; do not describe the scheduler as accepted or fixed.
- Render's exact current deployment SHA/settings were not inspected in its
  authenticated dashboard. Public behavior and separately recorded frontend
  deployment evidence do not prove that every service runs the latest Git commit.

## Public API and CORS

Before ingestion, checks at about **03:33** returned HTTP 200 for health
(`status=ok`, `service=geohazard-api`), both source lists, faults, volcano
bulletins and held clusters: 299 PHIVOLCS events,
40 USGS events, 155 faults, five volcano bulletins and zero clusters.

After the cycle, checks at about **03:39** returned:

| Endpoint | Result |
| --- | --- |
| `/api/v1/events` | 200; 404 retained primary event rows |
| `/api/v1/events?source=phivolcs` | 200; 362 rows; latest occurrence `2026-11-05T19:24:00Z` (November 6, 03:24 Manila) |
| `/api/v1/events?source=usgs` | 200; 42 rows; latest occurrence `2026-11-04T07:40:12.288000Z` |
| `/api/v1/events/summary?west=116&south=4&east=128&north=22` | 200; 399 events, average magnitude 2.64, maximum 5.8; latest occurrence 03:24 Manila |
| `/api/v1/subscribe` | 200; `status=ok`, channel `events:updates`, endpoint `/ws/events` |
| `/api/v1/volcano-zones` | 200; empty list, consistent with unresolved vector permission |
| `/api/v1/risk-profile/clusters` | 200; empty list under the existing quality hold |

Source lists retain older rows; API totals need not equal the latest cycle's
fetched count. The summary is bounding-box scoped, unlike the unbounded list;
the 399/404 difference is not itself a loss or deduplication failure. No full
catalog completeness or canonical-matching accuracy evaluation was performed.

A request with Origin `https://geohazard-ph-staging-web.onrender.com` received
`Access-Control-Allow-Origin` with that exact value. The browser successfully
loaded API data cross-origin. This verifies the allowed-origin path, not rejection
of every disallowed origin or inspection of all Render environment values.

TLS verification remained enabled. The base Python interpreter's certificate
store failed earlier; the installed backend environment's standard Requests CA
bundle and Windows curl successfully checked HTTPS. Earlier short request
timeouts alone did not establish a hosted outage.

## Manual ingestion and realtime delivery

[Run 42095142633](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/42095142633)
was dispatched at **03:34:15** on current `main`; its worker used the selected
published image, not a newly built image from that frontend/documentation commit.
The job completed successfully with strict source-error reporting enabled:

- USGS: **41 fetched / 41 processed**, logged at 03:35:08.
- PHIVOLCS: **336 fetched / 336 processed**, logged at 03:36:34.

A verified-TLS WSS subscriber connected at 03:34:07 with the web Origin and
received a real source-row message at **03:35:07.938**. Its fields included:

```json
{
  "source": "usgs",
  "external_id": "us7000tvwj",
  "canonical_id": "06c5dde9-4e1f-4815-a0ae-7c17e230ab4d",
  "is_primary": true,
  "occurred_at": "2026-11-04T07:40:12.288000Z"
}
```

The occurrence predates receipt: this proves committed-event delivery, not a new
earthquake at 03:35. The ingestion code republishes fetched records, including
unchanged historical rows. The message was not fabricated or injected into Redis.

The public dashboard was open before dispatch with an empty Notifications tab.
During the cycle it showed USGS notifications at 03:35 and PHIVOLCS notifications
at 03:36. The map updated from 339 to 404 events. This closes the bounded hosted
ingestion → database/Redis → API WSS → browser notification acceptance path.
It does not prove durable replay, delivery of every row, or reconnection after sleep.

## Browser and scene checks

The in-app browser displayed the public dashboard, rendered basemap/earthquake
markers, and accepted the activity-shading toggle with the recorded-count legend
and `Selected filters · counts, not risk` text. The USGS source filter showed
42 map events; restoring All showed 404. The fault-layer toggle was selectable;
API fault availability was checked separately. No console warnings/errors were
returned by the bounded captured-log inspections. This is one desktop-hosted
browser with a narrow app-panel viewport, not physical-phone or all-device QA.
Full regional polygon/color correctness and all overlay rendering remain unassessed.

The [November 5 browser scene record](browser-scene-analysis.md#staging-verification-2026-11-05)
already verifies public fixture inference with zero photo uploads. It was not rerun
in this acceptance session. A new **synthetic 32×32 JPEG** with explicit quality
override sent to the separate Python endpoint returned **503** with code
`scene_analysis_unavailable`. No user capture was used. This verifies the expected
unprovisioned server/mobile path, not an inference success or a browser failure.

## Android QA handoff

The latest [standalone Android QA run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/41168720762)
passed final APK verification and emulator startup without Metro. It built commit
`38853d48289df95502906615c4af15a78b78452b` after the Retake repair merged.
The `mobile/` files, Android QA workflow and supporting `scripts/` are unchanged
between that source commit and `392a936f`; the newer web/API changes do not make
this APK stale for the foreground mobile check.

- Application ID: `com.geohazardph.mobile.qa`.
- APK SHA-256: `f77606f27e3f6020fe5bd492790e9de8eef01b232865cb622d1a1054895d7e51`.
- The downloaded APK matched `build-info.json`; the tracked lockfile hash also
  matched its recorded SHA-256.
- [Artifact](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/41168720762/artifacts/13030253243)
  was available at the checkpoint and expires November 7 at 12:37 Manila.
  After expiration, build a fresh standalone QA APK from the intended revision.

For the next physical run, install that QA build, set its base URL to
`https://geohazard-ph-staging-api.onrender.com/api/v1`, and follow the
[mobile runtime checklist](mobile-runtime-smoke-test.md). Use a current source
event coordinate for a temporary saved location; record matching, offline
restart, recovery, Retake and cleanup. This session verified the artifact and
its CI evidence only; it did not install the APK or exercise a physical device.

## Remaining gates and next evidence

| Gate | Required next evidence |
| --- | --- |
| Automatic ingestion | A successful run with event `schedule`, selected worker SHA, both source counts and post-run source freshness; investigate missing triggers before changing cadence |
| Cold-start/reconnect and failure handling | Bounded check after natural API sleep or controlled restart, reconnect and a later real ingestion message; source/Redis failure behavior without secret exposure |
| Mobile staging | A current identified APK/device and the hosted base URL; foreground match, offline cache, restart, recovery and Retake; physical iOS separately |
| Database recovery | Secure backup and a verified restore into an isolated target; no restore test against the active database |
| Release migrations | Repeatable reviewed migration operation distinct from ingestion, with before/after revisions and recovery procedure |
| Provider budget | Fresh post-ingestion Upstash commands/bandwidth, Supabase size/egress and current Render plan/usage; November 5 figures remain historical |
| Epic 3 | Actual vector reuse clearance, reviewed imports and coverage; no new permission inferred |
| Epic 5 | Completed domain review, policy and validation design, then exact approved artifact version/hash; keep clusters empty |
| Epic 7 | Representative lawful evaluation data, baseline comparison, blur calibration and real phone/browser performance; mobile/server provisioning separately |

No device, provider-account usage, database backup/restore, scientific-review or
permission gate was cleared in this session. Follow [PLAN.md](../PLAN.md#current-delivery-queue-2026-11-06)
and the [operations record](free-split-deployment.md) for continued work.
