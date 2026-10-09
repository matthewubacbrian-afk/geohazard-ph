# Epic 4 Mobile Nearby Alerts — Design

**Date:** 2026-10-09

## Problem

Epic 4 is the remaining core client work. The current mobile screens are placeholders, the
API service can fetch events but is not connected to the app, and `offlineCache.ts` stores
values only in memory. A user cannot save a place, see which fetched events are nearby, or
return to the last event list without a network connection.

## Goals

- Let a user create, view, and delete named saved locations with decimal-degree coordinates
  and a radius from 1 through 500 kilometers.
- Fetch the existing primary-only `/api/v1/events` collection and show events within a
  saved location's radius using great-circle distance in kilometers.
- Persist saved locations, the configured API base URL, and the last successful event list
  across app restarts using device storage.
- On request failure, show a safe offline/stale state and display the last cached event list
  when available; expose a retry action.
- Provide a simple three-tab app shell for Nearby, Saved locations, and Alerts, with Alerts
  showing the same foreground proximity matches.
- Cover storage, coordinate/radius validation, matching boundaries, and fetch/cache fallback
  using the mobile Jest suite.

## Non-goals

- Background push notifications, notification permissions, push tokens, or server-side
  subscriptions.
- Automatic device geolocation or permission prompts; users enter coordinates directly.
- New backend endpoints, database tables, or changes to the event response contract.
- Historical browsing, map rendering, user accounts, or location synchronization across
  devices.

## Context And Constraints

- `mobile/src/services/api.ts::fetchEvents(baseUrl)` already maps the `/events` snake_case
  wire payload into the UI-native `HazardEvent` type.
- `GET /api/v1/events` is primary-only by default; the mobile client will preserve that
  behavior and will not request duplicate source rows.
- `mobile/src/services/offlineCache.ts` is currently an in-memory `Map` and must become an
  asynchronous persistent cache. AsyncStorage 1.24.0 supports the project's React Native
  0.75 dependency range; current AsyncStorage 3.x requires React Native 0.76 or later.
- Mobile tests run in Node and must mock the storage boundary rather than require a native
  runtime. The application package has no checked-in Android/iOS project configuration, so
  this slice validates its service logic in Jest and leaves native packaging setup for later.
- Mobile screens remain thin. Typed errors and explicit loading, empty, offline, and retry
  states follow `docs/error-handling-and-logging.md` and `docs/testing-standards.md`.
- Event timestamps and coordinates retain the backend values. Proximity is descriptive and
  does not represent an official warning or safety boundary.

## Alternatives Considered

1. **Saved locations, foreground proximity matching, and persistent offline reads (chosen).**
   This creates a usable vertical slice on the current events API and prepares a clean base
   for push delivery later. It adds one compatible storage dependency and a small app shell.
2. **Add background push delivery immediately.** This is closer to the full Epic 4 goal, but
   requires choosing and operating a push provider and implementing server-side subscription
   delivery, which is a separate infrastructure decision.
3. **Build saved-location screens only.** This minimizes code, but does not connect locations
   to hazard data or provide useful offline behavior, so it leaves the central user need
   unresolved.

## Design

### Architecture and data flow

```text
SavedLocationsScreen ──CRUD──> saved-locations service ──> AsyncStorage
                                             │
App shell ──refresh──> events API ──success──> persistent offline cache
    │                       │                      │
    └── Nearby / Alerts <── proximity matcher <──┘
                           (saved coordinates + radius_km)
```

The app shell owns the selected tab, saved locations, loading/error/offline state, and current
events. On startup it reads persisted settings, locations, and cached events, then attempts a
network refresh when the API base URL is configured. A successful fetch replaces the event
cache. A failed fetch keeps cached events visible and marks them stale. A user-triggered
refresh repeats the same flow.

### Components and interfaces

- `mobile/src/types/hazard.ts`: add `SavedLocation` with `id: string`, `name: string`,
  `latitude: number`, `longitude: number`, and `radius_km: number`; add `NearbyHazard` with
  `event: HazardEvent`, `location_id: string`, and `distance_km: number`.
