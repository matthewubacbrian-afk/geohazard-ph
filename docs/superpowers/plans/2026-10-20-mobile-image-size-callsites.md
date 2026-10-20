# Mobile image-size Consumer Calls — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trace the pinned Metro consumer of `image-size` 1.2.1 and document what file inputs, format selection, and calls are visible for the JXL/HEIF and ICNS loop advisories without changing risk dispositions.

**Architecture:** Use the merged PR #57 lockfile and Release reports to fix versions and paths. Inspect exact-version published Metro source and any directly called helper needed to identify `image-size` inputs. Publish a bounded dated record and keep the broader attack-path queue open.

**Tech Stack:** Markdown, tracked npm lockfile, exact-version npm package source, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`; use Conventional Commits.
- This is a documentation review. Do not change dependencies, app behavior, release report code, or any of the 34 `undetermined` dispositions.
- Distinguish the Metro dependency edge from an actual call and a local file path from attacker-controlled bytes. Do not infer build-only status or device safety from package names or source maps.
- Cite immutable exact-version source or SHA-512-verified package contents for call-site claims. If the call path extends beyond Metro, state the inspection boundary.
- Do not commit tarballs, `node_modules`, raw audit JSON, source maps, bundles, APKs, or app directories.
- Verify structure, whitespace, available local checks, independent review, and all five exact-head CI checks before merge.

### Task 1: Trace Metro's image-size use

**Files:**
- Create: `docs/mobile-image-size-callsites-2026-10-20.md`
- Modify: `docs/mobile-advisory-exposure-review-2026-10-20.md`

**Interfaces:** Consume `mobile/package-lock.json`, final PR #57 Android/iOS report identities, and Metro 0.80.12 published source. Produce a table of source file/function, `image-size` API call, file/buffer origin, JXL/HEIF/ICNS handling evidence, and limits for GHSA-5p2g-fcmc-qvqq and GHSA-w3rx-r6r6-pgpr.

- [ ] **Step 1: Verify versions and advisories.** Confirm `metro` 0.80.12, `image-size` 1.2.1, both direct GHSA references, and the shortest production lockfile path.
- [ ] **Step 2: Inspect exact-version source.** Verify the npm tarball against lockfile integrity, find all direct `image-size` uses in published Metro JavaScript, and inspect the relevant caller/helper chain.
- [ ] **Step 3: Trace inputs and formats.** Record what is known about file paths, buffers, format filtering, and build context. Leave attacker control and packaged-device reachability unresolved unless directly evidenced.
- [ ] **Step 4: Publish the bounded review and link it from the advisory record.** Keep both advisory references and all 34 finding dispositions `undetermined`.

### Task 2: Synchronize tracking and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/superpowers/plans/2026-10-20-mobile-fast-xml-parser-callsites.md`
- Modify: this plan

- [x] **Step 1: Mark PR #57 merged and cleaned up, then write this focused plan before investigation changes.** PR #57 merged at `521faeed` after five checks; both final reports were inspected, and its worktree/branches were removed.
- [ ] **Step 2: Verify documentation and relevant package checks.** Run `git diff --check`, structure verification, source/lockfile consistency checks, and available configured local suites. CI is the full package/native gate where local services or installs are unavailable.
- [ ] **Step 3: Commit, push, open one PR, and obtain independent review.** Record only exact-version-supported claims.
- [ ] **Step 4: Require five exact-head CI checks, merge, verify remote main, and remove this worktree and branch.** The next feature updates tracking before implementation.

## Notes for the executor

The two advisories concern zero-sized JXL/HEIF boxes and zero-length ICNS entries in `image-size` parsing. A dependency path or a generic image-size call cannot establish that these formats are processed by this project. No dependency override or release signoff is authorized by this evidence slice.
