from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from ml.clean_merge import load_and_merge_sources
from ml.classifier import train_random_forest
from ml.clustering import assign_risk_labels, fit_kmeans
from ml.features import RegionFeatures, build_region_features
from ml.ingest_kaggle import DEFAULT_DATASETS, download_datasets
from ml.persist import ArtifactBundle, save_json, save_metadata, save_models, save_risk_profiles


@dataclass
class TrainingResult:
    profile_count: int
    artifact_dir: Path
    model_version: str


def run_training(
    phivolcs_paths: list[Path] | None = None,
    usgs_paths: list[Path] | None = None,
    artifact_dir: Path = Path("ml/model_artifacts"),
    artifact_version: str = "v1",
    download: bool = False,
    k_values: list[int] | None = None,
    random_state: int = 42,
) -> TrainingResult:
    if download:
        downloaded = download_datasets(Path("data/raw"))
        phivolcs_paths = []
        usgs_paths = []
        for ds in downloaded:
            csvs = list(ds.path.rglob("*.csv"))
            if "phivolcs" in ds.slug.lower():
                phivolcs_paths.extend(csvs)
            else:
                usgs_paths.extend(csvs)
    else:
        if phivolcs_paths is None:
            phivolcs_paths = list(Path("data/raw").rglob("*.csv")) if Path("data/raw").exists() else []
        if usgs_paths is None:
            usgs_paths = []

    merged_rows, source_reports = load_and_merge_sources(phivolcs_paths or [], usgs_paths or [])
    region_features_list = list(build_region_features(merged_rows).values())

    if len(region_features_list) < 2:
        raise ValueError("At least two usable regions are required for clustering.")

    labels = assign_risk_labels(region_features_list)
    kmeans_result = fit_kmeans(region_features_list, k_values=k_values or [3, 4, 5], random_state=random_state)

    rf_result = train_random_forest(region_features_list, labels, random_state=random_state)

    bundle = ArtifactBundle.for_version(artifact_dir, artifact_version)

    profiles = []
    for name in labels:
        cluster_id = kmeans_result.assignments.get(name, 0)
        pred = rf_result.predictions.get(name)
        profiles.append({
            "region_name": name,
            "cluster": cluster_id,
            "label": labels[name],
            "confidence": pred.confidence if pred else 0.0,
            "feature_importances": rf_result.feature_importances,
            "model_version": artifact_version,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dataset_snapshot": ", ".join(ds.title for ds in DEFAULT_DATASETS),
        })

    save_risk_profiles(bundle, profiles)
    save_metadata(bundle, {
        "model_version": artifact_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "region_count": len(region_features_list),
        "datasets": [{"slug": ds.slug, "title": ds.title, "license": ds.license_name} for ds in DEFAULT_DATASETS],
        "source_reports": {k: {"accepted": v.accepted_rows, "rejected": v.rejected_rows} for k, v in source_reports.items()},
    })
    save_models(bundle, kmeans_result.model, rf_result.classifier, kmeans_result.scaler)

    import pandas as pd
    feature_data = [[r.region_name, r.event_count, r.mean_magnitude, r.max_magnitude, r.mean_depth_km, r.event_density] for r in region_features_list]
    pd.DataFrame(feature_data, columns=["region_name", "event_count", "mean_magnitude", "max_magnitude", "mean_depth_km", "event_density"]).to_csv(bundle.region_features_csv, index=False)

    return TrainingResult(profile_count=len(profiles), artifact_dir=bundle.root, model_version=artifact_version)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Train seismic risk profile models")
    parser.add_argument("--artifact-version", default="v1", help="Version tag for artifacts")
    parser.add_argument("--artifact-dir", default="ml/model_artifacts", help="Output directory")
    parser.add_argument("--download", action="store_true", help="Download datasets from Kaggle")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    args = parser.parse_args(argv)

    try:
        result = run_training(
            artifact_dir=Path(args.artifact_dir),
            artifact_version=args.artifact_version,
            download=args.download,
            random_state=args.random_state,
        )
        print(f"Training complete: {result.profile_count} profiles written to {result.artifact_dir}")
        return 0
    except Exception as exc:
        print(f"Training failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
