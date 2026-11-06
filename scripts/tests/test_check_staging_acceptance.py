"""Verify on-demand staging evidence without making network calls."""

import io
import json
import unittest
from contextlib import redirect_stdout
from http.client import IncompleteRead
from unittest.mock import patch
from urllib.error import HTTPError

from scripts import check_staging_acceptance as check


class StagingAcceptanceTests(unittest.TestCase):
    def test_snapshot_keeps_schedule_and_event_times_separate(self):
        runs = [
            {"databaseId": 1, "event": "schedule", "status": "completed",
             "conclusion": "success", "createdAt": "2026-11-06T00:00:00Z"},
            {"databaseId": 2, "event": "schedule", "status": "completed",
             "conclusion": "failure", "createdAt": "2026-11-06T06:00:00Z"},
            {"databaseId": 3, "event": "schedule", "status": "completed",
             "conclusion": "success", "createdAt": "2026-11-06T12:00:00Z"},
        ]
        with patch.object(check, "read_runs", return_value=runs), patch.object(
            check, "read_json", side_effect=[
                {"status": "ok"},
                [{"source": "usgs", "occurred_at": "2026-11-05T23:00:00-05:00"},
                 {"source": "usgs", "occurred_at": "2026-11-06T03:00:00Z"}],
                [],
            ],
        ):
            report = check.collect_snapshot()

        self.assertEqual([row["databaseId"] for row in report["scheduled_runs"]], [3, 2, 1])
        self.assertEqual(report["consecutive_successful_runs"], 1)
        self.assertEqual(report["sources"]["usgs"], {
            "event_count": 2, "latest_occurred_at": "2026-11-06T04:00:00+00:00",
        })
        self.assertEqual(report["sources"]["phivolcs"], {
            "event_count": 0, "latest_occurred_at": None,
        })

    def test_in_progress_run_does_not_hide_prior_completed_success(self):
        runs = [
            {"databaseId": 2, "event": "schedule", "status": "in_progress",
             "conclusion": "", "createdAt": "2026-11-06T06:00:00Z"},
            {"databaseId": 1, "event": "schedule", "status": "completed",
             "conclusion": "success", "createdAt": "2026-11-06T00:00:00Z"},
        ]
        with patch.object(check, "read_runs", return_value=runs), patch.object(
            check, "read_json", side_effect=[{"status": "ok"}, [], []]
        ):
            report = check.collect_snapshot()
        self.assertEqual(report["consecutive_successful_runs"], 1)
        self.assertEqual(len(report["scheduled_runs"]), 2)

    def test_rejects_naive_event_timestamp(self):
        with patch.object(check, "read_json", return_value=[
            {"source": "usgs", "occurred_at": "2026-11-06T03:00:00"},
        ]):
            with self.assertRaisesRegex(check.CheckError, "event timestamp"):
                check.source_snapshot("usgs")

    def test_health_retries_one_transient_cold_start(self):
        unavailable = HTTPError(check.API_ORIGIN, 503, "Unavailable", {}, None)
        with patch.object(
            check, "urlopen", side_effect=[unavailable, io.BytesIO(b'{"status":"ok"}')]
        ) as request, patch.object(check, "sleep") as delay:
            self.assertEqual(check.read_json("/health", retry_cold_start=True), {"status": "ok"})
        self.assertEqual(request.call_count, 2)
        delay.assert_called_once()

    def test_cli_omits_authentication_diagnostics_on_failure(self):
        output = io.StringIO()
        with patch.object(check.subprocess, "run") as run, redirect_stdout(output):
            run.side_effect = check.subprocess.CalledProcessError(1, [], stderr="private token")
            self.assertEqual(check.main(), 1)
        self.assertEqual(json.loads(output.getvalue()), {"error": "GitHub run query failed"})

    def test_truncated_response_produces_safe_json(self):
        output = io.StringIO()
        with patch.object(check, "read_runs", return_value=[]), patch.object(
            check, "urlopen", side_effect=IncompleteRead(b"untrusted response")
        ), redirect_stdout(output):
            self.assertEqual(check.main(), 1)
        self.assertEqual(
            json.loads(output.getvalue()), {"error": "Staging read failed for /health"}
        )
