import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from ml import ingest_kaggle
from ml.ingest_kaggle import (
    KaggleCredentialError,
    KaggleDataset,
    _kagglehub_download,
    _read_dataset_version,
    download_datasets,
)


def test_download_datasets_loads_credentials_from_repository_dotenv(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(ingest_kaggle, "REPOSITORY_ROOT", tmp_path)
    (tmp_path / ".env").write_text(
        "# Kaggle credentials\nKAGGLE_USERNAME='dotenv-user'\nKAGGLE_KEY=\"dotenv-key\"\n",
        encoding="utf-8",
    )
    calls: list[tuple[str | None, str | None]] = []

    def fake_downloader(slug: str, output_dir: Path) -> tuple[str, int]:
        calls.append((os.getenv("KAGGLE_USERNAME"), os.getenv("KAGGLE_KEY")))
        return str(output_dir), 7

    downloaded = download_datasets(
        tmp_path / "raw",
        datasets=[KaggleDataset("owner/example", "Example", "License")],
        downloader=fake_downloader,
    )

    assert calls == [("dotenv-user", "dotenv-key")]
    assert downloaded[0].version == 7


def test_download_datasets_preserves_nonempty_environment_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("KAGGLE_USERNAME", "shell-user")
    monkeypatch.setenv("KAGGLE_KEY", "")
    monkeypatch.setattr(ingest_kaggle, "REPOSITORY_ROOT", tmp_path)
    (tmp_path / ".env").write_text(
        "KAGGLE_USERNAME=dotenv-user\nKAGGLE_KEY=dotenv-key\n", encoding="utf-8"
    )
    calls: list[tuple[str | None, str | None]] = []

    def fake_downloader(slug: str, output_dir: Path) -> tuple[str, int]:
        calls.append((os.getenv("KAGGLE_USERNAME"), os.getenv("KAGGLE_KEY")))
        return str(output_dir), 7

    download_datasets(
        tmp_path / "raw",
        datasets=[KaggleDataset("owner/example", "Example", "License")],
        downloader=fake_downloader,
    )

    assert calls == [("shell-user", "dotenv-key")]


def test_download_datasets_ignores_unrelated_and_blank_dotenv_values(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(ingest_kaggle, "REPOSITORY_ROOT", tmp_path)
    (tmp_path / ".env").write_text(
        "OTHER_SECRET=unrelated\nKAGGLE_USERNAME=\nKAGGLE_KEY=\nmalformed\n", encoding="utf-8"
    )
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with pytest.raises(KaggleCredentialError):
        download_datasets(tmp_path / "raw", datasets=[])

    assert os.getenv("OTHER_SECRET") is None


def test_download_datasets_missing_dotenv_keeps_kaggle_config_fallback(
    monkeypatch, tmp_path
):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(ingest_kaggle, "REPOSITORY_ROOT", tmp_path / "missing-root")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    config = tmp_path / ".kaggle" / "kaggle.json"
    config.parent.mkdir()
    config.touch()

    assert download_datasets(tmp_path / "raw", datasets=[]) == []


@pytest.mark.parametrize("contents", [b"KAGGLE_USERNAME=\xff", None])
def test_download_datasets_reports_dotenv_read_errors_safely(
    monkeypatch, tmp_path, contents
):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(ingest_kaggle, "REPOSITORY_ROOT", tmp_path)
    env_file = tmp_path / ".env"
    if contents is not None:
        env_file.write_bytes(contents)
    else:
        env_file.mkdir()

    with pytest.raises(KaggleCredentialError) as exc:
        download_datasets(tmp_path / "raw", datasets=[])

    assert str(exc.value) == "Could not read Kaggle credentials from the repository .env file."
    assert "\xff" not in str(exc.value)


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
