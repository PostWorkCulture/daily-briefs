from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/London")
NOW = datetime.now(TZ)
UA = {"User-Agent": "Mozilla/5.0 DailyBriefs/4.0"}
ARSENAL_ID = "359"

COMPETITIONS = {
    "eng.1": "Premier League",
    "eng.fa": "FA Cup",
    "eng.league_cup": "League Cup",
    "uefa.champions": "Champions League",
    "eng.charity": "FA Community Shield",
}

STADIUMS = {
    "aston villa": "Villa Park",
    "bournemouth": "Vitality Stadium",
    "afc bournemouth": "Vitality Stadium",
    "brentford": "Gtech Community Stadium",
    "brighton": "Amex Stadium",
    "brighton and hove albion": "Amex Stadium",
    "chelsea": "Stamford Bridge",
    "coventry": "Coventry Building Society Arena",
    "coventry city": "Coventry Building Society Arena",
    "crystal palace": "Selhurst Park",
    "everton": "Hill Dickinson Stadium",
    "fulham": "Craven Cottage",
    "hull": "MKM Stadium",
    "hull city": "MKM Stadium",
    "ipswich": "Portman Road",
    "ipswich town": "Portman Road",
    "leeds": "Elland Road",
    "leeds united": "Elland Road",
    "liverpool": "Anfield",
    "manchester city": "Etihad Stadium",
    "manchester united": "Old Trafford",
    "newcastle": "St James' Park",
    "newcastle united": "St James' Park",
    "nottingham forest": "City Ground",
    "sunderland": "Stadium of Light",
    "tottenham": "Tottenham Hotspur Stadium",
    "tottenham hotspur": "Tottenham Hotspur Stadium",
}

# Historical fallbacks are only used when recent ESPN schedules do not contain a meeting.
HISTORICAL_MEETINGS = {
    "coventry city": {
        "score": "Arsenal 4–0 Coventry City",
        "date": "24 Jan 2014",
        "competition": "FA Cup",
        "source": "Transfermarkt / theScore",
    },
    "coventry": {
        "score": "Arsenal 4–0 Coventry City",
        "date": "24 Jan 2014",
        "competition": "FA Cup",
        "source": "Transfermarkt / theScore",
    },
    "hull city": {
        "score": "Hull City 0–4 Arsenal",
        "date": "8 Mar 2016",
        "competition": "FA Cup",
        "source": "BBC Sport",
    },
    "hull": {
        "score": "Hull City 0–4 Arsenal",
        "date": "8 Mar 2016",
        "competition": "FA Cup",
        "source": "BBC Sport",
    },
}

# Confirmed broadcaster/venue details can be pinned here when a source is stronger
# than the generic feed. The normal pipeline still handles future fixtures.
VERIFIED_FIXTURES = {
    ("2026-08-21", "coventry city"): {
        "opponent": "Coventry City",
        "stadium": "Emirates Stadium",
        "kickoff": "8:00pm",
        "competition": "Premier League",
        "tvChannel": "Sky Sports Main Event · Sky Sports Premier League",
        "source": "PremierLeague.com / Sky Sports",
        "previousMeeting": HISTORICAL_MEETINGS["coventry city"],
    },
    ("2026-08-31", "aston villa"): {
        "opponent": "Aston Villa",
        "stadium": "Villa Park",
        "kickoff": "8:00pm",
        "competition": "Premier League",
        "tvChannel": "Sky Sports",
        "source": "PremierLeague.com / Arsenal.com / Sky Sports",
        "previousMeeting": {
            "score": "Arsenal 4–1 Aston Villa",
            "date": "30 Dec 2025",
            "competition": "Premier League",
            "source": "Sky Sports",
        },
    },
}


def norm_team(value: str) -> str:
    value = re.sub(r"\s*\([^)]*\)\s*$", "", value or "").strip()
    value = re.sub(r"\bfc\b", "", value, flags=re.I)
    return re.sub(r"\s+", " ", value).strip().lower()


