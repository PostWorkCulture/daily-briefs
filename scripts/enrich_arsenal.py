from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/London")
NOW = datetime.now(TZ)
UA = {"User-Agent": "Mozilla/5.0 DailyBriefs/3.2"}
ARSENAL_ID = "359"
SEASON = NOW.year
OFFICIAL_PL_FIXTURE_URLS = (
    "https://www.premierleague.com/en/news/4675097/all-380-fixtures-for-202627-premier-league-season/",
    "https://www.premierleague.com/en/news/4675132/all-of-arsenals-fixtures-for-202627-premier-league-season",
)

# Never surface gambling / betting material in Daily Briefs.
BETTING_TERMS = {
    "bet", "bets", "betting", "odds", "bookmaker", "bookmakers", "bookie", "bookies",
    "gambling", "wager", "wagers", "accumulator", "acca", "tipster", "tips", "best price",
    "free bet", "enhanced odds", "bet builder", "sportsbook", "casino",
}

MEN_COMPETITIONS = {
    "Premier League", "FA Community Shield", "Community Shield", "FA Cup", "Carabao Cup",
    "League Cup", "Champions League", "UEFA Champions League", "Europa League",
    "UEFA Europa League", "Friendly Match", "Friendly Matches", "Club Friendly",
}
NON_MENS_ARSENAL = re.compile(
    r"\b(?:u[-\s]?(?:18|19|21|23)s?|under[-\s]?(?:18|19|21|23)s?|academy|"
    r"youth|women(?:['’]?s)?|girls?)\b",
    re.I,
)


def get_json(url: str) -> dict:
    try:
        r = requests.get(url, headers=UA, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


def get_html(url: str) -> tuple[str, str]:
    try:
        r = requests.get(url, headers=UA, timeout=25)
        r.raise_for_status()
        return r.text, r.url
    except Exception:
        return "", url


def contains_betting(text: str) -> bool:
    normalized = re.sub(r"[^a-z0-9+ ]+", " ", (text or "").lower())
    return any(term in normalized for term in BETTING_TERMS)


def clean_arsenal_news(items: list[dict]) -> list[dict]:
    clean = []
    for item in items:
        blob = " ".join([
            str(item.get("title", "")), str(item.get("summary", "")), str(item.get("source", ""))
        ])
        if contains_betting(blob) or NON_MENS_ARSENAL.search(blob):
            continue
        clean.append(item)
    return clean


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
        "date": dt.isoformat(), "dateLabel": dt.strftime("%a %-d %b"),
        "kickoff": dt.strftime("%-I:%M%p").lower().replace(":00", ""),
        "opponent": opponent.get("team", {}).get("displayName", "Opponent"),
        "competition": competition, "homeAway": arsenal.get("homeAway", ""),
        "completed": completed, "arsenalScore": a_score, "opponentScore": o_score,
        "result": f"{int(a_score) if float(a_score).is_integer() else a_score}–{int(o_score) if float(o_score).is_integer() else o_score}" if completed and a_score is not None and o_score is not None else "",
        "url": next((l.get("href") for l in event.get("links", []) if l.get("href")), ""),
        "source": "ESPN",
    }


