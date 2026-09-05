from __future__ import annotations

import html
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as dateparser
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
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

SOFIA_PRODUCT_ROLE_PATTERNS = (
    re.compile(r"\b(?:senior|lead|principal|group)\s+(?:data\s+)?product\s+(?:manager|owner|lead|developer)\b", re.I),
    re.compile(r"\b(?:head|director|vice president|vp)\s+of\s+(?:data\s+)?product(?:\s+development)?\b", re.I),
    re.compile(r"\b(?:data\s+)?product\s+(?:director|lead)\b", re.I),
    re.compile(r"\b(?:senior|lead|principal)\s+product\s+development\s+(?:manager|lead|director)\b", re.I),
    re.compile(r"\bproduct\s+development\s+(?:director|head|lead)\b", re.I),
    re.compile(r"\b(?:chief product officer|cpo)\b", re.I),
)
SOFIA_SOFTWARE_ROLE = re.compile(
    r"\b(?:software|frontend|front-end|backend|back-end|full[- ]stack|web|mobile|"
    r"engineer|engineering|programmer|devops|mlops|product design|designer|ux|ui|product marketing)\b",
    re.I,
)
SOFIA_EXCLUDED_SECTOR = re.compile(
    r"\b(?:casino|gambling|betting|gaming|video games?|mobile games?|midcore games?)\b",
    re.I,
)
SOFIA_DOMAIN_TERMS = re.compile(
    r"\b(?:b2b|financial|finance|fintech|market data|data product|business intelligence|"
    r"information services|strategic insight|consumer insight|market research|analytics|enterprise)\b",
    re.I,
)
SOFIA_REMOTE_TERMS = re.compile(
    r"\b(?:fully remote|remote[- ]first|100% remote|work from anywhere|remote role|remote job)\b",
    re.I,
)
SOFIA_REMOTE_NEGATION = re.compile(
    r"\b(?:do not offer remote|no remote work|remote work (?:is )?not available|not a remote role)\b",
    re.I,
)
SOFIA_THREE_WFH_TERMS = (
    re.compile(r"\b(?:at least\s+)?(?:3|three)\s+days?(?:\s+a\s+week)?\s+(?:working\s+)?(?:from\s+home|at\s+home|remote)\b", re.I),
    re.compile(r"\b(?:from\s+home|at\s+home|remote)\s+(?:for\s+)?(?:(?:at least|up to)\s+)?(?:3|three)\s+days?\b", re.I),
    re.compile(r"\b(?:at least\s+|up to\s+)?(?:2|two)\s+days?(?:\s+a\s+week)?\s+(?:in|at|from)\s+(?:the\s+)?office\b", re.I),
    re.compile(r"\b(?:in|at|from)\s+(?:the\s+)?office\s+(?:for\s+)?(?:at least\s+|up to\s+)?(?:2|two)\s+days?\b", re.I),
    re.compile(r"\boffice\s+(?:attendance\s+)?(?:twice|2\s+times)\s+a\s+week\b", re.I),
)
SOFIA_UK_LOCATION = re.compile(
    r"\b(?:united kingdom|u\.?k\.?|england|scotland|wales|northern ireland|london|"
    r"manchester|birmingham|bristol|bath|leeds|liverpool|edinburgh|glasgow|cambridge|"
    r"oxford|reading|surrey|kent|essex|hampshire|nottingham|sheffield|cardiff|belfast)\b",
    re.I,
)
SOFIA_SWEDEN_LOCATION = re.compile(
    r"\b(?:sweden|swedish|stockholm|gothenburg|göteborg|malmö|malmo|uppsala|lund)\b",
    re.I,
)
REMOTE_ELIGIBLE_LOCATION = re.compile(
    r"\b(?:remote|worldwide|global|anywhere|europe|european|emea|united kingdom|u\.?k\.?|sweden|swedish)\b",
    re.I,
)
REMOTE_EXCLUDED_LOCATION = re.compile(
    r"\b(?:united states|u\.?s\.?a?\.?|canada|latin america|latam|asia|apac|australia|new zealand)\b",
    re.I,
)
AI_CAREER_TERMS = re.compile(
    r"\b(?:AI|artificial intelligence|machine learning|generative AI|genAI|large language model|"
    r"LLMs?|responsible AI|AI (?:governance|assurance|policy|strategy|adoption|safety))\b",
    re.I,
)
PUBLIC_SECTOR_EMPLOYER_TERMS = re.compile(
    r"\b(?:civil service|government digital service|cabinet office|home office|"
    r"ministry of|department for|department of|hm revenue|hm treasury|dwp|defra|dhsc|dft|"
    r"office for national statistics|national audit office|national cyber security centre|"
    r"nhs|national health service|[a-z& ]+ council|local authority|parliament|"
    r"police|fire and rescue|ambulance service|uk research and innovation|ukri|"
    r"money and pensions service|met office|dvla|dvsa|hm land registry|"
    r"information commissioner's office|ico|ofcom|ofgem|uk health security agency|ukhsa)\b",
    re.I,
)
INACTIVE_LISTING = re.compile(
    r"\b(?:no longer accepting applications|job (?:has )?expired|position (?:has been )?filled|"
    r"vacancy (?:has )?closed|applications? closed)\b",
    re.I,
)

