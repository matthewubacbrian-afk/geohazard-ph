from pathlib import Path

from app.schemas.static_layer import StaticFeature
from ingestion.sources.static_layers import parse_features, read_features


def import_gem_faults(
    path: str, *, source_url: str, license_name: str, dataset_version: str
) -> list[StaticFeature]:
    return parse_features(
        read_features(Path(path)),
        kind="faults",
        source="gem",
        source_url=source_url,
        license_name=license_name,
        dataset_version=dataset_version,
    )
