import subprocess

from app.config import get_settings
from ingestion.sources.phivolcs_earthquake import _parse_bulletin_table


def fetch_page_with_curl(url: str) -> str:
    result = subprocess.run(
        [
            "curl",
            "--insecure",
            "--location",
            "--fail",
            "--compressed",
            "--silent",
            "--show-error",
            url,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def main() -> None:
    settings = get_settings()
    print("Warning: curl certificate verification is disabled for this diagnostic script.")
    html = fetch_page_with_curl(settings.phivolcs_earthquake_feed_url)
    events = _parse_bulletin_table(html)

    print(f"Fetched {len(events)} events")
    for event in events[:5]:
        print(
            event.external_id,
            event.occurred_at.isoformat(),
            event.latitude,
            event.longitude,
            event.magnitude,
            event.place_name,
        )


if __name__ == "__main__":
    main()
