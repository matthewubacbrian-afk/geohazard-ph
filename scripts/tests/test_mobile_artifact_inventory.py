import hashlib
import json
import plistlib
import zipfile
from pathlib import Path

import pytest

from scripts.mobile_artifact_inventory import build_report, main


def _inputs(tmp_path: Path) -> tuple[Path, Path]:
    source_map = tmp_path / "release.map"
    source_map.write_text(
        json.dumps(
            {
                "version": 3,
                "sources": [
                    "../node_modules/image-size/dist/index.js",
                    "..\\node_modules\\@react-native\\metro-config\\src\\index.js",
                    "src/App.tsx",
                ],
                "sourcesContent": ["private bundle source", "private dependency source", "app"],
            }
        ),
        encoding="utf-8",
    )
    audit_json = tmp_path / "audit.json"
    audit_json.write_text(
        json.dumps(
            {
                "metadata": {"vulnerabilities": {"high": 2, "total": 2}},
                "vulnerabilities": {
                    "metro": {
                        "severity": "high",
                        "nodes": ["node_modules/metro"],
                        "via": ["image-size"],
                    },
                    "image-size": {
                        "severity": "high",
                        "nodes": ["node_modules/image-size"],
                        "via": [{"source": 12345, "name": "image-size", "title": "sample"}],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return source_map, audit_json


def test_android_report_matches_sources_and_packaged_native_files(tmp_path: Path) -> None:
    source_map, audit_json = _inputs(tmp_path)
    apk = tmp_path / "app-release.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("assets/index.android.bundle", b"Hermes bytecode")
        archive.writestr("lib/arm64-v8a/libhermes.so", b"native code")
        archive.writestr("classes.dex", b"dex")

    report = build_report("android", source_map, apk, audit_json)

    assert report["platform"] == "android"
    assert report["bundle_path"] == "assets/index.android.bundle"
    assert report["artifact_sha256"] == hashlib.sha256(apk.read_bytes()).hexdigest()
    assert report["artifact_hash_scope"] == "android_apk_file"
    assert report["native_entries"] == ["lib/arm64-v8a/libhermes.so"]
    assert report["source_packages"] == ["@react-native/metro-config", "image-size"]
    assert report["advisories"] == [
        {
            "package": "image-size",
            "severity": "high",
            "source_map_observation": "listed",
            "matched_source_count": 1,
            "dependency_paths": ["node_modules/image-size"],
            "disposition": "undetermined",
        },
        {
            "package": "metro",
            "severity": "high",
            "source_map_observation": "not_listed",
            "matched_source_count": 0,
            "dependency_paths": ["node_modules/metro"],
            "disposition": "undetermined",
        },
    ]
    assert "private bundle source" not in json.dumps(report)
    assert "sample" not in json.dumps(report)


def test_ios_report_lists_executables_without_framework_metadata(tmp_path: Path) -> None:
    source_map, audit_json = _inputs(tmp_path)
    app = tmp_path / "GeoHazardPH.app"
    (app / "Frameworks" / "React.framework").mkdir(parents=True)
    (app / "main.jsbundle").write_bytes(b"iOS Hermes bytecode")
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "GeoHazardPH"}))
    (app / "GeoHazardPH").write_bytes(b"app executable")
    (app / "Frameworks" / "React.framework" / "React").write_bytes(b"native code")
    (app / "Frameworks" / "React.framework" / "Info.plist").write_bytes(b"metadata")

    report = build_report("ios", source_map, app, audit_json)

    assert report["bundle_path"] == "main.jsbundle"
    assert report["artifact_sha256"] == hashlib.sha256(b"iOS Hermes bytecode").hexdigest()
    assert report["artifact_hash_scope"] == "ios_main_jsbundle_file"
    assert report["native_entries"] == ["Frameworks/React.framework/React", "GeoHazardPH"]


def test_ios_report_rejects_missing_or_invalid_app_executable(tmp_path: Path) -> None:
    source_map, audit_json = _inputs(tmp_path)
    app = tmp_path / "GeoHazardPH.app"
    app.mkdir()
    (app / "main.jsbundle").write_bytes(b"iOS Hermes bytecode")

    with pytest.raises(ValueError, match=r"Info\.plist"):
        build_report("ios", source_map, app, audit_json)

    (app / "Info.plist").write_text("bad plist", encoding="utf-8")
    with pytest.raises(ValueError, match=r"Info\.plist"):
        build_report("ios", source_map, app, audit_json)

    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "../other"}))
    with pytest.raises(ValueError, match="executable name"):
        build_report("ios", source_map, app, audit_json)

    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "GeoHazardPH"}))
    with pytest.raises(ValueError, match="app executable"):
        build_report("ios", source_map, app, audit_json)


def test_report_rejects_missing_bundle_or_invalid_audit(tmp_path: Path) -> None:
    source_map, audit_json = _inputs(tmp_path)
    apk = tmp_path / "empty.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("classes.dex", b"dex")

    with pytest.raises(ValueError, match="bundle"):
        build_report("android", source_map, apk, audit_json)

    audit_json.write_text("not JSON", encoding="utf-8")
    with pytest.raises(ValueError, match="audit"):
        build_report("android", source_map, apk, audit_json)


def test_report_rejects_source_map_without_package_paths(tmp_path: Path) -> None:
    source_map, audit_json = _inputs(tmp_path)
    source_map.write_text(json.dumps({"sources": ["src/App.tsx"]}), encoding="utf-8")
    apk = tmp_path / "app-release.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("assets/index.android.bundle", b"Hermes bytecode")

    with pytest.raises(ValueError, match="package"):
        build_report("android", source_map, apk, audit_json)


def test_cli_writes_small_deterministic_report(tmp_path: Path) -> None:
    source_map, audit_json = _inputs(tmp_path)
    apk = tmp_path / "app-release.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("assets/index.android.bundle", b"Hermes bytecode")
    output = tmp_path / "report.json"

    assert main(
        [
            "--platform", "android",
            "--source-map", str(source_map),
            "--artifact", str(apk),
            "--audit-json", str(audit_json),
            "--output", str(output),
        ]
    ) == 0
    first = output.read_bytes()
    assert json.loads(first)["advisories"][0]["disposition"] == "undetermined"
    assert main(
        [
            "--platform", "android",
            "--source-map", str(source_map),
            "--artifact", str(apk),
            "--audit-json", str(audit_json),
            "--output", str(output),
        ]
    ) == 0
    assert output.read_bytes() == first
