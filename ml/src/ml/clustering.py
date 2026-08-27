from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ml.features import RegionFeatures

FEATURE_COLUMNS = ["event_count", "mean_magnitude", "max_magnitude", "mean_depth_km", "event_density"]

RISK_LABELS = ["Low", "Moderate", "High", "Very High"]


@dataclass(frozen=True)
class KSelection:
    k: int
    silhouette_score: float


@dataclass(frozen=True)
class KMeansResult:
    assignments: dict[str, int]
    risk_labels: dict[str, str]
    model: KMeans
    scaler: StandardScaler
    region_names: list[str]


def feature_matrix(rows: list[RegionFeatures]) -> tuple[list[str], pd.DataFrame]:
    region_names = [r.region_name for r in rows]
    data = [[getattr(r, col) for col in FEATURE_COLUMNS] for r in rows]
    return region_names, pd.DataFrame(data, columns=FEATURE_COLUMNS)


def choose_k(rows: list[RegionFeatures], k_values: tuple[int, ...] | list[int] = (3, 4, 5)) -> KSelection:
    _, matrix = feature_matrix(rows)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)

    valid_ks = [k for k in k_values if 2 <= k < len(rows)]
    if not valid_ks:
        fallback_k = min(2, len(rows))
        return KSelection(k=fallback_k, silhouette_score=0.0)

    best_k = valid_ks[0]
    best_score = -1.0
    for k in valid_ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(scaled)
        if len(set(labels)) < 2:
            continue
        score = silhouette_score(scaled, labels)
        if score > best_score:
            best_score = score
            best_k = k

    return KSelection(k=best_k, silhouette_score=round(best_score, 4))


def _cluster_severity_order(matrix: pd.DataFrame, labels: np.ndarray, n_clusters: int) -> dict[int, int]:
    centroids = []
    for cluster_id in range(n_clusters):
        mask = labels == cluster_id
        centroids.append(matrix.loc[mask].mean(axis=0).values)

    centroid_df = pd.DataFrame(centroids, columns=FEATURE_COLUMNS)
    centroid_df["cluster"] = range(n_clusters)
    centroid_df["severity"] = (
        centroid_df["event_count"]
        + centroid_df["mean_magnitude"]
        + centroid_df["max_magnitude"]
        + centroid_df["event_density"]
    )
    centroid_df = centroid_df.sort_values("severity").reset_index(drop=True)
    return {int(row["cluster"]): int(index) for index, row in centroid_df.iterrows()}


def _labels_for_clusters(assignments: dict[str, int], severity_map: dict[int, int]) -> dict[str, str]:
    available_labels = RISK_LABELS[: max(severity_map.values(), default=0) + 1]
    labels: dict[str, str] = {}
    for region_name, cluster_id in assignments.items():
        severity_idx = severity_map[cluster_id]
        labels[region_name] = available_labels[min(severity_idx, len(available_labels) - 1)]
    return labels


def fit_kmeans(
    rows: list[RegionFeatures],
    k_values: tuple[int, ...] | list[int] = (3, 4, 5),
    random_state: int = 42,
) -> KMeansResult:
    region_names, matrix = feature_matrix(rows)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)

    selection = choose_k(rows, k_values)
    km = KMeans(n_clusters=selection.k, n_init=10, random_state=random_state)
    cluster_ids = km.fit_predict(scaled)

    assignments = {name: int(label) for name, label in zip(region_names, cluster_ids)}
    severity_map = _cluster_severity_order(matrix, cluster_ids, km.n_clusters)
    risk_labels = _labels_for_clusters(assignments, severity_map)
    return KMeansResult(
        assignments=assignments,
        risk_labels=risk_labels,
        model=km,
        scaler=scaler,
        region_names=region_names,
    )


def _rank_severity(rows: list[RegionFeatures]) -> dict[str, float]:
    _, matrix = feature_matrix(rows)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(matrix)
    severity_cols = [
        FEATURE_COLUMNS.index(column)
        for column in ["event_count", "mean_magnitude", "max_magnitude", "event_density"]
    ]
    scores = scaled[:, severity_cols].mean(axis=1)
    ranked = sorted(zip([r.region_name for r in rows], scores), key=lambda item: item[1])
    n = len(ranked)
    return {name: rank / max(n - 1, 1) for rank, (name, _) in enumerate(ranked)}


def assign_risk_labels(rows: list[RegionFeatures]) -> dict[str, str]:
    if len(rows) < 2:
        return {rows[0].region_name: "Low"} if rows else {}

    n_labels = min(len(RISK_LABELS), len(rows))
    available_labels = RISK_LABELS[:n_labels]

    if len(rows) <= len(RISK_LABELS):
        severity = _rank_severity(rows)
        labels: dict[str, str] = {}
        for name, score in severity.items():
            idx = int(round(score * (len(available_labels) - 1)))
            labels[name] = available_labels[min(idx, len(available_labels) - 1)]
        return labels

    max_k = len(rows) - 1
    k_values = [k for k in range(2, n_labels + 1) if k <= max_k]
    return fit_kmeans(rows, k_values=k_values, random_state=42).risk_labels
