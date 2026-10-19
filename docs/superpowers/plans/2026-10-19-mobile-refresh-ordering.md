# Mobile refresh ordering — Implementation Plan

> **For agentic workers:** Follow this plan task by task, using a failing regression before changing behavior.

**Goal:** Only the newest mobile event-feed refresh can update events, offline state, errors, and loading state.

**Architecture:** A small service controller numbers refreshes and invokes state callbacks only for the latest request. `RootNavigator` delegates the network lifecycle to it and invalidates outstanding work when the API URL changes. The existing URL-scoped cache remains unchanged.

**Tech Stack:** React Native, TypeScript, Jest.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Preserve typed API errors and the current user-facing messages; do not log response payloads.
- Use Conventional Commits. Do not commit credentials, `node_modules`, or generated native outputs.
- Verify focused and full mobile Jest, strict TypeScript, backend and ML pytest/Ruff, web tests/build, structure, and whitespace. Require all five CI checks before merge.
- CI native builds do not replace physical-device user-flow evidence.

---

### Task 1: Test latest-refresh behavior

**Files:**
- Test: `mobile/tests/eventFeed.test.ts` or a new `mobile/tests/eventFeedRefresh.test.ts`

**Interfaces:**
- `createEventFeedRefreshController(loadFeed)` returns `refresh(baseUrl, handlers)` and `invalidate()`.
- `handlers` receive start, success, error, and finish only for the current request; superseded success and error results never call state callbacks.

- [x] **Step 1: Add deferred-promise tests** for older success arriving after newer success, older error arriving after newer success, and invalidation on server switch.
- [x] **Step 2: Run focused Jest and verify expected failures.**
- [x] **Step 3: Implement the controller** with a monotonically increasing request token.
- [ ] **Step 4: Run focused Jest and strict TypeScript.**
- [ ] **Step 5: Commit** with a focused Conventional Commit message.

---

### Task 2: Connect navigation state

**Files:**
- Modify: `mobile/src/navigation/RootNavigator.tsx`
- Test: controller tests above cover the callback behavior without a device renderer

**Interfaces:**
- `refreshEvents` passes the current normalized URL and callbacks that update `events`, `isOffline`, `errorMessage`, and `isLoading`.
- A changed API URL invalidates the old request before clearing the previous server's events. Saving the unchanged URL preserves the current feed.

- [x] **Step 1: Connect `RootNavigator` to the controller.**
- [ ] **Step 2: Run focused Jest, full mobile Jest, and strict TypeScript.**
- [ ] **Step 3: Commit** with a focused Conventional Commit message.

---

### Task 3: Verify and integrate

**Files:**
- Modify: `PLAN.md`, `docs/project-status.md`, this plan as evidence changes

- [ ] **Step 1: Run all package suites and linters** listed above; document any local environment limitation accurately.
- [ ] **Step 2: Request independent review** and address actionable findings.
- [ ] **Step 3: Push and open a PR** with actual verification evidence.
- [ ] **Step 4: Merge after all five CI checks pass**; verify the head on remote main and remove the worktree and branch.

## Notes for the executor

Keep this slice limited to screen refresh ordering. Older same-server requests can still overwrite newer values in AsyncStorage; cache-write ordering is a separate queued fix. A cache write failure still rejects a fresh load and is also planned separately. No API schema, persistence format, or source-data behavior changes here.

Local focused Jest passed four controller tests; the available broader mobile suite passed 41 tests across nine suites. The local dependency tree lacks native React Native packages, so the scene-analysis suite and strict TypeScript cannot complete locally. CI must run a clean install, all mobile tests, TypeScript, Android, and iOS before merge.
