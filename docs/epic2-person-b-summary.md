# Epic 2: Person B Implementation Summary

**Date:** 2026-09-08  
**Branch:** `personB`  
**Scope:** Realtime event delivery and the PHIVOLCS volcano feed.

## Implementation Status

Person B's publisher, Redis-to-WebSocket delivery, web live updates, and volcano
adapter/UI are implemented and tested. Full production-source integration remains
dependent on Person A's post-commit ingestion hook and successful TLS validation
for the PHIVOLCS source. Regular ingestion does not yet publish realtime messages.

The ownership boundary follows [ADR 0002](adr/0002-epic2-realtime-phivolcs-contracts.md).
`backend/app/services/ingest.py` was left unchanged.

## Realtime Backend

- Added `EventChange`, validating UUID identities, resolved canonical fields,
  coordinates, and timezone-aware event timestamps.
- Added `events_publisher.publish(events)` to publish individual JSON messages
  to Redis channel `events:updates`. Publish failures are logged without raising
  into a successfully committed ingestion operation.
- Implemented the unversioned WebSocket endpoint `/ws/events`.
- Subscribe to Redis before accepting the WebSocket, avoiding a first-message
  subscription race. Clean up subscriptions when clients disconnect.
- Validate browser origins against `CORS_ORIGINS`, bound slow sends to five
  seconds, and close failed streams so clients can reconnect.
- Replaced the `/api/v1/subscribe` stub with actual Redis connectivity status.

Key files:

- [EventChange schema](../backend/app/schemas/event_change.py)
- [Publisher](../backend/app/services/events_publisher.py)
- [Redis subscription service](../backend/app/services/realtime.py)
- [WebSocket route](../backend/app/api/v1/realtime.py)
- [Subscription status route](../backend/app/api/v1/subscribe.py)

## Web Live Updates

- Implemented `useRealtimeAlerts` with reconnect backoff, jitter, connection
  timeout, and cleanup on unmount.
- Validate incoming messages before updating the shared React Query events cache.
- Update existing events and remove demoted source rows. Canonical replacements
  retain one marker whether the new primary or demotion arrives first.
- Reconcile through REST after connection/reconnection and refresh events and
  summaries every 30 seconds to recover missed publications.
- Added a LIVE/reconnecting indicator and last-received-update time.
- Added USGS/PHIVOLCS source selection, applied locally to both map and list.
- Derive the ws/wss URL from the API base, with an optional `VITE_WS_URL` override.

LIVE reports transport connectivity, not ingestion-worker health or an official
hazard warning. Redis pub/sub provides no durable replay.

Key files:

- [Realtime hook](../web/src/hooks/useRealtimeAlerts.ts)
- [Message validation and cache updates](../web/src/api/realtime.ts)
- [Events query](../web/src/hooks/useEvents.ts)
- [Dashboard](../web/src/pages/Dashboard.tsx)
- [Source filter](../web/src/components/events/EventFilterBar.tsx)

## PHIVOLCS Volcano Feed

- Replaced the adapter stub with parsing of PHIVOLCS WOVODAT alert-status entries
  and English bulletin links/headings.
- Preserve published alert levels, including valid level zero, source links,
  retrieval time, and bulletin observation time converted from Manila time to UTC.
- Keep missing coordinates and bulletin dates null rather than inventing values.
  The observation timestamp is not the time an alert level changed.
- Implemented `/api/v1/volcanoes` using the adapter through a service cache.
- Distinguish transport failures from malformed source data with typed exceptions.
- Added a **Volcano bulletins** dashboard view with source attribution, dates,
  stale-data labels, loading/empty states, and a retryable error state.

Cache improvements:

| Behavior | Default |
| --- | --- |
| Source request timeout | 15 seconds |
| Successful cache lifetime | 5 minutes per API process |
| Retry delay after source failure | 1 minute |
| Maximum age for stale fallback | 1 hour |

Concurrent requests share one fetch per process. Failed refreshes can return
explicitly marked stale data while preserving its retrieval time. Missing or
expired cached data produces HTTP 503 with the standard error envelope.

Key files:

- [Volcano adapter](../backend/ingestion/sources/phivolcs_volcano.py)
- [Volcano schema](../backend/app/schemas/volcano.py)
- [Volcano cache service](../backend/app/services/volcanoes.py)
- [Volcano endpoint](../backend/app/api/v1/volcanoes.py)
- [Volcano panel](../web/src/components/volcanoes/VolcanoPanel.tsx)

## Infrastructure And Documentation

- Added Nginx forwarding for `/ws/` with WebSocket upgrade headers.
- Corrected Compose API/worker database and Redis hosts to service names and
  configured these services to read the local `.env`.
- Documented volcano settings in `.env.example`.
- Updated the README, API contracts, glossary, data-source notes, and runbook with
  behavior, limitations, configuration, and Person A's integration handoff.

The earlier Linux setup documentation and local environment installation were
separate setup work and are not part of the Epic 2 feature implementation.

## Verification Results

These results were recorded after the implementation and review fixes:

| Check | Result |
| --- | --- |
| Backend suite with local PostGIS and Redis | 47 tests passed |
| Web suite | 35 tests passed |
| Web TypeScript/production build | Passed |
| Ruff on changed Python files | Passed |
| Project structure verifier | Passed: 139 expected scaffold paths |
| `git diff --check` | Passed |
| `docker compose config --quiet` | Passed |
| Running API `/api/v1/subscribe` | Reported `status: ok` |
| Running API `/ws/events` handshake | Passed |
| Verified live PHIVOLCS fetch | Failed certificate validation; endpoint returned 503 |

Tests cover primary/demoted message delivery through real Redis to two clients,
publish-failure containment, WebSocket cleanup/origin rejection, reconnect/cache
updates, source filtering, fixture parsing, stale-cache limits, and volcano UI
states. Test publications use an isolated Redis channel.

The volcano fixture is a reduced historical HTML excerpt. It was inspected with
certificate verification bypassed only during fixture capture; runtime TLS
verification remains enabled. Fixtures are never served as fallback live data.

Existing non-blocking warnings remain: a large web bundle and dependency
deprecation warnings in backend tests.

## Remaining Integration Work

### Person A: connect canonical ingestion to publishing

Person A must provide the generalized ingestion service and wire the callback:

```python
from app.services.events_publisher import publish

processed = ingest_events(session, events, on_committed=publish)
```

Inside Person A's service, canonicalization must finish before commit. Invoke the
callback strictly after commit with every touched `EventChange`, including any
previously primary row that was demoted. The shared schema lives in
`app.schemas.event_change`.

Person A retains ownership of PHIVOLCS earthquake ingestion, canonical persistence,
matching, and REST source/duplicate filters. The tests in this slice do not claim
to verify that unfinished ingest-to-publisher integration.

### Environment/source: restore verified PHIVOLCS access

Correct the source certificate chain or the environment's trusted CA configuration,
then repeat the live fetch and `/api/v1/volcanoes` smoke test. Do not disable
runtime certificate verification. The runbook describes the trusted CA bundle
option for networks using a private CA.

No ML training, mobile push, GVP ingestion, canonicalization, or database schema
migration was introduced by this Person B slice. Changes remain uncommitted.

## Related Documentation

- [Epic 2 shared contracts](adr/0002-epic2-realtime-phivolcs-contracts.md)
- [Runbook and handoff](runbook.md)
- [API contracts](api-contracts.md)
- [Data sources and fixture provenance](data-sources.md)
- [Glossary](glossary.md)
