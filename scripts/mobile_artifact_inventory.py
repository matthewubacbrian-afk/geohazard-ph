"""Record observable mobile release contents without making risk conclusions."""

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path, label: str) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is missing or invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object: {path}")
    return value


def _package_from_source(source: str) -> str | None:
    normalized = source.replace("\\", "/")
    if "node_modules/" not in normalized:
        return None
    tail = normalized.rsplit("node_modules/", 1)[1]
    pieces = tail.split("/")
    if not pieces[0]:
        return None
    if pieces[0].startswith("@"):
        return "/".join(pieces[:2]) if len(pieces) > 1 and pieces[1] else None
    return pieces[0]


def _source_counts(source_map: dict) -> dict[str, int]:
    sources = source_map.get("sources")
    if not isinstance(sources, list) or not all(isinstance(item, str) for item in sources):
        raise ValueError("source map requires a string sources array")
    counts: dict[str, int] = {}
    for source in sources:
        package = _package_from_source(source)
        if package is not None:
            counts[package] = counts.get(package, 0) + 1
    if not counts:
        raise ValueError("source map has no package paths; cannot classify advisory observations")
    return counts


def _advisories(audit: dict, source_counts: dict[str, int]) -> list[dict]:
    vulnerabilities = audit.get("vulnerabilities")
    if not isinstance(vulnerabilities, dict):
        raise ValueError("audit JSON has no vulnerabilities object")
    rows = []
    for name, finding in sorted(vulnerabilities.items()):
        if not isinstance(name, str) or not isinstance(finding, dict):
            raise ValueError("audit vulnerabilities have an invalid entry")
        nodes = finding.get("nodes")
        severity = finding.get("severity")
        if not isinstance(nodes, list) or not all(isinstance(node, str) for node in nodes):
            raise ValueError(f"audit paths are invalid for {name}")
        if not isinstance(severity, str):
            raise ValueError(f"audit severity is invalid for {name}")
        matched = source_counts.get(name, 0)
        rows.append(
            {
                "package": name,
                "severity": severity,
                "source_map_observation": "listed" if matched else "not_listed",
                "matched_source_count": matched,
                "dependency_paths": sorted(set(nodes)),
                "disposition": "undetermined",
            }
        )
    return rows


def _android_artifact(apk: Path) -> tuple[str, str, list[str]]:
    try:
        with zipfile.ZipFile(apk) as archive:
            entries = archive.namelist()
    except (OSError, zipfile.BadZipFile) as exc:
        raise ValueError(f"Android artifact is missing or invalid: {apk}") from exc
    bundle = "assets/index.android.bundle"
    if bundle not in entries:
        raise ValueError(f"Android artifact has no release bundle: {apk}")
    native_entries = sorted(
        entry for entry in entries if entry.startswith("lib/") and entry.endswith(".so")
    )
    return _sha256(apk), bundle, native_entries


def _ios_artifact(app: Path) -> tuple[str, str, list[str]]:
    bundle = app / "main.jsbundle"
    if not bundle.is_file():
        raise ValueError(f"iOS artifact has no release bundle: {app}")
    native_entries = sorted(
        path.relative_to(app).as_posix()
        for path in (app / "Frameworks").rglob("*")
        if path.is_file() and (path.parent.suffix == ".framework" or path.suffix == ".dylib")
    )
    return _sha256(bundle), "main.jsbundle", native_entries


def build_report(
    platform: str, source_map_path: Path, artifact_path: Path, audit_json_path: Path
) -> dict:
    """Return a small deterministic report of observed release inputs."""
    source_map = _read_object(source_map_path, "source map")
    audit = _read_object(audit_json_path, "audit")
    source_counts = _source_counts(source_map)
    if platform == "android":
        artifact_hash, bundle_path, native_entries = _android_artifact(artifact_path)
    elif platform == "ios":
        artifact_hash, bundle_path, native_entries = _ios_artifact(artifact_path)
    else:
        raise ValueError(f"unsupported platform: {platform}")
    return {
        "platform": platform,
        "artifact_sha256": artifact_hash,
        "source_map_sha256": _sha256(source_map_path),
        "bundle_path": bundle_path,
        "native_entries": native_entries,
        "source_packages": sorted(source_counts),
        "advisories": _advisories(audit, source_counts),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=("android", "ios"))
    parser.add_argument("--source-map", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--audit-json", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.platform, args.source_map, args.artifact, args.audit_json)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
