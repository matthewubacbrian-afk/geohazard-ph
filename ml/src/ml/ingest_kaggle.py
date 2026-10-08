from __future__ import annotations

import os
from collections.abc import Callable
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
    version: int


DEFAULT_DATASETS = (
    KaggleDataset(PHIVOLCS_DATASET, "Philippine Earthquakes from PHIVOLCS", "CC0: Public Domain"),
    KaggleDataset(USGS_DATASET, "Philippine Earthquakes 1900-2026 from USGS", "Apache 2.0"),
)


def _has_credentials() -> bool:
    env_credentials = bool(os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"))
    config_file = Path.home() / ".kaggle" / "kaggle.json"
    return env_credentials or config_file.exists()


def _read_dataset_version(output_dir: Path, slug: str) -> int:
    owner, dataset_slug = slug.split("/", maxsplit=1)
    marker_root = output_dir / ".complete" / "datasets" / owner / dataset_slug
    versions = (
        [
            int(version_dir.name)
            for version_dir in marker_root.iterdir()
            if version_dir.is_dir() and (version_dir / "bundle.complete").exists()
        ]
        if marker_root.exists()
        else []
    )

    if not versions:
        raise RuntimeError(f"Could not determine Kaggle dataset version for {slug}.")

    return max(versions)


def _kagglehub_download(slug: str, output_dir: Path) -> tuple[str, int]:
    try:
        import kagglehub
    except ImportError as exc:
        raise KaggleCredentialError(
            "Install the kagglehub package before downloading datasets."
        ) from exc

    path = kagglehub.dataset_download(slug, output_dir=str(output_dir), force_download=True)
    return str(Path(path)), _read_dataset_version(output_dir, slug)


def download_datasets(
    raw_dir: Path,
    datasets: tuple[KaggleDataset, ...] | list[KaggleDataset] = DEFAULT_DATASETS,
    downloader: Callable[[str, Path], tuple[str, int]] | None = None,
) -> list[DownloadedDataset]:
    if not _has_credentials():
        raise KaggleCredentialError(
            "Kaggle credentials are required. Set KAGGLE_USERNAME and KAGGLE_KEY, "
            "or create ~/.kaggle/kaggle.json."
        )

    raw_dir.mkdir(parents=True, exist_ok=True)
    dl = downloader or _kagglehub_download

    downloaded: list[DownloadedDataset] = []
    for dataset in datasets:
        dataset_dir = raw_dir / dataset.slug.replace("/", "_")
        dataset_dir.mkdir(parents=True, exist_ok=True)
        path, version = dl(dataset.slug, dataset_dir)
        downloaded.append(
            DownloadedDataset(
                dataset.slug,
                dataset.title,
                dataset.license_name,
                Path(path),
                version,
            )
        )
    return downloaded