def sky_month_matches(month_date: datetime | None = None) -> list[dict]:
    month_date = month_date or NOW
    month_url = f"https://www.skysports.com/arsenal-scores-fixtures/{month_date.year}-{month_date.month:02d}-01"
    html, final_url = get_html(month_url)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    lines = [x.strip() for x in soup.stripped_strings if x.strip()]
    out: list[dict] = []
    current_date: datetime | None = None
    current_comp = "Football"

    date_re = re.compile(
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})(?:st|nd|rd|th)\s+([A-Za-z]+)$",
        re.I,
    )
    comp_re = re.compile(
        r"^(Premier League|FA Community Shield|Community Shield|Friendly Match(?:es)?|Champions League|UEFA Champions League|FA Cup|Carabao Cup|League Cup|Europa League|UEFA Europa League)$",
        re.I,
    )
    # Sky text currently resembles: “Arsenal are scheduled to play Manchester City . 3.00pm Arsenal vs Manchester City. Kick-off at 3:00pm”
    scheduled_re = re.compile(
        r"(?P<home>[A-Za-z0-9& .'-]+?)\s+are scheduled to play\s+(?P<away>[A-Za-z0-9& .'-]+?)\s*\.\s*(?:\d{1,2}\.\d{2}(?:am|pm)\s*)?(?P=home)\s+vs\s+(?P=away)\.\s*Kick-off at\s+(?P<ko>\d{1,2}:\d{2}(?:am|pm))",
        re.I,
    )
    # Completed rows often include a compact “Arsenal 2 Manchester City 1” style score string.
    result_re = re.compile(
        r"(?P<home>[A-Za-z0-9& .'-]+?)\s+(?P<hscore>\d+)\s+(?P<away>[A-Za-z0-9& .'-]+?)\s+(?P<ascore>\d+)(?:\s+Full Time|\s+FT|$)",
        re.I,
    )

    for line in lines:
        dm = date_re.match(line)
        if dm:
            try:
                current_date = datetime.strptime(
                    f"{dm.group(2)} {dm.group(3)} {month_date.year}", "%d %B %Y"
                ).replace(tzinfo=TZ)
            except Exception:
                current_date = None
            continue

        cm = comp_re.match(line)
        if cm:
            current_comp = cm.group(1)
            continue

        if not current_date:
            continue

        fm = scheduled_re.search(line)
        if fm:
            home, away = fm.group("home").strip(), fm.group("away").strip()
            if "arsenal" not in home.lower() and "arsenal" not in away.lower():
                continue
            try:
                tm = datetime.strptime(fm.group("ko").upper(), "%I:%M%p").time()
                dt = current_date.replace(hour=tm.hour, minute=tm.minute)
            except Exception:
                dt = current_date
            opponent = away if "arsenal" in home.lower() else home
            out.append({
                "date": dt.isoformat(), "dateLabel": dt.strftime("%a %-d %b"),
                "kickoff": dt.strftime("%-I:%M%p").lower().replace(":00", ""),
                "opponent": opponent, "competition": current_comp,
                "homeAway": "home" if "arsenal" in home.lower() else "away",
                "completed": False, "arsenalScore": None, "opponentScore": None,
                "result": "", "url": final_url, "source": "Sky Sports",
            })
            continue

        rm = result_re.search(line)
        if rm:
            home, away = rm.group("home").strip(), rm.group("away").strip()
            if "arsenal" not in home.lower() and "arsenal" not in away.lower():
                continue
            h_score, a_score = int(rm.group("hscore")), int(rm.group("ascore"))
            arsenal_home = "arsenal" in home.lower()
            opponent = away if arsenal_home else home
            out.append({
                "date": current_date.isoformat(), "dateLabel": current_date.strftime("%a %-d %b"),
                "kickoff": "", "opponent": opponent, "competition": current_comp,
                "homeAway": "home" if arsenal_home else "away", "completed": True,
                "arsenalScore": h_score if arsenal_home else a_score,
                "opponentScore": a_score if arsenal_home else h_score,
                "result": f"{h_score if arsenal_home else a_score}–{a_score if arsenal_home else h_score}",
                "url": final_url, "source": "Sky Sports",
            })

    return out


def all_sky_matches() -> list[dict]:
    # Pull previous, current and next month so last/next is never restricted by a calendar-month boundary.
    first = NOW.replace(day=1)
    previous = (first - timedelta(days=1)).replace(day=1)
    next_month = (first.replace(day=28) + timedelta(days=4)).replace(day=1)
    combined: list[dict] = []
    for month in (previous, first, next_month):
        combined.extend(sky_month_matches(month))
    return combined


def parse_official_pl_fixtures(
    html: str, url: str, now: datetime | None = None
) -> list[dict]:
    now = now or NOW
    text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
    pat = re.compile(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
        r"(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?\s*"
        r"(?:(\d{1,2}:\d{2})\s+)?"
        r"(Arsenal\s+v\s+[^\n(]+|[^\n(]+\s+v\s+Arsenal)"
        r"(?:\s+\(([^)\n]+)\))?",
        re.I,
    )
    months = {m.lower(): i for i, m in enumerate([
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ], 1)}
    candidates: list[dict] = []
    for m in pat.finditer(text):
        mon = months.get(m.group(3).lower())
        if not mon:
            continue
        year = int(m.group(4) or now.year)
        dt = datetime(year, mon, int(m.group(2)), tzinfo=TZ)
        if m.group(5):
            hh, mm = map(int, m.group(5).split(":")); dt = dt.replace(hour=hh, minute=mm)
        if dt < now - timedelta(hours=3):
            continue
        fixture = m.group(6).strip()
        parts = re.split(r"\s+v\s+", fixture, maxsplit=1, flags=re.I)
        if len(parts) != 2:
            continue
        home, away = parts
        opponent = away if home.lower() == "arsenal" else home
        candidates.append({
            "date": dt.isoformat(), "dateLabel": dt.strftime("%a %-d %b"),
            "kickoff": dt.strftime("%-I:%M%p").lower().replace(":00", "") if m.group(5) else "TBC",
            "opponent": opponent, "competition": "Premier League",
            "homeAway": "home" if home.lower() == "arsenal" else "away",
            "completed": False, "arsenalScore": None, "opponentScore": None,
            "result": "", "url": url, "source": "PremierLeague.com",
            "tvChannel": (m.group(7) or "TBC").strip(),
        })
    return candidates


