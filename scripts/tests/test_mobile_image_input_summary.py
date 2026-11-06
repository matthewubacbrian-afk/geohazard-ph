"""Behavioral tests for the bounded Release image-input summary."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mobile_image_input_summary import build_report


def _coverage(
    root: Path, pid: int, *, build: bool = True, image: bool = True, image_calls: int = 1
) -> dict:
    result = [
        {
            "url": (root / "metro" / "src" / "Server.js").as_uri(),
            "functions": [
                {"functionName": "build", "ranges": [{"startOffset": 10, "count": int(build)}]}
            ],
        }
    ]
    if image:
        result.append(
            {
                "url": (root / "image-size" / "dist" / "index.js").as_uri(),
                "functions": [
                    {"functionName": "", "ranges": [{"startOffset": 0, "count": 1}]},
                    {"functionName": "imageSize", "ranges": [{"startOffset": 20, "count": image_calls}]},
                ],
            }
        )
    return {"result": result}


def _write_run(tmp_path: Path, *, call: bool = True) -> tuple[Path, Path, Path]:
    root = tmp_path / "mobile" / "node_modules"
    coverage_dir = tmp_path / "coverage"
    trace_dir = tmp_path / "trace"
    coverage_dir.mkdir()
    trace_dir.mkdir()
    (coverage_dir / "coverage-101-123-0.json").write_text(
        json.dumps(_coverage(root, 101, image_calls=int(call))), encoding="utf-8"
    )
    (coverage_dir / "coverage-202-123-0.json").write_text(
        json.dumps(_coverage(root, 202, build=False, image=False)), encoding="utf-8"
    )
    packager = [
        {"pid": 101, "thread_id": 0, "event": "activation"},
        {"pid": 101, "thread_id": 0, "event": "module_load", "module_path": "image-size/dist/index.js"},
    ]
    if call:
        packager.append(
            {
                "pid": 101,
                "thread_id": 0,
                "event": "call",
                "input_kind": "buffer",
                "origin_class": "buffer_unknown",
                "byte_count": 16,
                "sha256": "a" * 64,
                "signature_class": "other",
                "callback": False,
            }
        )
    (trace_dir / "101.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in packager), encoding="utf-8"
    )
    (trace_dir / "202.jsonl").write_text(
        json.dumps({"pid": 202, "thread_id": 0, "event": "activation"}) + "\n", encoding="utf-8"
    )
    return coverage_dir, trace_dir, root


def test_correlates_calls_to_executed_metro_build_pid(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)

    report = build_report("android", coverage, trace, root)

    assert report == {
        "platform": "android",
        "packager_build_observed": True,
        "packager_process_count": 1,
        "packager_thread_count": 1,
        "covered_process_count": 2,
        "covered_thread_count": 2,
        "observer_activation_count": 2,
        "module_load_count": 1,
        "call_count": 1,
        "calls": [
            {
                "input_kind": "buffer",
                "origin_class": "buffer_unknown",
                "byte_count": 16,
                "sha256": "a" * 64,
                "signature_class": "other",
                "callback": False,
                "occurrences": 1,
                "process_class": "metro_build_thread",
            }
        ],
    }


def test_zero_calls_requires_observer_activation_and_module_load(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path, call=False)
    report = build_report("ios", coverage, trace, root)
    assert report["call_count"] == 0
    assert report["packager_build_observed"] is True
    assert report["module_load_count"] == 1


def test_accepts_multiple_thread_activations_in_one_packager_pid(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path, call=False)
    file = trace / "101.jsonl"
    rows = file.read_text(encoding="utf-8").splitlines()
    file.write_text(rows[0] + "\n" + "\n".join(rows) + "\n", encoding="utf-8")

    report = build_report("android", coverage, trace, root)

    assert report["packager_process_count"] == 1
    assert report["observer_activation_count"] == 3


def test_rejects_unobserved_worker_thread_with_image_coverage(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path, call=False)
    (coverage / "coverage-101-456-1.json").write_text(
        json.dumps(_coverage(root, 101, build=False, image_calls=0)), encoding="utf-8"
    )
    with pytest.raises(ValueError, match=r"missing observer activation.*101.*1"):
        build_report("android", coverage, trace, root)


def test_correlates_worker_thread_load_without_a_call(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path, call=False)
    (coverage / "coverage-101-456-1.json").write_text(
        json.dumps(_coverage(root, 101, build=False, image_calls=0)), encoding="utf-8"
    )
    file = trace / "101.jsonl"
    file.write_text(
        file.read_text(encoding="utf-8")
        + json.dumps({"pid": 101, "thread_id": 1, "event": "activation"}) + "\n"
        + json.dumps({"pid": 101, "thread_id": 1, "event": "module_load",
                      "module_path": "image-size/dist/index.js"}) + "\n",
        encoding="utf-8",
    )
    report = build_report("android", coverage, trace, root)
    assert report["covered_process_count"] == 2
    assert report["covered_thread_count"] == 3
    assert report["module_load_count"] == 2


def test_rejects_activation_without_matching_coverage(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    (trace / "303.jsonl").write_text(
        json.dumps({"pid": 303, "thread_id": 0, "event": "activation"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="observer activity without V8 coverage"):
        build_report("android", coverage, trace, root)


def test_rejects_unobserved_parser_execution(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path, call=False)
    (coverage / "coverage-101-123-0.json").write_text(
        json.dumps(_coverage(root, 101, image_calls=1)), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="parser execution count"):
        build_report("android", coverage, trace, root)


def test_includes_calls_from_non_build_release_node_process(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    child_call = {
        "pid": 202,
        "thread_id": 0,
        "event": "call",
        "input_kind": "path",
        "origin_class": "outside_workspace",
        "file_size": 10,
        "byte_count": 10,
        "sha256": "b" * 64,
        "signature_class": "other",
        "callback": False,
    }
    (trace / "202.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"pid": 202, "thread_id": 0, "event": "activation"}),
                json.dumps(
                    {"pid": 202, "thread_id": 0, "event": "module_load", "module_path": "image-size/dist/index.js"}
                ),
                json.dumps(child_call),
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (coverage / "coverage-202-123-0.json").write_text(
        json.dumps(_coverage(root, 202, build=False)), encoding="utf-8"
    )

    report = build_report("android", coverage, trace, root)

    assert report["call_count"] == 2
    assert {call["process_class"] for call in report["calls"]} == {
        "metro_build_thread", "other_release_thread"
    }


def test_rejects_path_like_observation_error(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    file = trace / "101.jsonl"
    rows = file.read_text(encoding="utf-8").splitlines()
    row = {"pid": 101, "thread_id": 0, "event": "call", "input_kind": "path", "origin_class": "unknown",
           "observation_error": "/private/asset.png", "callback": False}
    file.write_text("\n".join([*rows[:2], json.dumps(row)]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid observation error"):
        build_report("android", coverage, trace, root)


def test_accepts_observer_record_for_invalid_parser_argument(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    file = trace / "101.jsonl"
    rows = file.read_text(encoding="utf-8").splitlines()
    invalid = {
        "pid": 101,
        "thread_id": 0,
        "event": "call",
        "input_kind": "invalid",
        "origin_class": "unknown",
        "callback": False,
    }
    file.write_text("\n".join([*rows[:2], json.dumps(invalid)]) + "\n", encoding="utf-8")

    report = build_report("android", coverage, trace, root)

    assert report["call_count"] == 1
    assert report["calls"][0]["input_kind"] == "invalid"


def test_rejects_missing_metro_execution(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    file = coverage / "coverage-101-123-0.json"
    file.write_text(json.dumps(_coverage(root, 101, build=False)), encoding="utf-8")
    with pytest.raises(ValueError, match="no executed Metro build"):
        build_report("android", coverage, trace, root)


def test_rejects_missing_observer_activation(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    (trace / "101.jsonl").write_text(
        json.dumps({"pid": 101, "thread_id": 0, "event": "module_load", "module_path": "image-size/dist/index.js"})
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="observer activation"):
        build_report("android", coverage, trace, root)


def test_rejects_image_coverage_without_observed_module_load(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    rows = (trace / "101.jsonl").read_text(encoding="utf-8").splitlines()
    (trace / "101.jsonl").write_text(rows[0] + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="without observer module load"):
        build_report("android", coverage, trace, root)


def test_rejects_call_without_observed_module_load(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    rows = (trace / "101.jsonl").read_text(encoding="utf-8").splitlines()
    (trace / "101.jsonl").write_text(rows[0] + "\n" + rows[2] + "\n", encoding="utf-8")
    (coverage / "coverage-101-123-0.json").write_text(
        json.dumps(_coverage(root, 101, image=False)), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="call without observer module load"):
        build_report("android", coverage, trace, root)


@pytest.mark.parametrize("record", ["{bad", '{"pid":101,"thread_id":0,"event":"call","path":"/private"}'])
def test_rejects_malformed_or_raw_path_record(tmp_path: Path, record: str) -> None:
    coverage, trace, root = _write_run(tmp_path)
    (trace / "101.jsonl").write_text(record + "\n", encoding="utf-8")
    with pytest.raises((ValueError, TypeError)):
        build_report("android", coverage, trace, root)


def test_rejects_metro_coverage_outside_install_root(tmp_path: Path) -> None:
    coverage, trace, root = _write_run(tmp_path)
    outside = tmp_path / "other" / "node_modules"
    (coverage / "coverage-101-123-0.json").write_text(
        json.dumps(_coverage(outside, 101)), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="no executed Metro build"):
        build_report("android", coverage, trace, root)
