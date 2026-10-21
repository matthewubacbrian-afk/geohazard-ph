"""Summarize Node coverage from non-published mobile Release build processes."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import url2pathname

DIRECT_PACKAGES = ("braces", "fast-xml-parser", "image-size", "node-forge", "sprintf-js")


def _installed_path(url: str, root: Path) -> Path | None:
    parsed = urlsplit(url)
    if parsed.scheme != "file" or parsed.netloc not in ("", "localhost"):
        return None
    path = Path(url2pathname(parsed.path)).resolve()
    try:
        return path.relative_to(root)
    except ValueError:
        return None


def _direct_package(path: Path) -> str | None:
    pieces = path.parts
    if not pieces:
        return None
    package_index = 0
    for index, piece in enumerate(pieces[:-1]):
        if piece == "node_modules":
            package_index = index + 1
    package = pieces[package_index]
    return package if package in DIRECT_PACKAGES else None


def _covered_functions(entry: dict, file: Path) -> tuple[bool, set[tuple[str, str, int]]]:
    functions = entry.get("functions")
    if not isinstance(functions, list):
        raise TypeError("invalid V8 coverage functions array")
    loaded = False
    named: set[tuple[str, str, int]] = set()
    for function in functions:
        if not isinstance(function, dict) or not isinstance(function.get("functionName"), str):
            raise TypeError("invalid V8 coverage function")
        ranges = function.get("ranges")
        if not isinstance(ranges, list) or not ranges:
            raise TypeError("invalid V8 coverage function ranges")
        first = ranges[0]
        if (
            not isinstance(first, dict)
            or not isinstance(first.get("startOffset"), int)
            or isinstance(first.get("startOffset"), bool)
            or not isinstance(first.get("count"), int)
            or isinstance(first.get("count"), bool)
            or first["count"] < 0
        ):
            raise TypeError("invalid V8 coverage function range")
        if first["count"] > 0:
            loaded = True
            if function["functionName"]:
                named.add((file.as_posix(), function["functionName"], first["startOffset"]))
    return loaded, named


def build_report(platform: str, coverage_dir: Path, node_modules_root: Path) -> dict:
    """Return loaded files and executed named functions for direct advisory packages."""
    if platform not in ("android", "ios"):
        raise ValueError(f"unsupported platform: {platform}")
    files = sorted(coverage_dir.glob("coverage-*.json"))
    if not files:
        raise ValueError(f"no V8 coverage files in {coverage_dir}")
    root = node_modules_root.resolve()
    loaded: dict[str, set[str]] = {package: set() for package in DIRECT_PACKAGES}
    executed: dict[str, set[tuple[str, str, int]]] = {
        package: set() for package in DIRECT_PACKAGES
    }
    installed_entry_count = 0
    packager_build_observed = False
    for file in files:
        try:
            coverage = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid V8 coverage JSON: {file}") from exc
        if not isinstance(coverage, dict) or not isinstance(coverage.get("result"), list):
            raise TypeError(f"invalid V8 coverage result: {file}")
        for entry in coverage["result"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("url"), str):
                raise TypeError(f"invalid V8 coverage entry: {file}")
            relative = _installed_path(entry["url"], root)
            observed, names = _covered_functions(entry, relative or Path("."))
            if relative is None or not observed:
                continue
            installed_entry_count += 1
            if relative.as_posix() == "metro/src/Server.js" and any(
                name == "build" for _, name, _ in names
            ):
                packager_build_observed = True
            package = _direct_package(relative)
            if package is not None:
                loaded[package].add(relative.as_posix())
                executed[package].update(names)
    if not installed_entry_count:
        raise ValueError(f"no covered files under {root}")
    if not packager_build_observed:
        raise ValueError("no executed Metro build function in V8 coverage")
    return {
        "platform": platform,
        "coverage_file_count": len(files),
        "packager_build_observed": True,
        "packages": {
            package: {
                "loaded_files": sorted(loaded[package]),
                "executed_functions": [
                    {"path": path, "name": name, "start_offset": offset}
                    for path, name, offset in sorted(
                        executed[package], key=lambda item: (item[0], item[2], item[1])
                    )
                ],
            }
            for package in DIRECT_PACKAGES
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("android", "ios"), required=True)
    parser.add_argument("--coverage-dir", required=True, type=Path)
    parser.add_argument("--node-modules-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    report = build_report(args.platform, args.coverage_dir, args.node_modules_root)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