def official_pl_next_fixture() -> dict | None:
    for source_url in OFFICIAL_PL_FIXTURE_URLS:
        html, final_url = get_html(source_url)
        if not html:
            continue
        candidates = parse_official_pl_fixtures(html, final_url)
        if candidates:
            return min(candidates, key=lambda x: x["date"])
    return None


def reconcile_official_fixture(fixtures: list[dict], official: dict | None) -> list[dict]:
    if not official:
        return fixtures
    official_opponent = re.sub(
        r"\s+", " ", str(official.get("opponent") or "")
    ).strip().lower()
    official_competition = str(official.get("competition") or "").strip().lower()
    reconciled = [
        fixture
        for fixture in fixtures
        if fixture.get("completed")
        or re.sub(r"\s+", " ", str(fixture.get("opponent") or "")).strip().lower()
        != official_opponent
        or str(fixture.get("competition") or "").strip().lower()
        != official_competition
    ]
    reconciled.append(official)
    return reconciled


def espn_snapshot() -> tuple[list[dict], int | None, int | None, int | None]:
    competitions = {
        "eng.1": "Premier League", "eng.fa": "FA Cup", "eng.league_cup": "League Cup",
        "uefa.champions": "Champions League", "eng.charity": "FA Community Shield",
    }
    fixtures = []
    for code, name in competitions.items():
        for url in [
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/{ARSENAL_ID}/schedule?season={SEASON}",
            f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/arsenal/schedule?season={SEASON}",
        ]:
            data = get_json(url)
            parsed = [parse_fixture(e, name) for e in data.get("events", []) or []]
            parsed = [x for x in parsed if x]
            if parsed:
                fixtures.extend(parsed)
                break

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
    return fixtures, position, points, played


def snapshot(existing_news: list[dict]) -> dict:
    clean_news = clean_arsenal_news(existing_news)
    espn_fixtures, position, points, played = espn_snapshot()
    sky_fixtures = all_sky_matches()

    official_fixture = official_pl_next_fixture()
    all_fixtures = reconcile_official_fixture(
        sky_fixtures + espn_fixtures, official_fixture
    )
    unique = {}
    for item in all_fixtures:
        key = (item.get("date"), item.get("opponent"), item.get("competition"), item.get("completed"))
        # Sky is inserted first, so it wins duplicate fixture details over ESPN.
        unique.setdefault(key, item)
    fixtures = sorted(unique.values(), key=lambda x: dateparser.parse(x["date"]))

    # Men's first-team last completed match and next scheduled match across ALL competitions.
    past = [x for x in fixtures if x.get("completed") and dateparser.parse(x["date"]) <= NOW]
    future = [x for x in fixtures if not x.get("completed") and dateparser.parse(x["date"]) >= NOW - timedelta(hours=3)]

    last_result = past[-1] if past else None
    next_fixture = future[0] if future else None

    # Retain the official PL fallback when no all-competition source returns anything.
    if not next_fixture:
        next_fixture = official_fixture

    return {
        "lastResult": last_result,
        "nextFixture": next_fixture,
        "leaguePosition": position,
        "points": points,
        "played": played,
        "news": clean_news[:5],
        "sources": ["Sky Sports", "PremierLeague.com", "Arsenal.com", "ESPN"],
        "scope": "Arsenal men's first team · all competitions",
    }


def main() -> None:
    path = DATA / "pete.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    news = (payload.get("sections") or {}).get("Arsenal news", [])
    transfers = (payload.get("arsenal") or {}).get("transfers", [])
    transfer_rumours = (payload.get("arsenal") or {}).get("transferRumours", [])
    clean_news = clean_arsenal_news(news)
    if "sections" in payload and "Arsenal news" in payload["sections"]:
        payload["sections"]["Arsenal news"] = clean_news
    enriched = snapshot(clean_news)
    enriched["transfers"] = transfers
    enriched["transferRumours"] = transfer_rumours
    payload["arsenal"] = enriched
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Arsenal enrichment complete")


if __name__ == "__main__":
    main()
