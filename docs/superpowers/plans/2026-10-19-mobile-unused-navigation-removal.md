# Mobile unused navigation removal — Implementation Plan

> **For agentic workers:** Remove one unused direct package, verify the resulting dependency graph and all five CI checks, then update the tracked release evidence.

**Goal:** Remove `@react-navigation/native`, which is declared but unused by the current mobile app, without changing app navigation behavior.

**Architecture:** The app's `RootNavigator` owns tab state directly and imports no React Navigation module. Remove the unused declaration through npm so the lockfile prunes its transitive graph, then run source checks, a production audit, mobile tests/TypeScript, and Android/iOS builds. Keep React Native and native project configuration fixed.

**Tech Stack:** npm, React Native 0.75, Jest, TypeScript, Android and iOS CI.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Use Conventional Commits. Do not commit secrets, generated build output, caches, or raw audit JSON.
- Do not use `npm audit fix --force`; do not change React Native, unrelated direct dependencies, app source, or native configuration in this slice.
- A source search establishes that this repository does not import React Navigation; it does not prove distributed-app exploitability or guarantee the audit count. Verify the actual lockfile graph and audit after removal.
- Run the package suites, Python Ruff, structure and whitespace checks, and require all five CI checks, including Android and iOS simulator builds, before merge. Note local environment limits accurately.

---

### Task 1: Record the baseline and plan

**Files:**
- Modify: `PLAN.md`, `docs/project-status.md`, `docs/superpowers/plans/2026-10-19-mobile-compatible-dependency-refresh.md`
- Create: this plan

**Interfaces:**
- [PR #51](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/51) merged with a 38-finding production audit (10 moderate, 28 high, zero critical).
- `mobile/package.json` declares `@react-navigation/native` `^6.1.18`, and the lockfile resolves 6.1.18. `rg` finds no mobile import or `NavigationContainer`; `RootNavigator` uses local tab state.

- [x] **Step 1: Verify merged baseline and package use** in source and configuration.
- [x] **Step 2: Commit this tracked plan** before editing package files.

---

### Task 2: Remove the unused package

**Files:**
- Modify: `mobile/package.json`, `mobile/package-lock.json`

**Interfaces:**
- Use `npm uninstall @react-navigation/native --package-lock-only --ignore-scripts --no-audit --no-fund`.
- Require `npm ls @react-navigation/native --package-lock-only --all` to show it absent, and require the lockfile to retain React Native 0.75.5 and unrelated direct resolutions.

- [x] **Step 1: Remove the dependency** and inspect every lockfile change for related pruning only.
- [x] **Step 2: Rerun `npm audit --omit=dev --json`** and record exact before/after counts, including any findings that remain.
- [x] **Step 3: Verify navigation behavior** through the existing mobile suite and TypeScript where the local environment permits; native CI is required.
- [x] **Step 4: Commit** package changes with a Conventional Commit message.

---

### Task 3: Record evidence and integrate

**Files:**
- Modify: `docs/mobile-dependency-audit-2026-10-19.md`, `PLAN.md`, `docs/project-status.md`, this plan

**Interfaces:**
- Replace the prospective navigation-removal claim with measured audit and source evidence. Keep React Native/Metro migration and physical-device flow checks open.

- [x] **Step 1: Update the audit record and project tracking** with exact results.
- [x] **Step 2: Run all package suites, linters, structure, and whitespace checks**; document any local limit.
- [x] **Step 3: Request independent review** of the package graph and behavior claim.
- [x] **Step 4: Push and open a PR**; merge only after five green CI checks, verify the tested head on remote main, and remove this worktree and branch.

## Notes for the executor

This is dependency removal, not a navigation rewrite. Do not add a test that merely asserts a package is absent; the relevant behavior checks are the existing tab-flow tests, TypeScript resolution, and native builds. The [audit record](../../mobile-dependency-audit-2026-10-19.md) explains why the larger React Native/Metro advisory cluster remains a separate migration.

`npm uninstall --package-lock-only` removed the direct declaration and 12 orphaned lockfile packages, with no other dependency resolution or native file change. `npm ls @react-navigation/native --package-lock-only --all` reports an empty tree; React Native remains 0.75.5. The production audit fell from 38 findings (10 moderate, 28 high, zero critical) to 34 (six moderate, 28 high, zero critical). Clean CI must verify that navigation behavior and native builds remain intact.

Local Windows `npm ci --no-audit --no-fund` remained incomplete and was stopped before Jest or TypeScript became runnable. Backend and ML Ruff, the 140-path structure check, and `git diff --check` passed; the full package suites and native builds remain CI gates. Independent read-only review found no actionable issue, independently confirmed the exact 12-package prune and 38-to-34 audit change, and found no mobile source/configuration imports. The reviewer did not rerun installation, tests, or native builds.

[PR #52](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/52) passed all five clean CI checks and merged at `a3366d9c`. The tested head was verified on remote main, and the isolated worktree and local/remote branches were removed.
