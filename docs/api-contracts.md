# API Contracts

**Project**: GeoHazard PH
**Scope**: Every HTTP endpoint served by `backend/`. Read this before adding or modifying any endpoint.

This document defines the shared wire contract so that every endpoint an agent generates looks the same: naming, response shapes, errors, and versioning. Error envelope and logging details live in `docs/error-handling-and-logging.md`; service and route mechanics live in `BACKEND_STANDARDS.md`.

---

## Table Of Contents

1. Naming Conventions
2. Response Shapes
3. Error Format
4. Versioning
5. Pagination
6. Dates, Numbers, And Coordinates
7. Field Naming And Client Mapping
8. Endpoint Checklist
9. Known Deviations

---

## 1. Naming Conventions

- Base path: `/api/v1` (version comes from the include prefix, not per-resource).
- Resources use plural, lowercase, kebab-free nouns: `/events`, `/faults`, `/volcanoes`, `/risk-profile`.
- Static sub-resources are declared before path parameters: `/events/summary` before `/events/{event_id}`.
- Actions that are not CRUD use a noun segment: `/events/summary`, `/risk-profile/clusters`.
- Query parameters are lowercase `snake_case`: `?since=`, `?region_name=`, `?min_latitude=`.
- Path parameters that name a resource use the snake_case field name: `/risk-profile/{region_name}`.

Standard verbs:

| Verb | Path | Use |
| --- | --- | --- |
| GET | `/resources` | List (see Pagination) |
| GET | `/resources/{id}` | Single resource |
| POST | `/resources` | Create |
| PUT | `/resources/{id}` | Full replace |
| PATCH | `/resources/{id}` | Partial update |
| DELETE | `/resources/{id}` | Delete |

Prefer read-only endpoints for imported public hazard data until persistence and authority rules exist. Only add mutating endpoints when the data lifecycle is clear.

## 2. Response Shapes

Success responses are **not** wrapped in an envelope. Return the typed payload directly:

- Single resource → the resource object.
- Simple collection → a bare JSON array.
- Collection with metadata (pagination, summary) → a structured object with explicit fields:

```json
{
  "items": [...],
  "count": 142,
  "next_cursor": "eyJ..."
}
```

Rules:

- Every endpoint declares a `response_model` (FastAPI) so the shape is documented and enforced.
- Response keys are exactly the schema field names — no trailing `_at` vs `_date` drift.
- Empty collections return `[]` (or an empty `items` array), never `null` or `{}`.
- Nullable fields serialize as `null`, never as empty strings.
- `datetime` and `date` fields serialize as ISO 8601 strings (see Dates).

## 3. Error Format

All non-2xx responses use the error envelope defined in `docs/error-handling-and-logging.md`:

```json
{
  "error": {
    "code": "risk_profile_not_found",
    "message": "Risk profile not found for region: Bicol Region",
    "status": 404,
    "request_id": "req_01J8WC5E0Q8N4Y0F3XZJZAV0R2"
  }
}
```

- `code` is the stable machine-readable identifier; clients switch on it.
- `message` is human-readable and safe to expose.
- Validate with the HTTP status-code table in `CODING_STANDARDS.md`; 404 and 409 are distinguished by whether the resource may exist (`404`) or is in a conflicting state (`409`).

## 4. Versioning

- The API is versioned by URL path: `/api/v1/...`.
- Bump the major version only for breaking changes (renamed fields, removed endpoints, changed semantics).
- Additive changes (new optional fields, new endpoints) stay within the current version.
- Versioned route modules live under `backend/app/api/v1/`; a future `v2` adds a sibling directory rather than editing `v1` routes.
- `/health` is unversioned and returns a plain service object.

## 5. Pagination

- List endpoints that can grow use cursor-based pagination with `limit` and `cursor` query parameters.
- Response envelope for paginated lists:

```json
{
  "items": [...],
  "count": 142,
  "next_cursor": "eyJ..."
}
```

- `limit` defaults to 100 and caps at 500; invalid values return `422 validation_error`.
- `next_cursor` is `null` on the last page.
- Small, bounded collections (for example generated risk-profile clusters) return a bare array without pagination.

## 6. Dates, Numbers, And Coordinates

