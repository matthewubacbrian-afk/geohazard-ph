# Mobile XML builder path — Implementation Plan

> **For agentic workers:** Use the executing-plans workflow for this bounded evidence review. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bound the current mobile `fast-xml-parser` `XMLBuilder` advisory path by identifying direct installed consumers and their input origins without changing a vulnerability disposition.

**Architecture:** Verify the lockfile and installed version, search project source and the installed JavaScript tree for direct package imports and `XMLBuilder` use, inspect each discovered caller, then reconcile the result with the existing exact-Release V8 process trace. Publish a dated evidence record and update the plan, Epic 4 status, and advisory matrix. No runtime hook or audit-report schema change is needed for this source-inventory slice.

**Tech Stack:** React Native 0.75.5 CLI, npm lockfile, Node 22, Python 3, Markdown, GitHub Actions.

## Global constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/git-workflow.md`, and `docs/testing-standards.md`. Use Conventional Commits.
- Treat the PR #65 34-row audit as historical and the PR #66/67 12-row audit as dated current evidence. Keep every current disposition `undetermined`; absence of a static call or a named V8 entry is not attack-path or device clearance.
- Distinguish direct imports in pinned installed JavaScript from dynamic loading, uninspected generated code, build-only attribution, and physical-device execution.
- Keep `node_modules`, raw coverage, native artifacts, and audit JSON out of Git. Do not modify the mobile lockfile or Release-report format.
- Run local script/package checks, TypeScript, lint, structure, link, and whitespace checks. Require backend, ML, web, Android, and iOS exact-head CI checks and compare both final Release reports/traces against PR #67 before merge. Only an Android APK file hash may differ if the live audit remains the same.

### Task 1: Verify pinned consumers and process evidence

**Files:**
- Create: `docs/mobile-xml-builder-path-2026-10-25.md`

**Interfaces:** Read the tracked `mobile/package-lock.json`, installed JavaScript files under `mobile/node_modules`, and the dated PR #64/67 process and Release reports. Record the exact search scope and all direct consumers, then identify whether any call constructs or builds XML through `XMLBuilder` and where comment/CDATA values originate. State the limits of static search and V8 named-function coverage.

- [x] **Step 1: Inventory** direct package imports and `XMLBuilder` tokens across tracked mobile source and installed `.js`, `.cjs`, and `.mjs` files; inspect all matches and pin versions.
- [x] **Step 2: Reconcile** the three CLI call sites and PR #64 named-function result with the advisory's affected operation; write the bounded evidence record.
- [x] **Step 3: Commit** the source evidence separately from tracking updates.

### Task 2: Synchronize tracking and verify

**Files:**
- Modify: `PLAN.md`
- Modify: `docs/project-status.md`
- Modify: `docs/mobile-advisory-attack-path-gates-2026-10-21.md`
- Modify: this plan

**Interfaces:** Mark the direct-consumer inventory complete while retaining dynamic/generated caller, input-control, future framework, and device gates. Keep `node-forge` caller/key provenance as the next advisory slice.

- [x] **Step 1: Update** the plan, Epic 4 status, and advisory matrix to match the source evidence and current 12-row audit.
- [ ] **Step 2: Verify** local tests, TypeScript, lint, structure, links, and whitespace; record any unavailable integration services.
- [ ] **Step 3: Commit and push**, open a PR, require five exact-head checks, and compare Android/iOS Release reports and compact traces with PR #67.
- [ ] **Step 4: Merge only after the gate passes**, verify remote main, preserve ignored content, remove the clean worktree and merged branches, and correct post-merge tracking.

## Notes for the executor

- The prior [CLI consumer review](../../mobile-fast-xml-parser-callsites-2026-10-20.md) already documents three parser/validator calls in pinned Android and Apple CLI packages. Extend its scope to the full installed JavaScript tree; do not repeat its conclusions as a new proof of safety.
- [GHSA-gh4j-gqv2-49f6](https://github.com/advisories/GHSA-gh4j-gqv2-49f6) concerns unescaped comment/CDATA delimiters from `XMLBuilder`; `XMLParser`/`XMLValidator` execution alone does not exercise that operation.
