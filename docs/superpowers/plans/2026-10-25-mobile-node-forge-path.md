# Mobile node-forge caller path — Implementation Plan

> **For agentic workers:** Use the executing-plans workflow for this bounded evidence review. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bound the current mobile `node-forge`/`selfsigned` advisory path by identifying direct installed callers and available certificate/key provenance without changing a vulnerability disposition.

**Architecture:** Verify pinned versions and the active advisory preconditions, search tracked mobile source and installed JavaScript for direct `selfsigned`/`node-forge` imports or calls, inspect the installed `selfsigned.generate` and forge verification path, then reconcile those findings with the exact Android/iOS Release process summaries. Publish a dated evidence record and update the project plan, Epic 4 status, and advisory matrix. No dependency, runtime, or audited Release-report change is planned.

**Tech Stack:** React Native 0.75.5 dependency tree, npm lockfile, Node 22, Python 3, Markdown, GitHub Actions.

## Global constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/git-workflow.md`, and `docs/testing-standards.md`. Use Conventional Commits.
- Keep the historical 34-row audit separate from the current dated 12-row audit. Every current disposition remains `undetermined`; direct-token and scoped-process absences do not prove build-only status, safety, or device absence.
- Distinguish `selfsigned`'s self-created certificate and default generated key from caller-supplied `options.keyPair`, crafted external signature requirements, and any actual project caller.
- Keep `node_modules`, raw V8 coverage, audit JSON, native artifacts, and caches out of Git. Preserve Release-report and compact-trace schemas.
- Verify local scripts/packages, TypeScript, lint, structure, links, and whitespace. Require all five exact-head CI checks and compare both final Release reports and compact traces against PR #68. Only the Android APK hash may differ if audit identities remain unchanged.

### Task 1: Verify installed callers and advisory path

**Files:**
- Create: `docs/mobile-node-forge-path-2026-10-25.md`

**Interfaces:** Read `mobile/package-lock.json`, installed `.js`, `.cjs`, and `.mjs` files, the existing [pinned source review](../../mobile-node-forge-callsites-2026-10-20.md), and PR #68 Android/iOS Release summaries. Record direct caller matches, the internal verification call and key options, the absence or presence of exact-Release package loads, and the limits of these observations.

- [ ] **Step 1: Inventory** direct installed `selfsigned`/`node-forge` tokens and tracked mobile source, pin versions, and inspect all matches.
- [ ] **Step 2: Reconcile** `selfsigned.generate`/forge verification with the active advisory's crafted-signature and low-exponent-key preconditions and the Release process summaries; write the bounded evidence record.
- [ ] **Step 3: Commit** the source evidence separately from tracking updates.

### Task 2: Synchronize tracking and verify

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- Modify: this plan

**Interfaces:** Mark the direct-caller inventory complete while retaining dynamic/generated callers, certificate/key control, framework migration, and physical-device gates. Reprioritize the next engineering slice in the plan before starting it.

- [ ] **Step 1: Update** the plan, Epic 4 status, and advisory matrix to match the evidence and current 12-row audit.
- [ ] **Step 2: Verify** local tests, TypeScript, lint, structure, links, and whitespace; record unavailable integration services.
- [ ] **Step 3: Commit and push**, open a PR, require five exact-head checks, and compare Android/iOS reports and traces with PR #68.
- [ ] **Step 4: Merge only after the gate passes**, verify remote main, preserve ignored content, remove the clean worktree and merged branches, and correct post-merge tracking.

## Notes for the executor

- [GHSA-86w9-cpqp-85rv](https://github.com/advisories/GHSA-86w9-cpqp-85rv) concerns crafted RSA PKCS#1 v1.5 signature verification with extra nested `DigestAlgorithm` elements and a low-exponent key. A lockfile path or internally created certificate does not establish those inputs.
- The earlier [source review](../../mobile-node-forge-callsites-2026-10-20.md) found no direct import in the pinned dev-middleware tarball but did find `selfsigned.generate` calling forge chain verification. Extend the caller search to the installed JavaScript tree without interpreting a text-search absence as exhaustive execution proof.
