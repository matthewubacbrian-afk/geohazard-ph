# Web development-tool security — Implementation Plan

> **For agentic workers:** Use the subagent-driven-development or executing-plans skill task by task. Steps use checkboxes for tracking.

**Goal:** Remove the eight audited web development-tool advisories without changing the production application contract.

**Architecture:** Upgrade the direct Vite, Vitest and React-plugin toolchain together so the lockfile resolves patched transitive packages. The web app and its tests remain the compatibility check.

**Tech Stack:** npm, Vite, Vitest, React, TypeScript, GitHub Actions.

## Global Constraints

- Follow `CODING_STANDARDS.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Use Conventional Commits. Do not commit `node_modules`, `dist`, generated outputs, or secrets.
- Keep this dependency-only unless a compiler or test incompatibility requires a narrow compatibility fix.
- Node 22.12+ is required by Vitest 5; web CI uses Node 22 and the web Dockerfiles use Node 22.
- Run `npm test`, `npm run build`, `npm audit --json`, `npm audit --omit=dev --json`, `python scripts/verify_structure.py`, and `git diff --check`; require all five PR CI checks before merge.

---

### Task 1: Upgrade the audited development toolchain

**Files:**
- Modify: `web/package.json` — direct Vite, Vitest and React plugin versions.
- Modify: `web/package-lock.json` — reproducible resolved graph.
- Modify if required: `web/vite.config.ts` and affected web tests — narrow compatibility changes only.

**Interfaces:**
- Consumes: existing `npm test`, `npm run build`, and Vite worker import from the MapLibre migration.
- Produces: unchanged scripts and app behavior with patched tool versions.

- [x] **Step 1: Record failing baseline:** `npm audit --json` reported eight development-tool findings; production-only audit reported zero.
- [x] **Step 2: Implement:** pinned Vite 8.3.4, Vitest 5.0.5 and `@vitejs/plugin-react` 6.1.2; updated the lockfile. Vitest 5 required a constructable MapView test mock.
- [x] **Step 3: Verify:** fresh full and production audits each reported zero; 175 web tests passed across 35 files; production build passed and emitted a worker asset; clean `npm ci` passed.
- [x] **Step 4: Commit:** `61f7b571 fix: upgrade vulnerable web development tools`.

### Task 2: Record and integrate verified evidence

**Files:**
- Modify: `PLAN.md` — checklist, verification and next priority.
- Modify: `docs/project-status.md` — current audit and merge state.
- Modify: this plan — check completed steps with evidence.
- Modify if required: `README.md` — only if setup's Node guidance becomes inaccurate.

**Interfaces:**
- Consumes: Task 1 tests, audits and CI results.
- Produces: accurate tracked project status and one reviewable PR.

- [x] **Step 1:** structure verification passed all 140 paths and `git diff --check` was clean.
- [ ] **Step 2:** commit documentation evidence, push branch, and open a PR with actual test results.
- [ ] **Step 3:** merge only after all five CI checks pass; verify exact PR head is in `origin/main`.
- [ ] **Step 4:** archive this managed worktree and remove the merged branch.

## Notes for the executor

- The eight initial findings are `@vitest/mocker`, `esbuild`, `source-map-js`, `tinypool`, `undici`, `vite`, `vite-node`, and `vitest`. A fresh audit decides completion; do not assume a version bump removed all findings.
- The prior MapLibre feature is merged in PR #41. Keep this slice separate from PR #32 credential work and unrelated app behavior.
- No database, credentials, or staging host are needed for this slice. Existing external release and domain-review holds remain.
