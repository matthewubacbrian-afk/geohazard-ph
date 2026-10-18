"""Check that staging has an export-free default and an explicit reviewed mode."""

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT_TARGET = "/data/risk_profiles.json"


def render(*files: str, export_file: str | None = None) -> dict:
    environment = os.environ.copy()
    environment.pop("RISK_PROFILE_EXPORT_FILE", None)
    if export_file is not None:
        environment["RISK_PROFILE_EXPORT_FILE"] = export_file
    command = ["docker", "compose", "--env-file", ".env.staging.example"]
    for file in files:
        command.extend(("-f", file))
    command.extend(("config", "--no-normalize", "--format", "json"))
    result = subprocess.run(
        command, cwd=ROOT, env=environment, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)


def main() -> None:
    base = render("compose.staging.yml")
    api = base["services"]["api"]
    assert api["environment"]["RISK_PROFILE_EXPORT_PATH"] == EXPORT_TARGET
    assert not api.get("volumes"), "base staging mode must not mount a profile export"

    try:
        render("compose.staging.yml", "compose.staging.profile.yml")
    except RuntimeError as exc:
        assert "RISK_PROFILE_EXPORT_FILE" in str(exc)
    else:
        raise AssertionError("reviewed mode must require an explicit export path")

    reviewed = render(
        "compose.staging.yml",
        "compose.staging.profile.yml",
        export_file="./deploy-data/verification.json",
    )
    api = reviewed["services"]["api"]
    assert api["environment"]["RISK_PROFILE_EXPORT_PATH"] == EXPORT_TARGET
    volumes = api.get("volumes", [])
    assert len(volumes) == 1, "reviewed mode must mount exactly one profile export"
    volume = volumes[0]
    assert volume["type"] == "bind"
    assert volume["target"] == EXPORT_TARGET
    assert volume["read_only"] is True
    assert volume["bind"]["create_host_path"] is False
    assert Path(volume["source"]).name == "verification.json"
    print("Staging held and reviewed Compose modes verified.")


if __name__ == "__main__":
    main()
