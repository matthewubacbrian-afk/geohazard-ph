from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


PHIVOLCS_DATASET = "bwandowando/philippine-earthquakes-from-phivolcs"
USGS_DATASET = "bwandowando/philippine-earthquakes-1900-2025-from-usgs"


class KaggleCredentialError(RuntimeError):
    pass


@dataclass(frozen=True)
class KaggleDataset:
    slug: str
    title: str
    license_name: str


@dataclass(frozen=True)
class DownloadedDataset:
    slug: str
    title: str
    license_name: str
    path: Path


DEFAULT_DATASETS = (
    KaggleDataset(PHIVOLCS_DATASET, "Philippine Earthquakes from PHIVOLCS", "CC0: Public Domain"),
    KaggleDataset(USGS_DATASET, "Philippine Earthquakes 1900-2026 from USGS", "Apache 2.0"),
)


def _has_credentials() -> bool:
    env_credentials = bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))
    config_file = Path.home() / ".kaggle" / "kaggle.json"
    return env_credentials or config_file.exists()


def _load_default_api():
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError as exc:
        raise KaggleCredentialError("Install the kaggle package before downloading datasets.") from exc
    return KaggleApi()


def download_datasets(
    raw_dir: Path,
    datasets: tuple[KaggleDataset, ...] | list[KaggleDataset] = DEFAULT_DATASETS,
    api=None,
) -> list[DownloadedDataset]:
    if not _has_credentials():
        raise KaggleCredentialError(
            "Kaggle credentials are required. Set KAGGLE_USERNAME and KAGGLE_KEY, "
            "or create ~/.kaggle/kaggle.json."
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    kaggle_api = api or _load_default_api()
    kaggle_api.authenticate()

    downloaded: list[DownloadedDataset] = []
    for dataset in datasets:
        dataset_dir = raw_dir / dataset.slug.replace("/", "_")
        dataset_dir.mkdir(parents=True, exist_ok=True)
        kaggle_api.dataset_download_files(dataset.slug, path=dataset_dir, unzip=True)
        downloaded.append(
            DownloadedDataset(dataset.slug, dataset.title, dataset.license_name, dataset_dir)
        )
    return downloaded
