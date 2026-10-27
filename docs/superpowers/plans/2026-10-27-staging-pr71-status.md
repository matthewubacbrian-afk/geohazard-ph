# PR #71 staging status closeout — Implementation Plan

**Goal:** Reconcile current plan, status, and advisory tracking with the verified staging-workflow merge without changing application or deployment behavior.

**Base:** Remote main `271310fd` includes PR #71's tested `da7d3189`. Its five PR checks passed; branch-only staging run `40482711712` passed verification and skipped publication. Both final Release reports matched PR #70 except the exact reviewed audit-feed change from 12 to 9 undetermined rows and the Android APK hash. The direct `node-forge` finding remains high and undetermined.

## Tasks

- [x] Update `PLAN.md` to mark staging workflow maintenance complete and record the current nine-row audit, preserving the dated 34- and 12-row baselines and all epic holds.
- [x] Update `docs/project-status.md` and `docs/mobile-advisory-attack-path-gates-2026-10-21.md` with PR #71's merge, current audit count, and unresolved device, staging-host, and Epic 5 gates.
- [x] Close the focused staging plan with final run, report, merge, and cleanup evidence. Keep its earlier resume checkpoint as historical.
- [x] Verify local package suites, lint, TypeScript/build, structure, links, and whitespace sequentially. Staging mode check, 54 script tests plus 7 subtests, script Ruff, backend 128 unit tests/Ruff, ML 72 tests/Ruff, mobile 61 tests/TypeScript, web 175 tests/TypeScript/production build, structure 140 paths, 115 local links in eight documents, and whitespace passed. Docker-backed local integration was unavailable; PR CI must cover it. An independent read-only review found and verified corrections to two dated/merge-attribution sentences.
- [ ] Push, open a docs-only PR, require five green checks on the final head, compare Android/iOS Release reports and compact traces with PR #71 (only Android APK hash may differ), merge, and preserve any ignored files before removing the clean worktree and branch.

## Resume state

Branch `codex/staging-pr71-status` started at remote main `271310fd` and is pushed through tracking edit `977d7fed`; no PR yet at this checkpoint. All local checks listed above passed; local Docker-backed integration remains unavailable. Next: commit/push this verification record and reviewer fixes, open the docs PR, then require all five checks and unchanged Release reports/traces apart from the Android APK hash. New Architecture readiness follows this tracking closeout.
