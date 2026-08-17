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
PETE_ROLE_TERMS = re.compile(
    r"\b(?:ai|artificial intelligence|data|digital|automation|machine learning|analytics|"
    r"technology|technical|platform|cloud|cyber|information|solution architect|product)\b",
    re.I,
)
PETE_PUBLIC_SECTOR_TERMS = re.compile(
    r"\b(?:civil service|public sector|government|department for|cabinet office|gds|nhs|"
    r"local authority|ministry of|home office|public service)\b",
    re.I,
)
PETE_EXCLUDED_ROLE = re.compile(
    r"\b(?:software engineer|machine learning engineer|data engineer|developer|programmer|devops|mlops)\b",
    re.I,
)
INACTIVE_LISTING = re.compile(
    r"\b(?:no longer accepting applications|job (?:has )?expired|position (?:has been )?filled|"
    r"vacancy (?:has )?closed|applications? closed)\b",
    re.I,
)


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
        try:
            dt = dateparser.parse(entry.get("published", "")).astimezone(TZ)
            if NOW - dt > timedelta(days=max_age_days):
                continue
            meta = dt.strftime("%a %-d %b")
        except Exception:
            meta = "Recent"
        seen.add(key)
        out.append({"title": title.strip(), "summary": "", "meta": meta, "source": source.strip(), "url": entry.get("link", "")})
        if len(out) >= limit:
            break
    return out


def rss(url: str, section: str, limit: int = 6, max_age_days: int = 4) -> list[dict]:
    feed = feedparser.parse(url); items = []; seen = set()
    for entry in feed.entries[:limit * 4]:
        title = clean_html(entry.get("title", "")); key = re.sub(r"\W+", "", title.lower())[:120]
        if not title or key in seen: continue
        summary = clean_html(entry.get("summary", ""))[:220]
        try:
            dt = dateparser.parse(entry.get("published", "")).astimezone(TZ)
            if NOW - dt > timedelta(days=max_age_days): continue
            meta = dt.strftime("%a %-d %b")
        except Exception: meta = section
        seen.add(key)
        items.append({"title": title, "summary": summary, "meta": meta, "source": section, "url": entry.get("link", "")})
        if len(items) >= limit: break
    return items


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
            return dateparser.parse(str(value)).astimezone(TZ)
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
    if posted:
        item["postedAt"] = posted.date().isoformat()
    return score, posted or datetime.min.replace(tzinfo=TZ), item


