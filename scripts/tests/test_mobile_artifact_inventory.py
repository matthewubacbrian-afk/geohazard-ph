import hashlib
import json
import plistlib
import zipfile
from pathlib import Path

import pytest

from scripts.mobile_artifact_inventory import build_report, main


def _inputs(tmp_path: Path) -> tuple[Path, Path, Path]:
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
                        "via": [
                            {
                                "source": 12345,
                                "name": "image-size",
                                "title": "sample",
                                "url": "https://github.com/advisories/GHSA-example",
                                "range": "<=1.2.1",
                            }
                        ],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    lockfile = tmp_path / "package-lock.json"
    lockfile.write_text(
        json.dumps(
            {
                "packages": {
                    "node_modules/image-size": {"version": "1.2.1"},
                    "node_modules/metro": {"version": "0.75.5"},
                }
            }
        ),
        encoding="utf-8",
    )
    return source_map, audit_json, lockfile


def test_report_records_installed_versions_and_direct_advisory_references(tmp_path: Path) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
    audit = json.loads(audit_json.read_text(encoding="utf-8"))
    audit["vulnerabilities"]["image-size"]["via"][0].update(
        {"url": "https://github.com/advisories/GHSA-example", "range": "<=1.2.1"}
    )
    audit_json.write_text(json.dumps(audit), encoding="utf-8")
    apk = tmp_path / "app-release.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("assets/index.android.bundle", b"Hermes bytecode")

    report = build_report("android", source_map, apk, audit_json, lockfile)

    image_size, metro = report["advisories"]
    assert image_size["installed_nodes"] == [
        {"path": "node_modules/image-size", "version": "1.2.1"}
    ]
    assert image_size["advisory_references"] == [
        {
            "source": 12345,
            "url": "https://github.com/advisories/GHSA-example",
            "range": "<=1.2.1",
        }
    ]
    assert image_size["via_packages"] == []
    assert metro["installed_nodes"] == [{"path": "node_modules/metro", "version": "0.75.5"}]
    assert metro["advisory_references"] == []
    assert metro["via_packages"] == ["image-size"]
    assert all(item["disposition"] == "undetermined" for item in report["advisories"])


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ({"source": 12345, "url": "http://example.test/advisory", "range": "<=1.2.1"},
         "audit advisory reference is invalid for image-size"),
        ({"source": 12345, "url": "https://example.test/advisory"},
         "audit advisory reference is invalid for image-size"),
        (42, "audit via entry is invalid for image-size"),
    ],
)
def test_report_rejects_malformed_advisory_reference(
    tmp_path: Path, entry: object, message: str
) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
    audit = json.loads(audit_json.read_text(encoding="utf-8"))
    audit["vulnerabilities"]["image-size"]["via"] = [entry]
    audit_json.write_text(json.dumps(audit), encoding="utf-8")
    apk = tmp_path / "app-release.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("assets/index.android.bundle", b"Hermes bytecode")

    with pytest.raises(ValueError, match=message):
        build_report("android", source_map, apk, audit_json, lockfile)


@pytest.mark.parametrize("package_entry", [None, {}, {"version": 123}])
def test_report_rejects_missing_lockfile_version(tmp_path: Path, package_entry: object) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
    contents = json.loads(lockfile.read_text(encoding="utf-8"))
    if package_entry is None:
        del contents["packages"]["node_modules/image-size"]
    else:
        contents["packages"]["node_modules/image-size"] = package_entry
    lockfile.write_text(json.dumps(contents), encoding="utf-8")
    apk = tmp_path / "app-release.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("assets/index.android.bundle", b"Hermes bytecode")

    with pytest.raises(ValueError, match="lockfile version is missing for image-size"):
        build_report("android", source_map, apk, audit_json, lockfile)


