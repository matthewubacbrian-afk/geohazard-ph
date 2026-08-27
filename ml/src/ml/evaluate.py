from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score


def evaluate_clustering(matrix: pd.DataFrame, cluster_ids: np.ndarray) -> dict[str, float | int]:
    n_clusters = len(set(cluster_ids))
    n_samples = len(cluster_ids)
    result: dict[str, float | int] = {"n_clusters": n_clusters, "n_samples": n_samples}

    if 1 < n_clusters < n_samples:
        result["silhouette_score"] = round(float(silhouette_score(matrix, cluster_ids)), 4)
    else:
        result["silhouette_score"] = 0.0

    for cluster_id in range(n_clusters):
        mask = cluster_ids == cluster_id
        result[f"cluster_{cluster_id}_size"] = int(mask.sum())
    return result


def evaluate_classifier(labels: dict[str, str], predictions: dict[str, str]) -> dict[str, object]:
    correct = sum(1 for name in labels if labels[name] == predictions.get(name))
    total = len(labels)
    result: dict[str, object] = {
        "accuracy": round(correct / total, 4) if total > 0 else 0.0,
        "correct": correct,
        "total": total,
    }

    all_labels = sorted(set(list(labels.values()) + list(predictions.values())))
    per_class: dict[str, dict[str, int]] = {}
    for label in all_labels:
        tp = sum(1 for name in labels if labels[name] == label and predictions.get(name) == label)
        fp = sum(1 for name in labels if labels[name] != label and predictions.get(name) == label)
        fn = sum(1 for name in labels if labels[name] == label and predictions.get(name) != label)
        per_class[label] = {"tp": tp, "fp": fp, "fn": fn}
    result["per_class"] = per_class
    return result
