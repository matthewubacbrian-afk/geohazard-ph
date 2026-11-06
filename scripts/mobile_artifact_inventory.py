"""Record observable mobile release contents without making risk conclusions."""

import argparse
import hashlib
import json
import plistlib
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


def _advisories(audit: dict, source_counts: dict[str, int], packages: dict) -> list[dict]:
    vulnerabilities = audit.get("vulnerabilities")
    if not isinstance(vulnerabilities, dict):
        raise ValueError("audit JSON has no vulnerabilities object")
    rows = []
    for name, finding in sorted(vulnerabilities.items()):
        if not isinstance(name, str) or not isinstance(finding, dict):
            raise ValueError("audit vulnerabilities have an invalid entry")
        nodes = finding.get("nodes")
        severity = finding.get("severity")
        if not isinstance(nodes, list) or not nodes or not all(isinstance(node, str) for node in nodes):
            raise ValueError(f"audit paths are invalid for {name}")
        if not isinstance(severity, str):
            raise ValueError(f"audit severity is invalid for {name}")
        installed_nodes = []
        for node in sorted(set(nodes)):
            package = packages.get(node)
            version = package.get("version") if isinstance(package, dict) else None
            if not isinstance(version, str) or not version:
                raise ValueError(f"lockfile version is missing for {name}: {node}")
            installed_nodes.append({"path": node, "version": version})
        via = finding.get("via")
        if not isinstance(via, list) or not via:
            raise ValueError(f"audit via entries are invalid for {name}")
        via_packages = set()
        references = set()
        for entry in via:
            if isinstance(entry, str) and entry:
                via_packages.add(entry)
            elif isinstance(entry, dict):
                source = entry.get("source")
                url = entry.get("url")
                affected_range = entry.get("range")
                if (
                    not isinstance(source, int)
                    or isinstance(source, bool)
                    or source <= 0
                    or not isinstance(url, str)
                    or not url.startswith("https://")
                    or not isinstance(affected_range, str)
                    or not affected_range
                ):
                    raise ValueError(f"audit advisory reference is invalid for {name}")
                references.add((source, url, affected_range))
            else:
                raise ValueError(f"audit via entry is invalid for {name}")
        matched = source_counts.get(name, 0)
        rows.append(
            {
                "package": name,
                "severity": severity,
                "source_map_observation": "listed" if matched else "not_listed",
                "matched_source_count": matched,
                "dependency_paths": sorted(set(nodes)),
                "installed_nodes": installed_nodes,
                "via_packages": sorted(via_packages),
                "advisory_references": [
                    {"source": source, "url": url, "range": affected_range}
                    for source, url, affected_range in sorted(references)
                ],
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
    try:
        with (app / "Info.plist").open("rb") as source:
            app_info = plistlib.load(source)
    except (OSError, ValueError, TypeError, plistlib.InvalidFileException) as exc:
        raise ValueError(f"iOS artifact has no valid Info.plist: {app}") from exc
    executable = app_info.get("CFBundleExecutable") if isinstance(app_info, dict) else None
    if not isinstance(executable, str) or Path(executable).name != executable:
        raise ValueError(f"iOS artifact has no valid executable name: {app}")
    if not (app / executable).is_file():
        raise ValueError(f"iOS artifact has no app executable: {app}")
    native_entries = sorted(
        {executable}
        | {
            path.relative_to(app).as_posix()
            for path in (app / "Frameworks").rglob("*")
            if path.is_file()
            and (
                path.suffix == ".dylib"
                or (path.name == path.parent.stem and path.parent.suffix == ".framework")
            )
        }
    )
    return _sha256(bundle), "main.jsbundle", native_entries


def build_report(
    platform: str,
    source_map_path: Path,
    artifact_path: Path,
    audit_json_path: Path,
    lockfile_path: Path,
) -> dict:
    """Return a small deterministic report of observed release inputs."""
    source_map = _read_object(source_map_path, "source map")
    audit = _read_object(audit_json_path, "audit")
    lockfile = _read_object(lockfile_path, "lockfile")
    packages = lockfile.get("packages")
    if not isinstance(packages, dict):
        raise ValueError("lockfile has no packages object")
    source_counts = _source_counts(source_map)
    if platform == "android":
        artifact_hash, bundle_path, native_entries = _android_artifact(artifact_path)
        artifact_hash_scope = "android_apk_file"
    elif platform == "ios":
        artifact_hash, bundle_path, native_entries = _ios_artifact(artifact_path)
        artifact_hash_scope = "ios_main_jsbundle_file"
    else:
        raise ValueError(f"unsupported platform: {platform}")
    return {
        "platform": platform,
        "artifact_sha256": artifact_hash,
        "artifact_hash_scope": artifact_hash_scope,
        "source_map_sha256": _sha256(source_map_path),
        "bundle_path": bundle_path,
        "native_entries": native_entries,
        "source_packages": sorted(source_counts),
        "advisories": _advisories(audit, source_counts, packages),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", required=True, choices=("android", "ios"))
    parser.add_argument("--source-map", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--audit-json", required=True, type=Path)
    parser.add_argument("--lockfile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    report = build_report(
        args.platform, args.source_map, args.artifact, args.audit_json, args.lockfile
    )
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
