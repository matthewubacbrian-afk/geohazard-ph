# Mobile Image Asset Provenance — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish which supported-extension image assets the pinned Metro 0.80.12 packager can read from this app's tracked and installed inputs, while keeping the two `image-size` advisory dispositions evidence-bound.

**Architecture:** Start from the reviewed Metro-to-`image-size` call path and the exact lockfile, enumerate app and dependency asset producers, then run non-published Metro bundles outside the repository to observe generated asset output. Compare file signatures and provenance against the JXL/HEIF and ICNS parser preconditions. Record what the observation does and does not prove about CI or device execution.

**Tech Stack:** React Native 0.75.5, Metro 0.80.12, npm lockfile, PowerShell/Python inspection, Markdown, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`; use Conventional Commits and an isolated feature branch.
- Preserve all 34 `undetermined` Release-report dispositions. An absent asset, import, or source-map name in a bounded bundle does not prove that the dependency is harmless, build-only, or absent from another process.
- Keep bundle outputs, source maps, package tarballs, and extracted dependency files outside the repository. Do not commit generated artifacts, certificates, credentials, or raw audit JSON.
- Do not alter application behavior, dependencies, or advisory report generation in this evidence slice. If exact-build asset tracing needs code or CI instrumentation, record a separate follow-up.
- Verify structure, whitespace, local links, available package checks, independent review, five exact-head CI checks, and both final Android/iOS Release reports before merge.

### Task 1: Close the prior tracking step and establish the baseline

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/superpowers/plans/2026-10-21-mobile-advisory-attack-path-reconciliation.md`
- Create: this plan

**Interfaces:** Consume PR #62 state, merge commit, exact-head checks, and final Android/iOS JSON reports. Produce a tracked next-slice entry and mark the completed matrix step with its actual evidence.

- [x] **Step 1: Verify PR #62.** It merged at `ec96864a`; all five checks passed at `a23e6f3a`, both final reports retained 34 undetermined findings and 25 source-map packages, and the worktree and branches were removed.
- [ ] **Step 2: Commit this focused plan and status correction before the asset investigation changes.** Verify only intended Markdown paths are staged and `git diff --check` passes.

### Task 2: Inspect asset sources and a non-published Metro bundle

**Files:**
- Create: `docs/mobile-image-asset-provenance-2026-10-21.md`
- Modify: `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: this plan

**Interfaces:** Consume `mobile/package-lock.json`, the pinned Metro and `image-size` source, tracked mobile image paths, installed dependency asset paths, and a local Metro bundle/asset output generated under a temporary directory. Produce a bounded inventory of candidate image paths, owning package or tracked source, file signature, packager inclusion observation, and remaining attacker-control/exact-CI/device gates.

- [ ] **Step 1: Enumerate sources.** Search static image imports and `require` calls in the app and its reachable dependencies; distinguish Android/iOS native icon catalogs from Metro inputs. Record package versions and checksum or lockfile provenance for relevant installed packages.
- [ ] **Step 2: Generate and inspect a non-published Metro bundle.** Run pinned CLI with Release-like settings for Android and iOS, writing bundles, maps, and copied assets under a temporary directory; record command, exit status, asset paths, and whether output modules match the reviewed source path. Do not mistake this local bundle for exact CI execution.
- [ ] **Step 3: Check parser-input shape.** Inspect byte signatures of supported-extension candidate assets and whether JXL/HEIF or ICNS signatures occur. Separate the observed files from the hypothetical crafted-content route; do not create or execute an exploit payload.
- [ ] **Step 4: Publish bounded evidence.** Update the two matrix rows with actual observations and remaining gates. Leave all advisory dispositions undetermined.

### Task 3: Verify and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: this plan

- [ ] **Step 1: Run local checks.** Structure verification, script tests, backend/ML Ruff, `git diff --check`, local documentation links, and any package checks needed for generated bundle commands.
- [ ] **Step 2: Obtain independent review, commit, push, and open one PR.** Include the exact bundle command and limits in the PR description.
- [ ] **Step 3: Require five exact-head CI checks and compare both final Release reports with PR #62.** Merge only after success; verify the tested head on remote main, then archive and remove this worktree and branch.

## Notes for the executor

Metro asset enumeration is a build-input observation. The `image-size` advisories require crafted parser structures; the review must not infer attacker control from the mere ability of a developer or dependency update to change an asset. A supported-extension filename cannot rule out byte-signature dispatch, and a local bundle cannot replace CI or device evidence.
