import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from scripts import mobile_runtime_smoke as smoke

BUNDLE = "com.geohazardph.mobile"


class MobileRuntimeSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.artifact = Path(self.temp.name) / "app"
        self.artifact.write_bytes(b"test app")
        self.diagnostics = Path(self.temp.name) / "diagnostics"

    def test_android_installs_launches_and_checks_process_after_delay(self):
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            if command[:3] == ["adb", "shell", "pidof"]:
                return subprocess.CompletedProcess(command, 0, "1234\n", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        sleep = Mock()
        smoke.run_android(self.artifact, self.diagnostics, run=run, sleep=sleep)
        self.assertIn(["adb", "install", "-r", str(self.artifact)], commands)
        self.assertIn(["adb", "shell", "am", "start", "-W", "-n", f"{BUNDLE}/.MainActivity"], commands)
        self.assertIn(["adb", "shell", "pidof", BUNDLE], commands)
        self.assertIn(["adb", "shell", "screencap", "-p", "/sdcard/geohazard-startup.png"], commands)
        sleep.assert_called_once()
        self.assertGreaterEqual(sleep.call_args.args[0], 10)

    def test_android_qa_identity_is_used_for_launch_liveness_and_record(self):
        commands = []

        def run(command, **kwargs):
            commands.append(command)
            return subprocess.CompletedProcess(command, 0, '1234\n', '')

        package = f'{BUNDLE}.qa'
        activity = f'{BUNDLE}.MainActivity'
        smoke.run_android(self.artifact, self.diagnostics, run=run, sleep=lambda _: None,
                          bundle_id=package, activity=activity)
        self.assertIn(['adb', 'shell', 'am', 'start', '-W', '-n', f'{package}/{activity}'], commands)
        self.assertIn(['adb', 'shell', 'pidof', package], commands)
        record = json.loads((self.diagnostics / 'startup-result.json').read_text())
        self.assertEqual(record['bundle_id'], package)

    def test_android_exited_process_is_a_failure(self):
        def run(command, **kwargs):
            if command[:3] == ["adb", "shell", "pidof"]:
                return subprocess.CompletedProcess(command, 1, "", "")
            if command[:3] == ["adb", "logcat", "-d"]:
                return subprocess.CompletedProcess(command, 0, "FATAL EXCEPTION: app crashed", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        with self.assertRaisesRegex(smoke.SmokeError, "Android.*exited"):
            smoke.run_android(self.artifact, self.diagnostics, run=run, sleep=lambda _: None)
        self.assertIn("FATAL EXCEPTION", (self.diagnostics / "app-logcat.txt").read_text())

    def test_ios_selects_available_iphone_and_verifies_launched_pid(self):
        commands = []
        devices = {"devices": {
            "com.apple.CoreSimulator.SimRuntime.iOS-18-5": [
                {"name": "iPhone 16", "udid": "DEVICE-1", "state": "Shutdown", "isAvailable": True}
            ]
        }}

        def run(command, **kwargs):
            commands.append(command)
            if command == ["xcrun", "simctl", "list", "devices", "available", "-j"]:
                return subprocess.CompletedProcess(command, 0, json.dumps(devices), "")
            if command[:3] == ["xcrun", "simctl", "launch"]:
                return subprocess.CompletedProcess(command, 0, f"{BUNDLE}: 4567\n", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        pid_alive = Mock(return_value=True)
        smoke.run_ios(self.artifact, self.diagnostics, run=run, sleep=lambda _: None, pid_alive=pid_alive)
        self.assertIn(["xcrun", "simctl", "boot", "DEVICE-1"], commands)
        self.assertIn(["xcrun", "simctl", "install", "DEVICE-1", str(self.artifact)], commands)
        self.assertIn(["xcrun", "simctl", "launch", "DEVICE-1", BUNDLE], commands)
        pid_alive.assert_called_once_with(4567)
        self.assertIn(["xcrun", "simctl", "io", "DEVICE-1", "screenshot", str(self.diagnostics / "startup.png")], commands)

    def test_ios_missing_simulator_fails_clearly(self):
        def run(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, '{"devices": {}}', "")

        with self.assertRaisesRegex(smoke.SmokeError, "iPhone simulator"):
            smoke.run_ios(self.artifact, self.diagnostics, run=run, sleep=lambda _: None, pid_alive=lambda _: True)

    def test_ios_exited_process_is_a_failure(self):
        devices = {"devices": {"ios": [{"name": "iPhone 16", "udid": "DEVICE-1", "state": "Booted", "isAvailable": True}]}}

        def run(command, **kwargs):
            if command == ["xcrun", "simctl", "list", "devices", "available", "-j"]:
                return subprocess.CompletedProcess(command, 0, json.dumps(devices), "")
            if command[:3] == ["xcrun", "simctl", "launch"]:
                return subprocess.CompletedProcess(command, 0, f"{BUNDLE}: 4567\n", "")
            if command[:3] == ["xcrun", "simctl", "spawn"]:
                return subprocess.CompletedProcess(command, 0, "GeoHazardPH crash log", "")
            return subprocess.CompletedProcess(command, 0, "", "")

        with self.assertRaisesRegex(smoke.SmokeError, "iOS.*exited"):
            smoke.run_ios(self.artifact, self.diagnostics, run=run, sleep=lambda _: None, pid_alive=lambda _: False)
        self.assertIn("GeoHazardPH crash log", (self.diagnostics / "app-system-log.txt").read_text())

    def test_android_install_command_failure_is_reported(self):
        def run(command, **kwargs):
            return subprocess.CompletedProcess(command, 1, "", "install failed")

        with self.assertRaisesRegex(smoke.SmokeError, "install failed"):
            smoke.run_android(self.artifact, self.diagnostics, run=run, sleep=lambda _: None)

    def test_ios_boot_timeout_is_reported(self):
        devices = {"devices": {"ios": [{"name": "iPhone 16", "udid": "DEVICE-1", "state": "Shutdown", "isAvailable": True}]}}

        def run(command, **kwargs):
            if command == ["xcrun", "simctl", "list", "devices", "available", "-j"]:
                return subprocess.CompletedProcess(command, 0, json.dumps(devices), "")
            if command[:3] == ["xcrun", "simctl", "bootstatus"]:
                raise subprocess.TimeoutExpired(command, 60)
            return subprocess.CompletedProcess(command, 0, "", "")

        with self.assertRaisesRegex(smoke.SmokeError, "timed out"):
            smoke.run_ios(self.artifact, self.diagnostics, run=run, sleep=lambda _: None, pid_alive=lambda _: True)
    def test_ios_liveness_check_fails_closed_on_permission_error(self):
        with unittest.mock.patch("scripts.mobile_runtime_smoke.os.kill", side_effect=PermissionError):
            self.assertFalse(smoke._pid_alive(4567))
    def test_missing_artifact_is_a_failure(self):
        self.artifact.unlink()
        with self.assertRaisesRegex(smoke.SmokeError, "artifact"):
            smoke.run_android(self.artifact, self.diagnostics, run=Mock(), sleep=Mock())


if __name__ == "__main__":
    unittest.main()
