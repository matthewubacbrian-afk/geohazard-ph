# Selected Earthquake Pulse — Design

**Date:** 2026-10-10

## Problem

The dashboard's map markers cannot currently be selected. Selecting an item in
the Regional activity feed opens its details, but that selection is local to the
feed and does not identify or emphasize the same event on the map. Users need to
select a map circle and see its event data while retaining the surrounding feed.

## Goals

- A click on a rendered event circle selects the matching `HazardEvent`.
- The selected event's existing details appear inline in Regional activity while
  the event list stays available.
- Selecting an event in either the map or feed updates the same dashboard state
  and map camera.
- Only the selected map event has a slow, subtle pulse. Changing or clearing the
  selection moves or removes the pulse.
- Reduced-motion preferences disable animation while retaining a static selected
  marker highlight.
- Existing magnitude-dependent marker size, color, source filtering, and event
  details remain intact.

## Non-goals

- No backend, API client, event type, response mapping, or endpoint changes.
- No changes to earthquake data, magnitude styling, marker sizing, event
  filters, or risk-profile meaning.
- No automatic navigation to another dashboard view when a marker is selected.
- No pulse for unselected events or unrelated map layers.

## Context And Constraints

- `Dashboard` owns the event data and passes it to `DashboardMapArea` and
  `EventFeed`.
- `MapView` renders `events` in the MapLibre `event-circles` layer and already
  receives `selectedEvent` to move the camera.
- `EventFeed` currently owns a private selected ID and renders the existing
  `EventDetailPanel` after its list. That state must be lifted to `Dashboard`
  so map and feed selection stay synchronized.
- Keep React/TypeScript strict, CSS Modules, existing MapLibre integration, and
  current API contracts. Follow `CODING_STANDARDS.md`,
  `docs/testing-standards.md`, and `docs/glossary.md`.

## Alternatives Considered

1. **Keep the feed visible and show selected details inline (chosen).** Keeps
   nearby events in view and matches the user's selected visual option A.
2. **Replace the feed with a focused event detail view.** Gives the selection
   more space, but hides surrounding events until the user returns to the feed.
3. **Show details in a map popup only.** Keeps the side panel unchanged, but
   does not meet the request to show the selected event in the dashboard side.

## Design

### Architecture and data flow

```text
MapView circle click ─┐
                      ├─> Dashboard selectedEventId ──> MapView camera + pulse
Feed item click ──────┘                          └──> EventFeed inline details
Event detail close ─────> clear selectedEventId ─────> remove pulse and details
```

`Dashboard` is the single source of truth for `selectedEventId` and derives the
selected `HazardEvent` from the current visible events. Map click handlers
resolve a stable event ID from the rendered feature and call the selection
callback with the matching current event. Feed selection calls the same
callback. `EventFeed` receives a controlled selected event and clear callback;
it no longer owns a competing selection ID.

### Components and interfaces

- `MapView` adds optional `onSelectEvent?: (event: HazardEvent) => void`.
- Event GeoJSON features include `properties.eventId` so map clicks resolve to
  the latest matching event in `eventsRef.current`.
- A separate selected-event GeoJSON source contains only the selected point.
  Its halo layer animates radius and opacity slowly with a single
  `requestAnimationFrame` loop while selection exists. Replacing the selected
  point moves the halo; clearing selection empties/hides the selected source and
  cancels the loop. The base event circle layer remains static.
- When `prefers-reduced-motion: reduce` matches, the halo is a static highlight
  and no animation loop runs.
- `DashboardMapArea` forwards the selection callback to `MapView`.
- `EventFeed` accepts `selectedEvent?: HazardEvent | null` and
  `onClearSelection?: () => void`; when selected, that event is pinned at the
  top of the scrollable feed with `EventDetailPanel` rendered directly under
  its item. Other events continue below and remain subject to the existing feed
  category filters. The pinned selection remains visible if the feed's local
  category filter would otherwise hide it, so a map selection always has
  matching side-panel details.
- `Dashboard` passes the shared selection state/callback to both paths and
  stores the selected ID, derives the current event record, and clears it when
  `EventDetailPanel` closes. If refreshed/filtered dashboard events no longer
  contain the selection, selection is cleared.

### Configuration

No new settings or environment variables. Pulse timing and halo bounds are
constants local to `MapView`; motion remains subtle and does not alter the
magnitude color or radius encoding.

### Error handling

If a clicked map feature has no usable `eventId`, the handler does nothing. If
the event is no longer in the current filtered data, selection is cleared. No
API request is added; event attributes come from the existing `HazardEvent`.

### Data considerations

Selection uses the current `HazardEvent.id`, not array position, place name, or
coordinates. The GeoJSON point coordinates remain `[longitude, latitude]`.

## Rollout

Implement on `feat/selected-earthquake-pulse` from the merged `main`. Add and run
failing web tests before implementation, then implement and verify the web test
suite and build. Publish the completed feature as a PR against `main` and merge
it after review.

## Files

- `web/src/components/map/MapView.tsx` — map hit selection, selected point
  source/layer, reduced-motion-aware halo animation.
- `web/src/components/dashboard/DashboardMapArea.tsx` — pass map selection to
  the dashboard.
- `web/src/pages/Dashboard.tsx` — shared selection state and clearing when the
  selected event leaves the visible event set.
- `web/src/components/events/EventFeed.tsx` — controlled selection and inline
  details while keeping the event list visible.
- `web/src/components/events/EventFeed.module.css` — selected detail placement
  and scrolling layout if needed.
- `web/tests/MapView.test.tsx` — map click resolution, selected halo data, and
  reduced-motion behavior.
- `web/tests/EventFeed.test.tsx` — controlled selection and clearing while
  preserving the event list.
- `web/tests/DashboardStates.test.tsx` — map/feed shared selection wiring and
  stale selection clearing using the existing dashboard test setup.

## Testing Strategy

- `MapView.test.tsx`: a click on a feature resolves the correct event; selected
  source contains only that event; selection changes/clears update that source;
  reduced motion prevents animation while preserving the static highlight.
- `EventFeed.test.tsx`: selected event details render inline with other events
  still visible; closing details calls the controlled clear callback; selecting
  a feed event reports it to the parent.
- `DashboardStates.test.tsx` (or the closest existing dashboard integration test):
  map and feed selection share the selected event; clearing or losing the event
  removes the selection.
- Run `cd web && npm test`, `cd web && npm run build`, and
  `python scripts/verify_structure.py` when files are added/renamed.

## Acceptance Criteria

- [ ] Clicking a map event marker selects the correct current event.
- [ ] The selected event and details appear inline in Regional activity without
  removing the rest of the feed.
- [ ] Feed selection and map selection stay synchronized.
- [ ] Exactly one selected event halo pulses; other event markers remain static.
- [ ] Selecting a different event moves the halo; closing details or losing the
  event clears details and stops animation.
- [ ] Reduced-motion preference renders a static selected highlight.
- [ ] Magnitude radius/color, filters, and API contracts remain unchanged.
- [ ] Web tests, build, and required structure verification pass.

## Out Of Scope (backlog)

- Keyboard navigation among canvas-rendered events beyond the existing
  accessible event feed, which remains the equivalent event-selection control.
- Persisting selected event in the URL or across reloads.

---

## Spec self-review

- No placeholders remain; goals map to acceptance criteria and named tests.
- Interfaces and event identity are explicit; no API or schema change is
  described.
- The selected halo is a separate single-event overlay, so unselected markers
  cannot pulse.
- Scope is limited to map/feed selection and fits one feature plan.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-10-10-selected-earthquake-pulse.md`
- Terminology: `docs/glossary.md`
