import os
from pathlib import Path

import pytest

from ml.ingest_kaggle import KaggleDataset, KaggleCredentialError, download_datasets


def test_download_datasets_requires_credentials_when_config_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("KAGGLE_USERNAME", raising=False)
    monkeypatch.delenv("KAGGLE_KEY", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    with pytest.raises(KaggleCredentialError) as exc:
        download_datasets(tmp_path / "raw", datasets=[])

    assert "KAGGLE_USERNAME" in str(exc.value)
    assert "kaggle.json" in str(exc.value)


def test_download_datasets_calls_kaggle_api(monkeypatch, tmp_path):
    calls: list[tuple[str, str]] = []
    monkeypatch.setenv("KAGGLE_USERNAME", "user")
    monkeypatch.setenv("KAGGLE_KEY", "key")

    class FakeApi:
        def authenticate(self):
            calls.append(("authenticate", ""))

        def dataset_download_files(self, dataset, path, unzip):
            calls.append((dataset, str(path)))
            assert unzip is True

    datasets = [KaggleDataset("owner/example", "Example", "License")]

    downloaded = download_datasets(tmp_path / "raw", datasets=datasets, api=FakeApi())

    assert downloaded[0].slug == "owner/example"
    assert calls == [("authenticate", ""), ("owner/example", os.fspath(tmp_path / "raw" / "owner_example"))]
