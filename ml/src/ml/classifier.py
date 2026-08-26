from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from ml.clustering import FEATURE_COLUMNS
from ml.features import RegionFeatures


@dataclass(frozen=True)
class Prediction:
    label: str
    confidence: float


@dataclass(frozen=True)
class RandomForestResult:
    predictions: dict[str, Prediction]
    feature_importances: dict[str, float]
    classifier: RandomForestClassifier


def majority_label(labels: list[str]) -> str:
    return Counter(labels).most_common(1)[0][0]


def train_random_forest(
    rows: list[RegionFeatures],
    labels: dict[str, str],
    random_state: int = 42,
) -> RandomForestResult:
    region_names = [r.region_name for r in rows]
    X = np.array([[getattr(r, col) for col in FEATURE_COLUMNS] for r in rows])
    y = np.array([labels[name] for name in region_names])

    clf = RandomForestClassifier(n_estimators=100, random_state=random_state, class_weight="balanced")
    clf.fit(X, y)

    predictions: dict[str, Prediction] = {}
    probas = clf.predict_proba(X)
    classes = clf.classes_

    for i, name in enumerate(region_names):
        pred_label = clf.predict(X[i : i + 1])[0]
        confidence = float(probas[i].max())
        predictions[name] = Prediction(label=pred_label, confidence=round(confidence, 4))

    importances = dict(zip(FEATURE_COLUMNS, [round(float(v), 4) for v in clf.feature_importances_]))

    return RandomForestResult(predictions=predictions, feature_importances=importances, classifier=clf)
