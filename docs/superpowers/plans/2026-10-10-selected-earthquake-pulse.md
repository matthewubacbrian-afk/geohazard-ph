# Selected Earthquake Pulse Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let dashboard users select one earthquake from the map or activity feed, see its details while retaining the feed, and pulse only its map marker.

**Architecture:** `Dashboard` stores the selected event ID and derives the current event from the filtered map data. `MapView` emits map marker selection and renders one separate selected-marker halo layer. `EventFeed` receives controlled selection, pins its details at the top, and emits selection/clear actions.

**Tech Stack:** React 18, TypeScript strict, MapLibre GL, CSS Modules, Vitest, React Testing Library.

**Spec:** `docs/superpowers/specs/2026-10-10-selected-earthquake-pulse-design.md`

---

## Global Constraints

- Follow `AGENTS.md`, `CODING_STANDARDS.md`, `docs/glossary.md`, and `docs/testing-standards.md`.
- Do not alter API clients, hooks, endpoint params, data contracts, backend, ML, or mobile code.
- Keep event magnitude radius/color expressions unchanged; the animated halo is an extra layer containing only the selected point.
- Keep selection keyed by `HazardEvent.id`; event coordinates stay `[longitude, latitude]` in GeoJSON.
- Respect `prefers-reduced-motion`: render a static selected halo and do not schedule animation frames.
- Use TDD for each behavior. Run focused web tests first, then `cd web && npm test`, `cd web && npm run build`, `python scripts/verify_structure.py`, and `git diff --check` before publishing.
- Work on the existing `feat/selected-earthquake-pulse` branch in the current checkout. Commit each task using Conventional Commit messages.

### Task 1: Select map events and animate a single halo

**Files:**
- Modify: `web/src/components/map/MapView.tsx`
- Test: `web/tests/MapView.test.tsx`

- [ ] **Step 1: Add failing map-click selection test**

Extend the MapLibre test double so `map.on('click', 'event-circles', handler)` can be captured and invoked with a rendered feature. Add this test:

```tsx
it('selects the event represented by a clicked map circle', () => {
  const onSelectEvent = vi.fn();
  render(<MapView events={[event]} onSelectEvent={onSelectEvent} />);
  act(() => emit('style.load'));
  const click = layerHandlers.get('event-circles');

  act(() => click?.({ features: [{ properties: { eventId: 'e1' } }] }));

  expect(onSelectEvent).toHaveBeenCalledWith(event);
});
```

Also add tests for a missing `eventId` (no callback) and an ID that has
disappeared from `eventsRef.current` (no callback).

- [ ] **Step 2: Run the focused test and verify the expected failure**

Run: `cd web && npm test -- MapView.test.tsx -t "selects the event represented"`
Expected: FAIL because `MapView` does not yet register a circle selection callback.

- [ ] **Step 3: Add the selected point source and map click callback**

Add optional prop `onSelectEvent?: (event: HazardEvent) => void`, keep its latest value in a ref, and add `eventId: event.id` to `toFeatureCollection` feature properties:

```ts
properties: {
  eventId: event.id,
  place: event.place_name,
  magnitude: event.magnitude ?? null,
},
```

After adding `event-circles`, register a layer click handler. Remove a prior registration before re-registering after style replacement, and remove it on teardown:

```ts
const handleEventClick = (event: maplibregl.MapLayerMouseEvent) => {
  const eventId = event.features?.[0]?.properties?.eventId;
  if (typeof eventId !== 'string') return;
  const selected = eventsRef.current.find((row) => row.id === eventId);
  if (selected) onSelectEventRef.current?.(selected);
};
```

Add a `selected-event` GeoJSON source and `selected-event-pulse` circle layer containing only the selected event's point. Keep `event-circles` paint expressions unchanged. Represent a missing selection with an empty `FeatureCollection`; a selected event uses exactly this point feature shape:

```ts
{
  type: 'Feature',
  geometry: { type: 'Point', coordinates: [selectedEvent.longitude, selectedEvent.latitude] },
  properties: { magnitude: selectedEvent.magnitude ?? null },
}
```

The selected layer uses the existing magnitude color step expression. On a selected event change, update the source and restart no more than one animation loop; on deselection, clear the source and cancel its scheduled frame.

