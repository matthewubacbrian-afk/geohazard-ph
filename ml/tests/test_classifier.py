from ml.classifier import majority_label, train_random_forest
from ml.features import RegionFeatures


def test_majority_label_returns_most_common_label():
    assert majority_label(["High", "Low", "High", "Moderate"]) == "High"


def test_train_random_forest_returns_confidence_and_feature_importances():
    rows = [
        RegionFeatures("Palawan", 2, 3.4, 3.6, 22.0, 0.2),
        RegionFeatures("Bicol Region", 8, 4.9, 5.1, 27.5, 0.6),
        RegionFeatures("Eastern Visayas", 12, 6.0, 6.2, 39.5, 0.8),
        RegionFeatures("Davao Region", 10, 5.8, 6.0, 30.0, 0.7),
    ]
    labels = {
        "Palawan": "Low",
        "Bicol Region": "Moderate",
        "Eastern Visayas": "High",
        "Davao Region": "High",
    }

    result = train_random_forest(rows, labels, random_state=7)

    assert set(result.predictions) == set(labels)
    assert all(0.0 <= prediction.confidence <= 1.0 for prediction in result.predictions.values())
    assert "event_count" in result.feature_importances
