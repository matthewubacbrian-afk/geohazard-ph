"""Collect on-demand staging ingestion and feed evidence."""

import json
import subprocess
from datetime import UTC, datetime
from http.client import HTTPException
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

API_ORIGIN = "https://geohazard-ph-staging-api.onrender.com"
REPOSITORY = "matthewubacbrian-afk/geohazard-ph"
SOURCES = ("usgs", "phivolcs")
REQUEST_TIMEOUT_SECONDS = 20
COLD_START_RETRY_DELAY_SECONDS = 5


class CheckError(Exception):
    """An evidence source could not be read or validated."""


def read_runs() -> list[dict]:
    command = [
        "gh", "run", "list", "--repo", REPOSITORY, "--branch", "main",
        "--workflow", "ingest-staging.yml", "--event", "schedule", "--limit", "10",
        "--json", "databaseId,event,status,conclusion,createdAt,headSha,url",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise CheckError("GitHub run query failed") from exc
    try:
        runs = json.loads(result.stdout)
    except ValueError as exc:
        raise CheckError("GitHub returned invalid run JSON") from exc
    if not isinstance(runs, list) or any(
        not isinstance(run, dict)
        or run.get("event") != "schedule"
        or not isinstance(run.get("status"), str)
        or not isinstance(run.get("conclusion"), str)
        for run in runs
    ):
        raise CheckError("GitHub returned invalid scheduled run metadata")
    return runs


def read_json(path: str, *, retry_cold_start: bool = False) -> object:
    attempts = 2 if retry_cold_start else 1
    for attempt in range(attempts):
        try:
            with urlopen(API_ORIGIN + path, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                return json.load(response)
        except (OSError, HTTPException, ValueError) as exc:
            transient = (
                (isinstance(exc, HTTPError) and exc.code in {502, 503, 504})
                or isinstance(exc, TimeoutError)
                or (isinstance(exc, URLError) and isinstance(exc.reason, TimeoutError))
            )
            if not transient or attempt + 1 == attempts:
                raise CheckError(f"Staging read failed for {path}") from exc
            sleep(COLD_START_RETRY_DELAY_SECONDS)
    raise AssertionError("read attempts exhausted")


def parse_timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str):
        raise CheckError(f"Invalid {label}")
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CheckError(f"Invalid {label}") from exc
    if timestamp.tzinfo is None:
        raise CheckError(f"Invalid {label}: timezone required")
    return timestamp.astimezone(UTC)


def source_snapshot(source: str) -> dict[str, int | str | None]:
    events = read_json(f"/api/v1/events?source={source}")
    if not isinstance(events, list):
        raise CheckError(f"Invalid {source} event list")
    latest = None
    for event in events:
        if not isinstance(event, dict) or event.get("source") != source:
            raise CheckError(f"Invalid {source} event row")
        occurred_at = parse_timestamp(event.get("occurred_at"), f"{source} event timestamp")
        if latest is None or occurred_at > latest:
            latest = occurred_at
    return {
        "event_count": len(events),
        "latest_occurred_at": latest.isoformat() if latest else None,
    }


def collect_snapshot() -> dict:
    runs = sorted(
        read_runs(),
        key=lambda run: parse_timestamp(run.get("createdAt"), "scheduled run timestamp"),
        reverse=True,
    )
    consecutive_successes = 0
    for run in runs:
        if run["status"] != "completed":
            continue
        if run["conclusion"] != "success":
            break
        consecutive_successes += 1

    health = read_json("/health", retry_cold_start=True)
    if not isinstance(health, dict) or health.get("status") != "ok":
        raise CheckError("Staging health did not report ok")
    sources = {source: source_snapshot(source) for source in SOURCES}
    return {
        "observed_at": datetime.now(UTC).isoformat(),
        "health": "ok",
        "scheduled_runs": runs,
        "consecutive_successful_runs": consecutive_successes,
        "sources": sources,
    }


def main() -> int:
    try:
        report = collect_snapshot()
    except CheckError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