With reduced motion, set a visible static halo and schedule no animation. Otherwise, use one `requestAnimationFrame` loop to vary only the halo layer's radius and opacity on a roughly 1.8-second cycle. Start only while a selected event exists; changing the selection reuses the single loop and updates its point. Stop and cancel on deselection and unmount. Ignore map click features with absent/unknown IDs.

For each frame, normalize elapsed time as `phase = (timestamp % 1800) / 1800`, set radius to `13 + 7 * (0.5 - 0.5 * Math.cos(phase * 2 * Math.PI))`, and set opacity to `0.22 + 0.3 * (0.5 + 0.5 * Math.cos(phase * 2 * Math.PI))`. Check that the selected layer still exists before calling `setPaintProperty`, since a style reload can temporarily remove custom layers.

- [ ] **Step 4: Add halo update and reduced-motion tests**

Assert that the selected source receives one point with the selected event coordinates; changing selection updates it to only the new point; clearing selection empties the source and calls `cancelAnimationFrame`; reduced motion produces a static halo and does not call `requestAnimationFrame`. Assert that normal motion schedules one frame and calls `setPaintProperty` only for `selected-event-pulse`. Test that no marker base paint expression changes.

- [ ] **Step 5: Run map tests and commit**

Run: `cd web && npm test -- MapView.test.tsx`
Expected: all MapView tests pass.

```bash
git add web/src/components/map/MapView.tsx web/tests/MapView.test.tsx
git commit -m "feat: select and pulse dashboard map events"
```

### Task 2: Keep feed details controlled and visible inline

**Files:**
- Modify: `web/src/components/events/EventFeed.tsx`
- Test: `web/tests/EventFeed.test.tsx`

- [ ] **Step 1: Add failing controlled-selection tests**

Add the first test in `EventFeed.test.tsx`:

```tsx
it('pins the controlled selection and keeps the rest of the feed visible', () => {
  render(
    <EventFeed
      events={events}
      selectedEvent={events[0]}
      isLoading={false}
      error={null}
      onRetry={() => {}}
      onSelectEvent={() => {}}
      onClearSelection={() => {}}
    />,
  );

  expect(screen.getByRole('button', { name: /Quezon/i })).toHaveAttribute('aria-pressed', 'true');
  expect(screen.getByText('Coordinates')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Batangas/i })).toBeInTheDocument();
});
```

Add a second case that disables the selected event's category pill, then verifies the selected event and `Coordinates` stay visible while the other filtered row is hidden. Add a close assertion (`onClearSelection` called once) and assert clicking a different event calls `onSelectEvent` while the selected button remains unchanged until rerender.

- [ ] **Step 2: Run focused EventFeed tests and verify the expected failure**

Run: `cd web && npm test -- EventFeed.test.tsx`
Expected: FAIL because `selectedEvent` and `onClearSelection` are not controlled props yet.

- [ ] **Step 3: Make EventFeed selection controlled**

Add optional props `selectedEvent?: HazardEvent | null` and `onClearSelection?: () => void`; remove `selectedId` state. Derive filtered events as today. Render the selected event once at the start of the scrollable feed body using `EventFeedItem selected` and `EventDetailPanel`; exclude its ID from the remaining filtered rows so it is not duplicated. Render remaining items with `selected={false}` and the existing selection callback. Render the normal empty state only when there is neither a selected event nor a matching event row. Close invokes only `onClearSelection`.

Keep the existing loading and error messages, and render selected details whenever `selectedEvent` is non-null, including during a background refresh or event-list error. In loading/error states, show the selected event first and the existing status message below it. Preserve accessible pressed state and the close button label.

- [ ] **Step 4: Run focused EventFeed tests and commit**

Run: `cd web && npm test -- EventFeed.test.tsx`
Expected: all EventFeed tests pass, including existing loading, error, empty, and retry coverage.

```bash
git add web/src/components/events/EventFeed.tsx web/src/components/events/EventFeed.module.css web/tests/EventFeed.test.tsx
git commit -m "feat: show selected event details in activity feed"
```

### Task 3: Share selection state across dashboard, map, and feed

**Files:**
- Modify: `web/src/pages/Dashboard.tsx`
- Modify: `web/src/components/dashboard/DashboardMapArea.tsx`
- Test: `web/tests/EventSelection.test.tsx`

