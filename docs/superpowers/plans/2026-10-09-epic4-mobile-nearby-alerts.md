# Epic 4 Mobile Nearby Alerts — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let mobile users save locations and radii, view matching fetched earthquake events, and retain locations and the latest event list for offline use.

**Architecture:** Add typed AsyncStorage-backed services and pure validation/proximity helpers first. Connect those services to a small three-tab React Native shell; the shell owns API configuration, cached event data, loading, offline and retry state, while screens render inputs and results.

**Tech Stack:** React Native 0.75, TypeScript, AsyncStorage 1.24.0, Jest.

**Spec:** `docs/superpowers/specs/2026-10-09-epic4-mobile-nearby-alerts-design.md`

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/testing-standards.md`, and `docs/error-handling-and-logging.md`.
- Use Conventional Commits if committing; never include credentials, native build output, or generated artifacts.
- Keep API event wire fields snake_case and map them through `mobile/src/services/api.ts`.
- Do not request device location, add a backend endpoint, or imply official warnings/predictions.
- Use AsyncStorage 1.24.0; 3.x requires a newer React Native version than this package's 0.75 line.
- Run mobile Jest tests from `mobile/`, then `python scripts\verify_structure.py` and `git diff --check` from root.
- Mobile tests run in Node and mock native storage; the repository has no generated Android/iOS projects or mobile build script.

### Task 1: Persistent cache and saved-location service

**Files:**
- Modify: `mobile/package.json`, `mobile/package-lock.json`
- Modify: `mobile/src/types/hazard.ts`
- Modify: `mobile/src/services/offlineCache.ts`
- Create: `mobile/src/services/savedLocations.ts`
- Create: `mobile/src/services/settings.ts`
- Modify: `mobile/tests/offlineCache.test.ts`
- Create: `mobile/tests/savedLocations.test.ts`
- Create: `mobile/tests/settings.test.ts`

**Interfaces:**
- `SavedLocation`: `{ id: string; name: string; latitude: number; longitude: number; radius_km: number }`.
- `saveOfflineValue(key: string, value: unknown): Promise<void>` and `readOfflineValue<T>(key: string): Promise<T | undefined>` use JSON serialization and AsyncStorage.
- `loadSavedLocations(): Promise<SavedLocation[]>`, `saveSavedLocations(locations: SavedLocation[]): Promise<void>`, and pure `validateSavedLocation(input: Omit<SavedLocation, 'id'>): string | null`.
- `loadApiBaseUrl(): Promise<string>`, `saveApiBaseUrl(value: string): Promise<void>`, and pure `validateApiBaseUrl(value: string): string | null`; accepted URLs use HTTP(S), include a host, and end in `/api/v1`.
- Validation rejects blank names, non-finite values, latitude outside `[-90, 90]`, longitude outside `[-180, 180]`, and radius outside `[1, 500]`; `null` means valid.

- [x] **Step 1: Add failing service tests** for persistent read/write, malformed JSON, location round-trip, invalid name/coordinate/radius values, and API URL validation and persistence.
- [x] **Step 2: Run `npm test -- --runInBand tests/offlineCache.test.ts tests/savedLocations.test.ts tests/settings.test.ts`** from `mobile/`; confirm missing async APIs and validation fail for expected reasons.
- [x] **Step 3: Add `@react-native-async-storage/async-storage@1.24.0`; make the offline cache asynchronous and JSON-backed; implement saved-location and API URL persistence/validation.**
- [x] **Step 4: Mock AsyncStorage in the service tests and rerun the focused command; confirm all three suites pass.**
- [x] **Step 5: Commit the service slice** with `feat: persist mobile locations and event cache`.

### Task 2: Proximity matching and event refresh service

**Files:**
- Create: `mobile/src/services/proximity.ts`
- Create: `mobile/src/services/eventFeed.ts`
- Create: `mobile/tests/proximity.test.ts`
- Create: `mobile/tests/eventFeed.test.ts`
- Modify: `mobile/src/types/hazard.ts`

**Interfaces:**
- `NearbyHazard`: `{ event: HazardEvent; location_id: string; distance_km: number }`.
- `distanceKm(latitudeA: number, longitudeA: number, latitudeB: number, longitudeB: number): number` uses Haversine distance and mean Earth radius 6,371 km.
- `findNearbyHazards(events: HazardEvent[], locations: SavedLocation[]): NearbyHazard[]` includes an inclusive radius boundary and sorts by ascending distance, then event time newest first.
- `loadEventFeed(baseUrl: string): Promise<{ events: HazardEvent[]; isOffline: boolean }>` fetches through existing `fetchEvents`; on API/network failure it returns cached events with `isOffline: true`, or rethrows if no cache exists. An empty URL raises the existing safe `not_configured` error without fetching.

- [x] **Step 1: Add failing tests** for known distances, boundary inclusion, multiple location matches, deterministic ordering, successful fetch/cache update, offline fallback, absent-cache failure, empty URL, and malformed cached event rejection.
- [x] **Step 2: Run `npm test -- --runInBand tests/proximity.test.ts tests/eventFeed.test.ts`** from `mobile/`; confirm expected missing exports and behavior.
- [x] **Step 3: Implement the pure matcher and feed service**, reusing `fetchEvents` and the persistent cache without changing the API contract. Cached entries are shape-checked before display.
- [x] **Step 4: Rerun the focused command** and confirm every expected case passes.
- [x] **Step 5: Commit the feed slice** with `feat: match mobile events to saved locations`.

### Task 3: App tabs and saved-location setup

**Files:**
- Modify: `mobile/src/navigation/RootNavigator.tsx`
- Modify: `mobile/src/screens/SavedLocationsScreen.tsx`
- Modify: `mobile/src/screens/NearbyHazardsScreen.tsx`
- Modify: `mobile/src/screens/AlertsScreen.tsx`
- Create: `mobile/src/components/HazardMatchList.tsx`
- Create: `mobile/src/styles.ts`
- Create: `mobile/src/config.ts`
- Use: `mobile/tests/settings.test.ts`, `mobile/tests/eventFeed.test.ts`, and `mobile/tests/proximity.test.ts`

**Interfaces:**
- Root shell tabs are `Nearby`, `Saved locations`, and `Alerts`; default tab is Nearby.
- The shell persists `mobile.apiBaseUrl`, `mobile.savedLocations`, and `mobile.latestEvents`; `API_BASE_URL` defaults to `''`.
- Saved locations screen props: `locations`, `apiBaseUrl`, `onSaveLocation`, `onDeleteLocation`, and `onSaveApiBaseUrl`.
- Nearby and Alerts screen props: `matches`, `isLoading`, `isOffline`, `errorMessage`, `isConfigured`, and `onRefresh`.

- [x] **Step 1: Confirm failing-first coverage exists** for URL persistence, fetch/cache fallback, and proximity matching before connecting screens.
- [x] **Step 2: Run `npm test -- --runInBand tests/settings.test.ts tests/eventFeed.test.ts tests/proximity.test.ts`** from `mobile/`; confirm the service contracts pass before UI wiring.
- [x] **Step 3: Implement app state lifecycle and tabs.** Saved locations form accepts manual coordinates and radius, validates before saving, and supports deletion. Nearby/Alerts render loading, empty, error, stale/offline, and retry states. Alerts identifies foreground-only behavior; background push stays `not-configured`.
- [x] **Step 4: Run `npm test -- --runInBand` from `mobile/`**; all 6 suites and 28 tests pass. TypeScript check also passes.
- [x] **Step 5: Commit the app slice** with `feat: add mobile nearby alerts screens`.

### Task 4: Documentation and final verification

**Files:**
- Modify: `README.md`
- Modify: `docs/glossary.md`
- Modify: `docs/superpowers/plans/2026-10-09-epic4-mobile-nearby-alerts.md`

- [x] **Step 1: Document mobile setup** in `README.md`: configure an API base URL ending in `/api/v1`, use a device-reachable address, and explain saved coordinates/radii, cached events, and foreground-only alerts.
- [x] **Step 2: Run `npm test -- --runInBand`** from `mobile/`: 6 suites, 28 tests passed.
- [x] **Step 3: Run `python scripts\verify_structure.py` and `git diff --check`** from repository root: expected scaffold paths and whitespace checks pass.
- [x] **Step 4: Mark completed plan steps and inspect `git status --short`** to ensure only this feature's files changed.
- [x] **Step 5: Commit docs and final plan status** with `docs: document mobile nearby alert setup`.

## Notes for the executor

- Tasks 1 and 2 are sequential because the feed service uses Task 1's persistent cache. Task 3 consumes both services. Task 4 follows implementation and verification.
- The API server URL is device configuration, not a secret. It is saved on-device; never commit a developer's LAN address.
- No backend/PostGIS/Redis service is required by mobile unit tests.
- A device build cannot run until native Android/iOS project configuration is added in a separate slice.
