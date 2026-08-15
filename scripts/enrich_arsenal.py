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
UA = {"User-Agent": "Mozilla/5.0 DailyBriefs/3.1"}
ARSENAL_ID = "359"
SEASON = NOW.year


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


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1:'st',2:'nd',3:'rd'}.get(n%10,'th') }"


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
        "result": f"{a_score}–{o_score}" if completed and a_score is not None and o_score is not None else "",
        "url": next((l.get("href") for l in event.get("links", []) if l.get("href")), ""),
        "source": "ESPN",
    }


def sky_month_matches() -> list[dict]:
    month_url = f"https://www.skysports.com/arsenal-scores-fixtures/{NOW.year}-{NOW.month:02d}-01"
    html, final_url = get_html(month_url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    text = "\n".join(s.strip() for s in soup.stripped_strings if s.strip())
    # Sky's server-rendered page exposes date, competition and human-readable fixture sentences.
    date_re = re.compile(r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})(st|nd|rd|th)\s+([A-Za-z]+)$", re.I)
    comp_re = re.compile(r"^(Premier League|FA Community Shield|Friendly Match|Friendly Matches|Champions League|FA Cup|Carabao Cup|League Cup)$", re.I)
    fixture_re = re.compile(r"(?P<home>.+?) are scheduled to play (?P<away>.+?) \. (?P<time>\d{1,2}\.\d{2}(?:am|pm)) (?P=home) vs (?P=away)\. Kick-off at (?P<ko>\d{1,2}:\d{2}(?:am|pm))", re.I)
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    current_date = None
    current_comp = "Football"
    out = []
    for line in lines:
        dm = date_re.match(line)
        if dm:
            try:
                current_date = datetime.strptime(f"{dm.group(2)} {dm.group(4)} {NOW.year}", "%d %B %Y").replace(tzinfo=TZ)
            except Exception:
                current_date = None
            continue
        if comp_re.match(line):
            current_comp = line
            continue
        fm = fixture_re.search(line)
        if not fm or not current_date:
            continue
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
    return out


def sky_last_result() -> dict | None:
    # Search recent Sky match pages from links on this month's Arsenal page, newest first.
    month_url = f"https://www.skysports.com/arsenal-scores-fixtures/{NOW.year}-{NOW.month:02d}-01"
    html, _ = get_html(month_url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/football/" in href and "arsenal" in (a.get_text(" ", strip=True) + " " + href).lower():
            if href.startswith("/"):
                href = "https://www.skysports.com" + href
            links.append(href)
    seen = set()
    for href in reversed(links):
        if href in seen:
            continue
        seen.add(href)
        page, final_url = get_html(href)
        if not page:
            continue
        text = BeautifulSoup(page, "html.parser").get_text(" ", strip=True)
        if "Full Time" not in text and " FT " not in f" {text} ":
            continue
        m = re.search(r"Arsenal\s+(\d+)\s+.*?([A-Z][A-Za-z .'-]+)\s+(\d+)", text)
        if not m:
            m = re.search(r"([A-Z][A-Za-z .'-]+)\s+(\d+)\s+.*?Arsenal\s+(\d+)", text)
            if not m:
                continue
            opponent, o_score, a_score = m.group(1).strip(), m.group(2), m.group(3)
            home_away = "away"
        else:
            a_score, opponent, o_score = m.group(1), m.group(2).strip(), m.group(3)
            home_away = "home"
        date_match = re.search(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})(st|nd|rd|th)\s+([A-Za-z]+)\s+(\d{4})", text)
        if date_match:
            try:
                dt = datetime.strptime(f"{date_match.group(2)} {date_match.group(4)} {date_match.group(5)}", "%d %B %Y").replace(tzinfo=TZ)
            except Exception:
                dt = NOW
        else:
            dt = NOW
        comp = "Friendly Match" if "Friendly Match" in text else "FA Community Shield" if "Community Shield" in text else "Premier League" if "Premier League" in text else "Football"
        return {
            "date": dt.isoformat(), "dateLabel": dt.strftime("%a %-d %b"), "kickoff": "",
            "opponent": opponent, "competition": comp, "homeAway": home_away,
            "completed": True, "arsenalScore": int(a_score), "opponentScore": int(o_score),
            "result": f"{a_score}–{o_score}", "url": final_url, "source": "Sky Sports",
        }
    return None


