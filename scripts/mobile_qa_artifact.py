"""Verify standalone QA APKs and write source/artifact identity for testers."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

QA_PACKAGE = "com.geohazardph.mobile.qa"
RELEASE_PACKAGE = "com.geohazardph.mobile"
REQUIRED_ABIS = {"armeabi-v7a", "arm64-v8a", "x86", "x86_64"}


def inspect_manifest(apk: Path, aapt: str, *, run=subprocess.run) -> dict[str, Any]:
    """Inspect final APK metadata, rejecting unresolved boolean resources."""
    badging = run(
        [aapt, "dump", "badging", str(apk)], check=True, capture_output=True, text=True, timeout=30
    ).stdout
    tree = run(
        [aapt, "dump", "xmltree", str(apk), "AndroidManifest.xml"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    package = re.search(r"package: name='([^']+)'", badging)
    target = re.search(r"targetSdkVersion:'(\d+)'", badging)
    label = re.search(r"^application-label:'([^']+)'", badging, re.MULTILINE)
    if not package or not target or not label:
        raise ValueError("APK package, label or target SDK metadata is missing")
    if "android:networkSecurityConfig" in tree:
        raise ValueError("Custom network security config requires an explicit policy review")
    cleartext = None
    for line in tree.splitlines():
        if "android:usesCleartextTraffic" in line:
            boolean = re.search(r"\(type 0x12\)(0x[0-9a-fA-F]+)\s*$", line)
            if not boolean:
                raise ValueError("Unresolved cleartext manifest attribute")
            cleartext = int(boolean.group(1), 16) != 0
    return {
        "package": package.group(1),
        "label": label.group(1),
        "target_sdk": int(target.group(1)),
        "debuggable": "application-debuggable" in badging,
        "cleartext": cleartext,
    }


def _sha256(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def build_record(
    apk: Path,
    release_apk: Path,
    lockfile: Path,
    commit: str,
    aapt: str,
    *,
    inspect=inspect_manifest,
) -> dict[str, Any]:
    """Require bundled JS, phone/emulator ABIs, and scoped development networking."""
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Expected a full lowercase Git commit SHA")
    with zipfile.ZipFile(apk) as archive:
        try:
            if archive.getinfo("assets/index.android.bundle").file_size == 0:
                raise ValueError("QA JavaScript bundle is empty")
        except KeyError as exc:
            raise ValueError("QA JavaScript bundle is missing") from exc
        abis = {
            name.split("/")[1]
            for name in archive.namelist()
            if name.startswith("lib/") and name.endswith("/libhermes.so")
        }
        if not REQUIRED_ABIS <= abis:
            raise ValueError(
                f"QA APK is missing required native ABIs: {sorted(REQUIRED_ABIS - abis)}"
            )
    qa = inspect(apk, aapt)
    release = inspect(release_apk, aapt)
    if (
        qa["package"] != QA_PACKAGE
        or qa["label"] != "GeoHazard QA"
        or qa["debuggable"]
        or qa["cleartext"] is not True
        or qa["target_sdk"] < 28
    ):
        raise ValueError("QA manifest must use the QA identity, bundled runtime and local HTTP")
    if (
        release["package"] != RELEASE_PACKAGE
        or release["debuggable"]
        or release["cleartext"] is not False
        or release["target_sdk"] < 28
    ):
        raise ValueError("Release manifest must retain production identity and HTTPS defaults")
    return {
        "commit": commit,
        "application_id": QA_PACKAGE,
        "apk_sha256": _sha256(apk),
        "lockfile_sha256": _sha256(lockfile),
        "native_abis": sorted(abis),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("apk", "release-apk", "lockfile", "output"):
        parser.add_argument(f"--{flag}", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--aapt", required=True)
    args = parser.parse_args(argv)
    try:
        record = build_record(args.apk, args.release_apk, args.lockfile, args.commit, args.aapt)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, zipfile.BadZipFile, subprocess.SubprocessError) as exc:
        print(f"QA artifact verification failed: {exc}", file=sys.stderr)
        return 1
    print("QA artifact verified; device flows remain separate acceptance checks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
