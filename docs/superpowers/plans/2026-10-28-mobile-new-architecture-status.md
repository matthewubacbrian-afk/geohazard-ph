# Mobile New Architecture status closeout — Implementation Plan

**Goal:** Align the project plan, Epic 4 status, migration assessment, and focused readiness plan with the verified PR #73 merge.

**Base:** Remote main `fb283e6e` contains PR #73's tested head `f98bd22f`. All five exact-head checks passed. Android/iOS Debug and non-published Release builds passed with New Architecture flags. PR #72 and PR #73 iOS reports and all four compact traces match; Android changed only its APK hash and 16 added New Architecture native entries. Nine audit rows remain undetermined, with direct `node-forge` high.

## Tasks

- [x] Mark New Architecture **build** readiness delivered in `PLAN.md`, retaining separate Android/iOS device-flow acceptance and the Android SDK 24/iOS 15.1 support-floor decision.
- [x] Update `docs/project-status.md` and `docs/mobile-rn-migration-assessment-2026-10-20.md` with exact PR #73 evidence, avoiding a device-compatibility or security-clearance claim.
- [x] Close `docs/superpowers/plans/2026-10-27-mobile-new-architecture-readiness.md` with CI, report, merge, and ignored-file preservation evidence.
- [x] Run local package suites, lint, TypeScript/build, structure, local links, and whitespace sequentially: mobile 61/Jest and TypeScript; backend 128 unit/Ruff; ML 72/Ruff; scripts 54 plus 7 subtests and CI-scoped Ruff; web 175, TypeScript, and production build; structure 140 paths, 112 local links, and whitespace. Local Docker-backed integration remains unavailable and requires exact-head backend CI. Native builds require exact-head mobile/iOS CI.
- [x] Independent read-only review found no major overclaim and identified one ambiguous historical table sentence; the sentence was corrected before the PR. Its other minor checklist observation was already addressed by this verification checkpoint.
- [x] Push and open docs-only [PR #74](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/74) after the local gate and independent review.
- [ ] Require five green checks on final head and compare Android/iOS Release reports plus traces against PR #73. Merge only after the gate, then preserve ignored files before removing a clean merged worktree.

## Resume state

Branch `docs/mobile-new-arch-status` starts at remote main `fb283e6e`; [PR #74](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/74) is open with last pushed head `71532af8`. All local checks above passed; independent review's wording fix is committed. Next: commit/push this PR checkpoint, require five exact-head checks and both Release-report comparisons against PR #73, then merge only after the full gate. Physical-device flows, supported framework migration, staging host, and Epic 5 approval remain open.
