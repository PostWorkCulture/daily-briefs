from __future__ import annotations

import argparse
import html
import json
import os
import re
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HISTORY_PATH = DATA / "tv-picks-history.json"
TVMAZE_BROADCAST = "https://api.tvmaze.com/schedule"
TVMAZE_STREAMING = "https://api.tvmaze.com/schedule/web"
TZ = ZoneInfo("Europe/London")
PICK_COUNT = 5
PAST_DAYS = 7
FUTURE_DAYS = 7

STREAMING_SERVICES = {
    "Apple TV+",
    "BBC iPlayer",
    "Channel 4",
    "Disney+",
    "ITVX",
    "Netflix",
    "NOW",
    "Paramount+",
    "Prime Video",
    "Sky Go",
}

EXCLUDED_TYPES = {"Animation", "Game Show", "News", "Talk Show"}
EXCLUDED_TITLES = re.compile(
    r"\b(?:eastenders|emmerdale|hollyoaks|coronation street|loose women|good morning britain|"
    r"this morning|news at|squawk box|countdown)\b",
    re.I,
)
INTEREST_WEIGHTS = {
    "true crime": 90,
    "murder": 65,
    "crime": 48,
    "thriller": 45,
    "mystery": 42,
    "documentary": 40,
    "docuseries": 40,
    "investigation": 36,
    "scandal": 34,
    "science-fiction": 45,
    "sci-fi": 45,
    "football": 28,
    "sport": 12,
    "history": 18,
    "travel": 12,
}
DEEMPHASIS_WEIGHTS = {
    "gardening": 55,
    "garden": 45,
    "diy": 35,
    "nature": 30,
    "medical": 30,
    "cruising": 25,
}


def session() -> requests.Session:
    client = requests.Session()
    retry = Retry(total=3, backoff_factor=0.6, status_forcelist=(429, 500, 502, 503, 504))
    client.mount("https://", HTTPAdapter(max_retries=retry))
    client.headers.update({"User-Agent": "DailyBriefs/1.0 (+https://github.com/PostWorkCulture/daily-briefs)"})
    return client


def clean_text(value: str, limit: int = 190) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "…"


def show_for(episode: dict[str, Any]) -> dict[str, Any]:
    return episode.get("show") or (episode.get("_embedded") or {}).get("show") or {}


def channel_for(show: dict[str, Any]) -> dict[str, Any]:
    return show.get("webChannel") or show.get("network") or {}


def exact_artwork(episode: dict[str, Any], show: dict[str, Any]) -> str:
    for image in (episode.get("image") or {}, show.get("image") or {}):
        src = str(image.get("original") or "").strip()
        if src.startswith("https://static.tvmaze.com/uploads/images/original_untouched/"):
            return src
    return ""


def availability_label(episode: dict[str, Any], day: date) -> str:
    airdate = date.fromisoformat(str(episode.get("airdate")))
    offset = (airdate - day).days
    if offset == 0:
        when = "Today"
    elif offset == 1:
        when = "Tomorrow"
    elif offset == -1:
        when = "Available since yesterday"
    elif offset < -1:
        when = f"Available since {airdate.strftime('%a %-d %b')}"
    else:
        when = airdate.strftime("%a %-d %b")
    airtime = str(episode.get("airtime") or "").strip()
    if offset < 0:
        return when
    if airtime:
        try:
            airtime = datetime.strptime(airtime, "%H:%M").strftime("%-I:%M%p").lower().replace(":00", "")
        except ValueError:
            pass
        return f"{when}, {airtime}"
    return f"New {when.lower()}"


def category_label(show: dict[str, Any], haystack: str) -> str:
    if "true crime" in haystack or "murder" in haystack:
        return "True crime"
    show_type = str(show.get("type") or "").strip()
    genres = [str(item) for item in show.get("genres") or []]
    if show_type == "Documentary":
        return "Documentary"
    for preferred in ("Crime", "Thriller", "Mystery", "Science-Fiction", "Sports", "Drama"):
        if preferred in genres or preferred == show_type:
            return "Sci-fi" if preferred == "Science-Fiction" else preferred
    return show_type or (genres[0] if genres else "TV pick")


