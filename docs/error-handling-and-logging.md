# Error Handling And Logging

**Project**: GeoHazard PH
**Scope**: Cross-cutting rules for all packages — `backend/`, `ml/`, `web/`, `mobile/`.

This document is the single source of truth for how failures are surfaced and how operational output is recorded in every stack. It is referenced by `BACKEND_STANDARDS.md`, `docs/api-contracts.md`, and `docs/testing-standards.md`. Load it before writing code in any package.

Related contracts:
- `docs/api-contracts.md` — how the error envelope appears on the wire.
- `BACKEND_STANDARDS.md` — backend-specific error and logging application.

---

## Table Of Contents

1. Principles
2. Error Taxonomy
3. Error Envelope (API)
4. Backend
5. ML
6. Web
7. Mobile
8. Logging Rules By Stack
9. Secrets And Sensitive Data
10. Known Deviations

---

## 1. Principles

- **Classify, then surface.** Every failure is one of: expected business failure, invalid input, unavailable external dependency, or unexpected bug. The surface treatment differs by class.
- **Safe by default.** Error responses must never leak internals: credentials, tokens, file paths with secrets, SQL fragments, or stack traces.
- **Traceable.** Every unexpected failure is logged with enough context to reproduce, including a request identifier when one exists.
- **Consistent shape.** A client can parse any API error without guessing. One envelope, everywhere.
- **New code conforms on day one.** These rules are the target; where current code deviates, see Known Deviations.

## 2. Error Taxonomy

| Class | Meaning | HTTP status | Surface treatment |
| --- | --- | --- | --- |
| Business failure | Valid request violates domain rules | 409 (or 404 when absent) | Envelope with stable `code`; message actionable |
| Invalid input | Malformed parameters or body | 422 | Envelope; list offending fields when available |
| Not found | Resource does not exist | 404 | Envelope; message names the resource |
| Unauthorized | Missing/invalid identity | 401 | Envelope; never reveal why credentials failed |
| Forbidden | Valid identity, no permission | 403 | Envelope; generic message |
| Unavailable dependency | External source/DB/reachable service failed | 502/503 | Envelope; log root cause, surface generic message |
| Unexpected | Any other exception | 500 | Envelope with `generic_message`; full detail in logs only |

## 3. Error Envelope (API)

Every non-2xx API response uses this shape:

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

Rules:

- `code` is a stable machine-readable snake_case identifier. Clients switch on this, never on `message` text.
- `message` is human-readable and safe to expose. It may include resource names, but never internals.
- `status` mirrors the HTTP status code.
- `request_id` is optional; when a server-side request id is available, include it so logs and errors line up.
- FastAPI's built-in validation error (`422` with a `detail` array) is normalized to this envelope with `code: "validation_error"` and the field list in `message`.
- Success responses are NOT wrapped in an envelope by default; the envelope is reserved for errors (see `docs/api-contracts.md`).

### Implementing the envelope (FastAPI)

Register handlers on the app object, once in `backend/app/main.py`:

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


def to_error_response(status: int, code: str, message: str, request_id: str | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "status": status, "request_id": request_id}},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return to_error_response(422, "validation_error", "Request failed validation", ...)


@app.exception_handler(Exception)
async def unexpected_error_handler(request, exc):
    logger.exception("Unhandled exception", exc_info=exc)
    return to_error_response(500, "internal_error", "An unexpected error occurred", ...)
```

Domain exceptions raised by services are converted at the route boundary with a stable `code`:

```python
except RiskProfileNotFound as exc:
    raise HTTPException(status_code=404, detail=str(exc)) from exc
```

Route-level `HTTPException` uses the envelope when rendered through a handler or middleware that wraps `detail` into the `error` shape. Until a global middleware exists, handlers above normalize it.

## 4. Backend

- Services raise domain exceptions for expected failures (for example `RiskProfileNotFound`); they never return error sentinels.
- Routes translate domain exceptions to `HTTPException` and pick the status code.
- Unexpected exceptions propagate to the global handler, are logged with a stack trace, and return the generic 500 envelope.
- `HTTPException` detail strings are user-safe; keep them free of paths, credentials, and raw payloads.
- External-source failures (USGS, Kaggle, ...) raise typed exceptions that distinguish network, credential, and parsing failure (for example `USGSFetchError`, `KaggleCredentialError`).

## 5. ML

- Fail fast for missing required files, columns, or credentials. Include the missing path, column, or configuration key in the message.
- Raise typed exceptions for expected conditions (`KaggleCredentialError`, `ValueError` with the offending field list).
- CLI entrypoints print a short failure reason to stderr and exit nonzero; they never silently fall back to sample data on download failure.
- Invalid rows are counted and excluded from processing, with counts recorded in training metadata; only zero usable rows is a hard failure.

## 6. Web

- API clients throw typed, named errors — never bare strings. Keep the HTTP status and a safe message on the error.
- React Query state drives the UI: every data-backed view renders explicit loading, empty, and error states. Error states offer a retry action when the query supports `refetch`.
- User-facing messages are concise and safe; technical detail goes to the console or a logging sink only where appropriate.
- Never swallow errors silently; a catch that does nothing is a bug.

## 7. Mobile

- Mirrors the web rules: typed errors from `services/`, explicit state in every screen, and a retry path on failure.
- Do not assume network availability. Offline-capable paths degrade gracefully and record the failure to the offline layer.
- Push and notification paths report "not configured" as a first-class state rather than throwing.

## 8. Logging Rules By Stack

### Python (backend and ML)

- Use the standard `logging` module; never `print()` for operational output. Worker and scheduler entrypoints use loggers.
- One logger per module: `logger = logging.getLogger(__name__)`.
- Emit structured, key-value fields. Prefer `logger.info("ingest complete", extra={"fetched": n, "processed": m})` over string interpolation.
- Backend configures logging once at startup (`app/core/logging.py::configure_logging`), at `INFO`, with a format that includes level, logger name, and message.

### Web

- Keep user-facing and technical logging separate. `console.error` is reserved for local debugging; do not ship noisy per-request logs.
- React Query errors are logged at the hook or client boundary, once, with the failing resource named.

### Mobile

- Log at the service boundary only, once per failure, including the operation name and a correlation-friendly id when available.
- Do not log request bodies or full response payloads.

## 9. Secrets And Sensitive Data

- Never log credentials, tokens, session keys, `Authorization` headers, `.env` contents, or Kaggle secrets — in any stack.
- Never include secret-bearing file paths or raw source payloads in error responses.
- If a dependency or service echoes secrets in exceptions, sanitize before logging or surfacing.
- Commit-time guardrails in `CODING_STANDARDS.md` apply; adding a new secret requires an `.env.example` entry and no committed value.

## 10. Known Deviations

Tracked as backlog items in `docs/superpowers/plans/2026-08-29-standards-gap-remediation.md`. New code must conform to the contract above.

- Backend: no global exception handler or error envelope registered yet; validation errors return FastAPI's default shape.
- Backend: no structured logging wired; `app/core/logging.py::configure_logging` is unused.
- Backend: `ingestion/scheduler.py` uses `print()` for its completion summary.
- Web: API client throws generic `Error("Failed to fetch <resource>")` with no status or typed code.
- Mobile: `services/` have no error handling at all; the API base URL is hardcoded.