from __future__ import annotations

import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo


def safe_strftime(dt: date | datetime, fmt: str) -> str:
    if sys.platform == "win32":
        fmt = fmt.replace("%-d", "%#d").replace("%-I", "%#I")
    return dt.strftime(fmt)

from io import BytesIO
import hashlib
from PIL import Image, ImageOps
import feedparser
import requests
from dateutil import parser as dateparser
try:
    from scripts.paywall import is_paywalled, paywalled_url, without_paywalled
except ModuleNotFoundError:
    from paywall import is_paywalled, paywalled_url, without_paywalled
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
SCENERY_IMAGE_DIR = ROOT / "assets" / "scenery"
TZ = ZoneInfo("Europe/London")
NOW = datetime.now(TZ)
UA = {"User-Agent": "DailyBriefs/3.0 (+https://github.com/PostWorkCulture/daily-briefs)"}
LAT = 51.400
LON = -0.366
FACT_CATALOG = DATA / "fact-catalog.json"
FACT_HISTORY = DATA / "fact-history.json"
NON_MENS_ARSENAL = re.compile(
    r"\b(?:u[-\s]?(?:18|19|21|23)s?|under[-\s]?(?:18|19|21|23)s?|academy|"
    r"youth|women(?:['’]?s)?|girls?)\b",
    re.I,
)


def first_team_arsenal_news(items: list[dict]) -> list[dict]:
    return [
        item for item in editorial_news(items)
        if not NON_MENS_ARSENAL.search(
            " ".join(str(item.get(key, "")) for key in ("title", "summary", "source"))
        )
    ]

WEATHER_LABELS = {
    0: "Clear", 1: "Mostly clear", 2: "Partly cloudy", 3: "Cloudy",
    45: "Foggy", 48: "Foggy", 51: "Light drizzle", 53: "Drizzle",
    55: "Heavy drizzle", 61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow", 80: "Showers",
    81: "Showers", 82: "Heavy showers", 95: "Thunderstorms",
}


LOCAL_NEWS_HOME_QUERIES = (
    '("West Molesey" OR "East Molesey")',
    '(Molesey AND (Surrey OR Elmbridge OR Thames OR "Hurst Park" OR "Hurst Pool" OR "Molesey Heath" OR "Apps Court"))',
    'site:elmbridge.gov.uk (Molesey OR Hurst OR "West Molesey" OR "East Molesey")',
    'site:bbc.co.uk/news ("East Molesey" OR "West Molesey" OR Molesey)',
    'site:surreycomet.co.uk ("West Molesey" OR "East Molesey" OR Molesey)',
    'site:surreylive.news ("West Molesey" OR "East Molesey" OR Molesey)',
)
LOCAL_NEWS_QUERIES = (
    '("Kingston upon Thames" OR "Kingston Surrey" OR Surbiton)',
    '("Hampton Court" OR Teddington OR "Hampton Wick" OR "Hampton Hill" OR "Bushy Park")',
    '(Hampton AND (London OR Surrey OR Richmond))',
    '("Walton-on-Thames" OR "Walton on Thames" OR Hersham)',
    '("Thames Ditton" OR "Long Ditton" OR "Hinchley Wood" OR Esher OR "Sunbury-on-Thames")',
)
LOCAL_NEWS_PUBLICATION_QUERIES = (
    'site:kingston.nub.news (Kingston OR Surbiton OR "Hampton Wick")',
    'site:teddington.nub.news (Teddington OR "Hampton Wick" OR "Bushy Park")',
    'site:weybridgeandwalton.nub.news ("Walton-on-Thames" OR Hersham)',
    'site:richmondandtwickenhamtimes.co.uk (Teddington OR Hampton OR "Bushy Park")',
    'site:surreycomet.co.uk (Kingston OR Surbiton OR Teddington OR "Thames Ditton")',
    'site:surreylive.news (Kingston OR Teddington OR Walton OR Esher OR Hersham)',
)
LOCAL_NEWS_FAMILY_QUERIES = (
    '("West Molesey" OR "East Molesey" OR Molesey OR Kingston OR Surbiton OR Teddington OR Hampton) '
    '(family OR kids OR children OR festival OR park OR Halloween OR Christmas)',
    '("Hampton Court" OR "Walton-on-Thames" OR Hersham OR Esher OR "Thames Ditton") '
    '(family OR kids OR children OR festival OR event OR trail OR workshop OR "open day")',
)
LOCAL_NEWS_PLACE_EVIDENCE = (
    re.compile(r"\b(?:east|west)\s+molesey\b|\bmolesey\b", re.I),
    re.compile(r"\bkingston\s+upon(?:-|\s+)thames\b", re.I),
    re.compile(r"\bhampton\s+(?:court|wick|hill)\b|\bhampton\s*(?:&|and)\s*richmond\b", re.I),
    re.compile(r"\bteddington\b|\bbushy\s+park\b", re.I),
    re.compile(r"\bwalton(?:-|\s+)on(?:-|\s+)thames\b|\bwalton\s*(?:&|and)\s*hersham\b", re.I),
    re.compile(r"\b(?:thames|long)\s+ditton\b|\bhinchley\s+wood\b", re.I),
    re.compile(r"\besher\b|\bhersham\b|\bsurbiton\b|\bsunbury(?:-|\s+)on(?:-|\s+)thames\b", re.I),
    re.compile(r"\bhurst\s+(?:park|pool)\b|\bmolesey\s+(?:heath|lock|boat\s+club)\b|\bapps\s+court\s+farm\b|\bimber\s+court\b", re.I),
)
LOCAL_HOME_AREA_PLACES = re.compile(
    r"\b(?:west\s+molesey|east\s+molesey|molesey|hurst\s+(?:park|pool)|molesey\s+(?:heath|lock|boat\s+club)|apps\s+court\s+farm|imber\s+court)\b",
    re.I,
)
LOCAL_NEWS_FALSE_LOCATIONS = re.compile(
    r"\b(?:kingston\s+upon\s+hull|kingston,?\s+(?:jamaica|ontario|rhode\s+island|tennessee|tasmania)|"
    r"east\s+hampton|hampton\s+roads|hampton\s+university|hampton\s+(?:inn|by\s+hilton)|the\s+hamptons|"
    r"walton\s+county|walton[-\s]le[-\s]dale|walton[-\s]on[-\s]the[-\s]naze|walton\s+goggins|"
    r"virginia|tasmania|australia|forest\s+park,?\s+ga|georgia|ireland|jamaica|ontario|hagley park road|Omarion Hampton|Drake London)\b",
    re.I,
)
LOCAL_NEWS_FOREIGN_OR_LOW_VALUE_SOURCE = re.compile(
    r"\b(?:WTKR|IRIE FM|Jamaica Gleaner|Tasmanian Country|Teagasc|Legacy obituary|funeral home|obituary|YouTube|"
    r"BettingOdds|Betting|Gambling|Casino|Oddschecker|The Rugby Paper|The Non-League Football Paper|FotMob|Transfermarkt|"
    r"[A-Za-z]+ (?:FC|RFC|CC|Football Club|Rugby Club))\b",
    re.I,
)
LOCAL_NEWS_LOW_VALUE_CONTENT = re.compile(
    r"\b(?:obituary|funeral home|death notice|property listing|houses? for sale|jobs? available|"
    r"MOT|weather forecast|sponsored content|advertorial|download[^.]{0,80}\bapp)\b",
    re.I,
)
LOCAL_NEWS_WHATS_ON = re.compile(
    r"\b(?:what['’]?s\s+(?:going\s+)?on|what\s+is\s+(?:going\s+)?on|things\s+to\s+do)\b",
    re.I,
)
LOCAL_NEWS_PUBLICATIONS = re.compile(
    r"\b(?:Surrey Comet|Surrey Live|Kingston Nub News|Teddington Nub News|"
    r"Weybridge and Walton Nub News|Richmond and Twickenham Times|Molesey Matters|"
    r"Elmbridge Today|This Is Local London|MyLondon|Elmbridge Borough Council|London Daily News)\b",
    re.I,
)
LOCAL_FAMILY_ACTIVITY = re.compile(
    r"\b(?:child-friendly|festival|fete|fair|carnival|fun day|family day|kids? day|"
    r"Halloween|Christmas|Easter|half[- ]term|school holiday|playground|trail|"
    r"workshop|open day|activities|fireworks|lantern|grotto|"
    r"pumpkin|Santa|outdoor cinema|fun day)\b",
    re.I,
)
LOCAL_SPORT_TOPIC = re.compile(
    r"\b(?:football|rugby|cricket|hockey|tennis|netball|basketball|golf|cycling|"
    r"athletics|swimming|rowing|fixture|match|league|cup|tournament|FC|RFC|CC|unbeaten|derby|clash|side|team|hosts?|"
    r"women|men|season|forward|striker|winger|midfielder|defender|goalkeeper|players?|squad|injur(?:y|ies))\b",
    re.I,
)
LOCAL_SPORT_RESULT = re.compile(
    r"\b(?:score|result|match report|match sheet|beat|beats|beaten|defeat|defeats|defeated|"
    r"win|wins|won|loss|lost|draw|drew|victory|goals?|points?|innings|wickets?|"
    r"fixture|standings|table|round-up|roundup|vs\.?|v\b|head-to-head|stats|on loan|signing|signs|transfer|"
    r"injur(?:y|ies)|squad|players?)\b|\b\d+\s*[-–]\s*\d+\b",
    re.I,
)
LOCAL_SPORT_EXCEPTION = re.compile(
    r"\b(?:open|opens|opened|opening|unveil|unveils|unveiled|launch|launches|launched|"
    r"new\s+(?:manager|owner|facility|venue|pitch|ground|sports centre|clubhouse|investment|rules?)|"
    r"refurbish|refurbished|redevelop|redeveloped|expansion|major change|"
    r"closure|closes|relocat|merger|takeover|community pitch|sports centre|sports hub|"
    r"major event|festival|sports day|open day|fun run|marathon|regatta|"
    r"get involved|sign up)\b",
    re.I,
)
TOPIC_ONLY_TITLES = frozenset({
    'east molesey', 'west molesey', 'molesey', 'kingston', 'kingston upon thames',
    'teddington', 'surbiton', 'hersham', 'esher', 'walton', 'walton-on-thames',
    'walton on thames', 'hampton', 'hampton court', 'hampton wick', 'hampton hill',
    'bushy park', 'thames ditton', 'long ditton', 'hinchley wood', 'sunbury',
    'sunbury-on-thames'
})

