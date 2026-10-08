import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ml.ingest_kaggle import (
    KaggleCredentialError,
    KaggleDataset,
    _kagglehub_download,
    _read_dataset_version,
    download_datasets,
)


def test_download_datasets_requires_credentials_when_config_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with pytest.raises(KaggleCredentialError) as exc:
        download_datasets(tmp_path / "raw", datasets=[])

    assert "KAGGLE_USERNAME" in str(exc.value)
    assert "kaggle.json" in str(exc.value)


def test_download_datasets_calls_downloader(monkeypatch, tmp_path):
    calls: list[tuple[str, str]] = []
    monkeypatch.setenv("KAGGLE_USERNAME", "user")
    monkeypatch.setenv("KAGGLE_KEY", "key")

    def fake_downloader(slug: str, output_dir: Path) -> tuple[str, int]:
        calls.append((slug, str(output_dir)))
        return str(output_dir), 7

    datasets = [KaggleDataset("owner/example", "Example", "License")]

    downloaded = download_datasets(
        tmp_path / "raw", datasets=datasets, downloader=fake_downloader
    )

    assert downloaded[0].slug == "owner/example"
    assert downloaded[0].version == 7
    assert downloaded[0].path == tmp_path / "raw" / "owner_example"
    assert calls == [("owner/example", os.fspath(tmp_path / "raw" / "owner_example"))]


def test_kagglehub_download_forces_output_dir_and_reads_version(monkeypatch, tmp_path):
    calls: list[tuple[str, str, bool]] = []
    downloaded_path = tmp_path / "downloaded"

    def fake_dataset_download(slug: str, *, output_dir: str, force_download: bool) -> str:
        calls.append((slug, output_dir, force_download))
        marker = Path(output_dir) / ".complete" / "datasets" / "owner" / "example" / "7"
        marker.mkdir(parents=True)
        (marker / "bundle.complete").touch()
        downloaded_path.mkdir()
        return str(downloaded_path)

    monkeypatch.setitem(
        sys.modules,
        "kagglehub",
        SimpleNamespace(dataset_download=fake_dataset_download),
    )

    path, version = _kagglehub_download("owner/example", tmp_path)

    assert path == os.fspath(downloaded_path)
    assert version == 7
    assert calls == [("owner/example", os.fspath(tmp_path), True)]


def test_read_dataset_version_returns_marker_version(tmp_path):
    marker = tmp_path / ".complete" / "datasets" / "owner" / "example" / "7"
    marker.mkdir(parents=True)
    (marker / "bundle.complete").touch()

    assert _read_dataset_version(tmp_path, "owner/example") == 7


def test_read_dataset_version_returns_highest_when_markers_accumulate(tmp_path):
    for version in (3, 11):
        marker = tmp_path / ".complete" / "datasets" / "owner" / "example" / str(version)
        marker.mkdir(parents=True)
        (marker / "bundle.complete").touch()

    assert _read_dataset_version(tmp_path, "owner/example") == 11
