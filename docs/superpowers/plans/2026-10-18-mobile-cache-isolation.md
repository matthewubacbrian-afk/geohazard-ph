# Mobile event-cache isolation — Implementation Plan

> **For agentic workers:** Follow this plan task by task, using a failing regression before changing behavior.

**Goal:** Offline and restored hazard events come only from the currently selected API server.

**Architecture:** Derive an AsyncStorage key from the normalized API base URL. Use the same scoped read in network fallback and initial state restoration, after the saved URL resolves. Do not migrate the old unscoped event key: its server provenance is unknown.

**Tech Stack:** React Native, TypeScript, AsyncStorage, Jest.

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, and `docs/git-workflow.md`.
- Keep the snake_case API wire mapping in `mobile/src/services/api.ts`; this slice changes local cache ownership only.
- Use Conventional Commits. Do not commit credentials, generated native outputs, or `node_modules`.
- Verify mobile Jest and TypeScript, backend and ML pytest/Ruff, web tests/build, structure, and whitespace; require all five CI checks before merge.
- Device-flow evidence remains a separate acceptance gate. No database or live network is needed for these unit tests.

---

### Task 1: Scope offline event reads and writes

**Files:**
- Modify: `mobile/src/services/eventFeed.ts`
- Modify: `mobile/src/services/settings.ts` if normalization must be shared
- Test: `mobile/tests/eventFeed.test.ts`

**Interfaces:**
- `eventFeedCacheKey(baseUrl: string): string` uses the same trim/trailing-slash normalization as the saved API URL.
- `loadCachedEventFeed(baseUrl: string): Promise<HazardEvent[]>` returns only validated rows from that URL's cache, or an empty list when unconfigured or missing.
- `loadEventFeed(baseUrl)` writes to and falls back from that scoped key. The legacy `mobile.latestEvents` key is never read.

- [ ] **Step 1: Write failing tests** for equivalent URL spellings, server A/B isolation, offline fallback, invalid cached rows, and no legacy-key reuse.
- [ ] **Step 2: Run focused Jest and verify the expected failures.**
- [ ] **Step 3: Implement** the shared normalization and scoped cache access without changing wire mapping.
- [ ] **Step 4: Run focused Jest and TypeScript.**
- [ ] **Step 5: Commit** with a focused Conventional Commit message.

---

### Task 2: Restore the selected server's cache

**Files:**
- Modify: `mobile/src/navigation/RootNavigator.tsx`
- Test: `mobile/tests/eventFeed.test.ts` for the restoration service boundary

**Interfaces:**
- Initial restoration loads the API URL before reading event data, then calls `loadCachedEventFeed(restoredUrl)`.
- If URL or event storage fails, existing storage-warning behavior remains; an unconfigured URL does not restore another server's events.

- [ ] **Step 1: Add the restoration service regression** with server switching and malformed cache cases.
- [ ] **Step 2: Verify the focused test fails before implementation.**
- [ ] **Step 3: Connect initial restoration** to the scoped read; avoid parallel reading before the URL is known.
- [ ] **Step 4: Run focused Jest and TypeScript.**
- [ ] **Step 5: Commit** with a focused Conventional Commit message.

---

### Task 3: Verify and integrate

**Files:**
- Modify: `PLAN.md`, `docs/project-status.md`, this plan only as evidence changes

- [ ] **Step 1: Run the full package suites and linters** listed in Global Constraints; record any environment-only limitation truthfully.
- [ ] **Step 2: Request independent review** and address actionable findings.
- [ ] **Step 3: Push and open a PR** with actual checks and behavior changes described.
- [ ] **Step 4: Merge after all five CI checks pass**; verify the reviewed head is on remote main, then remove this worktree and branch.

## Notes for the executor

The old key is not safe to migrate because it does not identify the API server. A user may see no offline events until the selected server has been fetched once. Keep refresh ordering and cache-write-failure handling in their separate planned slices.