UK_POSITIVE_NEWS_QUERIES = (
    '("United Kingdom" OR Britain OR British OR England OR Scotland OR Wales OR "Northern Ireland") '
    '(breakthrough OR "promising trial" OR "new treatment" OR "new test" OR discovery OR innovation OR "save lives")',
    '("United Kingdom" OR Britain OR British OR England OR Scotland OR Wales OR "Northern Ireland") '
    '(charity OR community OR volunteer OR reunited OR rescued OR restored OR reopened OR celebrates OR award OR milestone OR fundraising)',
    '("United Kingdom" OR Britain OR British OR England OR Scotland OR Wales OR "Northern Ireland") '
    '(conservation OR renewable OR "clean energy" OR "jobs created" OR "new homes" OR investment OR funding OR regeneration OR "record low")',
    '(Britain OR England OR Scotland OR Wales) ("NHS trial" OR "charity raises" OR "species returns" OR "free school meals" OR "community opens")',
    'site:positive.news (UK OR Britain OR England OR Scotland OR Wales)',
)
UK_POSITIVE_NEWS_EVIDENCE = re.compile(
    r"\b(?:good news|breakthrough|promising (?:clinical |medical )?(?:trial|treatment|results)|"
    r"improv(?:e[ds]?|ement|ing)|rescu(?:e[ds]?|ing)|saved?|"
    r"reunit(?:e[ds]?|ing)|recover(?:y|ed|ing|s)?|restor(?:e[ds]?|ation|ing)|"
    r"reopen(?:s|ed|ing)? (?:to|for|after)|(?:station|museum|library|park|centre|community service) (?:reopens?|opens?)|"
    r"award(?:ed|s)?|honou?red|milestone|"
    r"celebrat(?:e[ds]?|ing)|record[- ]breaking|discover(?:y|ed|ies)|innovation|"
    r"new treatment|new (?:medical|diagnostic|screening|health) test|can spot|"
    r"save lives?|life[- ]saving|fundrais(?:er|ing)|"
    r"raises? (?:£|\$|€|\d)|donat(?:e[ds]?|ion|ions|ing)|volunteer(?:s|ed|ing)?|"
    r"funding (?:secured|awarded|announced)|investment (?:secured|announced)|"
    r"grants? (?:awarded|secured)|(?:jobs?|apprenticeships?) (?:created|secured|saved)|"
    r"new (?:jobs|apprenticeships?|homes|schools|hospitals?|services?)|species (?:returns?|recovers?)|"
    r"population (?:recovers?|rebounds?)|clean energy|renewable|cuts? emissions|"
    r"record low|free (?:meals|care|support|travel|classes))\b",
    re.I,
)
UK_NEGATIVE_NEWS_EVIDENCE = re.compile(
    r"\b(?:murder(?:ed|s)?|killed|killing|dead|deaths?|dies?|fatal(?:ity|ities)?|"
    r"attack(?:ed|s)?|war|bomb(?:ing|ed|s)?|explosion|shoot(?:ing|s)?|"
    r"stab(?:bing|bed|s)?|rape|sexual assault|abuse|terror(?:ism|ist)?|hostage|"
    r"genocide|death penalty|pleads? (?:guilty|not guilty)|charged with|arrest(?:ed|s)?|"
    r"jailed|prison sentence|police hunt|crash(?:ed|es)?|collision|disaster|"
    r"earthquake|wildfire|flood(?:ing|ed|s)?|crisis|emergency|outbreak|shortage|"
    r"collapse|bankrupt(?:cy)?|funding cuts?|spending cuts?|job losses|layoffs?|"
    r"closures?|scandal|fraud|corruption|protest(?:s|ers)?|strike action|warning|"
    r"threat(?:ens?|ened)?|fears?|concerns?|at risk|long waits?|waiting list|"
    r"mental health crisis|homeless(?:ness)?|poverty|sanctions?|invades?|air strike|"
    r"drone attack|territorial dispute|sovereignty|Falklands|demands?|denied|denials?|"
    r"tribunals?|boxing talks?|talks reopened|clock starts ticking|race to buy|ends? (?:its|their|her|his)|axed)\b",
    re.I,
)

SECTION_CONTENT_TYPES = {
    "Local news": "article",
    "UK news": "article",
    "Sweden": "article",
    "AI": "article",
    "Arsenal news": "article",
    "Career": "job",  # legacy validation only; no longer generated
    "Fun": "activity",
}
JOB_BOARD_SOURCE = re.compile(
    r"\b(?:Indeed|CV[- ]Library|Totaljobs|Reed(?:\.co\.uk)?|LinkedIn Jobs?|Glassdoor|"
    r"Adzuna|Jobsite|Jobs24|NHS Jobs?|Civil Service Jobs?|JobServe|Monster Jobs?)\b",
    re.I,
)
JOB_VACANCY_LANGUAGE = re.compile(
    r"\b(?:vacanc(?:y|ies)|job (?:advert|listing|opening|opportunit(?:y|ies))|"
    r"now hiring|hiring now|we(?:'re| are) hiring|join our team|apply now|"
    r"applications? (?:are )?(?:open|close|closing)|closing date|candidate pack)\b",
    re.I,
)
JOB_COMPENSATION_LANGUAGE = re.compile(
    r"(?:£\s?\d[\d,]*(?:\.\d+)?(?:\s?[kK])?(?:\s*[-–]\s*£?\s?\d[\d,]*(?:\.\d+)?(?:\s?[kK])?)?"
    r"\s*(?:per annum|p\.?a\.?|a year|plus benefits)|\bsalary\s*[:\-–]?\s*£)",
    re.I,
)
# Contractor adverts often omit the word "job" and use abbreviated pay units.
JOB_CONTRACT_RATE = re.compile(
    r"£\s?\d[\d,]*(?:\.\d+)?(?:\s*[-–]\s*£?\s?\d[\d,]*(?:\.\d+)?)?"
    r"\s*(?:p\.?[dh]\.?\b|/\s*(?:day|hour|hr)\b|per\s+(?:day|hour)\b|a\s+(?:day|hour)\b)",
    re.I,
)
JOB_ROLE_TITLE = re.compile(
    r"^(?:(?:senior|junior|lead|principal|contract|cybersecurity|software|data|business|"
    r"IT|AI|digital|project|programme|support|service|delivery|technical)\s+){0,5}"
    r"(?:engineer|analyst|developer|manager|consultant|architect|officer|administrator)\b",
    re.I,
)
# Local publishers (e.g. Nub News) syndicate bare "<Role> - <Place>" vacancy titles such as
# "Mobile Vehicle Technician - Esher" with no pay, IR35 or vacancy wording.
JOB_ROLE_PLACE_TITLE = re.compile(
    r"^(?:[A-Z][\w&/'’.]*\s+){0,4}"
    r"(?i:technician|engineer|mechanic|electrician|plumber|assistant|administrator|"
    r"co-?ordinator|advis[eo]r|operative|driver|cleaner|receptionist|supervisor|manager|"
    r"apprentice|officer|executive|consultant|nurse|carer|care worker|chef|cook|teacher|"
    r"analyst|developer|designer|specialist|associate|controller|planner|surveyor|"
    r"bookkeeper|accountant|porter|caretaker|valeter)\s*[-–|]\s*"
    r"[A-Z][\w'’.]*(?:\s+(?:upon|on|under|in|[A-Z][\w'’.]*)){0,3}(?:\s*\((?i:hybrid|remote|on-?site)\))?$",
)
JOB_URL_PATH = re.compile(r"https?://[^\s/]+/(?:[^\s?#]*/)?(?:jobs?|careers?|vacancies)(?:[/?#]|$)", re.I)
# Search feeds also index publisher recruitment directories and round-ups.
# Their Google News redirect hides the destination path and they may have no salary.
JOB_DIRECTORY_TITLE = re.compile(
    r"^(?:(?:latest|local|new|current|available|featured|this week['’]s)\s+)*"
    r"jobs?(?:\s+(?:in|near|at|with|available|of the week)\b|\s*[|:–-]|$)"
    r"|\b(?:job listings?|job search|jobs? round[- ]?up|jobs? of the week|"
    r"(?:browse|search|find|view)\s+(?:(?:all|local|latest|new)\s+)*jobs)\b",
    re.I,
)

JOB_SCHEMA_FIELDS = frozenset({"company", "salary", "postedDate", "location", "sector", "aiRelated"})


