# Mobile New Architecture status closeout — Implementation Plan

**Goal:** Align the project plan, Epic 4 status, migration assessment, and focused readiness plan with the verified PR #73 merge.

**Base:** Remote main `fb283e6e` contains PR #73's tested head `f98bd22f`. All five exact-head checks passed. Android/iOS Debug and non-published Release builds passed with New Architecture flags. PR #72 and PR #73 iOS reports and all four compact traces match; Android changed only its APK hash and 16 added New Architecture native entries. Nine audit rows remain undetermined, with direct `node-forge` high.

## Tasks

- [ ] Mark New Architecture **build** readiness delivered in `PLAN.md`, retain separate Android/iOS device-flow acceptance and the Android SDK 24/iOS 15.1 support-floor decision.
- [ ] Update `docs/project-status.md` and `docs/mobile-rn-migration-assessment-2026-10-20.md` with exact PR #73 evidence, avoiding a device-compatibility or security-clearance claim.
- [ ] Close `docs/superpowers/plans/2026-10-27-mobile-new-architecture-readiness.md` with CI, report, merge, and ignored-file preservation evidence.
- [ ] Run local package suites, lint, TypeScript/build, structure, local links, and whitespace sequentially. Docker-backed integration and native builds are covered by exact-head CI.
- [ ] Push, open a docs-only PR, require five green checks on final head and compare Android/iOS Release reports plus traces against PR #73. Merge only after the gate, then preserve ignored files before removing a clean merged worktree.

## Resume state

Branch `docs/mobile-new-arch-status` starts clean at remote main `fb283e6e`; no PR yet. The plan is the first branch change. Next: commit/push this plan, edit only the tracking docs, then verify the local and CI gate. Physical-device flows, supported framework migration, staging host, and Epic 5 approval remain open.
