# PHIVOLCS Earthquake Feed UTF-8 Decoding — Design

**Date:** 2026-10-29

## Problem

The physical Android check at `4e130fb8` displayed `Â°` in a PHIVOLCS earthquake
place name. The same text was present in the API response, so the error enters
before mobile rendering. The observed source sent UTF-8 bytes under `text/html`
without a charset. `backend/ingestion/sources/phivolcs_earthquake.py` currently
passes `response.text` to the parser; Requests selected ISO-8859-1 for that
response and produced mojibake.

## Goals

- Decode PHIVOLCS earthquake feed bytes as UTF-8 before parsing location text.
- Reproduce the observed missing-charset response in a DB-free regression test.
- Fail clearly if the source returns invalid UTF-8 instead of ingesting damaged text.
- Verify a fresh ingestion updates a matching stored event and the API/mobile
  display shows the degree symbol on the connected Android phone.

## Non-goals

- Do not change mobile rendering, the event API schema, or other source adapters.
- Do not rewrite historical events no longer present in the recent feed.
- Do not change TLS verification or infer that PHIVOLCS guarantees UTF-8 forever.

## Context And Constraints

The existing parser already handles a Unicode degree symbol in its fixture.
`fetch_recent_events` is the only HTTP-to-text boundary for the earthquake
feed. `ingest_events` updates `place_name` for an existing source/external-ID
match, so a fresh poll can repair recent stored events. The default API and
worker containers must be rebuilt before a local runtime check can exercise
new ingestion code. Follow `CODING_STANDARDS.md`, `BACKEND_STANDARDS.md`,
`docs/testing-standards.md`, and `docs/error-handling-and-logging.md`.

## Alternatives Considered

- Use Requests' apparent-encoding detection. It adds a content-dependent
  heuristic when the observed source bytes and expected encoding are known.
- Repair `Â°` in API or mobile output. This leaves the stored event damaged
  and misses other non-ASCII characters.

## Design

### Architecture and data flow

`fetch_recent_events` reads `response.content`, decodes with UTF-8 using strict
error handling, and passes the resulting string to `_parse_bulletin_table`.
The parser, `HazardEvent.place_name`, ingestion upsert, and `/api/v1/events`
contract remain unchanged.

### Components and interfaces

- `backend/ingestion/sources/phivolcs_earthquake.py`: keep
  `fetch_recent_events(settings, *, session=None) -> list[HazardEvent]` and
  decode the response bytes at this boundary.
- `backend/tests/unit/test_phivolcs_earthquake_parser.py`: fake a Requests-like
  response with UTF-8 `content`, missing charset, and misleading Latin-1
  `text`; assert `place_name` contains `°` and no `Â`. Assert invalid UTF-8
  raises `PhivolcsFetchError`.
- No new settings, dependencies, schema fields, or endpoint paths.

### Error handling and data

Keep request failures under the existing request-failed exception. Wrap a
strict UTF-8 decoding error as `PhivolcsFetchError` for feed parsing, without
logging or returning the source payload. A recurring feed poll updates recent
rows with the same source/external ID. Older stored rows remain as they were
until a separately reviewed backfill is justified.

## Rollout

Implement and test in an isolated fix branch. Integrate the already recorded
Android observations from `codex/android-device-smoke` into tracking without
losing their limitations. Rebuild only the local development API/worker needed
to verify a fresh feed poll, then inspect the API value and phone display.
Keep the separate scene-model preflight branch intact.

## Files

- `backend/ingestion/sources/phivolcs_earthquake.py`: response decoding.
- `backend/tests/unit/test_phivolcs_earthquake_parser.py`: regression cases.
- `docs/mobile-runtime-smoke-test.md`: corrected-device result, if observed.
- `docs/project-status.md`: observed defect and verified fix scope.
- `PLAN.md`: completion tracking for this focused defect.

## Testing Strategy

Run the focused test before implementation and confirm it fails on the old
code. After implementation, run the focused and full backend suites, backend
Ruff, structure verification if the tree changes, and `git diff --check`.
Use a fresh source response and local ingestion to inspect `/api/v1/events`;
check the same event on the Android phone. Do not label historical rows or
other platforms corrected by this one sample.

## Acceptance Criteria

- [ ] Missing-charset UTF-8 regression fails before and passes after the fix.
- [ ] Invalid UTF-8 produces a typed ingestion failure without damaged rows.
- [ ] Required local backend checks pass, and CI passes on the fix commit.
- [ ] A newly ingested PHIVOLCS event shows `°` in the API and on Android.
- [ ] Tracking records the exact commit, runtime result, and remaining limits.

## Out Of Scope (backlog)

- Historical event backfill and independent review of other source encodings.
- Scene-model packaging, iOS device testing, and staging deployment.
