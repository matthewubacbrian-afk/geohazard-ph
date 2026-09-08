import re
from datetime import UTC, datetime
from urllib.parse import urljoin, urlparse
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

from app.config import Settings, get_settings
from app.schemas.volcano import Volcano


class PhivolcsFetchError(Exception):
    """PHIVOLCS transport failed; never a valid empty feed."""


class PhivolcsParseError(Exception):
    """PHIVOLCS markup or data no longer matches the source contract."""


def parse_volcano_bulletins(html: str, source_url: str, retrieved_at: datetime) -> list[Volcano]:
    soup = BeautifulSoup(html, "html.parser")
    volcanoes: dict[str, Volcano] = {}
    try:
        for item in soup.select("span.scroll-item"):
            match = re.fullmatch(r"([A-Za-z -]+?)\s*-\s*(\d+)", item.get_text(" ", strip=True))
            if not match:
                raise PhivolcsParseError("Unrecognized alert status")
            name, level = match.groups()
            name = name.strip()
            if name in volcanoes:
                raise PhivolcsParseError("Duplicate alert status")
            volcanoes[name] = Volcano(
                id=f"phivolcs:{name.lower().replace(' ', '-')}",
                name=name,
                current_alert_level=int(level),
                source_url=source_url,
                retrieved_at=retrieved_at,
            )
        if not volcanoes:
            raise PhivolcsParseError("No alert status entries found")
        for link in soup.select('a[href*="/bulletin/activity-"]'):
            href = str(link.get("href", ""))
            if "lang=en" not in href:
                continue
            text = link.get_text(" ", strip=True)
            match = re.search(
                r"^(.+?) Volcano Summary of 24Hr Observation "
                r"(\d{2} [A-Za-z]+ \d{4} \d{1,2}:\d{2} [AP]M)",
                text,
            )
            if not match or match[1] not in volcanoes:
                raise PhivolcsParseError("Unrecognized bulletin heading")
            url = urljoin(source_url, href)
            if urlparse(url).netloc != urlparse(source_url).netloc:
                raise PhivolcsParseError("Unexpected bulletin host")
            date = (
                datetime.strptime(match[2], "%d %B %Y %I:%M %p")
                .replace(tzinfo=ZoneInfo("Asia/Manila"))
                .astimezone(UTC)
            )
            row = volcanoes[match[1]]
            if row.bulletin_at is None or date > row.bulletin_at:
                volcanoes[row.name] = Volcano.model_validate(
                    {**row.model_dump(), "bulletin_at": date, "bulletin_url": url}
                )
    except ValueError as exc:
        raise PhivolcsParseError("Invalid volcano bulletin data") from exc
    return sorted(volcanoes.values(), key=lambda row: row.name)


def fetch_volcano_bulletins(settings: Settings) -> list[Volcano]:
    try:
        response = requests.get(
            settings.phivolcs_volcano_url,
            timeout=settings.phivolcs_volcano_timeout_seconds,
            headers={"User-Agent": "GeoHazardPH/0.1 (public bulletin reader)"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise PhivolcsFetchError("PHIVOLCS volcano source unavailable") from exc
    return parse_volcano_bulletins(response.text, settings.phivolcs_volcano_url, datetime.now(UTC))


def fetch_latest_volcano_bulletins() -> list[Volcano]:
    return fetch_volcano_bulletins(get_settings())
