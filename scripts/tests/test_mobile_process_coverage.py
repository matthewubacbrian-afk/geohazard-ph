import json
from pathlib import Path

import pytest

from scripts.mobile_process_coverage import build_report, main


def _function(name: str, count: int, start: int = 0) -> dict:
    return {
        "functionName": name,
        "ranges": [{"startOffset": start, "endOffset": start + 20, "count": count}],
        "isBlockCoverage": True,
    }


def _coverage(coverage_dir: Path, entries: list[dict], name: str = "coverage-1.json") -> None:
    coverage_dir.mkdir(parents=True, exist_ok=True)
    (coverage_dir / name).write_text(json.dumps({"result": entries}), encoding="utf-8")


def test_report_separates_loaded_files_from_executed_named_functions(tmp_path: Path) -> None:
    root = tmp_path / "mobile" / "node_modules"
    coverage_dir = tmp_path / "coverage"
    _coverage(
        coverage_dir,
        [
            {
                "url": (root / "image-size" / "dist" / "types" / "jxl.js").as_uri(),
                "functions": [_function("", 1), _function("calculate", 0, 25)],
            },
            {
                "url": (root / "image-size" / "dist" / "types" / "png.js").as_uri(),
                "functions": [
                    _function("", 1),
                    _function("validate", 1, 25),
                    _function("calculate", 2, 50),
                ],
            },
            {
                "url": (root / "metro" / "src" / "index.js").as_uri(),
                "functions": [_function("", 1)],
            },
        ],
    )

    report = build_report("android", coverage_dir, root)

    assert report["platform"] == "android"
    assert report["coverage_file_count"] == 1
    assert report["packages"]["image-size"] == {
        "loaded_files": ["image-size/dist/types/jxl.js", "image-size/dist/types/png.js"],
        "executed_functions": [
            {"path": "image-size/dist/types/png.js", "name": "validate", "start_offset": 25},
            {"path": "image-size/dist/types/png.js", "name": "calculate", "start_offset": 50},
        ],
    }
    assert report["packages"]["braces"] == {"loaded_files": [], "executed_functions": []}


def test_report_accepts_nested_target_and_excludes_paths_outside_install(tmp_path: Path) -> None:
    root = tmp_path / "mobile" / "node_modules"
    coverage_dir = tmp_path / "coverage"
    _coverage(
        coverage_dir,
        [
            {
                "url": (root / "owner" / "node_modules" / "braces" / "index.js").as_uri(),
                "functions": [_function("", 1), _function("expand", 1, 30)],
            },
            {
                "url": (tmp_path / "other" / "node_modules" / "braces" / "index.js").as_uri(),
                "functions": [_function("", 1), _function("unsafe", 1, 30)],
            },
        ],
    )

    report = build_report("ios", coverage_dir, root)

    assert report["packages"]["braces"] == {
        "loaded_files": ["owner/node_modules/braces/index.js"],
        "executed_functions": [
            {"path": "owner/node_modules/braces/index.js", "name": "expand", "start_offset": 30}
        ],
    }


def test_report_requires_coverage_and_installed_tree_entries(tmp_path: Path) -> None:
    root = tmp_path / "mobile" / "node_modules"
    coverage_dir = tmp_path / "coverage"
    coverage_dir.mkdir()

    with pytest.raises(ValueError, match="no V8 coverage files"):
        build_report("android", coverage_dir, root)

    _coverage(
        coverage_dir,
        [{"url": (tmp_path / "elsewhere.js").as_uri(), "functions": [_function("", 1)]}],
    )
    with pytest.raises(ValueError, match="no covered files under"):
        build_report("android", coverage_dir, root)


@pytest.mark.parametrize("payload", ["{", "[]", '{"result": [{}]}'])
def test_report_rejects_malformed_coverage(tmp_path: Path, payload: str) -> None:
    root = tmp_path / "mobile" / "node_modules"
    coverage_dir = tmp_path / "coverage"
    coverage_dir.mkdir()
    (coverage_dir / "coverage-1.json").write_text(payload, encoding="utf-8")

    with pytest.raises((ValueError, TypeError), match="invalid V8 coverage"):
        build_report("android", coverage_dir, root)


def test_cli_writes_deterministic_summary(tmp_path: Path) -> None:
    root = tmp_path / "mobile" / "node_modules"
    coverage_dir = tmp_path / "coverage"
    output = tmp_path / "summary.json"
    _coverage(
        coverage_dir,
        [
            {
                "url": (root / "sprintf-js" / "src" / "sprintf.js").as_uri(),
                "functions": [_function("", 1), _function("sprintf", 1, 30)],
            }
        ],
    )

    assert main(
        [
            "--platform",
            "ios",
            "--coverage-dir",
            str(coverage_dir),
            "--node-modules-root",
            str(root),
            "--output",
            str(output),
        ]
    ) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["packages"]["sprintf-js"][
        "executed_functions"
    ] == [{"path": "sprintf-js/src/sprintf.js", "name": "sprintf", "start_offset": 30}]
