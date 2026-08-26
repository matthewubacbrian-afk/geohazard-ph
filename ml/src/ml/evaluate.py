from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score


def evaluate_clustering(matrix: pd.DataFrame, cluster_ids: np.ndarray) -> dict[str, float | int]:
    n_clusters = len(set(cluster_ids))
    result: dict[str, float | int] = {"n_clusters": n_clusters, "n_samples": len(cluster_ids)}

    if n_clusters >= 2 and len(cluster_ids) >= n_clusters:
        result["silhouette_score"] = round(float(silhouette_score(matrix, cluster_ids)), 4)
    else:
        result["silhouette_score"] = 0.0

    for c in range(n_clusters):
        mask = cluster_ids == c
        result[f"cluster_{c}_size"] = int(mask.sum())
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
    for lbl in all_labels:
        tp = sum(1 for n in labels if labels[n] == lbl and predictions.get(n) == lbl)
        fp = sum(1 for n in labels if labels[n] != lbl and predictions.get(n) == lbl)
        fn = sum(1 for n in labels if labels[n] == lbl and predictions.get(n) != lbl)
        per_class[lbl] = {"tp": tp, "fp": fp, "fn": fn}
    result["per_class"] = per_class
    return result
