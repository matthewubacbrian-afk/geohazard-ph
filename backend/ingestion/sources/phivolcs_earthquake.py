import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup

from app.config import Settings
from app.schemas.hazard_event import HazardEvent

PH_TZ = timezone(timedelta(hours=8))  # Philippine Standard Time, UTC+8


class PhivolcsFetchError(RuntimeError):
    """Raised when the PHIVOLCS feed cannot be fetched or parsed."""


def fetch_recent_events(
    settings: Settings, *, session: requests.Session | None = None
) -> list[HazardEvent]:
    http = session or requests
    try:
        response = http.get(settings.phivolcs_earthquake_feed_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        raise PhivolcsFetchError(f"PHIVOLCS feed request failed: {exc}") from exc

    try:
        return _parse_bulletin_table(response.text)
    except PhivolcsFetchError:
        raise
    except Exception as exc:
        raise PhivolcsFetchError(f"PHIVOLCS feed parsing failed: {exc}") from exc


def _parse_bulletin_table(html: str) -> list[HazardEvent]:
    soup = BeautifulSoup(html, "html.parser")

    data_table = next(
        (t for t in soup.find_all("table") if t.find("th") and "Latitude" in t.get_text()),
        None,
    )
    if data_table is None:
        raise PhivolcsFetchError("could not locate the earthquake data table")

    events: list[HazardEvent] = []
    for row in data_table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) != 6:
            continue  # header row or stray formatting rows
        try:
            events.append(_parse_row(cells))
        except (TypeError, ValueError) as exc:
            raise PhivolcsFetchError(f"unexpected row format: {exc}") from exc
    return events


def _parse_row(cells) -> HazardEvent:
    date_cell, lat_cell, lon_cell, depth_cell, mag_cell, loc_cell = cells

    occurred_at = _parse_datetime(date_cell.get_text(" ", strip=True))
    external_id = _extract_bulletin_id(date_cell)

    latitude = float(lat_cell.get_text(strip=True))
    longitude = float(lon_cell.get_text(strip=True))
    depth_km = float(depth_cell.get_text(strip=True))
    magnitude = float(mag_cell.get_text(strip=True))
    place_name = re.sub(r"\s+", " ", loc_cell.get_text(" ", strip=True)).strip()

    return HazardEvent(
        id=f"phivolcs-{external_id}" if external_id else f"phivolcs-{occurred_at.isoformat()}",
        hazard_type="earthquake",
        source="phivolcs",
        external_id=external_id,
        magnitude=magnitude,
        depth_km=depth_km,
        latitude=latitude,
        longitude=longitude,
        place_name=place_name,
        occurred_at=occurred_at,
    )


def _extract_bulletin_id(date_cell) -> str | None:
    link = date_cell.find("a")
    if not link or not link.get("href"):
        return None
    href = link["href"].replace("\\", "/")
    stem = href.rsplit("/", 1)[-1].removesuffix(".html")
    return stem or None


def _parse_datetime(value: str) -> datetime:
    normalized = re.sub(r"\s+", " ", value.strip())
    local_dt = datetime.strptime(normalized, "%d %B %Y - %I:%M %p")
    return local_dt.replace(tzinfo=PH_TZ).astimezone(timezone.utc)