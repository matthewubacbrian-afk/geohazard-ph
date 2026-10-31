# Standalone Android QA acceptance — 2026-10-31

## Build identity

- Workflow: [Android QA build run 41091235211](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/41091235211).
- Checkout: `c96b2080fbb6ebff347c5af7d2dea0add38de7d4` (PR merge checkout for QA implementation head `8ad89fe8`).
- Application: `com.geohazardph.mobile.qa`, label `GeoHazard QA`, version `1.0-qa`.
- APK SHA-256: `ba33c7c20631a8801c8163af71321ce27efb628bde6b71fddc6dac95934d6c9b`.
- Lockfile SHA-256: `c627bd12e251a63522ea22e5bfa606bf44fd2be1b6c08a9331bc33ae72a0476f`.
- Architectures: `armeabi-v7a`, `arm64-v8a`, `x86`, `x86_64`.

The downloaded APK hash and lockfile hash matched `build-info.json` before
installation. CI compiled both QA and reference Release, checked their final
manifests, verified the embedded JavaScript and native architectures, and passed
QA emulator startup. Its screenshot rendered Nearby with all four tabs.
All six checks on implementation head `8ad89fe8` passed, including iOS startup.

## Physical runtime and API

Android 14 Infinix X6532, using the downloaded APK without Metro. The old Metro
process was stopped and host port 8081 had no listener. The local API was the
current-source acceptance container from `18b9a0ac`, host port 8001; USB forwarded
phone port 8000 to that port. The API address was entered in QA's own settings.
The original debug app and its stored data were not replaced.

## Results

| Check | Observed result |
| --- | --- |
| Fresh launch | QA installed successfully and rendered Nearby with no configured API or locations. All four tabs were reachable. Installed package flags did not include DEBUGGABLE. |
| Input validation | Rejected API URL `bad`, blank name, latitude 91, longitude 181, and radius 0. |
| Online match | A 1 km temporary location at `4.25, 125.75` displayed the PHIVOLCS Balut Island event, magnitude 2.7 and distance 0 m, in Nearby and Alerts with a correct degree symbol. |
| Offline cache | Stopping only the acceptance API retained the match and displayed the cached/offline label in both lists. |
| Offline restart | Dismissed only QA through Recent Apps and confirmed its old process ended. Relaunched with a new process, changing observed PID 27843 to 5445; API URL, location, and cached match returned. The offline label remained after refresh failed. |
| Recovery | After the API health endpoint returned 200, refreshing cleared the offline label and retained the match. |
| No match and cleanup | A separate temporary location at `0, 0`, radius 1 km, displayed the no-match message. Removed all temporary locations and verified the saved-location prompt returned. |
| Photo capture | The user captured and accepted a non-private test photo in the native camera. A preview and Analyze action appeared in QA. |
| Preview cleanup | Leaving Scene review and returning cleared the preview and restored Open camera. No image analysis was submitted in this run. |

## Observed Retake gap

The captured preview had no direct Retake action before analysis. Source inspection
confirmed Retake existed only after a result or quality warning. This prevented
the planned initial-preview retake check. The separate `fix/mobile-scene-retake`
branch supplies a shared Retake control with rendered state-transition tests;
its own CI and physical acceptance must be recorded separately.

This record establishes foreground and basic capture behavior for this exact
downloaded binary. It does not establish model accuracy, candidate overlays,
outdoor-scene performance, physical iOS behavior, background push, store signing,
or production readiness. Oracle staging and the regional profile quality hold
remain unchanged. Both temporary locations were removed; the local API and QA
installation were left available for development.