LOCAL_NEWS_QUERIES = (
    '(Molesey OR "East Molesey" OR "West Molesey" OR "Hurst Pool" OR "Hurst Park")',
    '("Kingston upon Thames" OR "Kingston Surrey" OR Surbiton)',
    '("Hampton Court" OR Teddington OR "Hampton Wick" OR "Hampton Hill" OR "Bushy Park")',
    '(Hampton AND (London OR Surrey OR Richmond))',
    '("Walton-on-Thames" OR "Walton on Thames" OR Hersham)',
    '("Thames Ditton" OR "Long Ditton" OR "Hinchley Wood" OR Esher OR "Sunbury-on-Thames")',
)
LOCAL_NEWS_PUBLICATION_QUERIES = (
    'site:surreycomet.co.uk (Molesey OR Kingston OR Surbiton OR Teddington OR "Thames Ditton")',
    'site:surreylive.news (Molesey OR Kingston OR Teddington OR Walton OR Esher OR Hersham)',
    'site:kingston.nub.news (Kingston OR Surbiton OR "Hampton Wick")',
    'site:teddington.nub.news (Teddington OR "Hampton Wick" OR "Bushy Park")',
    'site:weybridgeandwalton.nub.news ("Walton-on-Thames" OR Hersham)',
    'site:richmondandtwickenhamtimes.co.uk (Teddington OR Hampton OR "Bushy Park")',
)
LOCAL_NEWS_FAMILY_QUERIES = (
    '(Molesey OR Kingston OR Surbiton OR Teddington OR Hampton) '
    '(family OR kids OR children OR festival OR park OR "what\'s on" OR Halloween OR Christmas)',
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
LOCAL_NEWS_FALSE_LOCATIONS = re.compile(
    r"\b(?:kingston\s+upon\s+hull|kingston,?\s+(?:jamaica|ontario|rhode\s+island|tennessee|tasmania)|"
    r"east\s+hampton|hampton\s+roads|hampton\s+university|hampton\s+(?:inn|by\s+hilton)|the\s+hamptons|"
    r"walton\s+county|walton[-\s]le[-\s]dale|walton[-\s]on[-\s]the[-\s]naze|walton\s+goggins|"
    r"virginia|tasmania|australia|forest\s+park,?\s+ga|georgia|ireland|jamaica|ontario|hagley park road|Omarion Hampton|Drake London)\b",
    re.I,
)
LOCAL_NEWS_FOREIGN_OR_LOW_VALUE_SOURCE = re.compile(
    r"\b(?:WTKR|IRIE FM|Jamaica Gleaner|Tasmanian Country|Teagasc|Legacy obituary|funeral home|obituary|YouTube)\b",
    re.I,
)
LOCAL_NEWS_LOW_VALUE_CONTENT = re.compile(
    r"\b(?:obituary|funeral home|death notice|property listing|houses? for sale|jobs? available|"
    r"MOT|weather forecast|sponsored content|advertorial|download[^.]{0,80}\bapp)\b",
    re.I,
)
PLAIN_HAMPTON = re.compile(r"\bhampton\b", re.I)
PLAIN_HAMPTON_LOCAL_CONTEXT = re.compile(
    r"\b(?:resident|council|road|street|park|school|pool|pub|shop|business|planning|police|"
    r"river|local|village|station|church|library|community|borough|ferry|traffic|closure)s?\b",
    re.I,
)
LOCAL_NEWS_PUBLICATIONS = re.compile(
    r"\b(?:Surrey Comet|Surrey Live|Kingston Nub News|Teddington Nub News|"
    r"Weybridge and Walton Nub News|Richmond and Twickenham Times|Molesey Matters|"
    r"Elmbridge Today|This Is Local London|MyLondon)\b",
    re.I,
)
LOCAL_FAMILY_ACTIVITY = re.compile(
    r"\b(?:child-friendly|festival|fete|fair|carnival|fun day|family day|kids? day|"
    r"Halloween|Christmas|Easter|half[- ]term|school holiday|playground|trail|"
    r"workshop|open day|what['’]s on|things to do|activities|fireworks|lantern|grotto|"
    r"pumpkin|Santa|outdoor cinema|fun day)\b",
    re.I,
)
LOCAL_SPORT_TOPIC = re.compile(
    r"\b(?:football|rugby|cricket|hockey|tennis|netball|basketball|golf|cycling|"
    r"athletics|swimming|rowing|fixture|match|league|cup|tournament|FC|RFC|CC)\b",
    re.I,
)
LOCAL_SPORT_RESULT = re.compile(
    r"\b(?:score|result|match report|beat|beats|beaten|defeat|defeats|defeated|"
    r"win|wins|won|loss|lost|draw|drew|victory|goals?|points?|innings|wickets?|"
    r"fixture|standings|table|round-up|roundup)\b|\b\d+\s*[-–]\s*\d+\b",
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
    "Career": "job",
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
        selected = next((item for item in unused if item.get("editorialPriority") == "human-first"), None)
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
            meta = dt.strftime("%a %-d %b")
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
            meta = dt.strftime("%a %-d %b")
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
    )


def editorial_news_item_is_in_scope(item: dict) -> bool:
    """Allow only article-shaped, non-vacancy items into editorial destinations."""
    content_type = str(item.get("contentType") or "article").casefold()
    return content_type == "article" and not news_item_is_job_vacancy(item)


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


def local_news_item_is_in_scope(item: dict) -> bool:
    """Require approved local evidence and reject routine sports coverage."""
    text = clean_html(" ".join(str(item.get(key, "")) for key in ("title", "summary")))
    source = clean_html(str(item.get("source", "")))
    if (
        not editorial_news_item_is_in_scope(item)
        or not text
        or LOCAL_NEWS_FALSE_LOCATIONS.search(f"{text} {source}")
        or LOCAL_NEWS_FOREIGN_OR_LOW_VALUE_SOURCE.search(source)
        or LOCAL_NEWS_LOW_VALUE_CONTENT.search(text)
        or local_event_has_expired(item)
    ):
        return False
    local = any(pattern.search(text) for pattern in LOCAL_NEWS_PLACE_EVIDENCE) or bool(
        re.search(r"\b(?:kingston|hampton)\b", text, re.I)
        and (local_publication_item(item) or re.search(r"\b(?:Surrey|London|Thames|Richmond upon Thames)\b", text, re.I))
    )
    if not local:
        return False
    routine_sport = LOCAL_SPORT_TOPIC.search(text) and LOCAL_SPORT_RESULT.search(text)
    return not routine_sport or bool(LOCAL_SPORT_EXCEPTION.search(text))


def local_publication_item(item: dict) -> bool:
    text = " ".join(str(item.get(key, "")) for key in ("source", "url"))
    return bool(LOCAL_NEWS_PUBLICATIONS.search(text) or re.search(
        r"https?://(?:www\.)?(?:surreycomet\.co\.uk|surreylive\.news|kingston\.nub\.news|"
        r"teddington\.nub\.news|weybridgeandwalton\.nub\.news|richmondandtwickenhamtimes\.co\.uk)/", text, re.I))


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
    """Prioritise local publications and family activities, then display newest first."""
    scoped = [item for item in items if local_news_item_is_in_scope(item)]
    prioritised = sorted(
        scoped,
        key=lambda item: (
            local_family_activity_item(item),
            local_publication_item(item),
            str(item.get("publishedAt") or ""),
        ),
        reverse=True,
    )
    selected: list[dict] = []
    selected_title_words: list[set[str]] = []
    selected_urls: set[str] = set()
    for item in prioritised:
        canonical = str(item.get("url") or "").split('#', 1)[0].split('?', 1)[0].rstrip('/')
        if canonical and canonical in selected_urls:
            continue
        title = clean_html(str(item.get("title", ""))).lower()
        title = re.sub(r"former (?:teddington school pupil|kingston resident)", "former local resident", title)
        words = set(re.findall(r"[a-z0-9]+", title))
        if any(
            len(words & existing) / max(1, len(words | existing)) >= 0.82
            for existing in selected_title_words
        ):
            continue
        selected.append(item)
        if canonical:
            selected_urls.add(canonical)
        selected_title_words.append(words)
        if len(selected) >= limit:
            break
    for item in selected:
        item["localPublication"] = local_publication_item(item)
        item["familyActivity"] = local_family_activity_item(item)
    return newest_news(selected, limit)


def local_news() -> list[dict]:
    # Prefer the freshest fortnight. If that cannot fill the 16-story target,
    # extend time to 30 days without widening beyond the approved KT8 cluster.
    for max_age_days in (14, 30):
        queries = (
            *LOCAL_NEWS_QUERIES,
            *LOCAL_NEWS_PUBLICATION_QUERIES,
            *LOCAL_NEWS_FAMILY_QUERIES,
        )
        with ThreadPoolExecutor(max_workers=8) as pool:
            groups = list(pool.map(
                lambda query: google_news(f'{query} when:{max_age_days}d', 32, max_age_days),
                queries,
            ))
        candidates = merge_news(*groups, limit=448)
        scoped = [item for item in candidates if local_news_item_is_in_scope(item)]
        selected = select_local_news(scoped, 16)
        if len(selected) >= 16 or max_age_days == 30:
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
    "reuters": "Trusted report",
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


def transfer_identity_words(title: str) -> set[str]:
    return {
        word for word in re.findall(r"[a-zà-öø-ÿ'’-]{3,}", clean_html(title).lower())
        if word not in TRANSFER_NAME_STOPWORDS
    }


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

    return newest_first(scoped_updates)[:6]


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
        query = f'site:x.com/{reporter["handle"]}/status Arsenal (transfer OR signing OR deal OR move OR bid OR talks OR loan OR contract OR exit) when:7d'
        for item in google_news(query, 10, 7):
            title = clean_html(item.get("title", ""))
            if "arsenal" not in title.lower() or not TRANSFER_TERMS.search(title) or SPECULATION_EXCLUSIONS.search(title):
                continue
            update = dict(item)
            update.update({
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


def sofia_role_match(title: str) -> bool:
    title = clean_html(title)
    if not any(pattern.search(title) for pattern in SOFIA_PRODUCT_ROLE_PATTERNS):
        return False
    return not SOFIA_SOFTWARE_ROLE.search(title)


def sofia_work_arrangement(job: dict, source: str) -> str | None:
    raw = " ".join(str(job.get(key, "")) for key in ("title", "position", "location", "description", "tags"))
    text = clean_html(html.unescape(raw))
    if SOFIA_REMOTE_NEGATION.search(text):
        return None

    source_is_remote = source in {"Remote OK", "Remotive", "Jobicy"} or bool(job.get("remote"))
    if source_is_remote or SOFIA_REMOTE_TERMS.search(text):
        return "remote"

    if any(pattern.search(text) for pattern in SOFIA_THREE_WFH_TERMS):
        location = clean_html(str(job.get("location", "")))
        if SOFIA_UK_LOCATION.search(f"{location} {text}") or SOFIA_SWEDEN_LOCATION.search(f"{location} {text}"):
            return "3-wfh-days"
    return None


def parse_job_date(job: dict) -> datetime | None:
    epoch = job.get("created_at") or job.get("epoch")
    if epoch:
        try:
            return datetime.fromtimestamp(int(epoch), TZ)
        except (TypeError, ValueError, OSError):
            pass
    value = job.get("date") or job.get("publication_date") or job.get("pubDate")
    if value:
        try:
            parsed = dateparser.parse(str(value))
            return parsed.astimezone(TZ) if parsed.tzinfo else parsed.replace(tzinfo=TZ)
        except Exception:
            pass
    return None


def job_country_focus(job: dict) -> str | None:
    location = clean_html(str(job.get("location") or ""))
    description = clean_html(html.unescape(str(job.get("description") or "")))
    text = f"{location} {description}"
    if SOFIA_UK_LOCATION.search(text):
        return "UK"
    if SOFIA_SWEDEN_LOCATION.search(text):
        return "Sweden"
    if REMOTE_ELIGIBLE_LOCATION.search(location) and not REMOTE_EXCLUDED_LOCATION.search(location):
        return "Europe/remote"
    return None


def sofia_job_item(job: dict, source: str) -> tuple[int, datetime, dict] | None:
    title = clean_html(str(job.get("title") or job.get("position") or ""))
    if not sofia_role_match(title):
        return None
    arrangement = sofia_work_arrangement(job, source)
    if not arrangement:
        return None
    country_focus = job_country_focus(job)
    if not country_focus:
        return None

    url = clean_html(str(job.get("url") or ""))
    if not url.startswith(("https://", "http://")):
        return None
    company = clean_html(str(job.get("company_name") or job.get("company") or "Employer not stated"))
    location = clean_html(str(job.get("location") or "Location not stated"))
    description = clean_html(html.unescape(str(job.get("description") or "")))
    if SOFIA_EXCLUDED_SECTOR.search(f"{title} {description}"):
        return None
    if job.get("inactive") or INACTIVE_LISTING.search(description):
        return None
    posted = parse_job_date(job)
    if posted and NOW - posted > timedelta(days=30):
        return None

    score = 4
    if re.search(r"\b(?:director|head|vice president|vp|principal|group)\b", title, re.I):
        score += 3
    elif re.search(r"\b(?:senior|lead)\b", title, re.I):
        score += 2
    if SOFIA_DOMAIN_TERMS.search(f"{title} {description}"):
        score += 3
    if arrangement == "remote":
        score += 2
    if country_focus in {"UK", "Sweden"}:
        score += 5
    if source == "LinkedIn":
        score += 1

    work_label = "Remote" if arrangement == "remote" else "3+ WFH days"
    posted_label = posted.strftime("Posted %a %-d %b") if posted else "Current posting"
    item = {
        "title": title,
        "summary": f"{company} · {location}",
        "meta": f"{work_label} · {posted_label}",
        "source": source,
        "url": url,
        "contentType": "job",
        "workArrangement": arrangement,
        "company": company,
        "location": location,
        "countryFocus": country_focus,
    }
    if source == "LinkedIn":
        item["postedDate"] += " · LinkedIn listing date"
    for field in ('metadataSourceUrl', 'metadataVerifiedAt'):
        if job.get(field):
            item[field] = job[field]
    if posted:
        item["postedAt"] = posted.date().isoformat()
    return score, posted or datetime.min.replace(tzinfo=TZ), item


def normalise_job(row: dict, source: str) -> dict:
    if source == "Arbeitnow":
        return {
            "title": row.get("title"), "company_name": row.get("company_name"),
            "location": row.get("location"), "description": row.get("description"),
            "url": row.get("url"), "created_at": row.get("created_at"), "remote": row.get("remote"),
            "salary": row.get("salary"),
        }
    if source == "Remote OK":
        return {
            "title": row.get("position"), "company_name": row.get("company"),
            "location": row.get("location") or "Remote", "description": row.get("description"),
            "tags": row.get("tags"), "url": row.get("url"), "epoch": row.get("epoch"), "remote": True,
            "salary": row.get("salary") or " - ".join(str(value) for value in (row.get("salary_min"), row.get("salary_max")) if value),
        }
    if source == "Remotive":
        return {
            "title": row.get("title"), "company_name": row.get("company_name"),
            "location": row.get("candidate_required_location") or "Remote",
            "description": row.get("description"), "tags": row.get("tags"),
            "url": row.get("url"), "publication_date": row.get("publication_date"), "remote": True,
            "salary": row.get("salary"),
        }
    if source == "Jobicy":
        return {
            "title": row.get("jobTitle"), "company_name": row.get("companyName"),
            "location": row.get("jobGeo") or "Remote", "description": row.get("jobDescription"),
            "tags": row.get("jobIndustry"), "url": row.get("url"), "pubDate": row.get("pubDate"), "remote": True,
            "salary": row.get("annualSalaryMin") or row.get("salary"),
        }
    if source == "Sweden JobTech":
        address = row.get("workplace_address") or {}
        location = ", ".join(x for x in (address.get("municipality"), address.get("region"), address.get("country")) if x)
        return {
            "title": row.get("headline"), "company_name": (row.get("employer") or {}).get("name"),
            "location": location or "Sweden", "description": (row.get("description") or {}).get("text"),
            "url": row.get("webpage_url"), "publication_date": row.get("publication_date"),
        }
    return dict(row)


def linkedin_jobs(keywords: str, location: str, target: str, starts: tuple[int, ...] = (0, 10)) -> list[tuple[dict, str]]:
    def fetch_page(start: int) -> list[tuple[dict, str]]:
        jobs = []
        try:
            response = requests.get(
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
                params={"keywords": keywords, "location": location, "f_TPR": "r2592000", "start": start},
                headers=UA,
                timeout=25,
            )
            response.raise_for_status()
        except Exception:
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        for card in soup.select("li"):
            link = card.select_one("a.base-card__full-link")
            title = card.select_one("h3.base-search-card__title")
            if not link or not title:
                continue
            company = card.select_one("h4.base-search-card__subtitle")
            place = card.select_one("span.job-search-card__location")
            stamp = card.select_one("time")
            jobs.append(({
                "title": title.get_text(" ", strip=True),
                "company_name": company.get_text(" ", strip=True) if company else "Employer not stated",
                "location": place.get_text(" ", strip=True) if place else location,
                "date": stamp.get("datetime") if stamp else None,
                "url": (link.get("href") or "").split("?", 1)[0],
                "description": "",
                "target": target,
            }, "LinkedIn"))
        return jobs

    with ThreadPoolExecutor(max_workers=min(4, len(starts))) as pool:
        return [job for page in pool.map(fetch_page, starts) for job in page]


def linkedin_description(job: dict) -> dict:
    if job.get("description") or not str(job.get("url") or "").startswith("http"):
        return job
    urls = [job["url"]]
    match = re.search(r'-(\d+)$', job['url'].split('?', 1)[0].rstrip('/'))
    if match:
        urls.insert(0, f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{match.group(1)}")
    for url in urls:
        try:
            response = requests.get(url, headers=UA, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            block = soup.select_one(".show-more-less-html__markup")
            if not block:
                continue
            enriched = dict(job)
            enriched['description'] = block.get_text(' ', strip=True)
            salary = re.search(
                r"£\s?\d{2,3}(?:,\d{3})?(?:\s*(?:-|–|to)\s*£?\s?\d{2,3}(?:,\d{3})?)?(?:\s*(?:per annum|per year|a year|p\.a\.))?",
                enriched['description'], re.I)
            if salary:
                enriched['salary'] = salary.group(0)
            if INACTIVE_LISTING.search(soup.get_text(' ', strip=True)):
                enriched['inactive'] = True
            return enriched
        except requests.RequestException:
            continue
    return job


def career_job_candidates() -> list[tuple[dict, str]]:
    queries = (
        '"artificial intelligence" government',
        '"AI" NHS',
        '"machine learning" government',
        '"generative AI" public sector',
        '"responsible AI" government',
        '"AI governance" public sector',
    )
    with ThreadPoolExecutor(max_workers=6) as pool:
        groups = pool.map(
            lambda query: linkedin_jobs(query, "United Kingdom", "public-ai", starts=(0, 10, 20)),
            queries,
        )
        return [job for group in groups for job in group]


def sofia_career_jobs(candidates: list[tuple[dict, str]] | None = None, limit: int = 10) -> list[dict]:
    candidates = candidates if candidates is not None else career_job_candidates()
    linkedin_candidates = [
        job for job, source in candidates
        if source == "LinkedIn" and job.get("target") == "sofia" and sofia_role_match(str(job.get("title") or ""))
    ]
    with ThreadPoolExecutor(max_workers=4) as pool:
        linkedin_enriched = {job.get("url"): enriched for job, enriched in zip(linkedin_candidates, pool.map(linkedin_description, linkedin_candidates))}

    ranked, seen = [], set()
    for job, source in candidates:
        if source == "LinkedIn":
            if job.get("target") != "sofia" or not sofia_role_match(str(job.get("title") or "")):
                continue
            job = linkedin_enriched.get(job.get("url"), job)
            if job.get("inactive"):
                continue
        result = sofia_job_item(job, source)
        if not result:
            continue
        score, posted, item = result
        key = re.sub(r"\W+", "", f"{item['title']}{item['company']}".lower())[:180]
        if not key or key in seen:
            continue
        seen.add(key)
        ranked.append((score, posted, item))
    ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return [item for _, _, item in ranked[:limit]]


def published_job_description(description: str, limit: int = 420) -> str:
    cleaned = clean_html(html.unescape(description)).strip()
    if not cleaned:
        return "Description not supplied by publisher."
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
    return f"{shortened}…"


def published_job_salary(job: dict) -> str:
    description = clean_html(html.unescape(str(job.get("description") or "")))
    match = re.search(
        r"£\s?\d{2,3}(?:,\d{3})?(?:\s*(?:-|–|to)\s*£?\s?\d{2,3}(?:,\d{3})?)?"
        r"(?:\s*(?:per annum|per year|a year|p\.a\.))?",
        description,
        re.I,
    )
    if match:
        return match.group(0)
    value = clean_html(str(job.get("salary") or "")).strip(" -")
    return value or "Not stated"


def job_has_passed_closing_date(description: str) -> bool:
    match = re.search(
        r"\b(?:close date|closing date|applications close)\s*:?\s*"
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}\s+[A-Za-z]+\s+\d{4})",
        description,
        re.I,
    )
    if not match:
        return False
    try:
        return dateparser.parse(match.group(1), dayfirst=True).date() < NOW.date()
    except (TypeError, ValueError, OverflowError):
        return False


def pete_job_item(job: dict, source: str) -> tuple[int, datetime, dict] | None:
    """Return only current UK public-sector vacancies with explicit AI relevance."""
    title = clean_html(str(job.get("title") or ""))
    company = clean_html(str(job.get("company_name") or job.get("company") or "Employer not stated"))
    location = clean_html(str(job.get("location") or "Location not stated"))
    description = clean_html(html.unescape(str(job.get("description") or "")))
    if "government digital service" in title.lower() and "government digital service" not in company.lower():
        return None
    if not AI_CAREER_TERMS.search(f"{title} {description}"):
        return None
    if not PUBLIC_SECTOR_EMPLOYER_TERMS.search(company):
        return None
    if not SOFIA_UK_LOCATION.search(f"{location} {description}"):
        return None
    if job.get("inactive") or INACTIVE_LISTING.search(description) or job_has_passed_closing_date(description):
        return None
    url = clean_html(str(job.get("url") or ""))
    if not url.startswith(("https://", "http://")):
        return None
    posted = parse_job_date(job)
    if posted and NOW - posted > timedelta(days=30):
        return None

    score = 5
    if re.search(r"\b(?:head|director|lead|senior|principal|architect|manager)\b", title, re.I):
        score += 2
    if AI_CAREER_TERMS.search(title):
        score += 3
    if source == "LinkedIn":
        score += 1
    posted_date = posted.strftime("%-d %B %Y") if posted else "Date not stated"
    item = {
        "title": title,
        "company": company,
        "description": published_job_description(description),
        "salary": published_job_salary(job),
        "postedDate": posted_date,
        "source": source,
        "location": location,
        "url": url,
        "contentType": "job",
        "countryFocus": "UK",
        "sector": "Public sector",
        "aiRelated": True,
    }
    if source == "LinkedIn":
        item["postedDate"] += " · LinkedIn listing date"
    for field in ('metadataSourceUrl', 'metadataVerifiedAt'):
        if job.get(field):
            item[field] = job[field]
    if posted:
        item["postedAt"] = posted.date().isoformat()
    return score, posted or datetime.min.replace(tzinfo=TZ), item


def verified_career_details(job: dict) -> dict:
    """Retain researched primary metadata only for the exact current vacancy."""
    try:
        catalog = json.loads((DATA / 'career-verified.json').read_text())
        verified = catalog.get(str(job.get('url') or '').split('?', 1)[0])
        normal_title = lambda title: re.sub(r'\W+', '', str(title).casefold())
        if not verified or normal_title(verified.get('title')) != normal_title(job.get('title')):
            return job
        company = str(job.get('company_name') or job.get('company') or '')
        if company.casefold() != str(verified.get('company') or '').casefold():
            return job
        age = (NOW.date() - dateparser.parse(verified['verifiedAt']).date()).days
        if not 0 <= age <= 14:
            return job
        enriched = dict(job)
        if verified.get('closingDate') and dateparser.parse(verified['closingDate']).date() < NOW.date():
            enriched['inactive'] = True
            return enriched
        for field in ('description', 'salary', 'location'):
            enriched[field] = verified[field]
        enriched['metadataSourceUrl'] = verified['originalEmployerUrl']
        enriched['metadataVerifiedAt'] = verified['verifiedAt']
        return enriched
    except (OSError, ValueError, KeyError, TypeError):
        return job


def public_ai_career_jobs(candidates: list[tuple[dict, str]] | None = None, limit: int = 10) -> list[dict]:
    candidates = candidates if candidates is not None else career_job_candidates()
    linkedin_candidates = [
        job for job, source in candidates
        if source == "LinkedIn" and job.get("target") == "public-ai"
        and AI_CAREER_TERMS.search(str(job.get("title") or ""))
        and PUBLIC_SECTOR_EMPLOYER_TERMS.search(str(job.get("company_name") or job.get("company") or ""))
    ]
    with ThreadPoolExecutor(max_workers=6) as pool:
        linkedin_enriched = {
            job.get("url"): enriched
            for job, enriched in zip(linkedin_candidates, pool.map(linkedin_description, linkedin_candidates))
        }

    ranked, seen = [], set()
    for job, source in candidates:
        if source == "LinkedIn":
            if job.get("target") != "public-ai":
                continue
            job = linkedin_enriched.get(job.get("url"), job)
        job = verified_career_details(job)
        result = pete_job_item(job, source)
        if not result:
            continue
        score, posted, item = result
        key = re.sub(r"\W+", "", f"{item['title']}{item['company']}".lower())[:180]
        if not key or key in seen:
            continue
        seen.add(key)
        ranked.append((score, posted, item))
    ranked.sort(key=lambda row: (row[1], row[0]), reverse=True)
    return [item for _, _, item in ranked[:limit]]


def pete_career_jobs(candidates: list[tuple[dict, str]] | None = None, limit: int = 10) -> list[dict]:
    return public_ai_career_jobs(candidates, limit)


def sofia_career_jobs(candidates: list[tuple[dict, str]] | None = None, limit: int = 10) -> list[dict]:
    return public_ai_career_jobs(candidates, limit)


def previous_career(profile: str) -> list[dict]:
    try:
        data = json.loads((DATA / f"{profile}.json").read_text(encoding="utf-8"))
        jobs = (data.get("sections") or {}).get("Career") or []
        return [
            job for job in jobs
            if job.get("contentType") == "job"
            and job.get("sector") == "Public sector"
            and job.get("aiRelated") is True
            and all(key in job for key in ("title", "company", "description", "salary", "postedDate", "source", "location"))
            and str(job.get("url") or "").startswith(("https://", "http://"))
        ]
    except Exception:
        return []


def previous_arsenal_position() -> int | None:
    """Keep the last verified rank when the live standings feed is temporarily unavailable."""
    try:
        data = json.loads((DATA / "pete.json").read_text(encoding="utf-8"))
        position = (data.get("arsenal") or {}).get("leaguePosition")
        return position if isinstance(position, int) and 1 <= position <= 20 else None
    except Exception:
        return None


def calendar_colour_data() -> dict:
    path = DATA / "calendar-colors.json"
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return {"eventPalette": {}, "events": {}}


def normalize_google_uid(component) -> str:
    uid = clean_html(str(component.get("uid", "")))
    return uid.split("@", 1)[0] if "@" in uid else uid


def calendar_events() -> list[dict]:
    url = os.getenv("GOOGLE_CALENDAR_ICS_URL", "").strip()
    if not url: return []
    try:
        r = requests.get(url, headers=UA, timeout=30); r.raise_for_status(); cal = Calendar.from_ical(r.content)
    except Exception: return []
    colours = calendar_colour_data(); palette = colours.get("eventPalette", {}); event_colours = colours.get("events", {})
    start_window = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
    next_month = (start_window.replace(day=28) + timedelta(days=4)).replace(day=1)
    following = (next_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    end_window = following - timedelta(seconds=1)
    events = []
    for component in cal.walk("VEVENT"):
        start = component.decoded("dtstart"); end = component.decoded("dtend") if component.get("dtend") else start
        all_day = not isinstance(start, datetime)
        if all_day: start = datetime.combine(start, datetime.min.time(), TZ)
        elif start.tzinfo is None: start = start.replace(tzinfo=TZ)
        else: start = start.astimezone(TZ)
        if not isinstance(end, datetime): end = datetime.combine(end, datetime.min.time(), TZ)
        elif end.tzinfo is None: end = end.replace(tzinfo=TZ)
        else: end = end.astimezone(TZ)
        if end < start_window or start > end_window: continue
        title = clean_html(str(component.get("summary", "Calendar event"))) or "Calendar event"
        event_id = normalize_google_uid(component); color_id = event_colours.get(event_id); colour = palette.get(str(color_id)) if color_id else None
        time_label = "All day" if all_day else start.strftime("%-I:%M%p").lower().replace(":00", "")
        events.append({"title": title, "summary": "", "url": "", "start": start.isoformat(), "end": end.isoformat(), "date": start.date().isoformat(), "time": time_label, "allDay": all_day, "color": colour, "colorId": color_id, "googleEventId": event_id, "calendarColorSource": "google" if color_id else "calendar-default"})
    events.sort(key=lambda x: x["start"])
    return events


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
        "date": dt.isoformat(), "dateLabel": dt.strftime("%a %-d %b"), "kickoff": dt.strftime("%-I:%M%p").lower().replace(":00", ""),
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


def build_profiles() -> dict[str, dict]:
    previous_position = previous_arsenal_position()
    wx = weather(); cal = calendar_events(); world_fact = world_fact_for_today()
    ai = editorial_news(
        merge_news(
            rss('https://openai.com/news/rss.xml', 'OpenAI', 6, 7),
            rss('https://deepmind.google/blog/rss.xml', 'Google DeepMind', 6, 7),
            google_news('(OpenAI OR Anthropic OR "Google DeepMind" OR "AI model") when:3d', 12, 3),
            limit=10,
        ),
        10,
    )
    arsenal_news = first_team_arsenal_news(google_news('Arsenal FC when:3d', 8, 3))
    transfers = arsenal_transfer_updates()
    transfer_rumours = arsenal_transfer_rumours()
    arsenal = arsenal_snapshot(arsenal_news, transfers, transfer_rumours)
    if arsenal.get("leaguePosition") is None and previous_position is not None:
        arsenal["leaguePosition"] = previous_position
    local = local_news()
    uk = uk_news()
    tonight = tonight_recommendations()
    career_candidates = career_job_candidates()
    current_career = public_ai_career_jobs(career_candidates)
    pete_career = current_career or previous_career("pete")
    sofia_career = current_career or previous_career("sofia")
    sweden = editorial_news(google_news('(Sweden OR Swedish) news when:4d', 7, 4), 7)
    family = google_news('(Surrey family events OR Kingston family events OR Elmbridge family events OR Hampton Court events) when:14d', 8, 14)

    stamp = NOW.strftime("%A, %-d %B %Y · refreshed %-I:%M%p").replace("AM", "am").replace("PM", "pm")
    pete_sections = {"AI": ai, "Arsenal news": arsenal_news, "Local news": local, "UK news": uk, "Career": pete_career}
    sofia_sections = {"Sweden": sweden, "Local news": local, "UK news": uk, "AI": ai, "Career": sofia_career}
    for profile, sections in (("Pete", pete_sections), ("Sofia", sofia_sections)):
        errors = section_content_type_errors(sections)
        if errors:
            raise RuntimeError(f"{profile} section content contract failed: {'; '.join(errors)}")
    def first(items, fallback): return items[0] if items else {"title": fallback, "summary": "", "meta": "", "source": "", "url": ""}
    return {
        "pete": {"updatedLabel": stamp, "worldFact": world_fact, "weather": wx, "calendar": cal, "arsenal": arsenal, "lead": first(ai or arsenal_news or local, "Your morning brief is ready."), "interests": [dict(first(ai, "AI updates"), section="AI"), dict(first(arsenal_news, "Arsenal"), section="Arsenal"), dict(first(local, "Local"), section="Local")], "watch": tonight, "sections": pete_sections},
        "sofia": {"updatedLabel": stamp, "worldFact": world_fact, "weather": wx, "calendar": cal, "lead": first(sweden or local or tonight, "Your morning brief is ready."), "interests": [dict(first(sweden, "Sweden"), section="Sweden"), dict(first(local, "Local"), section="Local"), dict(first(tonight, "Tonight"), section="Watch")], "watch": tonight, "sections": sofia_sections},
    }


def main() -> None:
    profiles = build_profiles()
    for name, payload in profiles.items():
        (DATA / f"{name}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Updated:", ", ".join(str(DATA / f"{x}.json") for x in profiles))

if __name__ == "__main__": main()