- `mobile/src/services/offlineCache.ts`: export async `saveOfflineValue(key, value): Promise<void>`
  and `readOfflineValue<T>(key): Promise<T | undefined>` over AsyncStorage JSON values. Invalid
  cached JSON is removed and treated as absent.
- `mobile/src/services/savedLocations.ts`: export async `loadSavedLocations(): Promise<SavedLocation[]>`,
  `saveSavedLocations(locations): Promise<void>`, and pure `validateSavedLocation(input)`; names
  must be nonblank, coordinates within latitude/longitude limits, and radius from 1 through
  500 km.
- `mobile/src/services/settings.ts`: export `loadApiBaseUrl(): Promise<string>`,
  `saveApiBaseUrl(value: string): Promise<void>`, and
  `validateApiBaseUrl(value: string): string | null`. Accepted URLs use HTTP(S), include a host,
  and end in `/api/v1`; save the trimmed URL without a trailing slash under `mobile.apiBaseUrl`.
- `mobile/src/services/proximity.ts`: export pure `distanceKm(latitudeA, longitudeA,
  latitudeB, longitudeB): number` and `findNearbyHazards(events, locations): NearbyHazard[]`.
  Include an event when distance is less than or equal to `radius_km`; return one match per
  event/location pair and sort by shortest distance, then event time newest first.
- `mobile/src/services/api.ts`: retain `fetchEvents(baseUrl)` and its typed failures. The caller
  passes a configured base URL ending in `/api/v1`; no new endpoint is introduced.
- `mobile/src/config.ts`: export an empty default `API_BASE_URL` that a release/build can
  replace without changing API-client code; users may also enter and persist a URL in the app.
- `mobile/src/screens/SavedLocationsScreen.tsx`: accept locations and create/delete callbacks;
  provide name, latitude, longitude, and radius inputs, validation feedback, and an API base
  URL input.
- `mobile/src/screens/NearbyHazardsScreen.tsx`: accept nearby matches, loading/offline/error
  state, and a retry callback; render explicit states and event details.
- `mobile/src/screens/AlertsScreen.tsx`: render the same proximity matches as an in-app
  foreground alert list and state clearly that background push is not configured.
- `mobile/src/components/HazardMatchList.tsx`: render each event/location match with source,
  place, timestamp, magnitude, and distance.
- `mobile/src/styles.ts`: shared React Native presentation styles for tabs, forms, state
  messages, and event cards.
- `mobile/src/navigation/RootNavigator.tsx`: own app-level async loading, persisted state,
  refresh, and a three-tab selector; default to Nearby.
- `mobile/src/services/pushNotifications.ts`: preserve `not-configured` as the explicit
  background notification status.

### Configuration

No secrets or server environment variables are required. `API_BASE_URL` defaults to empty so
the app displays a setup prompt instead of silently calling an invalid host. A user can enter
the API origin plus `/api/v1` in Saved locations; that value persists on-device. The setting
must use a device-reachable URL (for example, a LAN address on a physical device).

### Error handling

`fetchEvents` keeps its typed `ApiError`. Storage read failures fall back to empty in-memory
state and surface a concise saved-data warning; storage writes report an actionable save
error. Network errors display the cached event list when present with an explicit offline
label and retry button. Empty saved locations, empty event results, and no nearby matches have
separate explanatory UI. Background push continues to report `not-configured`.

### Data considerations

Coordinates are decimal degrees with north/east positive. Distance is calculated using the
Haversine formula and a mean Earth radius of 6,371 km. A radius match is inclusive at its
boundary. Locations and events remain local to the device; no location data is sent to the
backend. The event feed remains canonical/primary-only by using the existing API default.

## Rollout

Ship as one mobile feature branch based on current `main`. Add the dependency, service logic,
tab shell, screens, and setup documentation in dependency order. No migration or backend
deployment is needed. Existing push registration remains explicitly unconfigured.

## Files

### Mobile

