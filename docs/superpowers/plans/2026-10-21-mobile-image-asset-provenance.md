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
- [x] **Step 2: Commit this focused plan and status correction before the asset investigation changes.** Commit `028bfad8` contains only the intended Markdown paths; structure and whitespace checks passed.

### Task 2: Inspect asset sources and a non-published Metro bundle

**Files:**
- Create: `docs/mobile-image-asset-provenance-2026-10-21.md`
- Modify: `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: this plan

**Interfaces:** Consume `mobile/package-lock.json`, the pinned Metro and `image-size` source, tracked mobile image paths, installed dependency asset paths, and a local Metro bundle/asset output generated under a temporary directory. Produce a bounded inventory of candidate image paths, owning package or tracked source, file signature, packager inclusion observation, and remaining attacker-control/exact-CI/device gates.

- [x] **Step 1: Enumerate sources.** The app has no static image import/`require`; 10 tracked native launcher PNGs and 247 installed supported-suffix dependency files were enumerated after pinned `npm ci`.
- [x] **Step 2: Generate and inspect a non-published Metro bundle.** Both local `--dev false` platform bundles succeeded under `%TEMP%`; neither copied assets or listed image-file sources. Their 25 package-name sets match the corresponding final PR #62 reports, but the local maps are not exact CI maps.
- [x] **Step 3: Check parser-input shape.** The 257 current candidates have 43 PNG signatures and 214 SVG documents, with no JXL/HEIF or ICNS signature under a supported suffix. No exploit payload was created.
- [x] **Step 4: Publish bounded evidence.** The dated record and both matrix rows state the observations and remaining generated/external asset, exact-CI process, and device gates. All dispositions remain undetermined.

### Task 3: Verify and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: this plan

- [x] **Step 1: Run local checks.** Structure (140 paths), scripts (26 tests plus seven subtests), backend/ML Ruff, mobile Jest (61 tests), strict TypeScript, `git diff --check`, and local documentation links passed. Both local Metro bundles exited successfully.
- [x] **Step 2: Obtain independent review, commit, push, and open one PR.** Independent review approved the counts, signatures, local bundles, and report comparison; its TIFF/KTX wording refinement was applied. Commits `028bfad8` and `1c3c5afc` are pushed in [PR #63](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/63). Its description records the bundle commands and limits.
- [ ] **Step 3: Require five exact-head CI checks and compare both final Release reports with PR #62.** Merge only after success; verify the tested head on remote main, then archive and remove this worktree and branch.

## Notes for the executor

Metro asset enumeration is a build-input observation. The `image-size` advisories require crafted parser structures; the review must not infer attacker control from the mere ability of a developer or dependency update to change an asset. A supported-extension filename cannot rule out byte-signature dispatch, and a local bundle cannot replace CI or device evidence.
