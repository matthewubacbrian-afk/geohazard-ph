# Mobile dependency audit — 2026-10-19

This record tracks the mobile production-dependency graph at the current lockfile, not a claim that each advisory is reachable in the distributed Android or iOS app. Run the commands from `mobile/` on a clean checkout. Audit results can change as npm advisory data changes.

## Verified snapshot

| State | Moderate | High | Critical | Total |
| --- | ---: | ---: | ---: | ---: |
| Before [PR #50](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/50) | 10 | 31 | 1 | 42 |
| After PR #50, before this refresh | 10 | 31 | 0 | 41 |
| After compatible lockfile refresh | 10 | 28 | 0 | 38 |
| After [PR #52](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/52) unused-navigation removal | 6 | 28 | 0 | 34 |

The last three rows come from `npm audit --omit=dev --json` on 2026-10-19. [PR #51](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/51) merged the compatible refresh after all five CI checks passed. It ran `npm audit fix --package-lock-only --omit=dev --ignore-scripts --no-fund` without `--force` and changed only these `mobile/package-lock.json` resolutions:

| Transitive package | Before | After | Result |
| --- | --- | --- | --- |
| `brace-expansion` | 1.1.18 | 1.1.21 | High finding removed |
| `compression` | 1.8.1 | 1.8.2 | High finding removed |
| `joi` | 17.13.6 | 17.13.8 | High finding removed |

PR #51 left `mobile/package.json`, React Native 0.75.5, React Navigation 6.1.18, and native configuration unchanged. The new `compression` lock entry records its `destroy` dependency and funding metadata; no separate package entry was added because `destroy` was already resolved elsewhere in the lockfile.

[PR #52](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/52) removed the unused `@react-navigation/native` declaration with `npm uninstall @react-navigation/native --package-lock-only --ignore-scripts --no-audit --no-fund`. npm pruned its 12 orphaned lockfile packages, including `@react-navigation/core`, `query-string`, and `decode-uri-component`. No app source or native project file changed; React Native remains 0.75.5. The source search found no React Navigation import, while `RootNavigator` continues to own local tab state. The four moderate findings in that package chain disappeared in a fresh audit. All five CI checks, including mobile tests, TypeScript, Android, and iOS builds, passed before merge.

## Remaining findings and action

The remaining 34 npm findings are a dependency-chain count, including packages that inherit an affected transitive dependency. npm groups 27 under its proposed React Native 0.88.0 major upgrade and seven as `fixAvailable: true`. The seven include upstream chain entries; running the non-forced fix left them unresolved. In particular, `image-size` 1.2.1 enters through Metro and is within the advisory range. Metro currently requests `image-size` `^1.0.2`, while the available patched line is 2.0.4; do not override that major API boundary without a Metro compatibility review. See the [image-size advisories](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq) and [second advisory](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr).

1. **Design the React Native and Metro migration separately.** The remaining high and moderate chains include CLI, Metro, Jest/codegen, `braces`, `node-forge`, `fast-xml-parser`, and `sprintf-js`. npm proposes React Native 0.88.0 for 27 entries; that is a major native-platform change, not a lockfile refresh. [React Native 0.76's release notes](https://reactnative.dev/blog/2024/10/23/release-0.76-new-architecture) already enable the New Architecture by default and raise minimum iOS from 13.4 to 15.1 and Android from SDK 23 to 24. This repo currently sets Android minimum SDK 23. Review intervening release notes, library compatibility, Gradle/Pods, and supported-device policy before choosing upgrade steps.
2. **Establish exposure with build evidence.** Package paths suggest many findings are in development, bundling, or CLI tooling, while React Native is the app framework. `npm audit --omit=dev` still includes them in this dependency graph. There is no recorded compiled-bundle or app-package reachability analysis; classify each advisory against the actual shipped JS bundle and native packages before calling it exploitable or dismissing it. Run physical-device flows from the [mobile runtime checklist](mobile-runtime-smoke-test.md) after any native migration.

The React Native/Metro upgrade needs its own design and platform/device acceptance criteria. Background push and store release remain outside the current Epic 4 scope.

The [2026-10-20 migration assessment](mobile-rn-migration-assessment-2026-10-20.md) records the repository's native/toolchain baseline, official release constraints, artifact-evidence gap, and prioritized implementation features. Two fresh audit attempts on that date produced no result in the local Windows environment, so the 34-finding count above remains a dated 2026-10-19 snapshot rather than a newly verified count.