def normalise_job(row: dict, source: str) -> dict:
    if source == "Arbeitnow":
        return {
            "title": row.get("title"), "company_name": row.get("company_name"),
            "location": row.get("location"), "description": row.get("description"),
            "url": row.get("url"), "created_at": row.get("created_at"), "remote": row.get("remote"),
        }
    if source == "Remote OK":
        return {
            "title": row.get("position"), "company_name": row.get("company"),
            "location": row.get("location") or "Remote", "description": row.get("description"),
            "tags": row.get("tags"), "url": row.get("url"), "epoch": row.get("epoch"), "remote": True,
        }
    if source == "Remotive":
        return {
            "title": row.get("title"), "company_name": row.get("company_name"),
            "location": row.get("candidate_required_location") or "Remote",
            "description": row.get("description"), "tags": row.get("tags"),
            "url": row.get("url"), "publication_date": row.get("publication_date"), "remote": True,
        }
    if source == "Jobicy":
        return {
            "title": row.get("jobTitle"), "company_name": row.get("companyName"),
            "location": row.get("jobGeo") or "Remote", "description": row.get("jobDescription"),
            "tags": row.get("jobIndustry"), "url": row.get("url"), "pubDate": row.get("pubDate"), "remote": True,
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
    jobs = []
    for start in starts:
        try:
            response = requests.get(
                "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
                params={"keywords": keywords, "location": location, "f_TPR": "r2592000", "start": start},
                headers=UA,
                timeout=25,
            )
            response.raise_for_status()
        except Exception:
            continue
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


def linkedin_description(job: dict) -> dict:
    if job.get("description") or not str(job.get("url") or "").startswith("http"):
        return job
    try:
        response = requests.get(job["url"], headers=UA, timeout=25)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text(" ", strip=True)
        block = soup.select_one(".show-more-less-html__markup")
        enriched = dict(job)
        enriched["description"] = block.get_text(" ", strip=True) if block else page_text
        if INACTIVE_LISTING.search(page_text):
            enriched["inactive"] = True
        return enriched
    except Exception:
        return job


def career_job_candidates() -> list[tuple[dict, str]]:
    candidates: list[tuple[dict, str]] = []
    for page in range(1, 4):
        try:
            response = requests.get(
                "https://www.arbeitnow.com/api/job-board-api",
                params={"page": page},
                headers=UA,
                timeout=30,
            )
            response.raise_for_status()
            rows = response.json().get("data", [])
        except Exception:
            break
        if not rows:
            break
        candidates.extend((normalise_job(row, "Arbeitnow"), "Arbeitnow") for row in rows)

    try:
        response = requests.get("https://remoteok.com/api", headers=UA, timeout=30)
        response.raise_for_status()
        rows = response.json()
        candidates.extend((normalise_job(row, "Remote OK"), "Remote OK") for row in rows[1:] if isinstance(row, dict))
    except Exception:
        pass

    for params in ({"category": "product"}, {"search": "AI data digital"}):
        try:
            response = requests.get("https://remotive.com/api/remote-jobs", params=params, headers=UA, timeout=30)
            response.raise_for_status()
            candidates.extend((normalise_job(row, "Remotive"), "Remotive") for row in response.json().get("jobs", []))
        except Exception:
            pass

    try:
        response = requests.get("https://jobicy.com/api/v2/remote-jobs", params={"count": 50, "geo": "uk"}, headers=UA, timeout=30)
        response.raise_for_status()
        candidates.extend((normalise_job(row, "Jobicy"), "Jobicy") for row in response.json().get("jobs", []))
    except Exception:
        pass

    for query in ("product manager", "produktchef"):
        try:
            response = requests.get(
                "https://jobsearch.api.jobtechdev.se/search",
                params={"q": query, "limit": 100},
                headers=UA,
                timeout=30,
            )
            response.raise_for_status()
            candidates.extend((normalise_job(row, "Sweden JobTech"), "Sweden JobTech") for row in response.json().get("hits", []))
        except Exception:
            pass

    candidates.extend(linkedin_jobs("Senior Product Manager OR Product Director OR Head of Product", "United Kingdom", "sofia"))
    candidates.extend(linkedin_jobs("Senior Product Manager OR Product Director OR Head of Product", "Sweden", "sofia"))
    candidates.extend(linkedin_jobs("AI data digital public sector", "United Kingdom", "pete"))
    return candidates


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


def pete_job_item(job: dict, source: str) -> tuple[int, datetime, dict] | None:
    title = clean_html(str(job.get("title") or ""))
    company = clean_html(str(job.get("company_name") or job.get("company") or "Employer not stated"))
    location = clean_html(str(job.get("location") or "Location not stated"))
    description = clean_html(html.unescape(str(job.get("description") or "")))
    if PETE_EXCLUDED_ROLE.search(title):
        return None
    if not PETE_ROLE_TERMS.search(title) and not PETE_PUBLIC_SECTOR_TERMS.search(f"{title} {company}"):
        return None
    if not SOFIA_UK_LOCATION.search(f"{location} {description}"):
        return None
    if job.get("inactive") or INACTIVE_LISTING.search(description):
        return None
    url = clean_html(str(job.get("url") or ""))
    if not url.startswith(("https://", "http://")):
        return None
    posted = parse_job_date(job)
    if posted and NOW - posted > timedelta(days=30):
        return None

    score = 4
    if PETE_PUBLIC_SECTOR_TERMS.search(f"{title} {company} {description}"):
        score += 5
    if re.search(r"\b(?:head|director|lead|senior|principal|architect|manager)\b", title, re.I):
        score += 2
    if re.search(r"\b(?:ai|artificial intelligence|automation|machine learning)\b", title, re.I):
        score += 3
    if source == "LinkedIn":
        score += 1
    posted_label = posted.strftime("Posted %a %-d %b") if posted else "Current posting"
    item = {
        "title": title,
        "summary": f"{company} · {location}",
        "meta": f"UK · {posted_label}",
        "source": source,
        "url": url,
        "contentType": "job",
        "countryFocus": "UK",
        "company": company,
        "location": location,
    }
    if posted:
        item["postedAt"] = posted.date().isoformat()
    return score, posted or datetime.min.replace(tzinfo=TZ), item


def pete_career_jobs(candidates: list[tuple[dict, str]] | None = None, limit: int = 10) -> list[dict]:
    candidates = candidates if candidates is not None else career_job_candidates()
    ranked, seen = [], set()
    for job, source in candidates:
        if source == "LinkedIn" and job.get("target") != "pete":
            continue
        result = pete_job_item(job, source)
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


def previous_career(profile: str) -> list[dict]:
    try:
        data = json.loads((DATA / f"{profile}.json").read_text(encoding="utf-8"))
        jobs = (data.get("sections") or {}).get("Career") or []
        return [
            job for job in jobs
            if job.get("contentType") == "job" and str(job.get("url") or "").startswith(("https://", "http://"))
        ]
    except Exception:
        return []


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


def arsenal_snapshot(news: list[dict]) -> dict:
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
    }


