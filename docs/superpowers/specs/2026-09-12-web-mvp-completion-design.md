# Web MVP Completion - Design

**Date:** 2026-09-12

## Problem

The web application already has a production-quality Hero page, a working hazard dashboard, and page components for About, Data Sources, and Historical Browser. However, `web/src/App.tsx` selects pages with local React state, so browser history, deep links, and refreshes are not reliable. The dashboard summary is missing, regional risk data is represented by a legend rather than a rendered map overlay, and navigation/content cleanup is incomplete.

This prevents the web app from presenting a coherent, shareable MVP even though the backend data contracts and most UI components already exist.

## Goals

- Replace local page selection in `web/src/App.tsx` with URL-based routing for Hero, Dashboard, About, Data Sources, and Historical Browser.
- Make navigation links work on direct load, browser back/forward, and unknown-route fallback.
- Preserve stable dashboard view and filter state in URL query parameters where the existing dashboard supports those controls.
- Render regional risk profiles as a MapLibre overlay by joining existing risk-profile records to a documented Philippine-region boundary asset and using canonical risk labels.
- Add a dashboard summary card using the existing events-summary API data, including loading, empty, and error states.
- Present About, Data Sources, and Historical Browser as complete user-facing pages consistent with the existing design system.
- Add focused tests for routes, navigation, summary states, risk-overlay conversion, and the informational pages.
- Keep `npm test` and `npm run build` passing from `web/`.

## Non-goals

- Building a functional historical event browser or adding a historical-search backend endpoint.
- Adding authentication, alerts, push notifications, ML inference, or mobile functionality.
- Changing backend response contracts or database schemas.
- Introducing production hosting, TLS, Terraform, or deployment changes.
- Replacing the existing design system, map library, API client, or realtime transport.

## Context And Constraints

- The web stack is React 18, TypeScript, Vite, TanStack Query, and MapLibre GL.
- Existing pages include `Hero`, `Dashboard`, `About`, `DataSources`, and `HistoricalBrowser`; the implementation must reuse them where practical.
- `App.tsx` currently uses a `View` state union and callback props for navigation. This is the primary routing migration point.
- React Router is not currently listed in `web/package.json`; it will be added as the routing dependency if the chosen design is approved for implementation.
- Existing API hooks and types are the source of truth for events, event summaries, faults, volcano zones, volcanoes, and risk profiles.
- `RiskProfile` currently has no geometry, so region names must not be converted into fabricated polygons. The overlay requires a versioned, license-compatible Philippine-region boundary GeoJSON asset, with provenance recorded in `docs/data-sources.md`.
- Risk labels are descriptive statistical profiles of historical records, not predictions or official warnings. User-facing copy must preserve that distinction.
- Web tests use Vitest and Testing Library in `web/tests/`; MapLibre and network boundaries must remain mocked.
- Follow `CODING_STANDARDS.md`, `docs/glossary.md`, `docs/api-contracts.md`, and `docs/testing-standards.md`.

## Alternatives Considered

### React Router

Provides standard browser history, direct routes, redirects, query-string support, and a clear route boundary for future nested dashboard views. It adds one focused dependency and requires migrating the current callback-based navigation.

**Chosen** because the application already has multiple pages and dashboard state that benefits from durable URLs.

### Custom `window.history` routing

Avoids a dependency and could support the current five routes, but would require maintaining route parsing, navigation events, redirects, and query-state behavior locally.

**Rejected** because it duplicates mature router behavior and would create a fragile foundation for future dashboard routes.

### Hash routing

Works on static hosting without server fallback configuration and is small to implement.

**Rejected** because hash URLs are less suitable for shareable product routes and do not match the intended application navigation model.

## Design

### Architecture And Data Flow

The application will use a single router at the app boundary:

```text
browser URL
    -> React Router route
        -> page component
            -> existing hooks/API clients
                -> backend API or WebSocket
                    -> page/component state
```

Routes:

- `/` renders `Hero`.
- `/dashboard` renders `Dashboard`.
- `/about` renders `About`.
- `/data-sources` renders `DataSources`.
- `/historical` renders `HistoricalBrowser` as an informational future-feature page.
- Any unknown path redirects to `/`.

Dashboard query parameters will use existing domain names and remain optional. The implementation will only serialize controls that already have stable values, such as the active dashboard view, source filter, date filter, magnitude filter, and selected region. Invalid values fall back to the existing dashboard defaults rather than producing a broken screen.

