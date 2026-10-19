# Mobile compatible dependency refresh — Implementation Plan

> **For agentic workers:** Execute one bounded dependency slice, verify the exact lockfile diff, and require the full CI matrix before merge.

**Goal:** Apply compatible, non-forced mobile dependency fixes and leave an evidence-backed migration queue for the findings that remain.

**Architecture:** Keep direct React Native and React Navigation versions and native configuration fixed. Let npm refresh only lockfile resolutions allowed by current ranges, inspect each changed package, then compare production audit results. Record major-upgrade and runtime-evidence gates separately.

**Tech Stack:** npm lockfile, React Native 0.75, React Navigation 6, Jest, TypeScript, Android and iOS CI.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Use Conventional Commits. Do not commit credentials, generated artifacts, local caches, or audit JSON from a developer machine.
- Never use `npm audit fix --force`. Keep `mobile/package.json`, native configuration, React Native, and React Navigation direct resolutions unchanged in this slice. If npm proposes wider changes, revert and select compatible packages individually.
- An audit count is dependency-graph evidence, not proof of vulnerable-function reachability in a shipped app. Do not assert a security exploit or release readiness from package metadata alone.
- Verify a clean lockfile install, mobile Jest and TypeScript, backend/ML pytest and Ruff, web tests/build, structure, whitespace, and all five CI checks including Android and iOS native builds before merge. Record local environment limits accurately.

---

### Task 1: Capture baseline and plan the bounded update

**Files:**
- Modify: `PLAN.md`, `docs/project-status.md`
- Create: this plan

**Interfaces:**
- `origin/main` includes [PR #50](https://github.com/matthewubacbrian-afk/geohazard-ph/pull/50): `shell-quote` 1.12.0, 41 production audit findings (10 moderate, 31 high, zero critical).
- `npm audit fix --package-lock-only --dry-run --omit=dev` reports compatible fixes for some transitive packages while recommending breaking direct upgrades for React Native 0.88.0 and React Navigation 7.5.1.

- [x] **Step 1: Verify merged baseline** and rerun the production audit.
- [x] **Step 2: Commit this tracked plan** before changing the lockfile.

---

### Task 2: Apply only compatible lockfile resolutions

**Files:**
- Modify: `mobile/package-lock.json`

**Interfaces:**
- Run `npm audit fix --package-lock-only --omit=dev --ignore-scripts` without `--force`, or narrower `npm update <package> --package-lock-only` when needed.
- `mobile/package.json` and native project files must remain unchanged; React Native 0.75.5 and React Navigation 6.1.18 must remain resolved.

- [ ] **Step 1: Refresh the lockfile** and inspect all changed dependency entries and tarball integrity values.
- [ ] **Step 2: Re-audit production dependencies**; require zero critical and document before/after counts and unresolved root paths.
- [ ] **Step 3: Run a clean mobile install, Jest, and TypeScript** where the local environment permits; CI is authoritative for native builds.
- [ ] **Step 4: Commit** the bounded lockfile update with a Conventional Commit message.

---

### Task 3: Record the remaining migration and verify integration

**Files:**
- Create: `docs/mobile-dependency-audit-2026-10-19.md`
- Modify: `PLAN.md`, `docs/project-status.md`, this plan as evidence changes

**Interfaces:**
- Classify unresolved findings by direct dependency root, affected toolchain/runtime context, available non-breaking or major path, and verification needed. Make no reachability claim without code-path evidence.
- Keep React Native platform-minimum and new-architecture migration, navigation API migration, Android/iOS device-flow evidence, and shipped-code reachability as separate acceptance gates.

- [ ] **Step 1: Write the evidence and prioritized follow-up slices** using exact audit counts and source links.
- [ ] **Step 2: Run package suites, linters, structure, and whitespace checks**; document any local limit.
- [ ] **Step 3: Request independent review** of lockfile scope and audit claims.
- [ ] **Step 4: Push and open a PR**; merge only after all five CI checks pass, verify tested head on remote main, and remove this worktree and branch.

## Notes for the executor

The remaining 41 findings are grouped by npm's proposed fixes: 10 report `fixAvailable: true`, 27 point to a major React Native upgrade, and four point to a major React Navigation upgrade. These groups may change after compatible updates. React Native 0.76 already changes default architecture and minimum platform versions, so a larger upgrade requires separate design, native-build work, and device evidence. A zero-critical audit alone does not complete Epic 4.