- [ ] **Step 1: Add failing dashboard synchronization tests**

Update the `DashboardMapArea` test mock in `EventSelection.test.tsx` to expose its `onSelectEvent` callback. Assert that invoking that callback selects the matching map target and makes the event details visible in `EventFeed`. Assert selecting the feed row sends the same event to the map target. Assert closing the details removes the map target. Add a rerender case where `useEvents` no longer returns the selected ID; the map target and details must clear.

Use a mock that captures its prop instead of hard-coding the map target:

```tsx
let selectOnMap: ((selected: typeof event) => void) | undefined;
vi.mock('../src/components/dashboard/DashboardMapArea', () => ({
  default: ({ selectedEvent, onSelectEvent }: {
    selectedEvent?: typeof event | null;
    onSelectEvent?: (selected: typeof event) => void;
  }) => {
    selectOnMap = onSelectEvent;
    return <div role="status">{selectedEvent ? `Map target: ${selectedEvent.id}` : 'No map target'}</div>;
  },
}));
```

Invoke `selectOnMap?.(event)` inside `act`, assert `Map target: e1` and `Coordinates`, then click `Close detail` and assert `No map target`. The existing feed-row selection test must assert the same map target. Use a mutable event fixture returned by the mocked `useEvents` hook, rerender after removing its row, and assert selection/details clear.

- [ ] **Step 2: Run focused tests and verify expected failures**

Run: `cd web && npm test -- EventSelection.test.tsx`
Expected: FAIL because map selection is not forwarded and feed selection is not yet driven by dashboard state.

- [ ] **Step 3: Wire shared selected event ID**

In `Dashboard`, store `selectedEventId: string | null`. After computing `visibleEvents`, derive `selectedEvent = visibleEvents.find((event) => event.id === selectedEventId) ?? null`. If a non-null ID no longer resolves after filtering or REST/realtime updates, clear it in an effect:

```tsx
useEffect(() => {
  if (selectedEventId && !selectedEvent) setSelectedEventId(null);
}, [selectedEventId, selectedEvent]);
```

Pass `selectedEvent` and `onSelectEvent={(event) => setSelectedEventId(event.id)}` through `DashboardMapArea`; pass `selectedEvent` and `onClearSelection={() => setSelectedEventId(null)}` to `EventFeed`.

In `DashboardMapArea`, accept and forward `onSelectEvent?: (event: HazardEvent) => void` to `MapView`. Keep the existing `selectedEvent` camera behavior intact.

- [ ] **Step 4: Run integration-focused tests and commit**

Run: `cd web && npm test -- EventSelection.test.tsx`
Expected: map/feed selection synchronization and stale selection clearing pass.

```bash
git add web/src/pages/Dashboard.tsx web/src/components/dashboard/DashboardMapArea.tsx web/tests/EventSelection.test.tsx
git commit -m "feat: synchronize map and feed event selection"
```

### Task 4: Verify the complete feature and publish

**Files:**
- No additional files unless verification reveals a regression.

- [ ] **Step 1: Run the complete web test suite**

Run: `cd web && npm test`
Expected: all web tests pass; no existing behavior assertions are removed.

- [ ] **Step 2: Build and verify repository structure**

Run: `cd web && npm run build`
Expected: Vite production build succeeds.

Run: `python scripts/verify_structure.py`
Expected: all expected scaffold paths exist.

- [ ] **Step 3: Check the final diff and publish**

Run `git diff --check`, review `git status --short`, and confirm only this feature's intended tracked files are changed. Push `feat/selected-earthquake-pulse`, open a PR against `main` with Summary / Testing / Notes, attach the PR to the task, and merge with a standard merge commit after confirming GitHub reports it clean and checks have completed.

## Notes for the executor

- The palette work is already merged into `main` as PR #22 (`86f57f1`). This plan starts from that state.
- Use the existing current checkout on `feat/selected-earthquake-pulse`; do not switch to a separate worktree.
- The event feed uses its own category filter in addition to the map filter. The selected event is pinned above the remaining filtered rows so a map selection always has visible details.
- Never animate all map events: the dedicated halo source must contain zero or one point, and the base event layer remains static.
- If the MapLibre mock cannot model continuous animation deterministically, assert the request/cancel behavior and the exact one-feature halo source rather than testing wall-clock frames.
