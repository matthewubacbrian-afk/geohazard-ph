# Mobile shell-quote patch — Implementation Plan

> **For agentic workers:** Follow this plan task by task. A dependency-only change is verified by clean installs, the package suites, native builds, and a fresh audit rather than a test that mirrors the lockfile.

**Goal:** Remove the critical `shell-quote` advisory from the mobile production-dependency lockfile without a React Native or navigation major upgrade.

**Architecture:** Update only the transitive lockfile entry allowed by its two parent ranges, then run `npm audit --omit=dev` and the complete CI matrix. Record what remains as migration work. No application code or native configuration should change in this slice.

**Tech Stack:** npm lockfile, React Native, Jest, TypeScript, Android and iOS CI.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Use Conventional Commits. Do not commit credentials, `node_modules`, generated native outputs, or audit JSON from a developer machine.
- Do not run `npm audit fix --force` or silently accept a major React Native/native-platform migration. Inspect the lockfile diff after any package-manager action.
- Verify a clean mobile `npm ci`, `npm test -- --runInBand`, `npx tsc --noEmit`, backend/ML pytest and Ruff, web tests/build, structure, whitespace, and all five CI checks including Android and iOS builds before merge.
- An npm audit finding indicates a vulnerable package version in the dependency graph, not that its vulnerable function is reachable in the shipped app.

---

### Task 1: Record the baseline and compatible patch

**Files:**
- Modify: `PLAN.md`, `docs/project-status.md`
- Create: this plan

**Interfaces:**
- `mobile/package-lock.json` currently resolves `shell-quote` 1.10.0. `@react-native-community/cli-tools` 14.1.0 allows `^1.7.3`; `react-devtools-core` 5.3.2 allows `^1.6.1`.
- [GHSA-pqg4-j6r4-53mv](https://github.com/advisories/GHSA-pqg4-j6r4-53mv) affects `shell-quote` >=1.8.4 and <1.11.0; 1.11.0 is patched.
- The 2026-10-19 `npm audit --omit=dev --json` baseline is 42 findings: 10 moderate, 31 high, 1 critical. The audit proposes major direct upgrades for React Native 0.75.5 and React Navigation 6.1.18; those are separate work.

- [x] **Step 1: Refresh and inspect the audit** and trace the critical package's parent dependency ranges.
- [x] **Step 2: Commit this tracked plan** before changing the lockfile.

---

### Task 2: Patch only the transitive lockfile resolution

**Files:**
- Modify: `mobile/package-lock.json`

**Interfaces:**
- Keep `mobile/package.json` direct dependency versions unchanged.
- Resolve `shell-quote` to a non-vulnerable 1.x version supported by the two parent ranges; avoid unrelated lockfile churn.

- [x] **Step 1: Update the lockfile using npm** and inspect exact dependency changes.
- [x] **Step 2: Run the production audit** and verify zero critical findings, recording the remaining counts.
- [ ] **Step 3: Run clean mobile tests and TypeScript** where the local environment permits; CI is authoritative for native builds.
- [x] **Step 4: Commit** the bounded patch with a Conventional Commit message.

---

### Task 3: Verify and integrate

**Files:**
- Modify: `PLAN.md`, `docs/project-status.md`, this plan as evidence changes

- [ ] **Step 1: Run all package suites and linters** listed above, documenting any local environment limit accurately.
- [ ] **Step 2: Request independent review** of the lockfile diff and audit claim.
- [ ] **Step 3: Push and open a PR** with exact test and audit evidence.
- [ ] **Step 4: Merge after all five CI checks pass**; verify the head on remote main and remove the worktree and branch.

## Notes for the executor

The [React Native 0.76 release notes](https://reactnative.dev/blog/2024/10/23/release-0.76-new-architecture) document new default architecture and raised Android/iOS minimums; a direct upgrade is not a safe lockfile-only follow-up. The audit includes CLI/dev-tool packages under `--omit=dev` because React Native declares them in its production dependency graph. Confirming whether a vulnerable function is reachable in a distributed app requires a separate code-path assessment, so this patch makes only the version and audit-count claim.

`npm update shell-quote --package-lock-only` changed exactly the `shell-quote` lockfile entry from 1.10.0 to 1.12.0, leaving direct package versions unchanged. `npm ls shell-quote --package-lock-only --all` resolves 1.12.0 under both React Native CLI tools and React DevTools. The refreshed production audit reports 41 findings: 10 moderate, 31 high, zero critical, with no `shell-quote` finding. A local Windows `npm ci --no-audit --no-fund` was stopped after remaining incomplete for several minutes; it produced only deprecation notices and no completed install result. Clean CI must establish install, tests, TypeScript, and native builds before merge.
