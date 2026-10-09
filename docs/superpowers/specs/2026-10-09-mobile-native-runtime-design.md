# Mobile Native Runtime — Design

**Date:** 2026-10-09

## Problem

Epic 4 added saved locations, offline event caching, and foreground nearby alerts, but the
mobile package still has no native app entrypoint and its `android/` and `ios/` folders only
contain `.gitkeep`. The package therefore cannot currently be built or launched as a native
app. Its `app.json` name contains spaces, which is unsuitable for React Native's registered
native component name.

## Goals

- Add standard Android and iOS native projects compatible with the installed React Native
  0.75.5 line without replacing the existing application code or upgrading frameworks.
- Add the React Native `AppRegistry` entrypoint and a valid native module name while keeping
  the human-facing app label `GeoHazard PH`.
- Ensure AsyncStorage can be discovered through React Native autolinking in both native
  projects.
- Add convenient Android/iOS launch scripts and clear development environment instructions.
- Run Android debug compilation in mobile CI; continue running the mobile Jest suite.
- State clearly that this workstation lacks Android SDK tools and uses Java 25, so local
  Android/device verification is unavailable until the documented JDK 17 and SDK are set up.

## Non-goals

- Background push notifications, credentials, tokens, or server-side subscriptions.
- Store signing, release builds, publishing, or production API URLs.
- Expo migration, React Native upgrades, or unrelated mobile UI changes.
- Claiming a simulator or physical-device test without an available native runtime.

## Context And Constraints

- `mobile/package-lock.json` resolves React Native 0.75.5 and React 18.3.1.
- AsyncStorage 1.24.0 is already the selected storage version and must remain compatible.
- React Native Community CLI 14.x matches React Native 0.75.x; CLI documentation warns
  against independently changing the CLI major.
- The package has `babel.config.js` and `metro.config.js`, but no root `index.js`.
- Windows can build Android with Java 17 and Android SDK tooling; iOS compilation requires
  macOS/Xcode/CocoaPods. This workstation currently exposes Java 25 and no `adb` or
  `ANDROID_HOME`/`ANDROID_SDK_ROOT`.
- Mobile service tests use Jest in Node and do not require native files or an emulator.

## Alternatives Considered

1. **Generate bare native projects for both platforms (chosen).** This preserves the app's
   existing React Native architecture and AsyncStorage integration. Android build verification
   can run in CI; iOS build verification requires a Mac.
2. **Migrate to Expo.** This can improve device preview and native workflows but changes the
   framework and dependency/tooling model beyond the current readiness gap.
3. **Generate Android only.** This is easier to validate on the current OS but leaves iOS
   unsupported and does not fulfill the approved two-platform scope.

## Design

Generate the native folders using the React Native Community CLI 14.x template at the exact
installed React Native version. Preserve the existing `src/` screens, navigation, services,
tests, and Metro/Babel configuration. Configure `mobile/app.json` with the module name
`GeoHazardPH` and display label `GeoHazard PH`; add `mobile/index.js` to register the existing
`App` component. Use `com.geohazardph.mobile` as a development-only Android application ID and
iOS bundle identifier, explicitly replaceable before distribution.

The native projects use default autolinking so AsyncStorage 1.24.0 is linked from the existing
package. Add `android`, `ios`, `start`, and `test` npm scripts. Extend mobile CI to install with
the lockfile, run Jest, set up Java 17 and Android SDK tooling, and run the generated Android
debug Gradle build. Document Android Studio/SDK/JDK requirements, Metro/device run commands,
LAN API URL considerations, and the macOS-only iOS build step.

No new app behavior or permissions are introduced. The current empty API URL and on-device
saved locations remain unchanged. HTTP cleartext must not be enabled for release builds; use a
device-reachable HTTPS URL for production.

## Rollout

Land this as a focused feature branch based on merged `main`. The first Android build may run
in CI even when local SDK tooling is unavailable. A macOS runner/device remains necessary to
verify the iOS target. No backend, database migration, or production secret is involved.

## Files

### Mobile package

- `mobile/android/**` — generated Android application and Gradle configuration.
- `mobile/ios/**` — generated iOS application, Xcode project, and CocoaPods configuration.
- `mobile/app.json` — valid registered component name and display name.
- `mobile/index.js` — React Native application entrypoint.
- `mobile/package.json`, `mobile/package-lock.json` — platform scripts and Metro config dependency pinned to RN 0.75.5.
- `mobile/.gitignore` — generated native/build output ignore rules.
- `mobile/tests/appEntrypoint.test.ts` — registration name and AppRegistry regression coverage.
- `mobile/tests/metroConfig.test.ts` — Metro configuration dependency regression coverage.

### CI and documentation

- `.github/workflows/mobile-ci.yml` — lockfile install, Jest, and Android debug build.
- `scripts/verify_structure.py` — require native app entrypoint and representative Android/iOS project files instead of empty platform placeholders.
- `scripts/tests/test_verify_structure.py` — regression coverage for native scaffold expectations.
- `README.md` — native setup and run instructions and platform-specific limitations.
- `docs/superpowers/plans/2026-10-09-mobile-native-runtime.md` — implementation and verification record.

## Testing Strategy

- From `mobile/`, run `npm ci` and `npm test -- --runInBand`.
- Run TypeScript validation for `src/App.tsx` using the existing project-compatible command.
- Run `npx react-native config` from `mobile/` to verify CLI discovery and native-module
  autolinking configuration.
- Generate an Android JavaScript bundle with Metro to verify the real entrypoint and app graph.
- Run `gradlew.bat assembleDebug` only if Java 17 and Android SDK are available. CI must run
  `./gradlew assembleDebug` with Java 17 and Android SDK tooling.
- Run `python scripts\verify_structure.py` and `git diff --check` from the repository root.
- Do not claim an iOS build or real-device run on this Windows host.

## Acceptance Criteria

- [ ] React Native CLI reports both Android and iOS projects and discovers AsyncStorage.
- [ ] The native entrypoint registers `GeoHazardPH`; visible app branding remains `GeoHazard PH`.
- [ ] `npm ci`, the full mobile Jest suite, and the TypeScript check pass.
- [ ] Mobile CI is configured to compile the Android debug app with Java 17 and Android SDK tooling.
- [ ] Metro produces an Android bundle from `mobile/index.js`.
- [ ] README gives reproducible environment setup and run commands for Android and iOS and
  accurately states host-platform limitations.
- [ ] Structure verification and `git diff --check` pass.
- [ ] The structure verifier checks a native entrypoint and platform project files rather than the removed `.gitkeep` placeholders.

## Out Of Scope (backlog)

- iOS compilation/device verification on a Mac and Android emulator/physical-device UX review.
- Store signing and release distribution configuration.
- Background push delivery and provider selection.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-09-mobile-native-runtime.md`.
- Terminology: `docs/glossary.md`.