- All datetimes: ISO 8601 with timezone, `Z` or `+00:00` offset. Example: `2026-08-28T09:30:00Z`.
- Magnitude and depth: numbers; nullable as `null`. Round magnitudes once at serialization, not per consumer.
- Coordinates: decimal degrees. Field names are always `latitude` and `longitude`. GeoJSON geometry arrays stay `[longitude, latitude]`.
- Confidence and probability values: floats in `[0, 1]`.
- No locale-specific number formatting on the wire.

## 7. Field Naming And Client Mapping

- The wire format is `snake_case` for every field, in every package, with no exceptions.
- Web types mirror the API field-for-field (`web/src/types/hazard.ts` uses `hazard_type`, `place_name`, `occurred_at`).
- Mobile uses its own UI-native type names (camelCase) ONLY behind an explicit mapping layer in `mobile/src/services/api.ts`. A mobile type must never be consumed as if it were the raw API response; the mapping function owns the conversion and is unit tested.
- When a UI component needs a display derivation (percentages, relative time), derive it inside the component or a hook — not in the API shape.

## 8. Endpoint Checklist

When adding or changing an endpoint:

- [ ] Follow the plural noun naming and verb table above.
- [ ] Declare a `response_model`; no bare dict returns.
- [ ] Return the documented shape for the collection kind (bare array vs paginated object).
- [ ] Map expected failures to the error envelope with a stable `code`.
- [ ] Use ISO 8601 datetimes and decimal coordinates.
- [ ] Add a web type mirroring the schema, and a mobile mapping when mobile consumes it.
- [ ] Cover the route in an integration test and the service in a unit test (`docs/testing-standards.md`).
- [ ] Update `docs/runbook.md` or `docs/geohazard-system-architecture.md` when endpoints list changes.

## 9. Known Deviations

Tracked as backlog items in `docs/superpowers/plans/2026-08-29-standards-gap-remediation.md`. New and edited endpoints must conform today.

- No error envelope exists yet; errors return ad-hoc shapes or FastAPI defaults.
- Cursor pagination is not implemented anywhere; the events list returns a bare array (fine at current volume, but the contract now exists).
- `GET /api/v1/risk-profile/clusters` and `/risk-profile/{region_name}` omit `response_model`.
- Mobile types (`mobile/src/types/hazard.ts`) are camelCase with no mapping layer yet; mobile does not currently consume the API.
- `GET /api/v1/events/summary` accepts bare bbox query params without `min_`/`max_` prefixes; keep this shape unless the endpoint is versioned again.
## Epic 2 Person B endpoints

- `WS /ws/events` is **unversioned**, as sealed in ADR 0002. It is not
  `/api/v1/ws/events`. Each text frame is one `EventChange`, with UUID `id` and
  `canonical_id`, boolean `is_primary`, and the exact remaining fields in the ADR.
  Subscription is acknowledged by Redis before the WebSocket handshake completes.
  Non-primary messages retract the corresponding source row. There is no replay.
- Browser origins must match `CORS_ORIGINS`; non-browser clients may omit Origin.
  Redis failures close the stream with 1013; slow sends time out after five seconds.
  Clients reconnect and reconcile through REST. Server WebSocket protocol
  ping/pong handles idle connections; no application heartbeat frames are added.
- `GET /api/v1/subscribe` returns HTTP 200 with
  `{"status":"ok","channel":"events:updates","endpoint":"/ws/events"}` when Redis
  responds, or `status: "unavailable"` otherwise. This reports broker connectivity,
  not producer readiness or the existence of ingested data.
- `GET /api/v1/volcanoes` returns a bounded bare array of `Volcano` objects:
  `id`, `name`, nullable `latitude`/`longitude`, nullable integer
  `current_alert_level` (0–5), `source: "phivolcs"`, nullable `source_url`,
  `bulletin_url`, `bulletin_at`, `retrieved_at`, and boolean `stale`.
  Coordinates are nullable because this source does not supply them; this widens
  the former stub schema. Consumers must not place missing locations at (0, 0).
  The timestamp is the bulletin observation heading, not alert issuance.
- A cold or expired volcano cache with an unavailable/malformed source returns
  HTTP 503 with `error.code: "volcano_feed_unavailable"` in the standard envelope.
  A refresh failure can return cached rows with `stale: true`, unchanged
  `retrieved_at`, and a maximum default age of one hour.

The browser maintains one unfiltered events cache and applies source selection
locally to both map and list. It refetches on every connection and every 30 seconds
to recover missed or failed Redis publications. Person A still owns REST source
filters, canonical persistence, primary-only REST defaults, and ingest wiring.