def world_fact_for_today() -> dict:
    try:
        catalog = json.loads(FACT_CATALOG.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Fact catalogue unavailable: {exc}") from exc
    if not isinstance(catalog, list) or not catalog:
        raise RuntimeError("Fact catalogue is empty")

    required = {"id", "category", "country", "locationContext", "place", "source", "sourceUrl", "image", "imagePage", "photoCredit", "fact"}
    ids, fact_texts = [], []
    for item in catalog:
        missing = sorted(required - set(item))
        if missing:
            raise RuntimeError(f"Fact {item.get('id', '<unknown>')} is missing: {', '.join(missing)}")
        ids.append(str(item["id"]).strip())
        fact_texts.append(re.sub(r"\W+", "", str(item["fact"]).lower()))
    if len(ids) != len(set(ids)):
        raise RuntimeError("Fact catalogue contains duplicate IDs")
    if len(fact_texts) != len(set(fact_texts)):
        raise RuntimeError("Fact catalogue contains repeated fact text")

    if FACT_HISTORY.exists():
        history = json.loads(FACT_HISTORY.read_text(encoding="utf-8"))
    else:
        history = {"version": 1, "used": []}
    used = history.get("used")
    if not isinstance(used, list):
        raise RuntimeError("Fact history is malformed")
    used_ids = [str(row.get("id") or "") for row in used]
    used_dates = [str(row.get("date") or "") for row in used]
    if len(used_ids) != len(set(used_ids)):
        raise RuntimeError("Fact history already contains a repeated fact ID")
    if len(used_dates) != len(set(used_dates)):
        raise RuntimeError("Fact history contains more than one fact for a date")
    unknown = sorted(set(used_ids) - set(ids))
    if unknown:
        raise RuntimeError(f"Fact history references unknown IDs: {', '.join(unknown)}")

    today = NOW.date().isoformat()
    today_row = next((row for row in used if row.get("date") == today), None)
    if today_row:
        selected_id = today_row["id"]
    else:
        unused = [
            item for item in catalog
            if item["id"] not in set(used_ids) and item.get("editorialStatus") != "retired"
        ]
        # A fact's source link must be readable without a subscription.
        unused = [item for item in unused if not paywalled_url(item.get("sourceUrl"))]
        human_first = [item for item in unused if item.get("editorialPriority") == "human-first"]
        # Wild, jaw-dropping facts (tribes, rituals, records, extreme places) lead the queue.
        wild = [item for item in human_first if item.get("editorialBoost") == "wild"]
        pool = wild or human_first
        previous_id = used[-1].get("id") if used else None
        previous = next((item for item in catalog if item["id"] == previous_id), None)
        previous_category = str((previous or {}).get("category") or "").casefold()
        # Avoid two consecutive days of the same kind of fact when another is available.
        selected = next(
            (item for item in pool if str(item.get("category") or "").casefold() != previous_category),
            pool[0] if pool else None,
        )
        if selected is None:
            raise RuntimeError("Human-first fact catalogue exhausted; refusing to publish a general fallback")
        selected_id = selected["id"]
        used.append({"date": today, "id": selected_id})
        history["version"] = 1
        FACT_HISTORY.write_text(json.dumps(history, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    item = next(item for item in catalog if item["id"] == selected_id)
    result = dict(item)
    result.update({"date": today, "sequence": next(i for i, row in enumerate(used, 1) if row["id"] == selected_id)})
    return result


def cache_world_fact_image(fact: dict) -> None:
    src = str(fact.get("image") or "")
    if not src.startswith("https://"):
        return
    output = SCENERY_IMAGE_DIR / "world-fact.webp"
    SCENERY_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(
            src,
            headers={**UA, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"},
            timeout=25,
        )
        response.raise_for_status()
        image = ImageOps.exif_transpose(Image.open(BytesIO(response.content))).convert("RGB")
        image.save(output, "WEBP", quality=85, method=6)
    except Exception as exc:
        # Never pair today's fact with yesterday's photo: drop the stale cache
        # so the card shows no image rather than the wrong place.
        output.unlink(missing_ok=True)
        warn("World fact image", f"{fact.get('id')}: image could not be cached ({exc}); no photo published")
        return
    if output.is_file():
        digest = hashlib.sha256(output.read_bytes()).hexdigest()[:12]
        fact["localImage"] = f"assets/scenery/world-fact.webp?v={digest}"


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def best_outdoor_window(times: list[str], rain: list, codes: list) -> dict:
    candidates = []
    for ts, pop, code in zip(times, rain, codes):
        try:
            dt = datetime.fromisoformat(ts).replace(tzinfo=TZ)
        except Exception:
            continue
        if dt.date() != NOW.date() or not (8 <= dt.hour <= 20):
            continue
        pop = int(pop or 0)
        code = int(code or 0)
        score = pop + (30 if code >= 61 else 12 if code >= 51 else 0)
        candidates.append((dt, score, pop, code))
    if not candidates:
        return {"label": "Check the hourly forecast", "detail": "No clear outdoor window available."}

    best = min(candidates, key=lambda x: x[1])
    threshold = min(best[1] + 10, 30)
    good = [x for x in candidates if x[1] <= threshold]
    # Find the longest useful contiguous block containing the best hour.
    blocks, block = [], []
    for item in good:
        if block and item[0] - block[-1][0] != timedelta(hours=1):
            blocks.append(block); block = []
        block.append(item)
    if block: blocks.append(block)
    chosen = next((b for b in blocks if any(x[0] == best[0] for x in b)), [best])
    start, end = chosen[0][0], chosen[-1][0] + timedelta(hours=1)
    label = f"{start.strftime('%-I%p').lower()}–{end.strftime('%-I%p').lower()}"
    avg_rain = round(sum(x[2] for x in chosen) / len(chosen))
    condition = WEATHER_LABELS.get(best[3], "Settled")
    detail = f"Best window today · {condition.lower()} · about {avg_rain}% rain chance"
    return {"label": label, "detail": detail}


def weather() -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": "temperature_2m,weather_code",
        "hourly": "temperature_2m,precipitation_probability,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "timezone": "Europe/London",
        "forecast_days": 7,
    }
    try:
        r = requests.get(url, params=params, headers=UA, timeout=25)
        r.raise_for_status()
        d = r.json()
        temp = round(float(d["current"]["temperature_2m"]))
        code = int(d["current"].get("weather_code", 0))
        daily = []
        pops = d["daily"].get("precipitation_probability_max", [None] * len(d["daily"]["time"]))
        for day, hi, lo, wc, pop in zip(d["daily"]["time"], d["daily"]["temperature_2m_max"], d["daily"]["temperature_2m_min"], d["daily"]["weather_code"], pops):
            wc = int(wc)
            daily.append({
                "date": day, "high": round(hi), "low": round(lo),
                "summary": WEATHER_LABELS.get(wc, "Forecast"), "rainChance": pop,
                "weatherCode": wc,
            })
        hourly = d.get("hourly", {})
        outdoor = best_outdoor_window(
            hourly.get("time", []),
            hourly.get("precipitation_probability", []),
            hourly.get("weather_code", []),
        )
        return {
            "temp": f"{temp}°", "summary": WEATHER_LABELS.get(code, "Latest forecast"),
            "weatherCode": code, "daily": daily, "bestOutdoor": outdoor,
        }
    except Exception as exc:
        return {"temp": "—", "summary": "Weather unavailable", "daily": [], "bestOutdoor": {}, "error": str(exc)}


def google_news(query: str, limit: int = 6, max_age_days: int = 4) -> list[dict]:
    url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-GB&gl=GB&ceid=GB:en"
    feed = feedparser.parse(url)
    out, seen = [], set()
    for entry in feed.entries[:limit * 5]:
        raw = clean_html(entry.get("title", ""))
        source, title = "", raw
        if " - " in raw:
            title, source = raw.rsplit(" - ", 1)
        key = re.sub(r"\W+", "", title.lower())[:120]
        if not key or key in seen:
            continue
        published_at = ""
        try:
            dt = dateparser.parse(entry.get("published", "")).astimezone(TZ)
            if NOW - dt > timedelta(days=max_age_days):
                continue
            meta = safe_strftime(dt, "%a %-d %b")
            published_at = dt.isoformat()
        except Exception:
            meta = "Recent"
        seen.add(key)
        out.append({"title": title.strip(), "summary": "", "meta": meta, "publishedAt": published_at, "source": source.strip(), "url": entry.get("link", ""), "contentType": "article"})
        if len(out) >= limit:
            break
    return out


def rss(url: str, section: str, limit: int = 6, max_age_days: int = 4) -> list[dict]:
    feed = feedparser.parse(url); items = []; seen = set()
    for entry in feed.entries[:limit * 4]:
        title = clean_html(entry.get("title", "")); key = re.sub(r"\W+", "", title.lower())[:120]
        if not title or key in seen: continue
        summary = clean_html(entry.get("summary", ""))[:220]
        published_at = ""
        try:
            dt = dateparser.parse(entry.get("published", "")).astimezone(TZ)
            if NOW - dt > timedelta(days=max_age_days): continue
            meta = safe_strftime(dt, "%a %-d %b")
            published_at = dt.isoformat()
        except Exception: meta = section
        seen.add(key)
        items.append({"title": title, "summary": summary, "meta": meta, "publishedAt": published_at, "source": section, "url": entry.get("link", ""), "contentType": "article"})
        if len(items) >= limit: break
    return items


def merge_news(*groups: list[dict], limit: int) -> list[dict]:
    merged, seen = [], set()
    for group in groups:
        for item in group:
            title = clean_html(item.get("title", ""))
            url = str(item.get("url", "")).strip()
            key = re.sub(r"\W+", "", title.lower())[:120]
            if not title or not url or key in seen:
                continue
            seen.add(key)
            merged.append(item)
            if len(merged) >= limit:
                return merged
    return merged


def newest_news(items: list[dict], limit: int) -> list[dict]:
    """Put reliably dated stories first, newest to oldest, with undated items last."""
    return sorted(
        items,
        key=lambda item: str(item.get("publishedAt") or ""),
        reverse=True,
    )[:limit]


AI_ANTHROPIC = re.compile(r"\b(?:anthropic|claude)\b|(?:^|[/.])anthropic\.com", re.I)
AI_GOOGLE = re.compile(r"\b(?:google|deepmind|gemini|gemma)\b|(?:^|[/.])(?:google|deepmind)\.[a-z.]+", re.I)
GOOGLE_MAJOR_MODEL = re.compile(
    r"^(?:introducing\s+)?(?:gemini|gemma|veo|imagen|lyria|genie|alpha[a-z]+)\s+\d[\w.]*", re.I
)
GOOGLE_MAJOR_ACTION = re.compile(
    r"\b(?:launch(?:es|ed)?|unveil(?:s|ed)?|introduc(?:es|ing|ed)|announc(?:es|ed|ing)|"
    r"releas(?:es|ed)|rolls? out|now available|general availability|new (?:frontier )?model)\b",
    re.I,
)
GOOGLE_MINOR = re.compile(
    r"\b(?:tips?|how to|ways to|guide|responsibl[ey]|safely|safety|podcast|recap|behind the|"
    r"case study|collaborat\w*|partner\w*|customers?|students?|classroom|teachers?|"
    r"hackathon|webinar|workshop|award|q&a|interview|explainer)\b",
    re.I,
)
GOOGLE_AI_MAX = 2
ANTHROPIC_AI_MAX = 5


def ai_text(item: dict) -> str:
    # A Google News redirect URL says nothing about the story's company.
    url = re.sub(r"^https?://news\.google\.com\S*", "", str(item.get("url", "")), flags=re.I)
    return f"{item.get('title', '')} {item.get('source', '')} {item.get('summary', '')} {url}"


def is_anthropic_ai(item: dict) -> bool:
    return bool(AI_ANTHROPIC.search(ai_text(item)))


def is_google_ai(item: dict) -> bool:
    return not is_anthropic_ai(item) and bool(AI_GOOGLE.search(ai_text(item)))


def google_major_announcement(item: dict) -> bool:
    """Google/DeepMind/Gemini items qualify only as major launches or new models."""
    title = clean_html(item.get("title", ""))
    if GOOGLE_MINOR.search(title):
        return False
    return bool(GOOGLE_MAJOR_MODEL.search(title) or GOOGLE_MAJOR_ACTION.search(title))


def anthropic_first(items: list[dict]) -> list[dict]:
    """Anthropic/Claude stories always lead AI; Google keeps only major announcements."""
    def newest(group: list[dict]) -> list[dict]:
        return sorted(group, key=lambda x: str(x.get("publishedAt") or ""), reverse=True)

    anthropic = dedupe_ai_stories(newest([x for x in items if is_anthropic_ai(x)]))[:ANTHROPIC_AI_MAX]
    google = dedupe_ai_stories(newest([x for x in items if is_google_ai(x) and google_major_announcement(x)]))[:GOOGLE_AI_MAX]
    others = newest([x for x in items if not is_anthropic_ai(x) and not is_google_ai(x)])
    return dedupe_ai_stories(anthropic + google + others)


AI_STORY_STOPWORDS = frozenset("""
a an the and or but of in on at to for with by from as into over under about after before amid via vs
is are was were be been being has have had do does did will would could should may might can its it
this that these those new says said report reports reported according source sources exclusive live update
first more most than just now how why what who when where which here there not no up down out off
anthropic anthropics claude openai openais chatgpt google googles deepmind gemini meta microsoft nvidia apple amazon
deepseek qwen alibaba moonshot kimi baidu ernie zhipu minimax xai grok mistral ai artificial intelligence
model models company companies firm startup lab labs tech technology
""".split())
AI_STORY_SYNONYMS = {
    "subpoenaed": "subpoena", "subpoenas": "subpoena",
    "valuation": "value", "valued": "value", "valuations": "value",
    "lawsuit": "sue", "sues": "sue", "sued": "sue",
    "launches": "launch", "launched": "launch", "releases": "release", "released": "release",
}


def ai_story_tokens(item: dict) -> set[str]:
    words = re.findall(r"[a-z0-9$][a-z0-9.$]*", clean_html(item.get("title", "")).lower().replace("\u2019", "'"))
    tokens = set()
    for word in words:
        word = word.strip(".").replace("'s", "")
        word = AI_STORY_SYNONYMS.get(word, word)
        if len(word) < 2 or word in AI_STORY_STOPWORDS:
            continue
        tokens.add(word)
    return tokens


AI_STORY_COMPANY = re.compile(
    r"\b(anthropic|claude|openai|chatgpt|google|deepmind|gemini|meta|microsoft|nvidia|apple|amazon|"
    r"deepseek|qwen|alibaba|moonshot|kimi|baidu|ernie|zhipu|z\.ai|glm|minimax|bytedance|doubao|tencent|hunyuan|"
    r"xai|mistral)\b", re.I)
AI_COMPANY_ALIAS = {"claude": "anthropic", "chatgpt": "openai", "deepmind": "google", "gemini": "google",
                    "qwen": "alibaba", "kimi": "moonshot", "ernie": "baidu", "z.ai": "zhipu", "glm": "zhipu",
                    "doubao": "bytedance", "hunyuan": "tencent"}
CHINESE_AI_COMPANIES = frozenset({"deepseek", "alibaba", "moonshot", "baidu", "zhipu", "minimax", "bytedance", "tencent"})
AI_BUSINESS_TOPICS = {
    "value": {"value", "ipo", "valuation", "valued", "valuations"},
    "funding": {"funding", "raise", "raises", "raised", "round"},
    "legal": {"sue", "lawsuit", "court", "judge", "settle", "settlement", "dispute", "subpoena", "probe", "investigation"},
    "outage": {"outage", "down", "disruption"},
    "layoffs": {"layoffs", "layoff", "cuts", "jobs"},
    "deal": {"acquire", "acquires", "acquisition", "buy", "buys", "merger"},
}


def ai_story_company(item: dict) -> str:
    match = AI_STORY_COMPANY.search(clean_html(item.get("title", "")))
    if not match:
        return ""
    name = match.group(1).lower()
    return AI_COMPANY_ALIAS.get(name, name)


def ai_story_topics(item: dict) -> set[str]:
    words = set(re.findall(r"[a-z]+", clean_html(item.get("title", "")).lower()))
    words |= {AI_STORY_SYNONYMS.get(w, w) for w in words}
    return {topic for topic, vocab in AI_BUSINESS_TOPICS.items() if words & vocab}


def published_days_apart(left: dict, right: dict) -> float | None:
    try:
        a = datetime.fromisoformat(str(left.get("publishedAt")))
        b = datetime.fromisoformat(str(right.get("publishedAt")))
    except ValueError:
        return None
    return abs((a - b).total_seconds()) / 86400


AI_MODEL_NAME = re.compile(
    r"\b(gemini|gemma|claude(?: opus| sonnet| haiku| fable)?|gpt|o\d|llama|grok|mistral|deepseek(?:-v)?|qwen|kimi(?: k)?|glm|ernie|muse spark)"
    r"[\s-]?(\d+(?:\.\d+)?)\b",
    re.I,
)


def ai_model_names(item: dict) -> set[str]:
    title = clean_html(item.get("title", "")).lower()
    return {f"{m.group(1).replace('-v', '').strip()} {m.group(2)}" for m in AI_MODEL_NAME.finditer(title)}


def same_ai_story(left: dict, right: dict) -> bool:
    """Two items cover the same event when their distinctive title words overlap strongly,
    or when they report the same business development for the same company within two days."""
    left_url = str(left.get("url") or "").strip()
    if left_url and left_url == str(right.get("url") or "").strip():
        return True
    if ai_model_names(left) & ai_model_names(right):
        return True
    company = ai_story_company(left)
    if company and company == ai_story_company(right):
        gap = published_days_apart(left, right)
        if (gap is None or gap <= 2) and ai_story_topics(left) & ai_story_topics(right):
            return True
    a, b = ai_story_tokens(left), ai_story_tokens(right)
    if not a or not b:
        return False
    shared = a & b
    return len(shared) >= 2 or len(shared) / len(a | b) >= 0.5


def dedupe_ai_stories(items: list[dict]) -> list[dict]:
    """Keep the first (highest-priority) item for each event; drop later repeats."""
    kept: list[dict] = []
    for item in items:
        if not any(same_ai_story(item, existing) for existing in kept):
            kept.append(item)
    return kept


CHINESE_AI_LAB = re.compile(
    r"\b(?:deepseek|qwen|moonshot ai|kimi k\d|kimi(?= (?:ai|chatbot|model|app))|zhipu|z\.ai|glm-\d|minimax|"
    r"baidu(?=.{0,40}\b(?:ai|ernie|model)\b)|ernie(?: bot| \d)|alibaba(?=.{0,40}\b(?:ai|qwen|model)\b)|"
    r"bytedance(?=.{0,40}\b(?:ai|doubao|seed|model)\b)|doubao|tencent hunyuan|hunyuan)\b",
    re.I,
)
CHINESE_AI_NOISE = re.compile(r"\b(?:antonelli|r[aä]ikk[oö]nen|formula 1|f1|grand prix|stock picks?|shares? (?:rise|fall|jump|slump))\b", re.I)
CHINESE_AI_MAX = 3
CHINESE_AI_RETAIN_DAYS = 21


def chinese_ai_item(item: dict) -> bool:
    """A Chinese frontier lab must be the story's main subject, not a passing comparison."""
    title = clean_html(item.get("title", ""))
    if not CHINESE_AI_LAB.search(title) or CHINESE_AI_NOISE.search(title):
        return False
    return ai_story_company(item) in CHINESE_AI_COMPANIES


def previous_chinese_ai() -> list[dict]:
    """Last live-sourced Chinese-lab items, kept only while recent."""
    try:
        previous = json.loads((DATA / "pete.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    kept = []
    for item in (previous.get("sections") or {}).get("AI") or []:
        if not item.get("liveChineseLab") or not chinese_ai_item(item):
            continue
        try:
            published = datetime.fromisoformat(str(item.get("publishedAt")))
        except ValueError:
            continue
        if NOW - published <= timedelta(days=CHINESE_AI_RETAIN_DAYS):
            kept.append(item)
    return kept


def live_chinese_ai() -> list[dict]:
    """Current DeepSeek, Qwen, Moonshot/Kimi and other Chinese frontier-lab news."""
    fresh = google_news(
        '(DeepSeek OR Qwen OR "Moonshot AI" OR "Kimi K2" OR "Kimi K3" OR Zhipu OR MiniMax OR "Baidu ERNIE" OR Hunyuan OR Doubao) when:10d',
        30, 10,
    )
    candidates = [dict(item, liveChineseLab=True) for item in fresh if chinese_ai_item(item)]
    candidates = sorted(candidates, key=lambda x: str(x.get("publishedAt") or ""), reverse=True)
    candidates += previous_chinese_ai()
    pool = dedupe_ai_stories(editorial_news(candidates))
    # One story per lab first so DeepSeek, Qwen, Moonshot and others rotate; then fill by recency.
    picked, labs = [], set()
    for item in pool:
        lab = ai_story_company(item)
        if lab not in labs:
            picked.append(item)
            labs.add(lab)
    picked += [item for item in pool if item not in picked]
    return picked[:CHINESE_AI_MAX]


def news_item_is_job_vacancy(item: dict) -> bool:
    """Identify vacancy listings without rejecting reporting about jobs being created."""
    if str(item.get("contentType") or "").casefold() == "job":
        return True
    if len(JOB_SCHEMA_FIELDS.intersection(item)) >= 3:
        return True
    title = clean_html(str(item.get("title", "")))
    text = clean_html(" ".join(str(item.get(key, "")) for key in ("title", "summary", "source", "url")))
    return bool(
        re.search(r"\(\s*expired\s*\)", title, re.I)
        or JOB_BOARD_SOURCE.search(text)
        or JOB_VACANCY_LANGUAGE.search(text)
        or JOB_COMPENSATION_LANGUAGE.search(title)
        or JOB_CONTRACT_RATE.search(title)
        or JOB_DIRECTORY_TITLE.search(title)
        or JOB_ROLE_PLACE_TITLE.search(title.strip())
        or (JOB_ROLE_TITLE.search(title) and re.search(r"\b(?:inside|outside)\s+IR35\b", text, re.I))
        or JOB_URL_PATH.search(str(item.get("url", "")))
    )


REFERENCE_SOURCES = frozenset({"britannica", "encyclopaedia britannica", "encyclopedia britannica", "wikipedia", "investopedia", "dictionary.com", "merriam-webster"})


def reference_page(item: dict) -> bool:
    """Encyclopedia and dictionary entries are not news articles."""
    source = re.sub(r"\s+", " ", str(item.get("source") or "")).strip().casefold()
    url = str(item.get("url") or "")
    return source in REFERENCE_SOURCES or bool(re.search(r"https?://(?:[a-z]+\.)?(?:britannica\.com|wikipedia\.org|investopedia\.com)/", url, re.I))


def editorial_news_item_is_in_scope(item: dict) -> bool:
    """Allow only article-shaped, non-vacancy items into editorial destinations."""
    content_type = str(item.get("contentType") or "article").casefold()
    return (
        content_type == "article"
        and not news_item_is_job_vacancy(item)
        and not is_paywalled(item)
        and not reference_page(item)
    )


def editorial_news(items: list[dict], limit: int | None = None) -> list[dict]:
    """Quarantine non-articles and label every surviving editorial item explicitly."""
    articles = []
    for item in items:
        if not editorial_news_item_is_in_scope(item):
            continue
        article = dict(item)
        article["contentType"] = "article"
        articles.append(article)
    return articles if limit is None else articles[:limit]


def section_content_type_errors(sections: dict) -> list[str]:
    """Return hard publication errors for content placed in the wrong destination."""
    errors = []
    for section, expected_type in SECTION_CONTENT_TYPES.items():
        for index, item in enumerate(sections.get(section) or [], 1):
            actual_type = str(item.get("contentType") or "")
            title = clean_html(str(item.get("title") or "Untitled item"))
            if actual_type != expected_type:
                errors.append(
                    f"{section} item {index} has contentType {actual_type or '<missing>'}, "
                    f"expected {expected_type}: {title}"
                )
            if expected_type == "article" and news_item_is_job_vacancy(item):
                errors.append(f"{section} contains a job vacancy: {title}")
    return errors


def is_topic_page_only(title: str) -> bool:
    cleaned = re.sub(r"\s*-\s*BBC.*$", "", title, flags=re.I).strip().lower()
    return cleaned in TOPIC_ONLY_TITLES


def local_home_area_item(item: dict) -> bool:
    text = clean_html(" ".join(str(item.get(key, "")) for key in ("title", "summary")))
    return bool(LOCAL_HOME_AREA_PLACES.search(text))


def local_news_item_hub(item: dict) -> str:
    title_sum = clean_html(" ".join(str(item.get(k, "")) for k in ("title", "summary"))).lower()
    if LOCAL_HOME_AREA_PLACES.search(title_sum):
        return "molesey"
    if "surbiton" in title_sum:
        return "surbiton"
    if "kingston" in title_sum:
        return "kingston"
    if "teddington" in title_sum:
        return "teddington"
    if "hampton" in title_sum or "bushy" in title_sum:
        return "hampton"
    if "walton" in title_sum or "hersham" in title_sum:
        return "walton"
    if "ditton" in title_sum or "esher" in title_sum:
        return "esher"
    source = str(item.get("source", "")).lower()
    if "kingston" in source:
        return "kingston"
    if "teddington" in source:
        return "teddington"
    return "other"


def local_news_item_is_in_scope(item: dict) -> bool:
    """Require approved local evidence and reject routine sports coverage."""
    if is_paywalled(item):
        return False
    title = clean_html(str(item.get("title") or ""))
    if is_topic_page_only(title):
        return False
    text = clean_html(" ".join(str(item.get(key, "")) for key in ("title", "summary")))
    source = clean_html(str(item.get("source", "")))
    if (
        not editorial_news_item_is_in_scope(item)
        or not text
        or LOCAL_NEWS_FALSE_LOCATIONS.search(f"{text} {source}")
        or LOCAL_NEWS_FOREIGN_OR_LOW_VALUE_SOURCE.search(source)
        or LOCAL_NEWS_LOW_VALUE_CONTENT.search(text)
        or LOCAL_NEWS_WHATS_ON.search(text)
        or local_event_has_expired(item)
    ):
        return False
    local = any(pattern.search(text) for pattern in LOCAL_NEWS_PLACE_EVIDENCE) or bool(
        re.search(r"\b(?:kingston|hampton)\b", text, re.I)
        and (local_publication_item(item) or re.search(r"\b(?:Surrey|London|Thames|Richmond upon Thames)\b", text, re.I))
    )
    if not local:
        return False
    routine_sport = bool(re.search(r"\b(?:The Rugby Paper|The Non-League Football Paper|FotMob|Transfermarkt|[A-Za-z]+ (?:FC|RFC|CC|Football Club|Rugby Club))\b", source, re.I)) or bool(LOCAL_SPORT_TOPIC.search(text) and LOCAL_SPORT_RESULT.search(f"{text} {source}"))
    return not routine_sport or bool(LOCAL_SPORT_EXCEPTION.search(text))


def local_publication_item(item: dict) -> bool:
    text = " ".join(str(item.get(key, "")) for key in ("source", "url"))
    return bool(LOCAL_NEWS_PUBLICATIONS.search(text) or re.search(
        r"https?://(?:www\.)?(?:surreycomet\.co\.uk|surreylive\.news|kingston\.nub\.news|"
        r"teddington\.nub\.news|weybridgeandwalton\.nub\.news|richmondandtwickenhamtimes\.co\.uk|"
        r"elmbridge\.gov\.uk|londondaily\.news)/", text, re.I))


def local_event_has_expired(item: dict) -> bool:
    """Expire time-bound listings without treating dates in ordinary reporting as event dates."""
    title = clean_html(str(item.get("title") or ""))
    if not re.search(r"what['’]s on|things to do|this weekend|events? (?:this|today)|weekend weather", title, re.I):
        return False
    try:
        published = dateparser.parse(str(item.get("publishedAt") or "")).astimezone(TZ).date()
    except (ValueError, TypeError, OverflowError):
        return False
    if re.search(r"this weekend|what['’]s on|weekend weather", title, re.I):
        weekend_end = published + timedelta(days=(6 - published.weekday()) % 7)
        # Named forthcoming seasonal/event dates should not be treated as this week's listing.
        if not re.search(r"\b(?:Halloween|Christmas|Easter|next month)\b", title, re.I):
            return NOW.date() > weekend_end
    if re.search(r"\btoday\b", title, re.I):
        return NOW.date() > published
    return False


def local_family_activity_item(item: dict) -> bool:
    text = clean_html(" ".join(str(item.get(key, "")) for key in ("title", "summary")))
    return bool(LOCAL_FAMILY_ACTIVITY.search(text) and not re.search(
        r"adults?[- ]only|over[- ]18|nightclubs?|club night|beer festival|cocktail|bottomless brunch", text, re.I))


def select_local_news(items: list[dict], limit: int = 16) -> list[dict]:
    """Prioritise home area (Molesey), local publications and family activities, with hub balancing."""
    scoped = [item for item in items if local_news_item_is_in_scope(item)]
    prioritised = sorted(
        scoped,
        key=lambda item: (
            local_home_area_item(item),
            local_family_activity_item(item),
            local_publication_item(item),
            str(item.get("publishedAt") or ""),
        ),
        reverse=True,
    )
    selected: list[dict] = []
    selected_tokens: list[set[str]] = []
    selected_urls: set[str] = set()

    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from',
        'as', 'is', 'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'but', 'if', 'then', 'so', 'no', 'not', 'all', 'any', 'every', 'this', 'that', 'these',
        'those', 'what', 'which', 'who', 'whom', 'whose', 'when', 'where', 'why', 'how', 'about',
        'into', 'through', 'after', 'before', 'over', 'under', 'above', 'below', 'up', 'down', 'out',
        'off', 'again', 'further', 'once', 'here', 'there', 'both', 'each', 'few', 'more', 'most',
        'other', 'some', 'such', 'nor', 'only', 'own', 'same', 'than', 'too', 'very', 'can', 'will',
        'just', 'should', 'now', 'reveals', 'reveal', 'everything', 'know', 'latest', 'remains',
        'kingston', 'richmond', 'surrey', 'teddington', 'surbiton', 'elmbridge', 'london', 'borough',
        'council'
    }

    def item_tokens(item: dict) -> set[str]:
        text = clean_html(" ".join(str(item.get(k, "")) for k in ("title", "summary"))).lower()
        text = re.sub(r"\bblaze\b", "fire", text)
        return set(re.findall(r"[a-z0-9]+", text)) - stop_words

    hub_counts: dict[str, int] = {}
    hub_limits = {
        "kingston": 2,
        "teddington": 2,
        "surbiton": 1,
        "esher": 1,
        "hampton": 1,
        "walton": 1,
        "other": 1,
    }

    deferred = []
    for item in prioritised:
        canonical = str(item.get("url") or "").split('#', 1)[0].split('?', 1)[0].rstrip('/')
        if canonical and canonical in selected_urls:
            continue
        tokens = item_tokens(item)
        is_dup = False
        for prev in selected_tokens:
            shared = tokens & prev
            if (
                ('market' in shared and 'fire' in shared)
                or ('pub' in shared and ('outdoor' in shared or 'objections' in shared))
                or len(shared) >= 3
            ):
                is_dup = True
                break
        if is_dup:
            continue

        is_home = local_home_area_item(item)
        hub = local_news_item_hub(item)
        if not is_home and hub_counts.get(hub, 0) >= hub_limits.get(hub, 1):
            deferred.append((item, canonical, tokens))
            continue

        selected.append(item)
        if not is_home:
            hub_counts[hub] = hub_counts.get(hub, 0) + 1
        if canonical:
            selected_urls.add(canonical)
        selected_tokens.append(tokens)
        if len(selected) >= limit:
            break

    # Identify if home area items are selected and their newest date
    home_dates = [str(it.get("publishedAt") or "") for it in selected if local_home_area_item(it)]
    newest_home_date = max(home_dates) if home_dates else ""

    # Pass 2: Fill up to limit from deferred items with deduplication check
    if len(selected) < limit:
        for item, canonical, tokens in deferred:
            is_dup = False
            for prev in selected_tokens:
                shared = tokens & prev
                if len(shared) >= 3:
                    is_dup = True
                    break
            if is_dup:
                continue

            # If home area items exist, don't let deferred items newer than newest_home_date
            # push home area items past position 10 in the final newest_first order.
            item_date = str(item.get("publishedAt") or "")
            if newest_home_date and item_date > newest_home_date:
                newer_count = sum(1 for it in selected if str(it.get("publishedAt") or "") > newest_home_date)
                if newer_count >= 7:
                    continue

            selected.append(item)
            if canonical:
                selected_urls.add(canonical)
            selected_tokens.append(tokens)
            if len(selected) >= limit:
                break

    for item in selected:
        item["localPublication"] = local_publication_item(item)
        item["familyActivity"] = local_family_activity_item(item)
        item["homeArea"] = local_home_area_item(item)
    return newest_news(selected, limit)


def local_news() -> list[dict]:
    # Always search 30 days for Pete's immediate home area (Molesey/West Molesey),
    # and 14 days (extending to 30 days if needed) for neighbouring KT8 hubs.
    for max_age_days in (14, 30):
        with ThreadPoolExecutor(max_workers=8) as pool:
            home_groups = list(pool.map(
                lambda query: google_news(f'{query} when:30d', 32, 30),
                LOCAL_NEWS_HOME_QUERIES,
            ))
            other_queries = (
                *LOCAL_NEWS_QUERIES,
                *LOCAL_NEWS_PUBLICATION_QUERIES,
                *LOCAL_NEWS_FAMILY_QUERIES,
            )
            other_groups = list(pool.map(
                lambda query: google_news(f'{query} when:{max_age_days}d', 32, max_age_days),
                other_queries,
            ))
        candidates = merge_news(*home_groups, *other_groups, limit=512)
        scoped = [item for item in candidates if local_news_item_is_in_scope(item)]
        selected = select_local_news(scoped, 16)
        has_home = any(local_home_area_item(item) for item in selected)
        if (len(selected) >= 10 and has_home) or max_age_days == 30:
            return selected
    return []


def positive_uk_news_item_is_in_scope(item: dict) -> bool:
    """Keep explicitly uplifting stories and reject distressing or adversarial news."""
    text = clean_html(" ".join(str(item.get(key, "")) for key in ("title", "summary")))
    return bool(
        editorial_news_item_is_in_scope(item)
        and text
        and UK_POSITIVE_NEWS_EVIDENCE.search(text)
        and not UK_NEGATIVE_NEWS_EVIDENCE.search(text)
    )


def uk_news() -> list[dict]:
    # Use the BBC's UK feed plus targeted positive searches. Start with the
    # freshest fortnight and extend to 30 days only when needed for depth.
    # Never fill the section with a negative fallback.
    for max_age_days in (14, 30):
        with ThreadPoolExecutor(max_workers=6) as pool:
            groups = list(pool.map(
                lambda query: google_news(f'{query} when:{max_age_days}d', 48, max_age_days),
                UK_POSITIVE_NEWS_QUERIES,
            ))
        candidates = merge_news(rss('https://feeds.bbci.co.uk/news/uk/rss.xml', 'BBC News', 48, max_age_days), *groups, limit=320)
        positive = [item for item in candidates if positive_uk_news_item_is_in_scope(item)]
        if len(positive) >= 12 or max_age_days == 30:
            return newest_news(positive, 12)
    return []


TRUSTED_ARSENAL_TRANSFER_SOURCES = {
    "arsenal.com": "Official",
    "bbc sport": "Trusted report",
    "sky sports": "Trusted report",
    "the athletic": "Tier-one report",
    "the guardian": "Trusted report",
    "espn": "Trusted report",
    "the new york times": "Tier-one report",
}
X_TRANSFER_REPORTERS = (
    {"name": "David Ornstein", "handle": "David_Ornstein", "confidence": "Tier-one reporter", "profile": "https://x.com/David_Ornstein"},
    {"name": "Fabrizio Romano", "handle": "FabrizioRomano", "confidence": "Established reporter", "profile": "https://x.com/FabrizioRomano"},
    {"name": "Charles Watts", "handle": "charles_watts", "confidence": "Arsenal specialist", "profile": "https://x.com/charles_watts"},
    {"name": "James Benge", "handle": "jamesbenge", "confidence": "Arsenal specialist", "profile": "https://x.com/jamesbenge"},
)
TRANSFER_TERMS = re.compile(
    r"\b(?:transfer|sign(?:s|ed|ing)?|deal|move|bid|talks|loan|contract|exit|joins?|medical|target)\b",
    re.I,
)
TRANSFER_EXCLUSIONS = re.compile(
    r"\b(?:rumou?rs?|gossip|paper talk|odds|betting|women|women's|u21|u18|academy|girls|"
    r"vacanc(?:y|ies)|jobs?|careers?|creative|marketing|partnerships?|commercial)\b",
    re.I,
)
SPECULATION_EXCLUSIONS = re.compile(
    r"\b(?:paper talk|odds|betting|women|women's|u21|u18|academy|youth|girls)\b",
    re.I,
)
ARSENAL_FIGURES = re.compile(
    r"\b(?:arsenal|gunners|arteta|saka|odegaard|ødegaard|timber|saliba|havertz|calafiori|merino|raya)\b|"
    r"\bdeclan rice\b|\bben white\b|\bgabriel magalh[aã]es\b|\bgabriel martinelli\b",
    re.I,
)
OTHER_CLUBS_ONLY = re.compile(
    r"\b(?:tottenham|spurs|chelsea|manchester united|man utd|liverpool|man city|barcelona|real madrid|juventus|bayern)\b",
    re.I,
)


def news_timestamp(item: dict) -> float:
    value = str(item.get("publishedAt") or "").strip()
    if not value:
        return 0
    try:
        return dateparser.parse(value).timestamp()
    except Exception:
        return 0


def newest_first(items: list[dict]) -> list[dict]:
    return sorted(items, key=news_timestamp, reverse=True)


TRANSFER_NAME_STOPWORDS = {
    "arsenal", "transfer", "news", "sign", "signs", "signed", "signing",
    "join", "joins", "joined", "deal", "move", "loan", "contract", "target",
    "report", "official", "update", "first", "team", "player", "new", "the",
    "with", "from", "into", "amid", "after", "ahead", "agree", "agreed",
}
TRANSFER_STOPWORDS = {
    "arsenal", "transfer", "news", "sign", "signs", "signed", "signing",
    "join", "joins", "joined", "deal", "move", "loan", "contract", "target",
    "report", "official", "update", "first", "team", "player", "new", "the",
    "with", "from", "into", "amid", "after", "ahead", "agree", "agreed",
    "mikel", "arteta", "boss", "manager", "says", "admit", "admits", "rule",
    "rules", "out", "could", "will", "latest", "about",
}


def transfer_identity_words(title: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-zà-öø-ÿ'’-]{3,}", clean_html(title).lower())
        if word not in TRANSFER_NAME_STOPWORDS
    }


def transfer_subject_words(title: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-zà-öø-ÿ'’-]{3,}", clean_html(title).lower())
        if word not in TRANSFER_STOPWORDS
    }


def dedupe_transfer_updates(items: list[dict]) -> list[dict]:
    deduped = []
    seen_subjects = []
    for item in newest_first(items):
        title = item.get("title", "")
        subj = transfer_subject_words(title)
        if len(subj) >= 2 and any(len(subj & prev) >= 2 for prev in seen_subjects):
            continue
        if any(len(w) >= 5 and any(w in prev for prev in seen_subjects) for w in subj if w in ("dowman", "konsa", "sesko", "gyokeres", "zubimendi", "calafiori", "merino")):
            continue
        seen_subjects.append(subj)
        deduped.append(item)
    return deduped


def corroborating_transfer_report(item: dict, trusted_reports: list[dict]) -> dict | None:
    """Return independent corroboration for an official first-team transfer item."""
    identity = transfer_identity_words(item.get("title", ""))
    if len(identity) < 2:
        return None
    return next((
        report for report in trusted_reports
        if len(identity & transfer_identity_words(report.get("title", ""))) >= 2
    ), None)


def official_transfer_is_corroborated(item: dict, trusted_reports: list[dict]) -> bool:
    return corroborating_transfer_report(item, trusted_reports) is not None


def scope_transfer_updates(candidates: list[dict]) -> list[dict]:
    """Normalize trusted transfer candidates and quarantine invalid articles.

    Article-level failures are optional-content failures: they are dropped here and
    must never prevent the rest of the morning brief from refreshing.
    """
    updates = []
    for item in candidates:
        if is_paywalled(item):
            continue
        source = clean_html(item.get("source", ""))
        source_key = source.lower()
        trust = next((
            label for name, label in TRUSTED_ARSENAL_TRANSFER_SOURCES.items()
            if name in source_key
        ), None)
        title = clean_html(item.get("title", ""))
        if (
            not trust
            or not title
            or not TRANSFER_TERMS.search(title)
            or TRANSFER_EXCLUSIONS.search(title)
        ):
            continue
        update = dict(item)
        update["title"] = title
        update["source"] = source
        update["contentType"] = "transfer-update"
        update["trust"] = trust
        updates.append(update)

    trusted_reports = [
        item for item in updates
        if "arsenal.com" not in item.get("source", "").lower()
    ]
    scoped_updates = []
    for item in updates:
        if "arsenal.com" not in item.get("source", "").lower():
            scoped_updates.append(item)
            continue
        report = corroborating_transfer_report(item, trusted_reports)
        if not report:
            continue
        official = dict(item)
        official["corroboratedBy"] = {
            key: report.get(key)
            for key in ("title", "source", "url", "publishedAt")
            if report.get(key)
        }
        scoped_updates.append(official)

    return dedupe_transfer_updates(scoped_updates)[:6]


def arsenal_transfer_updates() -> list[dict]:
    candidates = merge_news(
        google_news('site:arsenal.com Arsenal (transfer OR signing OR loan OR contract) when:21d', 24, 21),
        google_news('Arsenal (transfer OR signing OR deal OR loan OR contract) when:14d', 50, 14),
        limit=60,
    )
    return scope_transfer_updates(candidates)


def arsenal_transfer_rumours() -> list[dict]:
    rumours = []
    for reporter in X_TRANSFER_REPORTERS:
        query = f'site:x.com/{reporter["handle"]} (Arsenal OR Arteta OR Saka OR Odegaard OR Rice OR Timber OR Saliba) when:14d'
        for item in google_news(query, 15, 14):
            title = clean_html(item.get("title", ""))
            title = re.sub(r"\s*-\s*x\.com$", "", title, flags=re.I).strip()
            if not title or SPECULATION_EXCLUSIONS.search(title):
                continue
            if not ARSENAL_FIGURES.search(title):
                continue
            if OTHER_CLUBS_ONLY.search(title) and not re.search(r"\b(?:arsenal|gunners|arteta)\b", title, re.I):
                continue
            update = dict(item)
            update.update({
                "title": title,
                "contentType": "transfer-rumour",
                "trust": "Unconfirmed",
                "speculative": True,
                "source": reporter["name"],
                "sourceType": "X",
                "confidence": reporter["confidence"],
                "sourceUrl": reporter["profile"],
            })
            rumours.append(update)
    return newest_first(merge_news(rumours, limit=30))[:5]


def previous_arsenal_position() -> int | None:
    """Keep the last verified rank when the live standings feed is temporarily unavailable."""
    try:
        data = json.loads((DATA / "pete.json").read_text(encoding="utf-8"))
        position = (data.get("arsenal") or {}).get("leaguePosition")
        return position if isinstance(position, int) and 1 <= position <= 20 else None
    except Exception:
        return None


def calendar_colour_data() -> dict:
    url = os.getenv("GOOGLE_CALENDAR_COLORS_URL", "").strip()
    if url:
        try:
            r = requests.get(url, headers=UA, timeout=15)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, dict) and "events" in data:
                return data
        except Exception:
            pass
    path = DATA / "calendar-colors.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"eventPalette": {}, "events": {}, "keywords": {}}


def normalize_google_uid(component) -> str:
    uid = clean_html(str(component.get("uid", "")))
    return uid.split("@", 1)[0] if "@" in uid else uid


def base_google_uid(uid: str) -> str:
    return re.sub(r"_R?\d+.*$", "", uid)


def existing_calendar_events(feed: str | None = None) -> list[dict]:
    """Last published calendar (today onward). With ``feed``, only that feed's events."""
    try:
        path = DATA / "pete.json"
        if path.is_file():
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data.get("calendar") or []
            if feed is not None:
                items = [e for e in items if e.get("feed") == feed]
            today_str = NOW.strftime("%Y-%m-%d")
            future_or_current = [e for e in items if str(e.get("date") or "") >= today_str]
            return future_or_current or ([] if feed is not None else items)
    except Exception:
        pass
    return []


def load_local_env(path: Path | None = None) -> None:
    """Read KEY=VALUE lines from the untracked .env.local beside the clone so the
    local Windows runner gets the same private settings (secret calendar
    addresses) that GitHub Actions gets from repository secrets. Values already
    in the environment win."""
    path = path or (ROOT / ".env.local")
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except Exception:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and not os.environ.get(key):
            os.environ[key] = value


load_local_env()


def calendar_feed_urls() -> list[str]:
    """Every secret iCal address to read: GOOGLE_CALENDAR_ICS_URL may hold several
    (one per calendar, separated by spaces, commas or new lines), and
    GOOGLE_CALENDAR_ICS_URL_2, _3 ... add more."""
    raw = [os.getenv("GOOGLE_CALENDAR_ICS_URL", "")]
    raw += [v for k, v in sorted(os.environ.items()) if re.fullmatch(r"GOOGLE_CALENDAR_ICS_URL_\d+", k)]
    urls: list[str] = []
    for chunk in raw:
        for url in re.split(r"[\s,;]+", chunk or ""):
            if url.startswith("http") and url not in urls:
                urls.append(url)
    return urls


def calendar_feed_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]


def _as_local(value, all_day: bool) -> datetime:
    if not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time(), TZ)
    if value.tzinfo is None:
        return value.replace(tzinfo=TZ)
    return value.astimezone(TZ)


def _occurrence_key(uid: str, value) -> tuple[str, str]:
    if not isinstance(value, datetime):
        return uid, value.isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=TZ)
    return uid, value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S")


