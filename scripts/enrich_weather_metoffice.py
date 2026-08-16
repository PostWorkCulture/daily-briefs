from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/London")
NOW = datetime.now(TZ)

# Home weather must come from the Met Office only.
HOME_POSTCODE = "KT8 2LE"
HOME_LABEL = "West Molesey, KT8 2LE"
MET_LOCATION = "Hampton W Wks"
MET_URL = "https://weather.metoffice.gov.uk/forecast/gcpsrrk8m?nearestTo=West+Molesey+%28Surrey%29"
UA = {"User-Agent": "Mozilla/5.0 DailyBriefs/4.0 (+https://github.com/PostWorkCulture/daily-briefs)"}

CONDITIONS = [
    "Thunderstorms", "Thunderstorm", "Heavy snow", "Light snow", "Snow",
    "Heavy rain", "Light rain", "Rain", "Heavy showers", "Light showers", "Showers",
    "Heavy drizzle", "Light drizzle", "Drizzle", "Fog", "Mist",
    "Overcast", "Cloudy", "Partly cloudy", "Sunny intervals", "Sunny",
    "Clear night", "Clear",
]


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def pct(value: str | None) -> int | None:
    if not value:
        return None
    if value.startswith("<"):
        return 4
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None


def condition_from(text: str) -> str | None:
    lower = text.lower()
    for condition in CONDITIONS:
        if condition.lower() in lower:
            return condition
    return None


def parse_current(text: str) -> tuple[int | None, str | None, int | None]:
    # Met Office summary block: Next hour / 18°C / Cloudy / ... / Rain <5%
    m = re.search(
        r"Next hour\s+(-?\d+)°C(?:\s+\d+ degrees Celsius)?\s+(.+?)\s+Feels like.*?Rain\s+(<5%|\d+%)",
        text,
        re.I | re.S,
    )
    if m:
        block_condition = condition_from(m.group(2))
        return int(m.group(1)), block_condition, pct(m.group(3))
    return None, None, None


def daily_blocks(soup: BeautifulSoup) -> list[dict]:
    # Forecast-day cards have headings such as “Today” or “Mon 17 Aug”.
    headings = []
    for h in soup.find_all(["h2", "h3", "h4"]):
        label = clean(h.get_text(" ", strip=True))
        if label == "Today" or re.match(r"^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)(day)?(?:\s+\d{1,2}\s+[A-Za-z]+)?$", label, re.I):
            headings.append(h)

    out = []
    seen_dates = set()
    sequence_date = NOW.date()
    for idx, h in enumerate(headings):
        container = h.parent
        block = clean(container.get_text(" ", strip=True)) if container else clean(h.get_text(" ", strip=True))
        # Expand one level if the immediate wrapper does not contain temperatures.
        if "Maximum daytime temperature" not in block and container and container.parent:
            block = clean(container.parent.get_text(" ", strip=True))

        temps = re.search(
            r"(-?\d+)°\s*Maximum daytime temperature:.*?(-?\d+)°\s*Minimum nighttime temperature",
            block,
            re.I | re.S,
        )
        if not temps:
            continue

        label = clean(h.get_text(" ", strip=True))
        if label.lower() == "today":
            day = NOW.date()
        else:
            dm = re.search(r"(\d{1,2})\s+([A-Za-z]+)", label)
            if dm:
                try:
                    candidate = datetime.strptime(f"{dm.group(1)} {dm.group(2)} {NOW.year}", "%d %B %Y").date()
                    if candidate < NOW.date() - timedelta(days=20):
                        candidate = candidate.replace(year=NOW.year + 1)
                    day = candidate
                except Exception:
                    day = sequence_date + timedelta(days=idx)
            else:
                day = sequence_date + timedelta(days=idx)

        if day.isoformat() in seen_dates:
            continue
        seen_dates.add(day.isoformat())

        condition = condition_from(block) or "Forecast"
        rain_match = re.search(r"Rain\s+(<5%|\d+%)", block, re.I)
        out.append({
            "date": day.isoformat(),
            "high": int(temps.group(1)),
            "low": int(temps.group(2)),
            "summary": condition,
            "condition": condition,
            "rainChance": pct(rain_match.group(1)) if rain_match else None,
            "source": "Met Office",
        })
        if len(out) >= 7:
            break
    return out


