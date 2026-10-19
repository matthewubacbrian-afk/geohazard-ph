# Mobile cache-write ordering — Implementation Plan

> **For agentic workers:** Follow this plan task by task, using a failing regression before changing behavior.

**Goal:** A superseded mobile event-feed request cannot replace newer events in the selected server's offline cache.

**Architecture:** `loadEventFeed` records the latest request token for each normalized API URL. Successful fetches persist only while current, through a per-key write queue so an already-started older write finishes before a newer write. `RootNavigator` continues to handle visible refresh ordering through its existing controller. Cache keys and persisted shapes stay unchanged.

**Tech Stack:** React Native, TypeScript, Jest, AsyncStorage.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, `docs/error-handling-and-logging.md`, and `docs/git-workflow.md`.
- Keep server-specific cache keys and offline fallback behavior. An older successful fetch may still resolve to its caller; screen state is already guarded by the refresh controller.
- Treat a failed cache write as a load failure in this slice; the separately queued persistence-resilience feature will change that behavior and user warning.
- Use Conventional Commits. Do not commit credentials, `node_modules`, or generated native outputs.
- Verify focused and full mobile Jest, strict TypeScript, backend and ML pytest/Ruff, web tests/build, structure, and whitespace. Require all five CI checks before merge. CI native builds do not replace physical-device user-flow evidence.

---

### Task 1: Reproduce stale offline restoration

**Files:**
- Test: `mobile/tests/eventFeed.test.ts`

**Interfaces:**
- Two `loadEventFeed(baseUrl)` calls against the same normalized URL can settle in either order.
- `loadCachedEventFeed(baseUrl)` must restore the newer request's events after both calls settle.

- [ ] **Step 1: Add deferred-fetch regression** with a newer network response before an older response; assert the older response does not write the cache and offline restoration returns the newer list.
- [ ] **Step 2: Run focused Jest and verify the stale-cache failure.**
- [ ] **Step 3: Add a deferred-write regression** where an older write has started before a newer response; assert the newer write runs after it and offline restoration returns the newer list.
- [ ] **Step 4: Run focused Jest and verify the out-of-order write failure.**

---

### Task 2: Enforce request and write order

**Files:**
- Modify: `mobile/src/services/eventFeed.ts`
- Test: `mobile/tests/eventFeed.test.ts`

**Interfaces:**
- `loadEventFeed(baseUrl): Promise<EventFeedResult>` and `loadCachedEventFeed(baseUrl): Promise<HazardEvent[]>` keep their signatures.
- A per-normalized-URL token identifies the newest started load. A per-cache-key promise chain serializes writes, skips a token that is no longer current, and recovers after a rejected prior write.
- State for a URL is removed once its latest load finishes; completed write queues are removed.

- [ ] **Step 1: Implement token tracking and per-key write serialization.**
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

The request token is scoped by normalized API URL, matching the cache key. A newer request that fails does not make an older response authoritative again. The queue must serialize actual AsyncStorage calls, not only the promises returned by `loadEventFeed`. Avoid global ordering between different API servers. Cache-write failure handling remains a separate feature, so tests must not imply that a failed write returns a fresh feed here.