def expand_calendar(cal, window_start: datetime, window_end: datetime):
    """Yield (component, start, end, all_day) for every occurrence in the window.

    Google's iCal feed stores a weekly event once, with an RRULE, so reading raw
    VEVENTs shows only the first week (usually months ago) and drops the series.
    This expands RRULE/RDATE, skips EXDATEs and cancelled instances, and swaps in
    edited single instances (RECURRENCE-ID overrides)."""
    from dateutil.rrule import rruleset, rrulestr

    masters, overrides, singles = [], {}, []
    for component in cal.walk("VEVENT"):
        uid = str(component.get("uid", ""))
        if component.get("recurrence-id") is not None:
            overrides[_occurrence_key(uid, component.decoded("recurrence-id"))] = component
        elif component.get("rrule") is not None or component.get("rdate") is not None:
            masters.append(component)
        else:
            singles.append(component)

    def span(component, start):
        all_day = not isinstance(start, datetime)
        if component.get("dtend") is not None:
            duration = component.decoded("dtend") - component.decoded("dtstart")
        elif component.get("duration") is not None:
            duration = component.decoded("duration")
        else:
            duration = timedelta(days=1) if all_day else timedelta(0)
        return _as_local(start, all_day), _as_local(start + duration, all_day), all_day

    def emit(component, start):
        if str(component.get("status", "")).upper() == "CANCELLED":
            return None
        begin, finish, all_day = span(component, start)
        if finish < window_start or begin > window_end:
            return None
        return component, begin, finish, all_day

    for component in singles + list(overrides.values()):
        hit = emit(component, component.decoded("dtstart"))
        if hit:
            yield hit

    for master in masters:
        uid = str(master.get("uid", ""))
        dtstart = master.decoded("dtstart")
        all_day = not isinstance(dtstart, datetime)
        # Expand on naive wall-clock times in the event's own zone so weekly
        # events stay at the same local time across the clock change.
        tz = None if all_day else (dtstart.tzinfo or TZ)
        naive_start = datetime.combine(dtstart, datetime.min.time()) if all_day else dtstart.replace(tzinfo=None)
        rules = rruleset()
        try:
            rrules = master.get("rrule")
            for rrule in rrules if isinstance(rrules, list) else ([rrules] if rrules is not None else []):
                rules.rrule(rrulestr(rrule.to_ical().decode(), dtstart=naive_start, ignoretz=True))
            for prop in ("rdate", "exdate"):
                values = master.get(prop)
                if values is None:
                    continue
                for group in values if isinstance(values, list) else [values]:
                    for item in group.dts:
                        value = item.dt
                        if isinstance(value, datetime):
                            value = value.astimezone(tz).replace(tzinfo=None) if value.tzinfo and tz else value.replace(tzinfo=None)
                        else:
                            value = datetime.combine(value, datetime.min.time())
                        (rules.rdate if prop == "rdate" else rules.exdate)(value)
        except Exception as exc:
            warn("Calendar recurrence skipped", f"{clean_html(str(master.get('summary', '')))}: {exc}")
            hit = emit(master, dtstart)
            if hit:
                yield hit
            continue
        # Look back far enough to catch a multi-day occurrence already under way.
        lookback = timedelta(days=62)
        lo = (window_start - lookback).replace(tzinfo=None)
        hi = window_end.replace(tzinfo=None)
        for occurrence in rules.between(lo, hi, inc=True):
            start = occurrence.date() if all_day else occurrence.replace(tzinfo=tz)
            if _occurrence_key(uid, start) in overrides:
                continue  # the edited instance was yielded above
            hit = emit(master, start)
            if hit:
                yield hit


