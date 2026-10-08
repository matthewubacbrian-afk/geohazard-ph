import numpy as np
import pandas as pd

from ml.clustering import (
    FEATURE_COLUMNS,
    RISK_LABELS,
    _cluster_severity_order,
    assign_risk_labels,
    choose_k,
    fit_kmeans,
)
from ml.features import RegionFeatures


def _rows():
    return [
        RegionFeatures("Palawan", 2, 3.4, 3.6, 22.0, 0.2),
        RegionFeatures("Bicol Region", 8, 4.9, 5.1, 27.5, 0.6),
        RegionFeatures("Eastern Visayas", 12, 6.0, 6.2, 39.5, 0.8),
        RegionFeatures("Davao Region", 10, 5.8, 6.0, 30.0, 0.7),
    ]


def test_assign_risk_labels_orders_clusters_by_severity():
    labels = assign_risk_labels(_rows())

    assert labels["Palawan"] == "Low"
    assert labels["Bicol Region"] in {"Moderate", "High"}
    assert labels["Eastern Visayas"] in {"High", "Very High"}


def test_choose_k_returns_valid_silhouette_choice():
    selected = choose_k(_rows(), k_values=[2, 3])

    assert selected.k in {2, 3}
    assert selected.silhouette_score > -1


def test_fit_kmeans_returns_region_assignments_and_model():
    result = fit_kmeans(_rows(), k_values=[2, 3], random_state=7)

    assert len(result.assignments) == 4
    assert result.model.n_clusters in {2, 3}
    assert result.scaler is not None


def test_fit_kmeans_returns_labels_from_same_cluster_assignments():
    result = fit_kmeans(_rows(), k_values=[2], random_state=7)

    assert set(result.risk_labels) == set(result.assignments)
    for region_name, cluster_id in result.assignments.items():
        same_cluster_regions = [
            other_region
            for other_region, other_cluster_id in result.assignments.items()
            if other_cluster_id == cluster_id
        ]
        labels = {result.risk_labels[other_region] for other_region in same_cluster_regions}
        assert len(labels) == 1


def test_fit_kmeans_pins_labels_by_ascending_mean_magnitude():
    result = fit_kmeans(_rows(), k_values=[3], random_state=42)
    labels = result.risk_labels

    assert labels["Palawan"] == "Low"
    assert RISK_LABELS.index(labels["Eastern Visayas"]) > RISK_LABELS.index(labels["Palawan"])


def test_cluster_severity_order_ignores_cluster_id_numbering():
    matrix = pd.DataFrame(
        [
            [2, 3.4, 3.6, 22.0, 0.2],
            [3, 3.6, 3.8, 23.0, 0.3],
            [12, 6.0, 6.2, 39.5, 0.8],
            [10, 5.8, 6.0, 30.0, 0.7],
        ],
        columns=FEATURE_COLUMNS,
    )

    severity_map = _cluster_severity_order(matrix, np.array([1, 1, 0, 0]), 2)

    assert severity_map[1] == 0
    assert severity_map[0] == 1
