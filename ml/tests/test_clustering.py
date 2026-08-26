from ml.clustering import assign_risk_labels, choose_k, fit_kmeans
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