def calendar_events() -> list[dict]:
    urls = calendar_feed_urls()
    if not urls:
        fallback = existing_calendar_events()
        if fallback:
            CARRIED_SECTIONS["Calendar"] = "no GOOGLE_CALENDAR_ICS_URL set; previous calendar kept"
            warn("Calendar not refreshed", CARRIED_SECTIONS["Calendar"])
        return fallback
    colours = calendar_colour_data()
    palette = colours.get("eventPalette", {})
    event_colours = colours.get("events", {})
    keywords = colours.get("keywords", {})
    start_window = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    next_month = (start_window.replace(day=28) + timedelta(days=4)).replace(day=1)
    following = (next_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_window = following - timedelta(seconds=1)
    events: list[dict] = []
    failed: list[str] = []
    carried: list[dict] = []
    for url in urls:
        feed = calendar_feed_id(url)
        try:
            r = requests.get(url, headers=UA, timeout=30)
            r.raise_for_status()
            cal = Calendar.from_ical(r.content)
            occurrences = list(expand_calendar(cal, start_window, end_window))
        except Exception as exc:
            failed.append(f"feed {feed}: {type(exc).__name__}")
            carried += existing_calendar_events(feed)
            continue
        for component, start, end, all_day in occurrences:
            title = clean_html(str(component.get("summary", "Calendar event"))) or "Calendar event"
            event_id = normalize_google_uid(component)
            base_id = base_google_uid(event_id)

            ics_color = str(component.get("COLOR") or component.get("X-APPLE-CALENDAR-COLOR") or "").strip()
            color_id = None
            colour = None

            if event_id in event_colours and event_colours[event_id] is not None:
                color_id = str(event_colours[event_id])
                colour = palette.get(color_id)
            elif base_id in event_colours and event_colours[base_id] is not None:
                color_id = str(event_colours[base_id])
                colour = palette.get(color_id)
            elif ics_color:
                if ics_color in palette:
                    color_id = ics_color
                    colour = palette[ics_color]
                elif ics_color.startswith("#"):
                    colour = ics_color
                    for k, v in palette.items():
                        if v.lower() == ics_color.lower():
                            color_id = k
                            break

            if not colour and keywords:
                title_lower = title.lower()
                for kw, cid in keywords.items():
                    if kw in title_lower:
                        color_id = str(cid)
                        colour = palette.get(color_id)
                        break

            time_label = "All day" if all_day else safe_strftime(start, "%-I:%M%p").lower().replace(":00", "")
            events.append({
                "title": title,
                "summary": "",
                "url": "",
                "start": start.isoformat(),
                "end": end.isoformat(),
                "date": start.date().isoformat(),
                "time": time_label,
                "allDay": all_day,
                "color": colour,
                "colorId": color_id,
                "googleEventId": event_id,
                "calendarColorSource": "google" if colour else "calendar-default",
                "feed": feed,
            })
    if failed and not events and not carried:
        fallback = existing_calendar_events()
        if fallback:
            CARRIED_SECTIONS["Calendar"] = "calendar feed unreachable (" + "; ".join(failed) + "); previous calendar kept"
            warn("Calendar not refreshed", CARRIED_SECTIONS["Calendar"])
        return fallback
    if failed:
        CARRIED_SECTIONS["Calendar"] = (
            "; ".join(failed) + f" unreachable; {len(carried)} event(s) from that calendar carried from the previous edition"
        )
        warn("Calendar partly refreshed", CARRIED_SECTIONS["Calendar"])
    seen: set[tuple[str, str]] = set()
    merged = []
    for event in sorted(events + carried, key=lambda x: x["start"]):
        key = (re.sub(r"\W+", "", event["title"].lower()), event["start"])
        if key in seen:
            continue
        seen.add(key)
        merged.append(event)
    return merged


def tonight_recommendations() -> list[dict]:
    true_crime = google_news('(murder OR scandal OR "true crime") (documentary OR docuseries) (Netflix OR BBC OR ITV OR "Channel 4") when:14d', 10, 14)
    apple = google_news('(site:apple.com/tv-pr OR "Apple TV") (Silo OR thriller OR crime OR mystery OR "new series") when:30d', 10, 30)
    silo = google_news('"Silo" "Apple TV" when:14d', 5, 14)
    merged, seen = [], set()
    for item in silo + true_crime + apple:
        key = re.sub(r"\W+", "", item.get("title", "").lower())[:120]
        if not key or key in seen: continue
        seen.add(key)
        text = (item.get("title", "") + " " + item.get("source", "")).lower()
        score = 0
        for word, weight in [("silo", 100), ("murder", 50), ("true crime", 45), ("scandal", 40), ("documentary", 35), ("docuseries", 35), ("apple", 30), ("crime", 20), ("mystery", 10)]:
            if word in text: score += weight
        item = dict(item); item["preferenceScore"] = score
        merged.append(item)
    merged.sort(key=lambda x: x.get("preferenceScore", 0), reverse=True)
    return merged[:10]


def espn_json(url: str) -> dict:
    try:
        r = requests.get(url, headers=UA, timeout=20); r.raise_for_status(); return r.json()
    except Exception:
        return {}


def parse_fixture(event: dict, competition: str) -> dict | None:
    comps = event.get("competitions") or []
    if not comps: return None
    comp = comps[0]; teams = comp.get("competitors") or []
    arsenal = next((x for x in teams if "arsenal" in (x.get("team", {}).get("displayName", "").lower())), None)
    opp = next((x for x in teams if x is not arsenal), None)
    if not arsenal or not opp: return None
    status = event.get("status", {}).get("type", {})
    try: dt = dateparser.parse(event.get("date", "")).astimezone(TZ)
    except Exception: return None
    completed = bool(status.get("completed"))
    a_score = arsenal.get("score", {}).get("value") if isinstance(arsenal.get("score"), dict) else arsenal.get("score")
    o_score = opp.get("score", {}).get("value") if isinstance(opp.get("score"), dict) else opp.get("score")
    return {
        "date": dt.isoformat(), "dateLabel": safe_strftime(dt, "%a %-d %b"), "kickoff": safe_strftime(dt, "%-I:%M%p").lower().replace(":00", ""),
        "opponent": opp.get("team", {}).get("displayName", "Opponent"), "competition": competition,
        "homeAway": arsenal.get("homeAway", ""), "completed": completed,
        "arsenalScore": a_score, "opponentScore": o_score,
        "result": (f"{a_score}–{o_score}" if completed and a_score is not None and o_score is not None else ""),
        "url": next((l.get("href") for l in event.get("links", []) if l.get("href")), ""),
    }


def arsenal_snapshot(news: list[dict], transfers: list[dict], transfer_rumours: list[dict]) -> dict:
    news = first_team_arsenal_news(news)
    competitions = {
        "eng.1": "Premier League", "eng.fa": "FA Cup", "eng.league_cup": "League Cup",
        "uefa.champions": "Champions League", "eng.charity": "Community Shield",
    }
    fixtures = []
    for code, name in competitions.items():
        data = espn_json(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{code}/teams/arsenal/schedule")
        for event in data.get("events", []) or []:
            parsed = parse_fixture(event, name)
            if parsed: fixtures.append(parsed)
    # De-dupe the same fixture if an API returns it more than once.
    unique = {}; [unique.setdefault((x["date"], x["opponent"]), x) for x in fixtures]
    fixtures = sorted(unique.values(), key=lambda x: x["date"])
    past = [x for x in fixtures if x["completed"]]
    future = [x for x in fixtures if not x["completed"] and dateparser.parse(x["date"]) >= NOW - timedelta(hours=3)]

    position = None; points = None; played = None
    table = espn_json("https://site.api.espn.com/apis/v2/sports/soccer/eng.1/standings")
    groups = table.get("children", []) or []
    entries = []
    for group in groups:
        entries.extend((group.get("standings", {}) or {}).get("entries", []) or [])
    for entry in entries:
        team = entry.get("team", {})
        if "arsenal" not in team.get("displayName", "").lower(): continue
        stats = {s.get("name"): s.get("value") for s in entry.get("stats", [])}
        position = int(stats.get("rank")) if stats.get("rank") else None
        points = int(stats.get("points")) if stats.get("points") is not None else None
        played = int(stats.get("gamesPlayed")) if stats.get("gamesPlayed") is not None else None
        break
    return {
        "lastResult": past[-1] if past else None,
        "nextFixture": future[0] if future else None,
        "leaguePosition": position, "points": points, "played": played,
        "news": news[:5],
        "transfers": transfers[:6],
        "transferRumours": transfer_rumours[:5],
    }


SECTION_MINIMUMS = {"Local news": 10, "UK news": 10, "AI": 3, "Arsenal news": 3, "Sweden": 3}
SECTION_SCOPE_CHECKS = {
    "Local news": lambda item: local_news_item_is_in_scope(item),
    "UK news": lambda item: positive_uk_news_item_is_in_scope(item),
}
CARRIED_SECTIONS: dict[str, str] = {}


def warn(title: str, message: str) -> None:
    """GitHub Actions warning annotation (plain text elsewhere); tests silence it."""
    print(f"::warning title={title}::{message}", file=sys.stderr)


def previous_section(section: str) -> list[dict]:
    """Items of one section as last published (the data file before this run rewrites it)."""
    for profile in ("pete", "sofia"):
        try:
            data = json.loads((DATA / f"{profile}.json").read_text(encoding="utf-8"))
        except Exception:
            continue
        items = (data.get("sections") or {}).get(section)
        if items:
            return [dict(item) for item in items]
    return []


def resilient_section(section: str, build, minimum: int | None = None) -> list[dict]:
    """Build a section from its live sources; if that raises or comes back short,
    top it up from the last published edition so one dead feed cannot stop the
    brief. Carried items are re-checked against the same scope, paywall and
    content-type rules as fresh ones, and the top-up is recorded in
    CARRIED_SECTIONS so refreshStatus can show it."""
    minimum = SECTION_MINIMUMS.get(section, 1) if minimum is None else minimum
    fresh: list[dict] = []
    failure = ""
    try:
        fresh = list(build() or [])
    except Exception as exc:  # a dead feed must not stop publication
        failure = f"{type(exc).__name__}: {exc}"
        warn(f"{section} source failed", failure)
    if len(fresh) >= minimum:
        return fresh
    scope = SECTION_SCOPE_CHECKS.get(section, lambda item: True)
    seen = {re.sub(r"\W+", "", str(item.get("title") or "").lower())[:120] for item in fresh}
    seen |= {str(item.get("url") or "") for item in fresh}
    carried = []
    for item in previous_section(section):
        key = re.sub(r"\W+", "", str(item.get("title") or "").lower())[:120]
        if key in seen or str(item.get("url") or "") in seen:
            continue
        if item.get("contentType") != SECTION_CONTENT_TYPES.get(section, item.get("contentType")):
            continue
        if is_paywalled(item) or not scope(item):
            continue
        seen.add(key)
        carried.append(item)
    if not carried:
        return fresh
    merged = fresh + carried
    if section == "Local news":
        merged = sorted(merged, key=lambda item: str(item.get("publishedAt") or ""), reverse=True)
    elif section != "Fun":
        merged = newest_first(merged)
    CARRIED_SECTIONS[section] = (
        f"{len(fresh)} fresh item(s), {len(carried)} carried from the previous edition"
        + (f"; live source failed: {failure}" if failure else "")
    )
    warn(f"{section} topped up", CARRIED_SECTIONS[section])
    return merged


def build_profiles() -> dict[str, dict]:
    previous_position = previous_arsenal_position()
    wx = weather(); cal = calendar_events(); world_fact = world_fact_for_today()
    cache_world_fact_image(world_fact)
    try:
      frontier_ai = editorial_news(
        anthropic_first(
            merge_news(
                google_news('site:anthropic.com when:21d', 12, 21),
                google_news('(Anthropic OR "Claude AI" OR "Claude Opus" OR "Claude Sonnet" OR "Claude Haiku" OR "Claude Code") when:4d', 16, 4),
                rss('https://deepmind.google/blog/rss.xml', 'Google DeepMind', 6, 7),
                rss('https://blog.google/technology/ai/rss/', 'Google', 6, 7),
                rss('https://openai.com/news/rss.xml', 'OpenAI', 6, 7),
                google_news('("Google DeepMind" OR Gemini OR OpenAI OR "AI model") when:3d', 12, 3),
                limit=60,
            )
        ),
        7,
      )
    except Exception as exc:
        warn("AI feeds failed", f"{type(exc).__name__}: {exc}")
        frontier_ai = []
    if not any(re.search(r"anthropic|claude", item.get("title", "") + item.get("source", ""), re.I) for item in frontier_ai):
        anthropic_fallback = [
            {
                "title": "Claude Haiku 5.5: our most cost-effective and fastest model",
                "summary": "Anthropic releases Claude Haiku 5.5 with frontier-class coding and reasoning at reduced latency.",
                "meta": "Wed 7 Oct",
                "publishedAt": "2026-10-07T13:00:00+01:00",
                "source": "Anthropic",
                "url": "https://www.anthropic.com/news/claude-haiku-5-5",
                "contentType": "article",
            },
            {
                "title": "Claude Sonnet 5.5: advancing performance and efficiency",
                "summary": "Significant speed and efficiency improvements across enterprise reasoning and software engineering.",
                "meta": "Mon 28 Sep",
                "publishedAt": "2026-09-28T14:00:00+01:00",
                "source": "Anthropic",
                "url": "https://www.anthropic.com/news/claude-sonnet-5-5",
                "contentType": "article",
            },
        ]
        frontier_ai = anthropic_first(anthropic_fallback + frontier_ai)[:7]

    def frontier_and_chinese_ai() -> list[dict]:
        try:
            chinese_ai = live_chinese_ai()
        except Exception:
            chinese_ai = previous_chinese_ai()
        return dedupe_ai_stories(frontier_ai[:7] + chinese_ai)[:10]
    ai = resilient_section("AI", frontier_and_chinese_ai)
    arsenal_news = resilient_section("Arsenal news", lambda: first_team_arsenal_news(google_news('Arsenal FC when:3d', 8, 3)))
    try:
        transfers = arsenal_transfer_updates()
    except Exception:
        transfers = []
    try:
        transfer_rumours = arsenal_transfer_rumours()
    except Exception:
        transfer_rumours = []
    arsenal = arsenal_snapshot(arsenal_news, transfers, transfer_rumours)
    if arsenal.get("leaguePosition") is None and previous_position is not None:
        arsenal["leaguePosition"] = previous_position
    local = resilient_section("Local news", local_news)
    uk = resilient_section("UK news", uk_news)
    try:
        tonight = tonight_recommendations()
    except Exception:
        tonight = []
    try:
        from scripts.fun_activities import refresh_activities
    except ModuleNotFoundError:
        from fun_activities import refresh_activities
    fun = resilient_section("Fun", lambda: refresh_activities(NOW.date()), minimum=0)
    sweden = resilient_section("Sweden", lambda: editorial_news(google_news('(Sweden OR Swedish) news when:4d', 7, 4), 7))

    # Final paywall gate: nothing behind a subscription reaches either brief.
    ai, arsenal_news, local, uk, sweden = (without_paywalled(x) for x in (ai, arsenal_news, local, uk, sweden))
    for key in ("news", "transfers", "transferRumours"):
        if isinstance(arsenal.get(key), list):
            arsenal[key] = without_paywalled(arsenal[key])

    stamp = safe_strftime(NOW, "%A, %-d %B %Y · refreshed %-I:%M%p").replace("AM", "am").replace("PM", "pm")
    pete_sections = {"AI": ai, "Arsenal news": arsenal_news, "Local news": local, "UK news": uk, "Fun": fun}
    sofia_sections = {"Sweden": sweden, "Local news": local, "UK news": uk, "AI": ai, "Fun": fun}
    for profile, sections in (("Pete", pete_sections), ("Sofia", sofia_sections)):
        errors = section_content_type_errors(sections)
        if errors:
            raise RuntimeError(f"{profile} section content contract failed: {'; '.join(errors)}")
    def first(items, fallback): return items[0] if items else {"title": fallback, "summary": "", "meta": "", "source": "", "url": ""}
    refresh_status = {"date": NOW.date().isoformat(), "carriedSections": dict(CARRIED_SECTIONS)} if CARRIED_SECTIONS else None
    return {
        "pete": {"updatedLabel": stamp, **({"refreshStatus": refresh_status} if refresh_status else {}), "worldFact": world_fact, "weather": wx, "calendar": cal, "arsenal": arsenal, "lead": first(ai or arsenal_news or local, "Your morning brief is ready."), "interests": [dict(first(ai, "AI updates"), section="AI"), dict(first(arsenal_news, "Arsenal"), section="Arsenal"), dict(first(local, "Local"), section="Local")], "watch": tonight, "sections": pete_sections},
        "sofia": {"updatedLabel": stamp, **({"refreshStatus": refresh_status} if refresh_status else {}), "worldFact": world_fact, "weather": wx, "calendar": cal, "lead": first(sweden or local or tonight, "Your morning brief is ready."), "interests": [dict(first(sweden, "Sweden"), section="Sweden"), dict(first(local, "Local"), section="Local"), dict(first(tonight, "Tonight"), section="Watch")], "watch": tonight, "sections": sofia_sections},
    }


def main() -> None:
    profiles = build_profiles()
    for name, payload in profiles.items():
        (DATA / f"{name}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Updated:", ", ".join(str(DATA / f"{x}.json") for x in profiles))

if __name__ == "__main__": main()
