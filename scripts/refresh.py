from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import feedparser
import requests
from dateutil import parser as dateparser
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
TZ = ZoneInfo("Europe/London")
NOW = datetime.now(TZ)
UA = {"User-Agent": "DailyBriefs/1.0 (+https://github.com/PostWorkCulture/daily-briefs)"}

# East Molesey / KT8 area. Change here if the brief location changes.
LAT = 51.400
LON = -0.366


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def weather() -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": "temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "timezone": "Europe/London",
        "forecast_days": 7,
    }
    try:
        r = requests.get(url, params=params, headers=UA, timeout=25)
        r.raise_for_status()
        d = r.json()
        temp = round(float(d["current"]["temperature_2m"]))
        code = int(d["current"].get("weather_code", 0))
        labels = {
            0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Cloudy",
            45: "Foggy", 48: "Foggy", 51: "Light drizzle", 53: "Drizzle",
            55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
            71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Showers",
            81: "Showers", 82: "Heavy showers", 95: "Thunderstorms",
        }
        daily = []
        for day, hi, lo, wc in zip(d["daily"]["time"], d["daily"]["temperature_2m_max"], d["daily"]["temperature_2m_min"], d["daily"]["weather_code"]):
            daily.append({"date": day, "high": round(hi), "low": round(lo), "summary": labels.get(int(wc), "Forecast")})
        return {"temp": f"{temp}°", "summary": labels.get(code, "Latest forecast"), "daily": daily}
    except Exception as exc:
        return {"temp": "—", "summary": f"Weather unavailable", "daily": [], "error": str(exc)}


def google_news(query: str, limit: int = 6) -> list[dict]:
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-GB&gl=GB&ceid=GB:en"
    feed = feedparser.parse(url)
    out = []
    for entry in feed.entries[: limit * 2]:
        title = clean_html(entry.get("title", ""))
        if " - " in title:
            title = title.rsplit(" - ", 1)[0]
        published = entry.get("published", "")
        try:
            dt = dateparser.parse(published).astimezone(TZ)
            if NOW - dt > timedelta(days=7):
                continue
            meta = dt.strftime("%a %-d %b")
        except Exception:
            meta = "Recent"
        out.append({"title": title, "summary": "", "meta": meta, "url": entry.get("link", "")})
        if len(out) >= limit:
            break
    return out


def rss(url: str, section: str, limit: int = 6) -> list[dict]:
    feed = feedparser.parse(url)
    items = []
    for entry in feed.entries[:limit]:
        title = clean_html(entry.get("title", ""))
        summary = clean_html(entry.get("summary", ""))[:220]
        published = entry.get("published", "")
        try:
            dt = dateparser.parse(published).astimezone(TZ)
            meta = dt.strftime("%a %-d %b")
        except Exception:
            meta = section
        items.append({"title": title, "summary": summary, "meta": meta, "url": entry.get("link", "")})
    return items


def calendar_events() -> list[dict]:
    url = os.getenv("GOOGLE_CALENDAR_ICS_URL", "").strip()
    if not url:
        return []
    try:
        r = requests.get(url, headers=UA, timeout=30)
        r.raise_for_status()
        cal = Calendar.from_ical(r.content)
    except Exception:
        return []

    start_window = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    end_window = start_window + timedelta(days=45)
    events = []
    for component in cal.walk("VEVENT"):
        start = component.decoded("dtstart")
        end = component.decoded("dtend") if component.get("dtend") else start
        if not isinstance(start, datetime):
            start = datetime.combine(start, datetime.min.time(), TZ)
        elif start.tzinfo is None:
            start = start.replace(tzinfo=TZ)
        else:
            start = start.astimezone(TZ)
        if not isinstance(end, datetime):
            end = datetime.combine(end, datetime.min.time(), TZ)
        elif end.tzinfo is None:
            end = end.replace(tzinfo=TZ)
        else:
            end = end.astimezone(TZ)
        if end < start_window or start > end_window:
            continue
        title = clean_html(str(component.get("summary", "Calendar event"))) or "Calendar event"
        when = start.strftime("%a %-d %b")
        if start.date() == NOW.date():
            when = "Today"
        elif start.date() == (NOW + timedelta(days=1)).date():
            when = "Tomorrow"
        if start.hour or start.minute:
            when += " · " + start.strftime("%-I:%M%p").lower().replace(":00", "")
        events.append({"title": title, "summary": "", "meta": when, "url": ""})
    events.sort(key=lambda x: x["meta"] not in ("Today", "Tomorrow"))
    return events[:12]


def build_profiles() -> dict[str, dict]:
    wx = weather()
    cal = calendar_events()

    ai = google_news('(OpenAI OR Anthropic OR "Google DeepMind" OR AI) when:7d', 7)
    arsenal = google_news('Arsenal FC when:7d', 7)
    local = google_news('(Kingston upon Thames OR Molesey OR Esher OR Walton-on-Thames OR Hampton) when:7d', 7)
    uk = google_news('UK positive news when:7d', 6)
    tv = google_news('(Netflix OR BBC iPlayer OR ITV OR Disney+) new series film UK when:7d', 6)
    career = google_news('(UK civil service jobs OR AI careers UK) when:7d', 5)
    sweden = google_news('Sweden news when:7d', 6)
    family = google_news('(Surrey family events OR Kingston family events OR Elmbridge events) when:14d', 6)

    stamp = NOW.strftime("%A, %-d %B %Y · refreshed %-I:%M%p").replace("AM", "am").replace("PM", "pm")

    pete_sections = {"AI": ai, "Arsenal": arsenal, "Local news": local, "UK news": uk, "Career": career}
    sofia_sections = {"Sweden": sweden, "Local news": local, "UK news": uk, "AI": ai, "Career": career}
    us_sections = {"Local ideas": family, "Local news": local, "UK news": uk}

    def first(items, fallback):
        return items[0] if items else {"title": fallback, "summary": "", "meta": "", "url": ""}

    return {
        "pete": {"updatedLabel": stamp, "weather": wx, "calendar": cal, "lead": first(ai or arsenal or local, "Your morning brief is ready."), "interests": [dict(first(ai, "AI updates"), section="AI"), dict(first(arsenal, "Arsenal"), section="Arsenal"), dict(first(local, "Local"), section="Local")], "watch": tv, "sections": pete_sections},
        "sofia": {"updatedLabel": stamp, "weather": wx, "calendar": cal, "lead": first(sweden or local or tv, "Your morning brief is ready."), "interests": [dict(first(sweden, "Sweden"), section="Sweden"), dict(first(local, "Local"), section="Local"), dict(first(tv, "Tonight"), section="Watch")], "watch": tv, "sections": sofia_sections},
        "us": {"updatedLabel": stamp, "weather": wx, "calendar": cal, "lead": first(family or local, "Your shared day is ready."), "interests": [dict(first(family, "Family ideas"), section="Family"), dict(first(local, "Local"), section="Local"), dict(first(tv, "Tonight"), section="Watch")], "watch": tv, "sections": us_sections},
    }


def main() -> None:
    profiles = build_profiles()
    for name, payload in profiles.items():
        (DATA / f"{name}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Updated:", ", ".join(str(DATA / f"{x}.json") for x in profiles))


if __name__ == "__main__":
    main()