def summary_fallback(text: str) -> list[dict]:
    # Fallback for the compact server-rendered summary used by the Met Office page.
    pattern = re.compile(
        r"(?:^|\s)(Today|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(-?\d+)°C.*?\s+(Sunny intervals|Sunny|Partly cloudy|Cloudy|Overcast|Light rain|Rain|Heavy rain|Light showers|Showers|Heavy showers|Drizzle|Fog|Thunderstorms).*?Rain\s+(<5%|\d+%)",
        re.I | re.S,
    )
    out = []
    for i, m in enumerate(pattern.finditer(text)):
        day = NOW.date() + timedelta(days=i)
        condition = clean(m.group(3)).title().replace("Sunny Intervals", "Sunny intervals").replace("Partly Cloudy", "Partly cloudy")
        out.append({
            "date": day.isoformat(), "high": int(m.group(2)), "low": None,
            "summary": condition, "condition": condition,
            "rainChance": pct(m.group(4)), "source": "Met Office",
        })
        if len(out) >= 7:
            break
    return out


def best_outdoor(daily: list[dict], current_rain: int | None, current_condition: str | None) -> dict:
    today = daily[0] if daily else {}
    condition = today.get("condition") or current_condition or "Forecast"
    rain = today.get("rainChance")
    if rain is None:
        rain = current_rain
    lower = condition.lower()
    wet = any(w in lower for w in ("rain", "shower", "drizzle", "thunder", "snow"))
    if wet:
        label = "Check hourly Met Office forecast"
        detail = f"{condition} expected" + (f" · rain chance around {rain}%" if rain is not None else "")
    elif rain is not None and rain >= 40:
        label = "Drier spells likely best"
        detail = f"{condition} · peak rain chance around {rain}%"
    else:
        label = "Good outdoor day"
        detail = f"{condition}" + (f" · rain chance around {rain}%" if rain is not None else "")
    return {"label": label, "detail": detail, "source": "Met Office"}


def met_weather() -> dict:
    try:
        r = requests.get(MET_URL, headers=UA, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = clean(soup.get_text(" ", strip=True))
        temp, current_condition, current_rain = parse_current(text)
        daily = daily_blocks(soup) or summary_fallback(text)

        if not daily and current_condition is None:
            raise ValueError("Met Office forecast could not be parsed")

        if current_condition is None and daily:
            current_condition = daily[0].get("condition")
        if temp is None and daily:
            temp = daily[0].get("high")

        return {
            "temp": f"{temp}°" if temp is not None else "—",
            "summary": current_condition or "Met Office forecast",
            "condition": current_condition or "Forecast",
            "currentRainChance": current_rain,
            "daily": daily[:7],
            "bestOutdoor": best_outdoor(daily, current_rain, current_condition),
            "source": "Met Office",
            "sourceUrl": MET_URL,
            "location": HOME_LABEL,
            "forecastPoint": MET_LOCATION,
        }
    except Exception as exc:
        # Do not fall back to a non-Met-Office provider: the user explicitly requires Met Office only.
        return {
            "temp": "—", "summary": "Met Office forecast unavailable", "condition": "Unavailable",
            "daily": [], "bestOutdoor": {}, "source": "Met Office", "sourceUrl": MET_URL,
            "location": HOME_LABEL, "forecastPoint": MET_LOCATION, "error": str(exc),
        }


def main() -> None:
    wx = met_weather()
    for name in ("pete", "sofia", "us"):
        path = DATA / f"{name}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["weather"] = wx
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Met Office weather applied for {HOME_POSTCODE}: {wx.get('summary')}")


if __name__ == "__main__":
    main()
