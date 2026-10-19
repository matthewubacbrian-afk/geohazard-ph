# Mobile cache-write resilience — Implementation Plan

> **For agentic workers:** Follow this plan task by task, using a failing regression before changing behavior.

**Goal:** A successful mobile event fetch remains visible when offline-cache persistence fails, with a clear warning that it will not be available offline.

**Architecture:** `loadEventFeed` distinguishes network failure from cache-write failure and reports the latter in its internal result. The existing refresh controller delivers the current result only. `RootNavigator` shows a separate event-cache warning so location or settings storage warnings are not overwritten. URL changes clear the warning for the previous server.

**Tech Stack:** React Native, TypeScript, Jest, AsyncStorage.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Keep typed network errors, offline fallback, URL-scoped cache keys, and the PR #48 write ordering. Do not present an unsaved fresh feed as an offline restore.
- Log a cache-write failure once at the service boundary without payloads or secrets. Present a concise user warning; do not hide a separate saved-location or API-setting warning.
- Use Conventional Commits. Do not commit credentials, `node_modules`, or generated native outputs.
- Verify focused and full mobile Jest, strict TypeScript, backend and ML pytest/Ruff, web tests/build, structure, and whitespace. Require all five CI checks before merge. CI native builds do not replace physical-device user-flow evidence.

---

### Task 1: Reproduce rejected storage with a usable fresh feed

**Files:**
- Test: `mobile/tests/eventFeed.test.ts`
- Test: `mobile/tests/eventFeedRefresh.test.ts`

**Interfaces:**
- `EventFeedResult` gains required `cacheWriteFailed: boolean` for fresh and offline results.
- A rejected cache save after a successful fetch resolves with the fetched events, `isOffline: false`, and `cacheWriteFailed: true`.
- A network failure without a valid cache still rejects; an offline fallback reports `cacheWriteFailed: false`.

- [ ] **Step 1: Add rejected-save and network-failure assertions.**
- [ ] **Step 2: Run focused Jest and verify the expected failure.**
- [ ] **Step 3: Update controller test fixtures for the new internal result shape.**

---

### Task 2: Return fresh data and surface a distinct warning

**Files:**
- Modify: `mobile/src/services/eventFeed.ts`
- Modify: `mobile/src/navigation/RootNavigator.tsx`
- Test: `mobile/tests/eventFeed.test.ts`

**Interfaces:**
- `loadEventFeed(baseUrl): Promise<EventFeedResult>` catches only cache-write errors after a successful network fetch, logs the operation once, and returns fresh events with `cacheWriteFailed: true`.
- `RootNavigator` keeps an event-cache warning separate from its existing settings/location `storageWarning`. A subsequent successfully saved result or changed API URL clears the event-cache warning.
- Non-API refresh errors use a load-failure message; a cache-write failure is delivered through `onSuccess`, not `onError`.

- [ ] **Step 1: Implement service result and warning wiring.**
- [ ] **Step 2: Run focused Jest, full mobile Jest, and strict TypeScript.**
- [ ] **Step 3: Commit** the behavior with a focused Conventional Commit message.

---

### Task 3: Verify and integrate

**Files:**
- Modify: `PLAN.md`, `docs/project-status.md`, this plan as evidence changes

- [ ] **Step 1: Run all package suites and linters** listed above; document any local environment limitation accurately.
- [ ] **Step 2: Request independent review** and address actionable findings.
- [ ] **Step 3: Push and open a PR** with actual verification evidence.
- [ ] **Step 4: Merge after all five CI checks pass**; verify the head on remote main and remove the worktree and branch.

## Notes for the executor

The warning describes offline availability, not network freshness. Do not conflate a write failure with `isOffline: true`; the user can still see the newly fetched events. A failure to read the cache after a network failure remains a load failure. The separate event-cache warning must not erase an unrelated saved-location or API-setting warning. Verify the current screen result is not superseded before applying either events or the warning.
