# Local API acceptance — 2026-10-30

## Environment and scope

Source commit: `18b9a0ac`. Docker Engine reported version `29.7.2` after the
user restored Docker Desktop. The existing local PostgreSQL and Redis containers
were restarted, preserving their volumes. A separate API image was built from
this worktree as `ghph-android-acceptance-api:18b9a0ac` and started in container
`ghph-acceptance-api` on host port 8001 using the existing development database.
The phone's USB forward maps its port 8000 to that host port.

This is local development evidence, not staging or production acceptance.
The previously inaccessible Docker socket was not deleted by this session;
successful startup alone does not establish the original socket failure's cause.

## Observed results

| Check | Result |
| --- | --- |
| API startup | Uvicorn logged completed startup. `GET /health` returned HTTP 200 with `status: ok` and `service: geohazard-api`. |
| Held profiles | `GET /api/v1/risk-profile/clusters` returned HTTP 200 and `[]` on both the existing and current-source local APIs. No profile export was provisioned. |
| Current-source ingestion | One bounded scheduler cycle from the new image fetched and processed 39 USGS events, then fetched 1,768 PHIVOLCS rows and processed 1,766 unique events. The worker logged its normal stopping message. |
| Current-source event API | The new API returned 1,864 events. The newest observed event was `phivolcs-2026_1030_114944_B1`, timestamped `2026-10-30T11:49:00Z`, with a correctly decoded degree symbol in its place name. Counts are dated observations. |
| Redis connectivity | `GET /api/v1/subscribe` returned `status: ok`, channel `events:updates`, and endpoint `/ws/events`. |
| WebSocket connectivity | A client connected to `/ws/events`. No message arrived in a 45-second observation window. This verifies the connection only; delivery of a newly committed event was not established by this observation. |

The bounded worker ran against the existing development database and updated
source events. No historical encoding repair, test-fixture reset, database
replacement, or profile release was performed.

## Remaining acceptance

- Repeat acceptance on a freshly built native app and complete the remaining
  capture/retake cases; record native and JavaScript source versions.
- Complete camera and model checks separately; default model unavailability
  does not establish successful scene analysis.
- Keep Oracle staging deferred and the regional profile quality hold in force.

## Mobile preparation evidence

The connected Infinix X6532 runs the October 28 debug binary associated with
`4e130fb8`. Native Android/iOS source and the mobile lockfile have no diff between
that commit and `18b9a0ac`. The lockfile SHA-256 matched the previously installed
dependency set: `C627BD12E251A63522EA22E5BFA606BF44FD2BE1B6C08A9331BC33AE72A0476F`.

Fresh dependency installation was slow and stopped before completion; its partial
directory was preserved outside the repository. The matching existing dependency
set was reused to run the current source's 61 mobile tests (10 suites), all of
which passed, followed by successful strict TypeScript checking under Node
22.22.0. A temporary source snapshot and Metro launcher outside the repository
produced a 6,722,780-byte development bundle. All 26 copied source and configuration
files matched the worktree byte for byte. These checks do not establish a
fresh native build or device-flow acceptance by themselves.

The installed app showed a blank surface after repeated reloads. Logs included
`ReactInstance task returned null` and `reactInstance is null` following failed
bundle loads. A manual close and reopen was requested because automatic approval
review rejected the app restart command. A manual close/reopen subsequently
recovered the app. The checks below did not reproduce a normal-startup defect;
failed debug reload recovery remains a development-runtime observation.

## Physical Android follow-up

Runtime: Android 14 Infinix X6532. Native debug binary: `4e130fb8`; JavaScript
snapshot: `18b9a0ac`. This is a mixed build, not a newly built APK.

| Check | Result |
| --- | --- |
| Input validation | Rejected `bad` as API URL, blank name, latitude 91, longitude 181, and radius 0. Restored the existing API URL afterward. |
| Live match | Temporary `QA-20261030` at `4.25, 125.75`, radius 1 km, matched the recorded PHIVOLCS event in Nearby and Alerts, with magnitude 2.7, distance 0 m, and correctly decoded `16° E`. |
| Offline refresh | Stopped only `ghph-acceptance-api`; Nearby and Alerts kept the match and displayed the offline cached-data label. |
| Process restart while offline | Dismissed only GeoHazard through Recent Apps. After its old process disappeared, relaunched it; the new process restored the saved location and cached match, retaining the offline label after refresh failed. Observed process changed from 8216 to 10589. |
| Recovery | Restarted the acceptance API and refreshed; the match remained and the offline label cleared. |
| No match and removal | Removed the first temporary location; a new 1 km `QA-no-match` location at `0, 0` displayed the no-match message. Removed it and verified the saved-location prompt returned. |
| Camera opening and cancellation | Open camera launched the native CaptureActivity. Canceling returned to Scene review with no preview or error; navigating away and back retained the empty capture state. |
| Denial and recovery | Changed this app's Camera permission to Don't allow. Scene review itself produced no prompt; tapping Open camera displayed the Android prompt. Declining displayed the instruction to enable camera access in system settings without a crash. Restored the original Allow only while using the app setting and verified the native camera opened again. Canceled and returned to Nearby. |

No photos were captured during the unattended follow-up. Indoor/outdoor capture,
retake, image analysis, candidate overlays, model calibration, and physical iOS
remain open. No product defect was established by these completed foreground
checks, so no application code was changed. Both temporary locations were removed,
the original camera permission was restored, and the acceptance API was left running.

## Realtime delivery follow-up

A WebSocket client connected before a second bounded ingestion cycle. It received
an ingestion-generated USGS update for `us6000tyq7`, canonical ID
`d2b53a9f-112b-424f-a379-2e9dd21367b9`, magnitude 5.3. Its occurrence time was
`2026-10-01T05:34:10.575000Z`; receiving this update does not establish a newly
occurring earthquake. This verifies a live path from ingestion through Redis
to the WebSocket client, beyond the initial connection-only observation.
The second worker exited 0 after fetching/processing 39 USGS events and fetching
1,769 PHIVOLCS rows with 1,767 unique events processed.
