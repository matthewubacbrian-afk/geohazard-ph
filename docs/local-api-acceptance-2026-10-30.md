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

- Observe a newly committed event reaching a connected WebSocket client.
- Complete physical Android flows using the runtime checklist and explicitly
  record both native app and JavaScript source versions.
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
fresh native build or device-flow acceptance.

The installed app showed a blank surface after repeated reloads. Logs included
`ReactInstance task returned null` and `reactInstance is null` following failed
bundle loads. A manual close and reopen was requested because automatic approval
review rejected the app restart command. A clean-start result is still required
before classifying this observation as an application defect.
