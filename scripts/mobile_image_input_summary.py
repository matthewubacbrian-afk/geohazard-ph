"""Correlate bounded image-size observations with a Release Metro build process."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from mobile_process_coverage import _covered_functions, _installed_path

COVERAGE_NAME = re.compile(r"coverage-([1-9][0-9]*)-[0-9]+-([0-9]+)\.json\Z")
TRACE_NAME = re.compile(r"([1-9][0-9]*)\.jsonl\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
ERROR_CODE = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,31}\Z")
SIGNATURES = {"icns", "jxl", "heif", "other"}
ORIGINS = {"buffer_unknown", "workspace", "installed_dependency", "outside_workspace", "unknown"}


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _nonnegative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _coverage_threads(
    coverage_dir: Path, node_modules_root: Path
) -> tuple[set[tuple[int, int]], set[tuple[int, int]], set[tuple[int, int]], Counter]:
    files = sorted(coverage_dir.glob("coverage-*.json"))
    if not files:
        raise ValueError("no V8 coverage files")
    build_threads: set[tuple[int, int]] = set()
    image_threads: set[tuple[int, int]] = set()
    covered_threads: set[tuple[int, int]] = set()
    image_execution_counts: Counter[tuple[int, int]] = Counter()
    root = node_modules_root.resolve()
    for file in files:
        match = COVERAGE_NAME.fullmatch(file.name)
        if match is None:
            raise ValueError(f"invalid V8 coverage filename: {file.name}")
        thread = (int(match.group(1)), int(match.group(2)))
        covered_threads.add(thread)
        try:
            coverage = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid V8 coverage JSON: {file.name}") from exc
        if not isinstance(coverage, dict) or not isinstance(coverage.get("result"), list):
            raise TypeError(f"invalid V8 coverage result: {file.name}")
        for entry in coverage["result"]:
            if not isinstance(entry, dict) or not isinstance(entry.get("url"), str):
                raise TypeError(f"invalid V8 coverage entry: {file.name}")
            relative = _installed_path(entry["url"], root)
            observed, names = _covered_functions(entry, relative or Path("."))
            if not observed or relative is None:
                continue
            if relative.as_posix() == "metro/src/Server.js" and any(
                name == "build" for _, name, _ in names
            ):
                build_threads.add(thread)
            if relative.as_posix() == "image-size/dist/index.js":
                image_threads.add(thread)
                functions = [
                    function for function in entry["functions"]
                    if function["functionName"] == "imageSize"
                ]
                if len(functions) != 1:
                    raise ValueError("missing unique image-size parser function in V8 coverage")
                image_execution_counts[thread] += functions[0]["ranges"][0]["count"]
    if not build_threads:
        raise ValueError("no executed Metro build function in V8 coverage")
    return build_threads, image_threads, covered_threads, image_execution_counts


def _validate_record(record: object, pid: int) -> dict:
    if (
        not isinstance(record, dict)
        or not _positive_int(record.get("pid"))
        or record["pid"] != pid
        or not _nonnegative_int(record.get("thread_id"))
    ):
        raise TypeError("invalid observer PID or thread ID")
    base = {"pid", "thread_id", "event"}
    event = record.get("event")
    if event == "activation":
        if set(record) != base:
            raise ValueError("invalid observer activation")
    elif event == "module_load":
        module_path = record.get("module_path")
        if set(record) != base | {"module_path"} or module_path != "image-size/dist/index.js":
            raise ValueError("invalid observer module path")
    elif event == "call":
        kind = record.get("input_kind")
        if kind not in {"buffer", "path", "invalid"} or record.get("origin_class") not in ORIGINS:
            raise ValueError("invalid observer input class")
        if not isinstance(record.get("callback"), bool):
            raise TypeError("invalid observer callback flag")
        if kind == "invalid" and "observation_error" not in record:
            if record["origin_class"] != "unknown":
                raise ValueError("invalid argument origin")
            expected = base | {"input_kind", "origin_class", "callback"}
        elif "observation_error" in record:
            if not isinstance(record["observation_error"], str) or not ERROR_CODE.fullmatch(
                record["observation_error"]
            ):
                raise ValueError("invalid observation error")
            expected = base | {"input_kind", "origin_class", "observation_error", "callback"}
        else:
            if not _nonnegative_int(record.get("byte_count")):
                raise TypeError("invalid observer byte count")
            if not isinstance(record.get("sha256"), str) or not SHA256.fullmatch(record["sha256"]):
                raise TypeError("invalid observer digest")
            if record.get("signature_class") not in SIGNATURES:
                raise ValueError("invalid observer signature class")
            expected = base | {"input_kind", "origin_class", "byte_count", "sha256", "signature_class", "callback"}
            if kind == "path":
                if not _nonnegative_int(record.get("file_size")):
                    raise TypeError("invalid observer file size")
                expected.add("file_size")
        if set(record) != expected:
            raise ValueError("invalid observer call fields")
    else:
        raise ValueError("invalid observer event")
    return record


def _trace_records(trace_dir: Path) -> dict[tuple[int, int], list[dict]]:
    files = sorted(trace_dir.glob("*.jsonl"))
    if not files:
        raise ValueError("no observer JSONL files")
    records: dict[tuple[int, int], list[dict]] = {}
    for file in files:
        match = TRACE_NAME.fullmatch(file.name)
        if match is None:
            raise ValueError(f"invalid observer filename: {file.name}")
        pid = int(match.group(1))
        try:
            lines = file.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            raise ValueError(f"invalid observer JSONL: {file.name}") from exc
        if not lines:
            raise ValueError(f"empty observer JSONL: {file.name}")
        for line in lines:
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid observer JSONL: {file.name}") from exc
            validated = _validate_record(row, pid)
            records.setdefault((pid, validated["thread_id"]), []).append(validated)
    return records


def build_report(
    platform: str, coverage_dir: Path, trace_dir: Path, node_modules_root: Path
) -> dict:
    """Return validated image-size observations from scoped Release Node threads."""
    if platform not in {"android", "ios"}:
        raise ValueError(f"unsupported platform: {platform}")
    build_threads, image_threads, covered_threads, image_execution_counts = _coverage_threads(
        coverage_dir, node_modules_root
    )
    records = _trace_records(trace_dir)
    for pid, thread_id in records.keys() - covered_threads:
        raise ValueError(
            f"observer activity without V8 coverage for PID {pid}, thread {thread_id}"
        )
    activations = 0
    loads = 0
    calls: Counter[tuple] = Counter()
    for pid, thread_id in sorted(covered_threads):
        thread = (pid, thread_id)
        events = records.get(thread, [])
        activation_count = sum(row["event"] == "activation" for row in events)
        if activation_count < 1:
            raise ValueError(f"missing observer activation for PID {pid}, thread {thread_id}")
        activations += activation_count
        load_count = sum(row["event"] == "module_load" for row in events)
        if thread in image_threads and load_count == 0:
            raise ValueError(
                f"image-size coverage without observer module load for PID {pid}, thread {thread_id}"
            )
        if load_count == 0 and any(row["event"] == "call" for row in events):
            raise ValueError(f"call without observer module load for PID {pid}, thread {thread_id}")
        call_count = sum(row["event"] == "call" for row in events)
        if call_count != image_execution_counts[thread]:
            raise ValueError(f"parser execution count mismatch for PID {pid}, thread {thread_id}")
        loads += load_count
        for row in events:
            if row["event"] == "call":
                fields = tuple(sorted(
                    [
                        (key, value)
                        for key, value in row.items()
                        if key not in {"pid", "thread_id", "event"}
                    ] + [(
                        "process_class",
                        "metro_build_thread" if thread in build_threads else "other_release_thread",
                    )]
                ))
                calls[fields] += 1
    return {
        "platform": platform,
        "packager_build_observed": True,
        "packager_process_count": len({pid for pid, _ in build_threads}),
        "packager_thread_count": len(build_threads),
        "covered_process_count": len({pid for pid, _ in covered_threads}),
        "covered_thread_count": len(covered_threads),
        "observer_activation_count": activations,
        "module_load_count": loads,
        "call_count": sum(calls.values()),
        "calls": [
            {**dict(fields), "occurrences": count}
            for fields, count in sorted(calls.items())
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--platform", choices=("android", "ios"), required=True)
    parser.add_argument("--coverage-dir", required=True, type=Path)
    parser.add_argument("--trace-dir", required=True, type=Path)
    parser.add_argument("--node-modules-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = build_report(args.platform, args.coverage_dir, args.trace_dir, args.node_modules_root)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
