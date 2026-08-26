from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import joblib


@dataclass(frozen=True)
class ArtifactBundle:
    root: Path
    risk_profiles_json: Path
    metadata_json: Path
    region_features_csv: Path
    kmeans_model_path: Path
    scaler_path: Path
    rf_model_path: Path

    @classmethod
    def for_version(cls, root: Path, version: str) -> ArtifactBundle:
        version_dir = root / version
        version_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            root=version_dir,
            risk_profiles_json=version_dir / "risk_profiles.json",
            metadata_json=version_dir / "metadata.json",
            region_features_csv=version_dir / "region_features.csv",
            kmeans_model_path=version_dir / "kmeans_model.joblib",
            scaler_path=version_dir / "scaler.joblib",
            rf_model_path=version_dir / "random_forest_model.joblib",
        )


def save_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def save_risk_profiles(bundle: ArtifactBundle, profiles: list[dict[str, object]]) -> None:
    save_json(bundle.risk_profiles_json, profiles)


def save_metadata(bundle: ArtifactBundle, metadata: dict[str, object]) -> None:
    save_json(bundle.metadata_json, metadata)


def save_models(bundle: ArtifactBundle, kmeans_result, rf_result, scaler) -> None:
    joblib.dump(kmeans_result, bundle.kmeans_model_path)
    joblib.dump(scaler, bundle.scaler_path)
    joblib.dump(rf_result, bundle.rf_model_path)
