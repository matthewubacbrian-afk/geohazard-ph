"""Fail-closed startup smoke checks for existing mobile Release simulator builds."""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BUNDLE_ID = "com.geohazardph.mobile"
STARTUP_WAIT_SECONDS = 15


class SmokeError(RuntimeError):
    """A platform could not prove that the app survived startup."""


def _invoke(run, command, *, timeout=120, check=True):
    try:
        result = run(command, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise SmokeError(f"{' '.join(command)} timed out after {timeout}s") from exc
    except OSError as exc:
        raise SmokeError(f"Could not run {' '.join(command)}: {exc}") from exc
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout or "no output").strip()[-500:]
        raise SmokeError(f"{' '.join(command)} failed: {detail}")
    return result


def _validate_artifact(artifact):
    if not artifact.exists():
        raise SmokeError(f"Release artifact is missing: {artifact}")


def _write_result(diagnostics, platform, device, pid):
    diagnostics.mkdir(parents=True, exist_ok=True)
    (diagnostics / "startup-result.json").write_text(
        json.dumps({"platform": platform, "device": device, "bundle_id": BUNDLE_ID,
                    "pid": str(pid), "scope": "startup liveness only"}, indent=2) + "\n",
        encoding="utf-8",
    )


def run_android(artifact, diagnostics, *, run=subprocess.run, sleep=time.sleep):
    """Install and launch the Release APK on an already booted emulator."""
    artifact = Path(artifact)
    diagnostics = Path(diagnostics)
    _validate_artifact(artifact)
    _invoke(run, ["adb", "get-state"], timeout=20)
    _invoke(run, ["adb", "install", "-r", str(artifact)], timeout=180)
    launch = _invoke(run, ["adb", "shell", "am", "start", "-W", "-n",
                           f"{BUNDLE_ID}/.MainActivity"], timeout=60)
    if "Error" in launch.stdout or "Exception" in launch.stdout:
        raise SmokeError(f"Android launch failed: {launch.stdout.strip()[-500:]}")
    sleep(STARTUP_WAIT_SECONDS)
    process = _invoke(run, ["adb", "shell", "pidof", BUNDLE_ID], timeout=20, check=False)
    if process.returncode != 0 or not process.stdout.strip():
        raise SmokeError("Android app exited during startup")
    diagnostics.mkdir(parents=True, exist_ok=True)
    _invoke(run, ["adb", "shell", "screencap", "-p", "/sdcard/geohazard-startup.png"], timeout=30)
    _invoke(run, ["adb", "pull", "/sdcard/geohazard-startup.png", str(diagnostics / "startup.png")], timeout=30)
    _write_result(diagnostics, "android", "emulator", process.stdout.strip())


def _select_iphone(raw):
    try:
        devices = json.loads(raw)["devices"]
    except (ValueError, KeyError, TypeError) as exc:
        raise SmokeError("iOS simulator listing is malformed") from exc
    candidates = [
        (runtime, device)
        for runtime, entries in devices.items()
        if "ios" in runtime.lower()
        for device in entries
        if device.get("name", "").startswith("iPhone") and device.get("isAvailable")
    ]
    if not candidates:
        raise SmokeError("No available iPhone simulator on the CI runner")
    candidates.sort(key=lambda item: (item[1].get("state") != "Booted", item[0], item[1]["name"]))
    return candidates[0][1]


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return False


def run_ios(artifact, diagnostics, *, run=subprocess.run, sleep=time.sleep, pid_alive=_pid_alive):
    """Boot an available iPhone, install Release .app and check its host PID."""
    artifact = Path(artifact)
    diagnostics = Path(diagnostics)
    _validate_artifact(artifact)
    listing = _invoke(run, ["xcrun", "simctl", "list", "devices", "available", "-j"], timeout=30)
    device = _select_iphone(listing.stdout)
    udid = device["udid"]
    if device.get("state") != "Booted":
        _invoke(run, ["xcrun", "simctl", "boot", udid], timeout=90)
    _invoke(run, ["xcrun", "simctl", "bootstatus", udid, "-b"], timeout=300)
    _invoke(run, ["xcrun", "simctl", "install", udid, str(artifact)], timeout=180)
    launch = _invoke(run, ["xcrun", "simctl", "launch", udid, BUNDLE_ID], timeout=90)
    match = re.search(rf"{re.escape(BUNDLE_ID)}:\s*(\d+)", launch.stdout)
    if not match:
        raise SmokeError(f"iOS launch did not return an app PID: {launch.stdout.strip()[-500:]}")
    pid = int(match.group(1))
    sleep(STARTUP_WAIT_SECONDS)
    if not pid_alive(pid):
        raise SmokeError("iOS app exited during startup")
    diagnostics.mkdir(parents=True, exist_ok=True)
    _invoke(run, ["xcrun", "simctl", "io", udid, "screenshot", str(diagnostics / "startup.png")], timeout=30)
    _write_result(diagnostics, "ios", f"{device['name']} ({udid})", pid)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=["android", "ios"], required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--diagnostics", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.platform == "android":
            run_android(args.artifact, args.diagnostics)
        else:
            run_ios(args.artifact, args.diagnostics)
    except SmokeError as exc:
        args.diagnostics.mkdir(parents=True, exist_ok=True)
        (args.diagnostics / "startup-failure.txt").write_text(str(exc) + "\n", encoding="utf-8")
        print(f"{args.platform} startup smoke failed: {exc}", file=sys.stderr)
        return 1
    print(f"{args.platform} Release app survived startup; user flows remain unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
