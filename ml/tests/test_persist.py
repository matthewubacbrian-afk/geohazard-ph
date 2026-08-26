import json

from ml.persist import ArtifactBundle, save_risk_profiles


def test_save_risk_profiles_writes_json_export(tmp_path):
    bundle = ArtifactBundle.for_version(tmp_path, "v-test")
    profiles = [
        {
            "region_name": "Bicol Region",
            "cluster": 1,
            "label": "High",
            "confidence": 0.82,
            "feature_importances": {"event_count": 0.4},
            "model_version": "v-test",
        }
    ]

    save_risk_profiles(bundle, profiles)

    saved = json.loads(bundle.risk_profiles_json.read_text(encoding="utf-8"))
    assert saved[0]["region_name"] == "Bicol Region"
