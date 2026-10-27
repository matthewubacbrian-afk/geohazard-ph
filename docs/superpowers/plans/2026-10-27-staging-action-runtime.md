# Staging workflow action refresh — Implementation Plan

**Goal:** Refresh the staging workflow's remaining deprecated actions and Linux runner while preserving its held-export mode and main-only publication guard.

**Architecture:** Update only action majors and runner labels in `deploy-staging.yml`. Use the same maintained actions verified by PR #70: checkout v7, setup-python v7, setup-node v7, upload-artifact v7, and Ubuntu 24.04. Keep Docker actions, build inputs, artifact paths (including `.env.staging.example`), permissions, and the publication guard unchanged. Dispatch the workflow on this feature branch to exercise verification with publication skipped.

**Tech Stack:** GitHub Actions, Python 3.12, Node 22, Docker Compose configuration, unittest.

## Constraints and evidence

- Follow the repository coding, Git, and testing standards. Commit and push the plan before workflow edits.
- Preserve the Epic 5 hold, all current advisory dispositions, and the five automatic PR checks.
- Require local package tests/lint/types/build, structure, links, and whitespace. Record unavailable Docker integration accurately.
- Require five passing checks on the final PR commit and Android/iOS report/trace comparison with PR #70. The PR #71 Android audit feed now returns nine rows rather than the dated 12-row baseline; accept this drift only if both platforms show the exact three inherited-row removals and React Native inherited-severity/via change described below. All remaining rows must stay `undetermined`, all other report fields and compact traces must match, and only the Android APK hash may additionally differ. Stop if either platform has another difference.
- Additionally dispatch `deploy-staging.yml` on the feature branch and verify the run's SHA, successful `verify` job, and skipped `publish` job. Do not dispatch it on main for this maintenance slice.
- This validates the staging verification path and configuration compatibility. It does not exercise publication, deploy a host, or establish live staging/device evidence.

## Tasks

- [x] Record PR #70 merged at `fcf8c0b6` from tested head `cf95281f`, update tracking, and commit/push this plan. Plan commit `4176f424` is pushed.
- [x] Update `.github/workflows/deploy-staging.yml` action majors and Linux runner labels. Inspect the diff to preserve the main-only publication guard, held-export verification, registry/image configuration, and hidden example-env artifact. Existing Compose checks and 54 script tests plus 7 subtests passed, with staging-script Ruff clean.
- [x] Run existing staging configuration and deployment tests and full local checks. Existing Compose check, 54 script tests plus 7 subtests, backend 128 unit tests and Ruff, ML 72 tests and Ruff, mobile 61 tests and TypeScript, web 175 tests and production build, structure 140 paths, 115 local links, and whitespace passed. Local backend integration remains unavailable because the Docker engine did not respond; require CI.
- [x] Commit/push the verification record, open PR #71, and dispatch branch-only staging verification. Run 40479866255 verified commit `fb03e095` with `verify` successful and `publish` skipped. The independent workflow review of `619d15ba` found no actionable issues.
- [x] Inspect five CI results and the manual verification run for the same commit; compare both Release reports and compact traces with PR #70. Five checks passed on `da7d3189`; branch-only run `40482711712` passed `verify` and skipped `publish`. Both final reports had the exact nine-row audit-feed delta; only the Android APK hash also differed. All compact traces matched.
- [x] Merge after verification, confirm tested commit on remote main, preserve ignored files, remove only the clean merged feature worktree/branches, and update tracking. PR #71 merged at `271310fd`; `da7d3189` is an ancestor of remote main. All 25 ignored paths were preserved at `C:\Users\matth\.codex\preserved-worktree-ignored\ci-staging-action-runtime-2026-10-27` before the clean worktree and branches were removed. Tracking is reconciled in the separate PR #71 status closeout slice.

## Files

- `.github/workflows/deploy-staging.yml`
- `PLAN.md`, `docs/project-status.md`, `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- `docs/superpowers/plans/2026-10-26-ci-action-runtime-pr-workflows.md`
- This plan

## Remaining gates

The updated publication job still needs a future authorized main-branch release run. OCI/DNS and live-host evidence, physical-device flows, the framework support-floor decision, and Epic 5 domain approval remain independent.

## Audit-feed drift observed on PR #71

Both final Release reports for `da7d3189` have nine rows versus PR #70's 12. The inherited `@react-native/community-cli-plugin`, `@react-native/dev-middleware`, and `selfsigned` rows disappeared; the inherited `react-native` row changed from high to moderate and lost only its CLI-plugin `via_packages` link. The direct `node-forge` row remains high and `undetermined`; all nine rows remain `undetermined`. The mobile lockfile is unchanged. An independent reviewer identified and corrected an over-permissive comparison; exact reconstructed JSON and all four compact traces match PR #70, apart from the Android APK hash. This records audit-feed drift, not a vulnerability clearance or a device finding.

## Historical resume state

The earlier checkpoint was branch `ci/staging-action-runtime`, [PR #71](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/71), with local staging checks, backend 128/Ruff, ML 72/Ruff, mobile 61/TypeScript, web 175/build, structure, links, and whitespace passed. Docker-backed local integration was unavailable, but staging CI integration passed. The final gate and merge are recorded above; New Architecture readiness is next after tracking closeout.
