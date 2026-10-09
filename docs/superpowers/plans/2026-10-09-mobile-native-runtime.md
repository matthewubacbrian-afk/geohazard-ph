# Mobile Native Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the merged Epic 4 React Native app buildable for Android and iOS while retaining the existing app behavior.

**Architecture:** Generate bare native projects from the React Native 0.75 template using its compatible Community CLI major. Connect those projects to the existing React Native app through `AppRegistry`, keep AsyncStorage under normal autolinking, and add an Android CI build because this Windows host lacks the SDK.

**Tech Stack:** React Native 0.75.5, Community CLI 14.x, React 18, TypeScript, Gradle, Xcode/CocoaPods, Jest, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-09-mobile-native-runtime-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Preserve React Native 0.75.5 and use Community CLI 14.x; do not upgrade or migrate frameworks.
- Keep native project files generated from the matching 0.75.5 template; do not hand-edit generated
  build logic unless a required app integration setting needs it.
- Use `GeoHazardPH` as the registered module name and `GeoHazard PH` as the display label.
- Use `com.geohazardph.mobile` only as a development identifier; no signing or publishing config.
- Do not commit local SDK paths, secrets, build outputs, caches, or personal API URLs.
- Run mobile tests, TypeScript validation, React Native CLI config, structure verification, and
  `git diff --check`; report native builds only when actually run.

---

## Task 1: Generate and connect native application projects

**Files:**
- Replace placeholder: `mobile/android/.gitkeep` with generated Android project files.
- Replace placeholder: `mobile/ios/.gitkeep` with generated iOS project files.
- Modify: `mobile/app.json`.
- Create: `mobile/index.js`.
- Modify: `mobile/package.json`.
- Create: `mobile/.gitignore` from the matching React Native native template.
- Modify: `mobile/package-lock.json` for the Metro config dependency.
- Test: `mobile/tests/appEntrypoint.test.ts`, `mobile/tests/metroConfig.test.ts`.

**Interfaces:**
- Consumes: existing `mobile/src/App.tsx` and React Native 0.75.5 app package.
- Produces: root `index.js` registering `App` under `GeoHazardPH`; Android and iOS projects
  using development identifier `com.geohazardph.mobile`; npm scripts `start`, `android`, `ios`,
  and `test`.

- [x] Generate template into a temporary directory using Community CLI 14.1.2 and React Native 0.75.5 with `--package-name com.geohazardph.mobile`; do not generate over the existing app.
- [x] Copy only generated `android/` and `ios/` project contents into the matching placeholders and include the native `.gitignore`.
- [x] Set the native module name to `GeoHazardPH`, display label to `GeoHazard PH`, and development application ID/bundle ID to `com.geohazardph.mobile`.
- [x] Add `index.js` that imports `AppRegistry` from `react-native`, imports `App` from `./src/App`, reads `appName` from `./app.json`, and registers it. Its regression test failed first on the invalid name/missing entrypoint, then passed.
- [x] Add `android` and `ios` scripts while retaining existing `start` and `test`; the existing `start` script remains unchanged and React Native 0.75.5 resolves Community CLI/platform commands at 14.1.0.
- [x] Run `npm ci` from `mobile/`, then `npx react-native config`; both platform paths are discovered and AsyncStorage is autolinked for Android and iOS.
- [x] Add the missing direct `@react-native/metro-config@0.75.5` dev dependency required by the existing Metro config, with a test that failed on the missing package before installation.

## Task 2: Add reproducible Android native-build CI

**Files:**
- Modify: `.github/workflows/mobile-ci.yml`.

**Interfaces:**
- Consumes: `mobile/package-lock.json` and generated `mobile/android/gradlew`.
- Produces: a pull-request and `main` CI job that runs locked npm install, Jest, and Android
  `assembleDebug` on an Ubuntu runner with Java 17 and Android SDK.

- [x] Change mobile dependency installation from `npm install` to lockfile-based `npm ci`.
- [x] Preserve the mobile Jest step.
- [x] Configure Java 17 and Android SDK on the Ubuntu runner, then run `./gradlew assembleDebug` from `mobile/android`.
- [x] Keep signing, publishing, and secrets out of this workflow.

## Task 3: Document native setup and platform verification

**Files:**
- Modify: `README.md`.
- Modify: `docs/superpowers/plans/2026-10-09-mobile-native-runtime.md`.
- Modify: `scripts/verify_structure.py`.
- Test: `scripts/tests/test_verify_structure.py`.

**Interfaces:**
- Produces: documented Android setup/launch commands and iOS macOS/Xcode/CocoaPods setup and
  launch commands; clearly distinguishes local test coverage from device/build verification.

- [x] Document JDK 17, Android Studio/SDK requirements, `npm ci`, Metro, emulator/device startup, and the Android launch command.
- [x] Document Xcode/CocoaPods as Mac-only prerequisites and give the `pod install` and iOS launch commands.
- [x] Explain that Android device API URLs must be reachable from that device and that cleartext HTTP is development-only.
- [x] State this host's Java 25/no-SDK limitation without reporting an unrun native build as passing.

## Task 4: Verify and record results

**Files:**
- Modify: `docs/superpowers/plans/2026-10-09-mobile-native-runtime.md`.

**Interfaces:**
- Consumes: Task 1 native files, Task 2 CI definition, Task 3 documented commands.
- Produces: recorded pass/fail/skipped results for Jest, type check, CLI config, structure check,
  whitespace check, and available native builds.

- [x] Run `npm test -- --runInBand` from `mobile/`: 8 suites and 31 tests pass.
- [x] Run the existing TypeScript check and `npx react-native config` from `mobile/`; both pass.
- [x] Run `python -m unittest discover -s scripts/tests -v` and `python scripts\verify_structure.py` from repository root; one test passes and all 140 expected paths exist.
- [x] Run `git diff --check` from repository root after all documentation updates; both the working-tree and staged checks pass.
- [x] Check local Android tooling: Java 25 is present; `adb`, `ANDROID_HOME`, and `ANDROID_SDK_ROOT` are absent, so local Android/device build is unavailable. CI is configured for the Android debug build.
- [x] Generate an Android JavaScript bundle with Metro (`--max-workers 2`) to verify the registered entrypoint and module graph.
- [x] Record iOS/device verification as outstanding because this Windows host has no iOS/Xcode or Android device runtime.

## Notes for the executor

- Run mobile commands from `mobile/`; run structure and repository checks from the repository root.
- The Metro bundle output and copied assets belong under the operating-system temporary directory,
  not in the repository.
- This host has Java 25 but no Android SDK or emulator. The generated Gradle wrapper is 8.8, which
  does not officially support running on Java 25; use JDK 17 for local Android builds.
- Android debug CI is configured but cannot be observed until the feature branch is pushed and CI
  runs. The iOS project is generated but needs a Mac/Xcode and CocoaPods for build verification.
- Keep push notifications, release signing, and production identifiers out of this feature.