- `mobile/package.json`, `mobile/package-lock.json` — add AsyncStorage 1.24.0.
- `mobile/src/config.ts` — default API URL configuration.
- `mobile/src/types/hazard.ts` — saved-location and proximity result types.
- `mobile/src/services/offlineCache.ts` — persistent JSON cache.
- `mobile/src/services/savedLocations.ts` — validated saved-location persistence.
- `mobile/src/services/settings.ts` — API URL validation and persistence.
- `mobile/src/services/proximity.ts` — pure distance and radius matching.
- `mobile/src/services/api.ts` — preserve the existing typed events client.
- `mobile/src/navigation/RootNavigator.tsx` — app data lifecycle and three tabs.
- `mobile/src/screens/SavedLocationsScreen.tsx` — location and API URL forms.
- `mobile/src/screens/NearbyHazardsScreen.tsx` — nearby event list and request states.
- `mobile/src/screens/AlertsScreen.tsx` — foreground alert list and push status.
- `mobile/src/components/HazardMatchList.tsx` — shared event match presentation.
- `mobile/src/styles.ts` — shared React Native screen styles.
- `mobile/tests/offlineCache.test.ts` — persistence and invalid JSON behavior.
- `mobile/tests/savedLocations.test.ts` — load/save and input validation.
- `mobile/tests/settings.test.ts` — API URL validation and persistence.
- `mobile/tests/proximity.test.ts` — distance, boundary, sorting, and multiple locations.
- `mobile/tests/api.test.ts` — retain mapping/errors and cover refresh fallback if housed in a
  service test.
- `mobile/tests/eventFeed.test.ts` — network refresh, cache fallback, and configured/unconfigured
  API URL behavior.

### Documentation

- `docs/glossary.md` — define `SavedLocation`, `radius_km`, and foreground realtime alerts.
- `README.md` — explain API URL setup and the mobile slice's offline/foreground behavior.

## Testing Strategy

- From `mobile/`, use Jest service tests with a mocked AsyncStorage module. Cover storage
  persistence across service calls, malformed cache values, saved-location validation,
  Haversine calculations, exact-radius inclusivity, stable ordering, API success, network/API
  errors, cache fallback, malformed cached-event shape rejection, and no-URL setup state.
- Run `npm test` from `mobile/` and `npm run build` is not applicable because this package
  has no build script or TypeScript project file.
- From repository root, run `python scripts\verify_structure.py` and `git diff --check`.
- Native device builds are not acceptance criteria because this repository does not include
  generated Android/iOS projects; the feature keeps its logic device-independent and uses
  AsyncStorage's documented auto-linking when a native project is added.

## Acceptance Criteria

- [ ] `npm test` passes from `mobile/` with storage, validation, matching, API, and offline
  fallback coverage.
- [ ] The user can add a named location with valid coordinates and a radius from 1–500 km,
  see it in the list, and delete it.
- [ ] Invalid names, out-of-range coordinates, radii below 1 km, and radii above 500 km
  are rejected with field-level feedback.
- [ ] A configured `/api/v1` URL loads primary events; nearby lists include only events at
  or inside each saved radius and display their source, place, time, magnitude, and distance.
- [ ] Locations, API URL, and the last successful event list persist across app restarts.
- [ ] A network failure shows cached events as stale/offline with a retry action; absent cache
  shows a clear empty/offline state.
- [ ] Nearby, Saved locations, and Alerts tabs are reachable; Alerts uses the same nearby
  matches and clearly identifies itself as foreground-only.
- [ ] No mobile location data is sent to the backend and no official warning/forecast claim is
  introduced.
- [ ] `python scripts\verify_structure.py` and `git diff --check` pass.

## Out Of Scope (backlog)

- Background push provider setup, APNs/FCM credentials, device token registration, and backend
  notification delivery.
- Automatic geolocation, saved-location editing, or cloud synchronization.
- Native Android/iOS project generation and device build pipelines.
- Map views, notification preferences per hazard type, quiet hours, and historical replay.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-09-epic4-mobile-nearby-alerts.md`.
- Terminology: `docs/glossary.md`.
