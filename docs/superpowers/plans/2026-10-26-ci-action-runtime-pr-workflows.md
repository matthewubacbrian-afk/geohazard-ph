# PR workflow action-runtime refresh — Implementation Plan

> **For agentic workers:** Use the executing-plans workflow for this bounded CI change. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace deprecated action runtimes in the four automatic PR workflows while preserving the five checks and Android/iOS Release evidence.

**Architecture:** Pin Linux jobs to Ubuntu 24.04, update maintained action majors in backend, ML, web, and mobile CI, and keep the existing action inputs, SDK versions, build commands, artifact names, and report schemas. Update the two existing mobile-workflow tests that name action majors. The manually dispatched staging workflow is a separate follow-up because these five PR checks do not exercise it.

**Tech Stack:** GitHub Actions, Python unittest, Node 22, React Native 0.75.5, Android Gradle, Xcode simulator.

## Global constraints

- Follow `CODING_STANDARDS.md`, `docs/git-workflow.md`, and `docs/testing-standards.md`; use Conventional Commits.
- Keep `main` deployable, the Epic 5 profile export held, and all 12 current mobile advisory rows `undetermined` unless the live evidence requires a separately reviewed update.
- Do not change app/runtime dependencies, SDK levels, native build commands, Release-report JSON, compact trace schemas, artifact names, or retention. Do not publish APK/IPA binaries.
- Local gate: script, backend unit, ML, web, and mobile tests; backend/ML Ruff; mobile TypeScript; web build; structure and whitespace. Backend integration needs Docker, otherwise exact-head CI supplies it.
- Merge gate: all five checks green on one PR head, then compare both final Release reports and compact process/image traces against merged PR #69. Investigate any difference beyond the Android APK hash before merge.

## Verified source assumptions — 2026-10-26

- The [official checkout releases](https://github.com/actions/checkout/releases), [setup-node releases](https://github.com/actions/setup-node/releases), [setup-python releases](https://github.com/actions/setup-python/releases), [setup-java releases](https://github.com/actions/setup-java/releases), [upload-artifact releases](https://github.com/actions/upload-artifact/releases), and [setup-android releases](https://github.com/android-actions/setup-android/releases) expose maintained major tags `v7`, `v7`, `v7`, `v6`, `v7`, and `v4`, respectively. Recheck the actual tags before editing.
- The observed PR #69 hosted runner version was 2.338.0, above the 2.327.1 minimum required by Node 24 actions. Keep application Node at 22; action runtime and project runtime are separate.
- [setup-android's documented empty `packages` input](https://github.com/android-actions/setup-android#additional-packages) still skips its default package installation. Retain the explicit SDK installation that follows it.
- [upload-artifact v7](https://github.com/actions/upload-artifact) retains `name`, `path`, `if-no-files-found`, and `retention-days`; the six mobile artifact names are distinct.

### Task 1: Record merged evidence and plan the scope

**Files:** `PLAN.md`, `docs/project-status.md`, `docs/mobile-advisory-attack-path-gates-2026-10-21.md`, `docs/superpowers/plans/2026-10-25-mobile-node-forge-path.md`, this plan.

**Interfaces:** Record PR #69's tested head, merge commit, five CI results, Android/iOS comparison, and cleanup limits. Split automatic PR action maintenance from manual staging action maintenance in the priority queue.

- [x] **Step 1: Reconcile** tracking with GitHub and the downloaded PR #69 reports.
- [x] **Step 2: Commit and push** the plan and tracking before changing workflows. Committed and pushed as `b1be9f39`.

### Task 2: Update action versions without changing build behavior

**Files:** `.github/workflows/backend-ci.yml`, `.github/workflows/ml-ci.yml`, `.github/workflows/web-ci.yml`, `.github/workflows/mobile-ci.yml`, `scripts/tests/test_mobile_ci_workflow.py`.

**Interfaces:** Use `actions/checkout@v7`, `actions/setup-node@v7`, `actions/setup-python@v7`, `actions/setup-java@v6`, `actions/upload-artifact@v7`, and `android-actions/setup-android@v4` where present. Use `ubuntu-24.04` for the four Linux jobs; keep `macos-15` for iOS.

- [x] **Step 1: Update the existing test assertions** for the new upload and Android-setup major tags; run that focused test and verify the old workflow fails for the expected string mismatch. Before the workflow edit, eight tests ran with one expected assertion failure and one expected missing-tag error.
- [x] **Step 2: Edit only the four PR workflows** and rerun the focused test. Inspect the full diff for unchanged commands, inputs, and artifact paths. The same eight tests pass after the action-tag edit.
- [ ] **Step 3: Commit and push** the bounded workflow/test change.

### Task 3: Verify and deliver

**Files:** this plan and the tracking docs only if verification reveals a necessary correction.

- [ ] **Step 1: Run** local package tests, type/build/lint, structure, links, and whitespace sequentially; record unavailable services without claiming a pass.
- [ ] **Step 2: Open a PR** with actual local results; require all five exact-head checks and both Release report/trace comparisons with PR #69.
- [ ] **Step 3: Merge only when green**, verify tested head on remote main, preserve ignored paths, remove only this clean merged worktree and branches, and synchronize tracking.

## Notes for the executor

- Do not update `deploy-staging.yml` in this slice: it is manually dispatched and needs a separate validation gate.
- A Node 24 action runtime does not upgrade the application Node 22 toolchain or React Native framework.
- If a new action changes artifact layout or native output, investigate rather than relaxing the comparison gate.