def build_profiles() -> dict[str, dict]:
    wx = weather(); cal = calendar_events()
    ai = google_news('(OpenAI OR Anthropic OR "Google DeepMind" OR "AI model") when:3d', 8, 3)
    arsenal_news = google_news('Arsenal FC when:3d', 8, 3)
    arsenal = arsenal_snapshot(arsenal_news)
    local = google_news('(Kingston upon Thames OR Molesey OR Esher OR Walton-on-Thames OR Elmbridge) when:4d', 8, 4)
    uk = rss('https://feeds.bbci.co.uk/news/rss.xml', 'BBC News', 6, 2) or google_news('UK news when:2d', 6, 2)
    tonight = tonight_recommendations()
    career_candidates = career_job_candidates()
    pete_career = pete_career_jobs(career_candidates) or previous_career("pete")
    sofia_career = sofia_career_jobs(career_candidates) or previous_career("sofia")
    sweden = google_news('(Sweden OR Swedish) news when:4d', 7, 4)
    family = google_news('(Surrey family events OR Kingston family events OR Elmbridge family events OR Hampton Court events) when:14d', 8, 14)

    stamp = NOW.strftime("%A, %-d %B %Y · refreshed %-I:%M%p").replace("AM", "am").replace("PM", "pm")
    pete_sections = {"AI": ai, "Arsenal news": arsenal_news, "Local news": local, "UK news": uk, "Career": pete_career}
    sofia_sections = {"Sweden": sweden, "Local news": local, "UK news": uk, "AI": ai, "Career": sofia_career}
    def first(items, fallback): return items[0] if items else {"title": fallback, "summary": "", "meta": "", "source": "", "url": ""}
    return {
        "pete": {"updatedLabel": stamp, "weather": wx, "calendar": cal, "arsenal": arsenal, "lead": first(ai or arsenal_news or local, "Your morning brief is ready."), "interests": [dict(first(ai, "AI updates"), section="AI"), dict(first(arsenal_news, "Arsenal"), section="Arsenal"), dict(first(local, "Local"), section="Local")], "watch": tonight, "sections": pete_sections},
        "sofia": {"updatedLabel": stamp, "weather": wx, "calendar": cal, "lead": first(sweden or local or tonight, "Your morning brief is ready."), "interests": [dict(first(sweden, "Sweden"), section="Sweden"), dict(first(local, "Local"), section="Local"), dict(first(tonight, "Tonight"), section="Watch")], "watch": tonight, "sections": sofia_sections},
    }


def main() -> None:
    profiles = build_profiles()
    for name, payload in profiles.items():
        (DATA / f"{name}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Updated:", ", ".join(str(DATA / f"{x}.json") for x in profiles))

if __name__ == "__main__": main()
