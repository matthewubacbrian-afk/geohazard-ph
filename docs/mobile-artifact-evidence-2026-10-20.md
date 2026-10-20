# Mobile Release Artifact Evidence — 2026-10-20

This record covers non-published Release builds of the React Native 0.75.5 app in
[PR #54](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/54). The
[first clean CI run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/39344690959)
passed all five project checks at head `3d76763f` and uploaded small Android and
iOS JSON reports. Inspection exposed an iOS file-list error, which the
[corrected clean run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/39370776500)
at head `2c5890d7` resolved. The [final-head run](https://github.com/matthewubacbrian-afk/geohazard-ph/actions/runs/39375918287)
at `a16805ba` passed all five project checks. Its Android and iOS reports were
downloaded and inspected before [PR #54](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/54)
merged. The workflow retains reports for seven days; this page keeps the
essential observations after those attachments expire.

| Observation | Android Release APK | iOS unsigned Release simulator app |
| --- | --- | --- |
| Metro source-map package names | 25 | 25 |
| Fresh npm production-graph findings | 34: six moderate, 28 high, zero critical | 34: six moderate, 28 high, zero critical |
| Finding whose package name is listed in the map | `react-native` (404 source entries) | `react-native` (400 source entries) |
| Other finding package names not listed in the map | 33 | 33 |
| Packaged native-file observation | 196 `.so` entries: 49 in each of four Android ABIs | `GeoHazardPH` app executable and `Frameworks/hermes.framework/hermes` |

The corrected Android report identifies the APK file with SHA-256
`5edb6baafcd2a10c6bfe8ef51ac4a9e7ade94e17af2a077d6c2377acd636f44e`.
The corrected iOS report's `artifact_sha256` is the **`main.jsbundle` hash**, not a
hash of the complete `.app` directory:
`ee6dca3c3a6672054060cf3c1e0436ac74f4b65651bf163847189a9c549ad5b0`.
The Android and iOS source-map hashes are respectively
`45fb6e3cbe2ecc2eb51f574b2445c8d76fa190c64b1bc3ea7dbbc8f1a0a078ea`
and `f65522694eac430286068b517e3266ff10c6e8f486ee36eec35c278030026d47`.
The final report format labels these scopes `android_apk_file` and
`ios_main_jsbundle_file`. It repeats the same source-map hashes and iOS bundle
hash; the final APK file hash is
`84b880b9020ddb523b458815f156890c57cea52eec2c958b5205803628bbc6ff`.

Inspection of the first iOS report found that the native-file filter counted
`Frameworks/hermes.framework/Info.plist` and omitted the app executable. The
correction reads the app's `CFBundleExecutable` and includes only that file,
framework-named binaries, and `.dylib` files. The corrected report lists the
two expected executables above and no framework metadata.

These are package-name and selected file-path observations, not advisory
dispositions. An unlisted JavaScript package may still affect build tooling or
compiled native code; a listed package does not establish use of the vulnerable
API or an attack path. The Android list excludes DEX contents, and the iOS list
cannot attribute statically linked code inside the app executable. Every
finding remains **undetermined** pending consumer-call and attack-path review in
[PLAN.md](../PLAN.md). No APK, `.app`, raw source map, bundle code, or raw npm
audit payload is committed or uploaded by this workflow.

[PR #55](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/55)
subsequently added installed lockfile versions, direct advisory references,
and inherited package links to both report formats. Its final reports retained
34 undetermined findings on each platform. The
[dated path and precondition review](mobile-advisory-exposure-review-2026-10-20.md)
connects the six direct references to shortest observed lockfile paths and
states the affected operations and remaining reachability questions.
