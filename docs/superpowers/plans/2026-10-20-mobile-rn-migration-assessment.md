# Mobile React Native migration assessment — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce an evidence-backed, independently shippable sequence for resolving the remaining mobile dependency findings without claiming that an npm finding is reachable in the shipped app.

**Architecture:** Keep the current React Native 0.75.5 app and native projects fixed in this assessment. Compare the lockfile advisory chains with shipped-bundle evidence and official upgrade requirements, then define bounded migration and validation features with explicit gates.

**Tech Stack:** React Native, Metro, npm, Android Gradle, CocoaPods, GitHub Actions, Markdown.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/git-workflow.md`, and `docs/glossary.md`.
- This feature changes documentation only. Do not modify package manifests, lockfiles, native files, app behavior, or generated output.
- Use primary release and package sources for upgrade requirements; distinguish verified facts from proposed policy and unknown device coverage.
- Require each later code-changing implementation plan to specify its rollback triggers and how to restore the preceding coherent dependency and native configuration.
- Run `python scripts/verify_structure.py` and `git diff --check`; require all five CI checks before merge.
- Use Conventional Commits and keep this assessment in its own worktree, branch, and PR.

---

### Task 1: Capture the current graph and platform baseline

**Files:**
- Modify: `docs/mobile-dependency-audit-2026-10-19.md`
- Create: `docs/mobile-rn-migration-assessment-2026-10-20.md`

**Interfaces:**
- Consumes: current `mobile/package.json`, `mobile/package-lock.json`, Android/iOS project files, CI workflows, and npm audit output.
- Produces: a reproducible table of advisory chains, observed package roles, current platform minimums, and evidence gaps.

- [x] **Step 1: Inspect the current lockfile, native project, and CI configuration** on the isolated branch.
- [x] **Step 2: Attempt the current production audit and classify available findings** without equating dependency presence with runtime reachability. Two local attempts returned no output; the dated 2026-10-19 snapshot remains the only count.
- [x] **Step 3: Record a concise baseline** with exact versions, paths, commands, counts, and unresolved evidence.
- [x] **Step 4: Commit** the baseline with a `docs:` Conventional Commit (`d33899a2`).

---

### Task 2: Research a bounded migration sequence

**Files:**
- Modify: `docs/mobile-rn-migration-assessment-2026-10-20.md`, `PLAN.md`, `docs/project-status.md`, this plan

**Interfaces:**
- Consumes: official React Native release and upgrade guidance, package compatibility information, the current platform baseline, and `docs/mobile-runtime-smoke-test.md`.
- Produces: prioritized feature slices, each with exact scope, CI/device checks, and release/rollback conditions.

- [x] **Step 1: Verify platform and toolchain requirements** against primary sources for candidate React Native releases.
- [x] **Step 2: Separate migration slices** by dependency and native impact; put platform-policy and real-device decisions at explicit gates.
- [x] **Step 3: Update the prioritized queue and Epic 4 status** to match the assessment and remaining external evidence.
- [x] **Step 4: Run structure and whitespace verification** and request independent technical review; no critical or important issue was found, and both minor documentation gaps were corrected.
- [x] **Step 5: Commit, push, and open a PR**; merge only after five green CI checks, verify the tested head on remote main, and remove the feature worktree and branches.

## Notes for the executor

This plan is docs-only and does not require new tests that mirror documentation. The implementation features it identifies need separate focused plans and isolated branches. If npm advisory data changes, record the date and exact command; do not rewrite the 2026-10-19 historical snapshot as though it were current.

[PR #53](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/53) merged at `9fd7ec19` after independent Astra review and five green CI checks. The tested head was verified on remote main, and the isolated worktree and local/remote branches were removed. Local backend unit tests passed 128/128, ML tests passed 72/72, and Python lint, structure, and whitespace checks passed. The full local backend integration run stopped at its first service-dependent test; clean CI supplied the complete suite and native builds.