def test_android_report_matches_sources_and_packaged_native_files(tmp_path: Path) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
    apk = tmp_path / "app-release.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("assets/index.android.bundle", b"Hermes bytecode")
        archive.writestr("lib/arm64-v8a/libhermes.so", b"native code")
        archive.writestr("classes.dex", b"dex")

    report = build_report("android", source_map, apk, audit_json, lockfile)

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
            "installed_nodes": [{"path": "node_modules/image-size", "version": "1.2.1"}],
            "via_packages": [],
            "advisory_references": [
                {
                    "source": 12345,
                    "url": "https://github.com/advisories/GHSA-example",
                    "range": "<=1.2.1",
                }
            ],
            "disposition": "undetermined",
        },
        {
            "package": "metro",
            "severity": "high",
            "source_map_observation": "not_listed",
            "matched_source_count": 0,
            "dependency_paths": ["node_modules/metro"],
            "installed_nodes": [{"path": "node_modules/metro", "version": "0.75.5"}],
            "via_packages": ["image-size"],
            "advisory_references": [],
            "disposition": "undetermined",
        },
    ]
    assert "private bundle source" not in json.dumps(report)
    assert "sample" not in json.dumps(report)


def test_ios_report_lists_executables_without_framework_metadata(tmp_path: Path) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
    app = tmp_path / "GeoHazardPH.app"
    (app / "Frameworks" / "React.framework").mkdir(parents=True)
    (app / "main.jsbundle").write_bytes(b"iOS Hermes bytecode")
    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "GeoHazardPH"}))
    (app / "GeoHazardPH").write_bytes(b"app executable")
    (app / "Frameworks" / "React.framework" / "React").write_bytes(b"native code")
    (app / "Frameworks" / "React.framework" / "Info.plist").write_bytes(b"metadata")

    report = build_report("ios", source_map, app, audit_json, lockfile)

    assert report["bundle_path"] == "main.jsbundle"
    assert report["artifact_sha256"] == hashlib.sha256(b"iOS Hermes bytecode").hexdigest()
    assert report["artifact_hash_scope"] == "ios_main_jsbundle_file"
    assert report["native_entries"] == ["Frameworks/React.framework/React", "GeoHazardPH"]


def test_ios_report_rejects_missing_or_invalid_app_executable(tmp_path: Path) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
    app = tmp_path / "GeoHazardPH.app"
    app.mkdir()
    (app / "main.jsbundle").write_bytes(b"iOS Hermes bytecode")

    with pytest.raises(ValueError, match=r"Info\.plist"):
        build_report("ios", source_map, app, audit_json, lockfile)

    (app / "Info.plist").write_text("bad plist", encoding="utf-8")
    with pytest.raises(ValueError, match=r"Info\.plist"):
        build_report("ios", source_map, app, audit_json, lockfile)

    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "../other"}))
    with pytest.raises(ValueError, match="executable name"):
        build_report("ios", source_map, app, audit_json, lockfile)

    (app / "Info.plist").write_bytes(plistlib.dumps({"CFBundleExecutable": "GeoHazardPH"}))
    with pytest.raises(ValueError, match="app executable"):
        build_report("ios", source_map, app, audit_json, lockfile)


def test_report_rejects_missing_bundle_or_invalid_audit(tmp_path: Path) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
    apk = tmp_path / "empty.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("classes.dex", b"dex")

    with pytest.raises(ValueError, match="bundle"):
        build_report("android", source_map, apk, audit_json, lockfile)

    audit_json.write_text("not JSON", encoding="utf-8")
    with pytest.raises(ValueError, match="audit"):
        build_report("android", source_map, apk, audit_json, lockfile)


def test_report_rejects_source_map_without_package_paths(tmp_path: Path) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
    source_map.write_text(json.dumps({"sources": ["src/App.tsx"]}), encoding="utf-8")
    apk = tmp_path / "app-release.apk"
    with zipfile.ZipFile(apk, "w") as archive:
        archive.writestr("assets/index.android.bundle", b"Hermes bytecode")

    with pytest.raises(ValueError, match="package"):
        build_report("android", source_map, apk, audit_json, lockfile)


def test_cli_writes_small_deterministic_report(tmp_path: Path) -> None:
    source_map, audit_json, lockfile = _inputs(tmp_path)
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
            "--lockfile", str(lockfile),
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
            "--lockfile", str(lockfile),
            "--output", str(output),
        ]
    ) == 0
    assert output.read_bytes() == first