def candidate(episode: dict[str, Any], day: date) -> dict[str, Any] | None:
    show = show_for(episode)
    title = clean_text(show.get("name") or "", 90)
    if not title or EXCLUDED_TITLES.search(title):
        return None
    show_type = str(show.get("type") or "").strip()
    if show_type in EXCLUDED_TYPES:
        return None
    language = str(show.get("language") or "").lower()
    if language and language != "english":
        return None

    channel = channel_for(show)
    source = clean_text(channel.get("name") or "", 50)
    web_channel = show.get("webChannel") or {}
    network = show.get("network") or {}
    network_country = (network.get("country") or {}).get("code")
    if web_channel and source not in STREAMING_SERVICES:
        return None
    if not web_channel and network_country != "GB":
        return None

    artwork = exact_artwork(episode, show)
    if not artwork:
        return None
    try:
        airdate = date.fromisoformat(str(episode.get("airdate") or ""))
    except ValueError:
        return None
    offset = (airdate - day).days
    if not -PAST_DAYS <= offset <= FUTURE_DAYS:
        return None

    episode_summary = clean_text(episode.get("summary") or "")
    show_summary = clean_text(show.get("summary") or "")
    summary = episode_summary or show_summary or f"A current {show_type.lower() or 'programme'} to consider."
    genres = [str(item) for item in show.get("genres") or []]
    haystack = " ".join([title, summary, show_type, *genres]).lower()
    score = max(12, 74 - abs(offset) * 8)
    if offset < 0:
        score -= 4
    for term, weight in INTEREST_WEIGHTS.items():
        if term in haystack:
            score += weight
    for term, weight in DEEMPHASIS_WEIGHTS.items():
        if term in haystack:
            score -= weight
    if show_type == "Documentary":
        score += 42
    if source in {"BBC One", "BBC Two", "BBC iPlayer", "Channel 4", "ITV1", "ITVX", "Netflix", "Apple TV+", "Prime Video", "Sky Atlantic", "Paramount+"}:
        score += 18
    if episode.get("number") == 1:
        score += 28
    score += min(int(show.get("weight") or 0), 100) / 10

    official = str(show.get("officialSite") or channel.get("officialSite") or episode.get("url") or show.get("url") or "").strip()
    if not official.startswith(("https://", "http://")):
        return None
    availability = availability_label(episode, day)
    return {
        "title": title,
        "summary": summary,
        "meta": f"{source or 'TV'} · {availability}",
        "source": source or "TVMaze",
        "url": official,
        "badge": category_label(show, haystack),
        "artwork": artwork,
        "artworkAlt": f"{title} programme artwork",
        "artworkSource": "TVMaze",
        "airdate": airdate.isoformat(),
        "showId": show.get("id"),
        "episodeId": episode.get("id"),
        "contentType": "tv-pick",
        "generatedDate": day.isoformat(),
        "preferenceScore": round(score, 1),
    }


def fetch_candidates(day: date, client: requests.Session | None = None) -> list[dict[str, Any]]:
    client = client or session()
    episodes: list[dict[str, Any]] = []
    batch_started = time.monotonic()
    batch_count = 0
    for offset in range(-PAST_DAYS, FUTURE_DAYS + 1):
        target = (day + timedelta(days=offset)).isoformat()
        for url, params in (
            (TVMAZE_BROADCAST, {"country": "GB", "date": target}),
            (TVMAZE_STREAMING, {"date": target}),
        ):
            if batch_count == 18:
                elapsed = time.monotonic() - batch_started
                if elapsed < 10.2:
                    time.sleep(10.2 - elapsed)
                batch_started = time.monotonic()
                batch_count = 0
            response = client.get(url, params=params, timeout=30)
            batch_count += 1
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list):
                raise RuntimeError(f"TVMaze returned non-list data for {target}")
            episodes.extend(payload)

    by_show: dict[str, dict[str, Any]] = {}
    for episode in episodes:
        item = candidate(episode, day)
        if not item:
            continue
        key = str(item.get("showId") or item["title"]).lower()
        previous = by_show.get(key)
        if previous is None or (item["preferenceScore"], item["airdate"]) > (previous["preferenceScore"], previous["airdate"]):
            by_show[key] = item
    return sorted(by_show.values(), key=lambda item: (-item["preferenceScore"], item["airdate"], item["title"]))


def load_history() -> list[dict[str, Any]]:
    try:
        payload = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return [entry for entry in payload.get("days") or [] if entry.get("date") and entry.get("titles")]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def select_picks(candidates: list[dict[str, Any]], day: date, history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recent = {
        str(title).casefold()
        for entry in history[-3:]
        if entry.get("date") != day.isoformat()
        for title in entry.get("titles") or []
    }
    fresh = [item for item in candidates if item["title"].casefold() not in recent]
    fallback = [item for item in candidates if item["title"].casefold() in recent]
    selected: list[dict[str, Any]] = []
    source_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for item in fresh + fallback:
        source = item["source"]
        category = item["badge"]
        if source_counts.get(source, 0) >= 2 or category_counts.get(category, 0) >= 2:
            continue
        selected.append(item)
        source_counts[source] = source_counts.get(source, 0) + 1
        category_counts[category] = category_counts.get(category, 0) + 1
        if len(selected) == PICK_COUNT:
            break
    if len(selected) < PICK_COUNT:
        for item in fresh + fallback:
            if item in selected:
                continue
            selected.append(item)
            if len(selected) == PICK_COUNT:
                break
    if len(selected) < PICK_COUNT:
        raise RuntimeError(f"Only {len(selected)} current TV Picks passed the programme, artwork and availability rules")
    return selected


def save(picks: list[dict[str, Any]], day: date, history: list[dict[str, Any]]) -> None:
    for profile in ("pete", "sofia"):
        path = DATA / f"{profile}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["watch"] = [dict(item) for item in picks]
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    current = {"date": day.isoformat(), "titles": [item["title"] for item in picks]}
    history = [entry for entry in history if entry.get("date") != day.isoformat()]
    history.append(current)
    HISTORY_PATH.write_text(json.dumps({"days": history[-30:]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate current programme-first TV Picks")
    parser.add_argument("--date", help="Europe/London date in YYYY-MM-DD format (for testing/backfills)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    day = date.fromisoformat(args.date or os.getenv("TV_PICKS_DATE") or datetime.now(TZ).date().isoformat())
    history = load_history()
    candidates = fetch_candidates(day)
    picks = select_picks(candidates, day, history)
    save(picks, day, history)
    print(f"TV Picks: selected {len(picks)} current programmes for {day.isoformat()} from {len(candidates)} exact-artwork candidates")


if __name__ == "__main__":
    main()