The risk overlay will join loaded `RiskProfile` records by `region_name` to the versioned Philippine-region boundary asset, then transform matched rows into the GeoJSON/features expected by the map layer. The transformation will remain a pure function so it can be tested without MapLibre. The map will render the overlay independently of event loading; a risk-profile failure will leave the event map usable and show a local error or unavailable state for the overlay. Unmatched regions will be omitted and counted for diagnostics rather than drawn at guessed coordinates.

The summary card will consume the existing event-summary query. It will show the count, average or maximum magnitude values already supplied by the contract, and the latest event timestamp. It will not invent warning levels or derive official alert status.

### Components And Files

- `web/src/App.tsx`: own the router and shared settings-panel boundary.
- `web/src/navigation/`: contain route definitions or navigation helpers if the existing structure supports that location.
- `web/src/pages/About.tsx`: project purpose and limitations.
- `web/src/pages/DataSources.tsx`: source provenance and licensing references.
- `web/src/pages/HistoricalBrowser.tsx`: future-feature explanation with a dashboard link; no fake controls.
- `web/src/components/dashboard/`: summary card and its loading, empty, and error states.
- `web/src/components/map/`: risk overlay layer and pure profile-to-feature conversion where those modules fit the existing map ownership.
- `web/src/data/philippine-regions.json`: versioned, simplified and quantized GeoJSON FeatureCollection region boundaries used by the risk overlay, with documented provenance.
- `web/src/hooks/` and `web/src/api/`: reuse existing query hooks and API clients; do not move business logic into page components.
- `web/src/types/`: reuse canonical wire-format fields and add only narrowly scoped UI types if needed.
- `web/tests/`: add behavior-focused tests matching the existing component naming conventions.

### Interfaces

The route boundary will expose typed page navigation through React Router rather than the current `onNavigate` callback. Existing page props unrelated to routing, such as settings access, remain supported during migration.

The risk conversion helper will have a pure interface equivalent to:

```ts
function riskProfilesToFeatureCollection(
  profiles: RiskProfile[],
    boundaries: GeoJSON.FeatureCollection<GeoJSON.Polygon | GeoJSON.MultiPolygon>,
): GeoJSON.FeatureCollection<GeoJSON.Polygon | GeoJSON.MultiPolygon>;
```

The boundary feature property used for the join must be declared in the boundary asset and normalized with the same case-insensitive region-name rule as backend risk-profile lookup. Known province-level aliases, including `Palawan` to `Mimaropa`, are maintained in the web overlay adapter. The helper must preserve boundary geometry and add the profile label, confidence, and region name to feature properties. It must not fabricate geometry from region names.

### Configuration

No new environment variables or backend settings are required. The web build will use the existing API base URL and MapLibre configuration.

### Error Handling

- Unknown routes redirect to the Hero route.
- Invalid query parameters are ignored and replaced by dashboard defaults.
- API loading and error states remain local to the affected dashboard region where possible.
- Summary and risk-profile failures are rendered as user-visible recoverable states with retry behavior where the existing query abstraction supports it.
- The WebSocket LIVE indicator continues to describe transport connectivity only.
- Informational pages remain renderable without API access.

### Data Considerations

No schema or migration changes are needed. Existing snake_case wire fields and glossary terminology remain authoritative. Dates remain ISO 8601 values from the API and are formatted only at the presentation boundary. Risk labels remain `Low`, `Moderate`, `High`, and `Very High`, with descriptive disclaimer text.

## Rollout

This is a web-only feature branch. Implementation should land in these logical increments:

1. Select and document a license-compatible Philippine-region boundary asset, then add it as a versioned web data asset.
2. Add React Router and migrate `App.tsx` plus shared navigation.
3. Complete and test the three informational routes, including the future-feature Historical page.
4. Add and test the dashboard summary card.
5. Add the pure risk-profile/boundary conversion and MapLibre overlay.
6. Serialize stable dashboard state, remove routing cleanup gaps, and update stale footer/navigation content.
7. Run the complete web test/build checks and the structure verifier if the file tree changed.

No feature flag or database migration is required. The route migration should preserve the existing default Hero entry point.

## Files

### Web application

