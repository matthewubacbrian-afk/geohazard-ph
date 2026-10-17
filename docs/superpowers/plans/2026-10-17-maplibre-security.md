# MapLibre dependency security — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the vulnerable production MapLibre release while retaining an
interactive map and a clear fallback on devices without WebGL2.

**Architecture:** Update the single map dependency, adapt its ESM/worker setup
at `MapView`, and verify map behavior and the built worker asset.

**Tech Stack:** React, TypeScript, MapLibre GL JS, Vite, Vitest.

**Spec:** `docs/superpowers/specs/2026-10-17-maplibre-security-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/testing-standards.md`, and
  `docs/git-workflow.md`; use Conventional Commits.
- Keep the existing event, basemap, overlay and attribution behavior.
- Do not commit generated `web/dist`, `node_modules`, credentials, or caches.
- Verify `npm test`, `npm run build`, `npm audit --omit=dev`, structure and
  whitespace checks, then all five repository CI checks before merging.
- The map migration does not clear any domain, data-permission, staging, or
  physical-device acceptance gate.

---

### Task 1: Reproduce map initialization gaps

**Files:**
- Modify: `web/tests/MapView.test.tsx`

**Interfaces:**
- Consumes: existing `MapView` props and mocked MapLibre boundary.
- Produces: a test that requires worker URL setup before `Map` construction and
  a test that requires an accessible WebGL2 failure message.

- [ ] **Step 1: Write the failing tests** with an explicit worker spy and a
  `GPUInitializationError` constructor failure.
- [ ] **Step 2: Run the focused test**, confirming the expected old-code failure.
- [ ] **Step 3: Keep the tests in place** for the migration task.
- [ ] **Step 4: Rerun focused tests** after Task 2.
- [ ] **Step 5: Commit** together with the implementation as one logical fix.

---

### Task 2: Upgrade and adapt MapLibre

**Files:**
- Modify: `web/package.json`, `web/package-lock.json`
- Modify: `web/src/components/map/MapView.tsx`, `MapView.module.css`
- Modify: `README.md`

**Interfaces:**
- Consumes: MapLibre v6 ESM exports, `GPUInitializationError`, and Vite's
  `maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url` asset import.
- Produces: the same `MapView` props and map interactions, configured worker,
  and an accessible fallback on unsupported WebGL2 devices.

- [ ] **Step 1: Pin a patched MapLibre release** and regenerate only the web
  lockfile; do not use force audit fixes.
- [ ] **Step 2: Implement v6 imports and worker setup**, and catch only
  `GPUInitializationError` at construction.
- [ ] **Step 3: Run focused tests**, then full `npm test` and `npm run build`.
- [ ] **Step 4: Run `npm audit --omit=dev`** and inspect remaining findings.
- [ ] **Step 5: Commit** with a `fix:` message after diff/structure checks.

---

### Task 3: Review, CI, and delivery tracking

**Files:**
- Modify: `PLAN.md`, `docs/project-status.md`, this plan and its design spec.

**Interfaces:**
- Consumes: verification output and PR CI status.
- Produces: accurate security and epic status, PR with test evidence.

- [ ] **Step 1: Record actual local results and remaining audit findings**.
- [ ] **Step 2: Request independent review**, fix material issues, and rerun
  affected checks.
- [ ] **Step 3: Push/open PR** with Summary, Testing, Notes; wait for five CI
  checks to pass.
- [ ] **Step 4: Merge, verify exact head is in `origin/main`, archive the
  managed worktree and remove the merged branch.**
- [ ] **Step 5: Begin separate development-tool remediation** from current main.

## Notes for the executor

Perform Task 1 before Task 2 so the regression is shown red on the old code.
The CI suites use their own services. Local backend integration requires the
session-owned PostGIS/Redis containers described in `PLAN.md` if rerun. Do not
interpret a successful build as physical browser rendering evidence.
