from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/London")
NOW = datetime.now(TZ)
UA = {"User-Agent": "DailyBriefs/3.0 (+https://github.com/PostWorkCulture/daily-briefs)"}
ARSENAL_ID = "359"
SEASON = NOW.year


def get_json(url: str) -> dict:
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def parse_fixture(event: dict, competition: str) -> dict | None:
    comps = event.get("competitions") or []
    if not comps:
        return None
    teams = comps[0].get("competitors") or []
    arsenal = next((x for x in teams if "arsenal" in x.get("team", {}).get("displayName", "").lower()), None)
    opponent = next((x for x in teams if x is not arsenal), None)
    if not arsenal or not opponent:
        return None
    try:
        dt = dateparser.parse(event.get("date", "")).astimezone(TZ)
    except Exception:
        return None
    completed = bool(event.get("status", {}).get("type", {}).get("completed"))
    a_score = arsenal.get("score", {}).get("value") if isinstance(arsenal.get("score"), dict) else arsenal.get("score")
    o_score = opponent.get("score", {}).get("value") if isinstance(opponent.get("score"), dict) else opponent.get("score")
    return {
        "date": dt.isoformat(),
        "dateLabel": dt.strftime("%a %-d %b"),
        "kickoff": dt.strftime("%-I:%M%p").lower().replace(":00", ""),
        "opponent": opponent.get("team", {}).get("displayName", "Opponent"),
        "competition": competition,
        "homeAway": arsenal.get("homeAway", ""),
        "completed": completed,
        "arsenalScore": a_score,
        "opponentScore": o_score,
        "result": f"{a_score}–{o_score}" if completed and a_score is not None and o_score is not None else "",
        "url": next((l.get("href") for l in event.get("links", []) if l.get("href")), ""),
    }


def snapshot(existing_news: list[dict]) -> dict:
    competitions = {
        "eng.1": "Premier League",
        "eng.fa": "FA Cup",
        "eng.league_cup": "League Cup",
        "uefa.champions": "Champions League",
        "eng.charity": "Community Shield",
    }
    fixtures = []
    for code, name in competitions.items():
        urls = [
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/{ARSENAL_ID}/schedule?season={SEASON}",
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/arsenal/schedule?season={SEASON}",
        ]
        for url in urls:
            data = get_json(url)
            parsed = [parse_fixture(e, name) for e in data.get("events", []) or []]
            parsed = [x for x in parsed if x]
            if parsed:
                fixtures.extend(parsed)
                break

    unique = {}
    for item in fixtures:
        unique.setdefault((item["date"], item["opponent"], item["competition"]), item)
    fixtures = sorted(unique.values(), key=lambda x: x["date"])
    past = [x for x in fixtures if x["completed"]]
    future = [x for x in fixtures if not x["completed"] and dateparser.parse(x["date"]) >= NOW - timedelta(hours=3)]

    position = points = played = None
    table = get_json(f"https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings?season={SEASON}")
    entries = []
    for group in table.get("children", []) or []:
        entries.extend((group.get("standings", {}) or {}).get("entries", []) or [])
    for entry in entries:
        if "arsenal" not in entry.get("team", {}).get("displayName", "").lower():
            continue
        stats = {s.get("name"): s.get("value") for s in entry.get("stats", [])}
        position = int(stats["rank"]) if stats.get("rank") else None
        points = int(stats["points"]) if stats.get("points") is not None else None
        played = int(stats["gamesPlayed"]) if stats.get("gamesPlayed") is not None else None
        break

    return {
        "lastResult": past[-1] if past else None,
        "nextFixture": future[0] if future else None,
        "leaguePosition": position,
        "points": points,
        "played": played,
        "news": existing_news[:5],
    }


def main() -> None:
    path = DATA / "pete.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    news = (payload.get("sections") or {}).get("Arsenal news", [])
    payload["arsenal"] = snapshot(news)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Arsenal enrichment complete")


if __name__ == "__main__":
    main()
