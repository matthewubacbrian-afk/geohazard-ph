# Mobile Android CI SDK Setup — Design

**Date:** 2026-10-09

## Problem

Pull request #17 adds an Android debug build to Mobile CI. Its JavaScript tests
pass, but the workflow fails inside `android-actions/setup-android@v3` before the
explicit SDK installation and Gradle build steps. The action defaults to installing
the SDK package named `tools`; the Android SDK manager reports that package is not
available. This leaves the native Android project unverified in CI.

## Goals

- Prevent the setup action from requesting the unavailable `tools` package.
- Keep SDK package installation explicit and versioned in
  `.github/workflows/mobile-ci.yml`.
- Pass the mobile Jest suite and Android `assembleDebug` job on the PR branch.

## Non-goals

- Build or sign an iOS application; that requires macOS and Xcode.
- Change React Native application code, dependencies, SDK levels, or Gradle files.
- Merge the pull request or change repository branch protection.

## Context And Constraints

- The failing run is `37882128310` for commit `ff9ab974ce91b89080d00d322532f25bfd712c6f`.
- The failing step is `android-actions/setup-android@v3`; the following SDK install
  and Gradle steps were skipped.
- The action's documented `packages` input defaults to `tools platform-tools` and
  accepts an empty value to skip additional package installation.
- Preserve the current Android API 34, Build Tools 34.0.0, Platform Tools, NDK
  26.1.10909125, JDK 17, and Gradle debug build requirements.

## Alternatives Considered

1. **Skip the Android build in CI.** Rejected because the PR introduces native
   Android scaffolding and CI should verify it.
2. **Keep the action defaults and retry.** Rejected because the failed package is
   absent from the SDK repository, so retrying does not address the cause.
3. **Skip the action's extra packages and install the declared SDK set explicitly.**
   Chosen because it removes the obsolete package request and keeps the build
   environment reproducible in the workflow.

## Design

### Architecture and data flow

Mobile CI will continue to install Node dependencies and run Jest first. It then
sets up JDK 17 and Android command-line tools, asks the setup action to install no
extra SDK packages, explicitly installs the versions already required by the
project, and runs `./gradlew assembleDebug` from `mobile/android`.

### Components and interfaces

- `.github/workflows/mobile-ci.yml`: set the setup action input `packages: ""`.
- Keep the explicit `sdkmanager` package list and `assembleDebug` command unchanged.
- No application API, schema, or package interface changes.

### Error handling

Setup, SDK installation, and Gradle build failures remain fatal to the CI job.
The log must show the explicit SDK package install and build steps running; a green
Jest step alone does not satisfy this change.

### Data considerations

No application data or credentials are involved. SDK licenses remain accepted by
the setup action as they are today.

## Rollout

Create a focused fix branch from the current PR #17 head. Push only after local
workflow review, then rerun PR CI. Keep the existing PR blocked from merge until
the Android build passes.

## Files

- `.github/workflows/mobile-ci.yml` — avoid the obsolete SDK package while retaining
  explicit Android SDK setup and build steps.

## Testing Strategy

- Run `npm ci` and `npm test -- --runInBand` from `mobile/`.
- Run the Android debug build in GitHub Actions using the declared JDK and SDK
  packages; this Windows host does not have the Android SDK configured.
- Inspect the Actions log to confirm setup, SDK installation, and Gradle build all
  complete successfully.

## Acceptance Criteria

- [ ] `android-actions/setup-android@v3` no longer attempts to install `tools`.
- [ ] The explicit SDK package installation succeeds.
- [ ] Mobile Jest tests pass.
- [ ] `./gradlew assembleDebug` passes in PR CI.
- [ ] The PR status shows all required checks passing before merge.

## Out Of Scope (backlog)

- iOS simulator/device build verification and release signing.
- Android release signing or store distribution.

## Related documents

- Implementation plan: to be created after review at
  `docs/superpowers/plans/2026-10-09-mobile-android-ci-setup.md`.
