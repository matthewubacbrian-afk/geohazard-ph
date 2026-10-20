# Mobile node-forge Consumer Calls — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trace the pinned React Native development middleware and `selfsigned` consumer of `node-forge` 1.4.0 to actual cryptographic calls and input origins relevant to GHSA-86w9-cpqp-85rv without changing advisory dispositions.

**Architecture:** Fix the versions and root path from the merged PR #58 lockfile/Release reports. Inspect exact-version published middleware and `selfsigned` source, then document the caller operation and evidence limit in one dated record.

**Tech Stack:** Markdown, tracked npm lockfile, exact-version npm package source, GitHub Actions.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/git-workflow.md`; use Conventional Commits.
- This is a documentation review. Do not change dependencies, app behavior, Release reports, or any of the 34 `undetermined` dispositions.
- Separate certificate/key generation from RSA PKCS#1 v1.5 signature verification. A dependency edge or method name is not proof that the advisory's input precondition is met.
- Cite immutable exact-version source or SHA-512-verified package contents. State any uninspected transitive path and attacker-control limit.
- Do not commit tarballs, `node_modules`, raw audit JSON, source maps, bundles, APKs, or app directories.
- Verify structure, whitespace, available local checks, independent review, and five exact-head CI checks before merge.

### Task 1: Trace the pinned consumer

**Files:**
- Create: `docs/mobile-node-forge-callsites-2026-10-20.md`
- Modify: `docs/mobile-advisory-exposure-review-2026-10-20.md`

**Interfaces:** Consume `mobile/package-lock.json`, final PR #58 Android/iOS report identities, and exact published `@react-native/dev-middleware` 0.75.5 and `selfsigned` 2.4.1 source. Produce a table of consumer file/function, `node-forge` API called, input origin, relationship to vulnerable signature verification, and evidence limit.

- [x] **Step 1: Verify versions and advisory.** Confirm the shortest production path, `node-forge` 1.4.0, and GHSA-86w9-cpqp-85rv.
- [x] **Step 2: Inspect exact-version source.** Verify package tarballs against lockfile integrity; find direct `node-forge` imports and relevant middleware calls to `selfsigned`.
- [x] **Step 3: Trace the operation and input.** Identify whether the consumer calls vulnerable RSA verification, key/certificate generation, or another operation. Avoid conclusions about other `node-forge` users, attacker control, and device inclusion without evidence.
- [x] **Step 4: Publish the bounded review and link it from the advisory record.** Keep the direct reference and all 34 finding dispositions `undetermined`.

### Task 2: Synchronize tracking and integrate

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/superpowers/plans/2026-10-20-mobile-image-size-callsites.md`
- Modify: this plan

- [x] **Step 1: Mark PR #58 merged and cleaned up, then write this focused plan before investigation changes.** PR #58 merged at `3827dd03` after five checks; both final reports were inspected, and its worktree/branches were removed.
- [x] **Step 2: Verify documentation and relevant package checks.** Run `git diff --check`, structure verification, source/lockfile consistency checks, and available configured local suites. CI is the full package/native gate where local services or installs are unavailable.
- [ ] **Step 3: Commit, push, open one PR, and obtain independent review.** Record only exact-version-supported claims.
- [ ] **Step 4: Require five exact-head CI checks, merge, verify remote main, and remove this worktree and branch.** The next feature updates tracking before implementation.

## Notes for the executor

The advisory concerns verification of a crafted RSA PKCS#1 v1.5 signature with extra nested DigestAlgorithm elements and a low-exponent key. A certificate-generation path alone is not the affected operation. This slice does not authorize a build-only or exploitable classification or release signoff.
