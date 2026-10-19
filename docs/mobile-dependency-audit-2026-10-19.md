# Mobile dependency audit — 2026-10-19

This record tracks the mobile production-dependency graph at the current lockfile, not a claim that each advisory is reachable in the distributed Android or iOS app. Run the commands from `mobile/` on a clean checkout. Audit results can change as npm advisory data changes.

## Verified snapshot

| State | Moderate | High | Critical | Total |
| --- | ---: | ---: | ---: | ---: |
| Before [PR #50](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/50) | 10 | 31 | 1 | 42 |
| After PR #50, before this refresh | 10 | 31 | 0 | 41 |
| After compatible lockfile refresh | 10 | 28 | 0 | 38 |

The last two rows come from `npm audit --omit=dev --json` on 2026-10-19. This refresh ran `npm audit fix --package-lock-only --omit=dev --ignore-scripts --no-fund` without `--force` and changed only these `mobile/package-lock.json` resolutions:

| Transitive package | Before | After | Result |
| --- | --- | --- | --- |
| `brace-expansion` | 1.1.18 | 1.1.21 | High finding removed |
| `compression` | 1.8.1 | 1.8.2 | High finding removed |
| `joi` | 17.13.6 | 17.13.8 | High finding removed |

`mobile/package.json`, React Native 0.75.5, React Navigation 6.1.18, and native configuration remain unchanged. The new `compression` lock entry records its `destroy` dependency and funding metadata; no separate package entry was added because `destroy` was already resolved elsewhere in the lockfile. A clean install plus Jest, TypeScript, Android, and iOS builds are required before this result can merge.

## Remaining findings and action

The remaining 38 npm findings are a dependency-chain count, including packages that inherit an affected transitive dependency. npm groups 27 under its proposed React Native 0.88.0 major upgrade, four under React Navigation 7.5.1, and seven as `fixAvailable: true`. The seven include upstream chain entries; running the non-forced fix left them unresolved. In particular, `image-size` 1.2.1 enters through Metro and is within the advisory range. Metro currently requests `image-size` `^1.0.2`, while the available patched line is 2.0.4; do not override that major API boundary without a Metro compatibility review. See the [image-size advisories](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq) and [second advisory](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr).

1. **Remove the unused navigation dependency in its own PR.** `@react-navigation/native` is a direct dependency, but a repository search of mobile source and configuration found no import or use; `RootNavigator` implements local tab state. Removing the package and its lock graph should be tested with Jest, TypeScript, Android, and iOS builds and a fresh audit. The four moderate findings currently flow through `@react-navigation/core` → `query-string` → `decode-uri-component`; [React Navigation's 6-to-7 guide](https://reactnavigation.org/docs/upgrading-from-6.x/) is relevant only if the package becomes necessary again. Do not claim the findings are gone until the removal is verified.
2. **Design the React Native and Metro migration separately.** The remaining high and moderate chains include CLI, Metro, Jest/codegen, `braces`, `node-forge`, `fast-xml-parser`, and `sprintf-js`. npm proposes React Native 0.88.0 for 27 entries; that is a major native-platform change, not a lockfile refresh. [React Native 0.76's release notes](https://reactnative.dev/blog/2024/10/23/release-0.76-new-architecture) already enable the New Architecture by default and raise minimum iOS from 13.4 to 15.1 and Android from SDK 23 to 24. This repo currently sets Android minimum SDK 23. Review intervening release notes, library compatibility, Gradle/Pods, and supported-device policy before choosing upgrade steps.
3. **Establish exposure with build evidence.** Package paths suggest many findings are in development, bundling, or CLI tooling, while React Native is the app framework. `npm audit --omit=dev` still includes them in this dependency graph. There is no recorded compiled-bundle or app-package reachability analysis; classify each advisory against the actual shipped JS bundle and native packages before calling it exploitable or dismissing it. Run physical-device flows from the [mobile runtime checklist](mobile-runtime-smoke-test.md) after any native migration.

The next independently shippable change is the unused navigation dependency removal. The React Native/Metro upgrade needs its own design and platform/device acceptance criteria. Background push and store release remain outside the current Epic 4 scope.