def premier_league_fixture_fallback() -> dict | None:
    # Official PL page is our league cross-check when Sky parsing is unavailable.
    html, url = get_html("https://www.premierleague.com/en/news/4675132/all-of-arsenals-fixtures-for-202627-premier-league-season")
    if not html:
        return None
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    # Search only for fixtures on/after today and choose the nearest date.
    months = {m:i for i,m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"],1)}
    pat = re.compile(r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})\s+([A-Za-z]+)(?:\s+(\d{4}))?\s+(?:(\d{1,2}:\d{2})\s+)?(Arsenal\s+v\s+[^\n]+?|[^\n]+?\s+v\s+Arsenal)")
    candidates = []
    for m in pat.finditer(text):
        mon = months.get(m.group(3))
        if not mon:
            continue
        year = int(m.group(4) or NOW.year)
        dt = datetime(year, mon, int(m.group(2)), tzinfo=TZ)
        if m.group(5):
            hh, mm = map(int, m.group(5).split(":")); dt = dt.replace(hour=hh, minute=mm)
        if dt < NOW - timedelta(hours=3):
            continue
        fixture = m.group(6)
        home = fixture.split(" v ")[0].strip(); away = fixture.split(" v ")[1].strip()
        opponent = away if home.lower() == "arsenal" else home
        candidates.append({"date":dt.isoformat(),"dateLabel":dt.strftime("%a %-d %b"),"kickoff":dt.strftime("%-I:%M%p").lower().replace(":00", "") if m.group(5) else "TBC","opponent":opponent,"competition":"Premier League","homeAway":"home" if home.lower()=="arsenal" else "away","completed":False,"arsenalScore":None,"opponentScore":None,"result":"","url":url,"source":"PremierLeague.com"})
    return min(candidates, key=lambda x: x["date"]) if candidates else None


def espn_snapshot() -> tuple[list[dict], int | None, int | None, int | None]:
    competitions = {"eng.1":"Premier League","eng.fa":"FA Cup","eng.league_cup":"League Cup","uefa.champions":"Champions League","eng.charity":"Community Shield"}
    fixtures = []
    for code, name in competitions.items():
        for url in [f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/{ARSENAL_ID}/schedule?season={SEASON}",f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/arsenal/schedule?season={SEASON}"]:
            data = get_json(url); parsed = [parse_fixture(e,name) for e in data.get("events",[]) or []]; parsed = [x for x in parsed if x]
            if parsed:
                fixtures.extend(parsed); break
    position = points = played = None
    table = get_json(f"https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings?season={SEASON}")
    entries=[]
    for group in table.get("children",[]) or []:
        entries.extend((group.get("standings",{}) or {}).get("entries",[]) or [])
    for entry in entries:
        if "arsenal" not in entry.get("team",{}).get("displayName","").lower(): continue
        stats={s.get("name"):s.get("value") for s in entry.get("stats",[])}
        position=int(stats["rank"]) if stats.get("rank") else None; points=int(stats["points"]) if stats.get("points") is not None else None; played=int(stats["gamesPlayed"]) if stats.get("gamesPlayed") is not None else None; break
    return fixtures, position, points, played


def snapshot(existing_news: list[dict]) -> dict:
    espn_fixtures, position, points, played = espn_snapshot()
    sky = sky_month_matches()
    all_fixtures = sky + espn_fixtures
    unique={}
    for item in all_fixtures:
        unique.setdefault((item["date"],item["opponent"],item["competition"]),item)
    fixtures=sorted(unique.values(),key=lambda x:x["date"])
    past=[x for x in fixtures if x.get("completed")]
    future=[x for x in fixtures if not x.get("completed") and dateparser.parse(x["date"])>=NOW-timedelta(hours=3)]
    last_result = sky_last_result() or (past[-1] if past else None)
    next_fixture = (future[0] if future else None) or premier_league_fixture_fallback()
    return {"lastResult":last_result,"nextFixture":next_fixture,"leaguePosition":position,"points":points,"played":played,"news":existing_news[:5],"sources":["Sky Sports","PremierLeague.com","Arsenal.com","ESPN"]}


def main() -> None:
    path=DATA/"pete.json"
    payload=json.loads(path.read_text(encoding="utf-8"))
    news=(payload.get("sections") or {}).get("Arsenal news",[])
    payload["arsenal"]=snapshot(news)
    path.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Arsenal enrichment complete")

if __name__=="__main__":
    main()