def clean_opponent(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", value or "").strip()


def normalize_kickoff(value: str) -> str:
    raw = (value or "").strip().lower().replace(" ", "")
    if not raw or raw == "tbc":
        return "TBC"
    for fmt in ("%I:%M%p", "%I%p"):
        try:
            dt = datetime.strptime(raw.upper(), fmt)
            return dt.strftime("%-I:%M%p").lower()
        except Exception:
            pass
    return value


def fixture_date_key(fixture: dict) -> str:
    try:
        return dateparser.parse(fixture.get("date", "")).astimezone(TZ).date().isoformat()
    except Exception:
        return ""


def score_value(competitor: dict):
    raw = competitor.get("score")
    if isinstance(raw, dict):
        raw = raw.get("value")
    try:
        value = float(raw)
        return int(value) if value.is_integer() else value
    except Exception:
        return None


def parse_meeting(event: dict, competition: str, wanted: str) -> dict | None:
    comps = event.get("competitions") or []
    if not comps:
        return None
    comp = comps[0]
    teams = comp.get("competitors") or []
    arsenal = next((x for x in teams if "arsenal" in norm_team(x.get("team", {}).get("displayName", ""))), None)
    opponent = next((x for x in teams if x is not arsenal), None)
    if not arsenal or not opponent:
        return None
    opp_name = opponent.get("team", {}).get("displayName", "")
    if norm_team(opp_name) != wanted:
        return None
    if not event.get("status", {}).get("type", {}).get("completed"):
        return None
    a_score, o_score = score_value(arsenal), score_value(opponent)
    if a_score is None or o_score is None:
        return None
    try:
        dt = dateparser.parse(event.get("date", "")).astimezone(TZ)
    except Exception:
        return None
    arsenal_home = arsenal.get("homeAway") == "home"
    score = f"Arsenal {a_score}–{o_score} {opp_name}" if arsenal_home else f"{opp_name} {o_score}–{a_score} Arsenal"
    return {
        "score": score,
        "date": dt.strftime("%-d %b %Y"),
        "competition": competition,
        "source": "ESPN",
        "sortDate": dt.isoformat(),
    }


def latest_recent_meeting(opponent: str) -> dict | None:
    wanted = norm_team(opponent)
    meetings: list[dict] = []
    # Three seasons catches current-season return fixtures and almost all recent PL opponents.
    for season in (NOW.year, NOW.year - 1, NOW.year - 2):
        for code, competition in COMPETITIONS.items():
            urls = [
                f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/{ARSENAL_ID}/schedule?season={season}",
                f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/arsenal/schedule?season={season}",
            ]
            data = {}
            for url in urls:
                try:
                    r = requests.get(url, headers=UA, timeout=10)
                    r.raise_for_status()
                    data = r.json()
                except Exception:
                    data = {}
                if data.get("events"):
                    break
            for event in data.get("events", []) or []:
                item = parse_meeting(event, competition, wanted)
                if item:
                    meetings.append(item)
        if meetings:
            break
    if not meetings:
        return None
    latest = max(meetings, key=lambda x: dateparser.parse(x["sortDate"]))
    latest.pop("sortDate", None)
    return latest


def stadium_for(fixture: dict, opponent: str) -> str:
    for key in ("stadium", "venue"):
        if fixture.get(key):
            return str(fixture[key]).strip()
    if fixture.get("homeAway") == "home":
        return "Emirates Stadium"
    return STADIUMS.get(norm_team(opponent), "TBC")


def broadcaster_from_existing(fixture: dict) -> str:
    existing = str(fixture.get("tvChannel") or "").strip()
    if existing:
        return existing
    raw_opponent = str(fixture.get("opponent") or "")
    m = re.search(r"\(([^)]*(?:Sky Sports|TNT Sports|BBC|ITV)[^)]*)\)\s*$", raw_opponent, re.I)
    return m.group(1).strip() if m else "TBC"


def enrich_fixture(fixture: dict) -> dict:
    fixture = dict(fixture or {})
    opponent = clean_opponent(str(fixture.get("opponent") or "Opponent"))
    fixture["opponent"] = opponent
    fixture["kickoff"] = normalize_kickoff(str(fixture.get("kickoff") or "TBC"))
    fixture["stadium"] = stadium_for(fixture, opponent)
    fixture["tvChannel"] = broadcaster_from_existing(fixture)

    key = (fixture_date_key(fixture), norm_team(opponent))
    verified = VERIFIED_FIXTURES.get(key)
    if verified:
        fixture.update({k: v for k, v in verified.items() if k != "previousMeeting"})
        fixture["previousMeeting"] = dict(verified["previousMeeting"])
        return fixture

    previous = latest_recent_meeting(opponent) or HISTORICAL_MEETINGS.get(norm_team(opponent))
    fixture["previousMeeting"] = previous or {
        "score": "No previous meeting found",
        "date": "",
        "competition": "",
        "source": "",
    }
    return fixture


def main() -> None:
    path = DATA / "pete.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    arsenal = payload.setdefault("arsenal", {})
    next_fixture = arsenal.get("nextFixture")
    if next_fixture:
        arsenal["nextFixture"] = enrich_fixture(next_fixture)
    payload["arsenal"] = arsenal
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Arsenal next-fixture detail enrichment complete")


if __name__ == "__main__":
    main()