- Modify: `web/package.json` - add the routing dependency.
- Modify: `web/src/App.tsx` - replace local page switching with route configuration.
- Modify: `web/src/pages/About.tsx` - complete or align content with the approved MVP copy.
- Modify: `web/src/pages/DataSources.tsx` - complete or align source/provenance content.
- Modify: `web/src/pages/HistoricalBrowser.tsx` - provide the informational future-feature page.
- Modify: existing navigation/footer files - route links and current-year content.
- Create or modify: dashboard summary component and module styles.
- Create or modify: risk overlay helper/layer and module styles.
- Create: `web/src/data/philippine-regions.json` - boundary asset used by the risk overlay.
- Create or modify: route/query-state helpers only where needed by the existing structure.

### Tests

- Create or modify: route/navigation tests for direct paths, links, history, and fallback.
- Create or modify: summary-card tests for loading, empty, success, and error states.
- Create or modify: risk-overlay conversion tests for valid profiles and unavailable data.
- Create or modify: informational-page tests for page headings, future-feature messaging, and links.

### Documentation

- Modify: `docs/superpowers/specs/2026-09-12-web-mvp-completion-design.md` - this design specification.
- Create later: `docs/superpowers/plans/2026-09-12-web-mvp-completion.md` - implementation plan after spec approval.

## Testing Strategy

Tests will remain isolated from live APIs and MapLibre rendering.

- Route tests verify each supported path, unknown-path fallback, navigation links, and browser-history behavior.
- Dashboard tests verify query-state restoration and preserve existing map/feed behavior.
- Summary-card tests verify loaded, empty, loading, error, and retry states using mocked query data.
- Risk-overlay tests verify pure conversion behavior, case-insensitive region joins, canonical risk labels, valid geometry handling, unmatched-region omission, and no fabricated geometry when data is incomplete.
- Informational-page tests verify visible purpose/content, source links, future-feature language, and dashboard navigation.
- Run `npm test` and `npm run build` from `web/` after implementation.
- Run `python scripts\verify_structure.py` if files are added or moved.

## Acceptance Criteria

- [ ] `npm install` from `web/` installs the routing dependency without dependency conflicts.
- [ ] `/`, `/dashboard`, `/about`, `/data-sources`, and `/historical` render directly after a browser refresh.
- [ ] Unknown paths redirect to `/`.
- [ ] Browser back and forward navigate between pages correctly.
- [ ] Navigation exposes Dashboard, About, Data Sources, and Historical without stale or dead links.
- [ ] The Historical page clearly describes a future feature and does not present non-functional search controls.
- [ ] The dashboard summary displays API-backed values and has loading, empty, and error states.
- [ ] The risk overlay joins profiles to a versioned, license-compatible region boundary asset, renders only valid geometry-backed data, and uses the canonical descriptive risk labels.
- [ ] Boundary asset provenance and licensing are recorded in `docs/data-sources.md`.
- [ ] Risk-profile unavailability does not prevent the event map from rendering.
- [ ] Stable dashboard filters and selected region can be restored from a copied URL.
- [ ] Informational pages render without a running backend.
- [ ] `npm test` passes from `web/`.
- [ ] `npm run build` passes from `web/`.
- [ ] No generated `web/dist/` artifact is added to the change.

## Out Of Scope (backlog)

- Functional historical browsing, date-range search, export, and comparison views.
- Backend hazard-summary implementation if the existing events-summary contract is insufficient for the dashboard card.
- ML inference or predictive map layers.
- User accounts, authorization, alert subscriptions, and push notifications.
- Mobile navigation and mobile map support.
- Production Docker, TLS, Terraform, hosting, and deployment automation.

---

## Spec self-review

- No unfinished placeholders remain.
- The Historical Browser is consistently defined as informational and out of scope for functional search.
- The spec treats existing page components as incremental targets rather than assuming they are absent.
- Every goal has corresponding acceptance criteria and testing coverage.
- The scope is limited to one web implementation plan and does not include backend, mobile, ML, or production infrastructure work.

## Related documents

- Implementation plan: `docs/superpowers/plans/2026-09-12-web-mvp-completion.md` (to be created after spec approval).
- Terminology: `docs/glossary.md`.
- API contracts: `docs/api-contracts.md`.
- Testing standards: `docs/testing-standards.md`.
- General standards: `CODING_STANDARDS.md`.