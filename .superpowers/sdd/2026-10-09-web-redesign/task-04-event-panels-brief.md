# Task 4: Event and summary panels

## Objective

Restyle the live event feed, filter, event selection/details, dashboard summary,
and realtime status to match the approved GeoHazard PH design. Preserve all data,
filters, hooks, API contracts, refresh intervals, and current unavailable states.

## Scope and constraints

- Update CSS Modules under `web/src/components/events/` and dashboard styles for
  `DashboardMapArea` and `RealtimeStatus`; adjust dashboard panel alignment only
  if needed.
- Keep the event list and map on the same `visibleEvents` collection.
- Do not edit hooks, API clients, realtime transport, event types, params, filters,
  cache reconciliation, or 30-second intervals.
- Preserve actual server summary values, retry/loading/error/empty states, units,
  source and timestamps, keyboard focus/selection, and honest “Coming soon” fields.
- Put the exact disclaimer “GeoHazard PH is not an official PHIVOLCS/NDRRMC advisory”
  in dashboard data/status context.
- Keep the preceding uncommitted sidebar fix intact.

## Verification

Run the five focused Vitest files from the approved plan and `npm run build` in
`web/`. Review the diff for protected interfaces and run `git diff --check`.

## Acceptance

The existing behavior assertions remain intact, additional assertions cover feed
selection and retry affordances, updated panels use the semantic tokens and visible
focus/selected states, and all requested checks pass. Commit as
`style: clarify live event and summary panels`.
