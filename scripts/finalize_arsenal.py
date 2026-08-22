from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
TZ = ZoneInfo("Europe/London")
NOW = datetime.now(TZ)

BETTING_TERMS = (
    " bet ", " betting ", " odds ", " bookmaker", " bookie", " gambling ",
    " wager", " accumulator", " acca ", " tipster", " free bet", " bet builder",
    " sportsbook", " casino ",
)

TRUSTED_RESULT_SOURCES = {
    "arsenal.com": 0,
    "bbc": 1,
    "bbc sport": 1,
    "sky sports": 2,
    "espn": 3,
}

RESULT_SIGNAL = re.compile(r"\b(?:report|result|highlights?|full[- ]time|full time)\b", re.I)
SCORELINE = re.compile(
    r"(?P<home>[A-Za-z][A-Za-z0-9 .&'’\-]{1,48}?)\s+"
    r"(?P<hscore>\d{1,2})\s*[-–—]\s*(?P<ascore>\d{1,2})\s+"
    r"(?P<away>[A-Za-z][A-Za-z0-9 .&'’\-]{1,48})",
    re.I,
)


def betting_item(item: dict) -> bool:
    text = " " + re.sub(
        r"\s+", " ",
        " ".join(str(item.get(k, "")) for k in ("title", "summary", "source")).lower(),
    ) + " "
    return any(term in text for term in BETTING_TERMS)


def verified_como_result() -> dict:
    return {
        "date": "2026-08-12T19:30:00+01:00",
        "dateLabel": "Wed 12 Aug",
        "kickoff": "7:30pm",
        "opponent": "Como",
        "competition": "Friendly Match · Emirates Cup",
        "homeAway": "home",
        "completed": True,
        "arsenalScore": 1,
        "opponentScore": 1,
        "result": "1–1 (won 4–3 pens)",
        "url": "https://www.skysports.com/football/arsenal-vs-como/562442",
        "source": "Verified result",
    }


def verified_community_shield_result() -> dict:
    return {
        "date": "2026-08-16T15:00:00+01:00",
        "dateLabel": "Sun 16 Aug",
        "kickoff": "3pm",
        "opponent": "Manchester City",
        "competition": "FA Community Shield",
        "homeAway": "neutral",
        "completed": True,
        "arsenalScore": 3,
        "opponentScore": 0,
        "result": "3–0",
        "url": "https://www.skysports.com/football/arsenal-vs-manchester-city/report/556659",
        "source": "Sky Sports / Arsenal.com",
        "image": "https://e0.365dm.com/26/08/1600x900/skysports-arsenal-man-city_7323378.jpg?20260816170357",
        "imageAlt": "Arsenal players after the 3-0 Community Shield win over Manchester City",
    }


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ)
    except Exception:
        return None


def clean_team(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip(" .:-|")
    text = re.sub(r"\s+(?:extended|highlights?|report)$", "", text, flags=re.I)
    return text.strip(" .:-|")


def infer_competition(texts: list[str]) -> str:
    blob = " ".join(texts).lower()
    checks = (
        ("Premier League", ("premier league",)),
        ("FA Community Shield", ("community shield",)),
        ("Champions League", ("champions league",)),
        ("FA Cup", ("fa cup",)),
        ("League Cup", ("league cup", "carabao cup")),
        ("Europa League", ("europa league",)),
        ("Friendly Match", ("friendly", "emirates cup")),
    )
    for label, terms in checks:
        if any(term in blob for term in terms):
            return label
    return "Men's first team"


def parse_news_result(item: dict) -> dict | None:
    source = str(item.get("source") or "").strip().lower()
    if source not in TRUSTED_RESULT_SOURCES:
        return None

    title = str(item.get("title") or "").strip()
    if not RESULT_SIGNAL.search(title):
        return None

    match = SCORELINE.search(title)
    if not match:
        return None

    home = clean_team(match.group("home"))
    away = clean_team(match.group("away"))
    if home.lower() != "arsenal" and away.lower() != "arsenal":
        return None

    published = parse_dt(item.get("publishedAt"))
    if not published or published > NOW + timedelta(hours=2):
        return None

    hscore = int(match.group("hscore"))
    ascore = int(match.group("ascore"))
    arsenal_home = home.lower() == "arsenal"
    opponent = away if arsenal_home else home

    return {
        "date": published.replace(hour=12, minute=0, second=0, microsecond=0).isoformat(),
        "dateLabel": published.strftime("%a %-d %b"),
        "kickoff": "",
        "opponent": opponent,
        "competition": infer_competition([title]),
        "homeAway": "home" if arsenal_home else "away",
        "completed": True,
        "arsenalScore": hscore if arsenal_home else ascore,
        "opponentScore": ascore if arsenal_home else hscore,
        "result": f"{hscore if arsenal_home else ascore}–{ascore if arsenal_home else hscore}",
        "url": str(item.get("url") or ""),
        "source": str(item.get("source") or ""),
        "_publishedAt": published.isoformat(),
        "_sourcePriority": TRUSTED_RESULT_SOURCES[source],
        "_title": title,
    }


def newest_news_result(payload: dict) -> dict | None:
    sections = payload.get("sections") or {}
    arsenal = payload.get("arsenal") or {}
    items = []
    seen = set()
    for source_items in (sections.get("Arsenal news") or [], arsenal.get("news") or []):
        for item in source_items:
            key = (item.get("title"), item.get("publishedAt"), item.get("source"))
            if key in seen:
                continue
            seen.add(key)
            items.append(item)

    parsed = [x for x in (parse_news_result(item) for item in items) if x]
    if not parsed:
        return None

    parsed.sort(
        key=lambda x: (
            parse_dt(x["_publishedAt"]) or datetime.min.replace(tzinfo=TZ),
            -int(x["_sourcePriority"]),
        ),
        reverse=True,
    )
    newest_date = (parse_dt(parsed[0]["_publishedAt"]) or NOW).date()
    newest = [x for x in parsed if (parse_dt(x["_publishedAt"]) or NOW).date() == newest_date]

    # Prefer Arsenal.com for the canonical report, but use any same-day trusted
    # headline to enrich the competition label.
    newest.sort(key=lambda x: (int(x["_sourcePriority"]), -(parse_dt(x["_publishedAt"]) or NOW).timestamp()))
    chosen = dict(newest[0])

    same_match_texts = []
    for candidate in newest:
        if (
            candidate["opponent"].lower() == chosen["opponent"].lower()
            and candidate["arsenalScore"] == chosen["arsenalScore"]
            and candidate["opponentScore"] == chosen["opponentScore"]
        ):
            same_match_texts.append(candidate.get("_title", ""))
    chosen["competition"] = infer_competition(same_match_texts or [chosen.get("_title", "")])

    for private_key in ("_publishedAt", "_sourcePriority", "_title"):
        chosen.pop(private_key, None)
    return chosen


def use_fixture_details(candidate: dict, arsenal: dict) -> dict:
    fixture = arsenal.get("nextFixture") or {}
    if not fixture:
        return candidate
    candidate_dt = parse_dt(candidate.get("date"))
    fixture_dt = parse_dt(fixture.get("date"))
    if (
        candidate_dt
        and fixture_dt
        and candidate_dt.date() == fixture_dt.date()
        and str(candidate.get("opponent") or "").lower() == str(fixture.get("opponent") or "").lower()
    ):
        enriched = dict(candidate)
        for key in ("date", "dateLabel", "kickoff", "competition", "homeAway"):
            if fixture.get(key):
                enriched[key] = fixture[key]
        return enriched
    return candidate


def apply_last_result_fallback(payload: dict) -> None:
    arsenal = payload.setdefault("arsenal", {})
    fallback = (
        verified_community_shield_result()
        if NOW >= datetime.fromisoformat("2026-08-16T15:00:00+01:00")
        else verified_como_result()
    )
    news_result = newest_news_result(payload)
    if news_result:
        news_result = use_fixture_details(news_result, arsenal)

    candidates = [fallback]
    if news_result:
        candidates.append(news_result)

    last = arsenal.get("lastResult")
    if last:
        candidates.append(last)

    def candidate_dt(item: dict) -> datetime:
        return parse_dt(item.get("date")) or datetime.min.replace(tzinfo=TZ)

    newest = max(candidates, key=candidate_dt)

    # Preserve the approved Community Shield image only while that remains the
    # actual latest result.
    if (
        newest.get("opponent") == "Manchester City"
        and candidate_dt(newest) == candidate_dt(fallback)
    ):
        newest = dict(newest)
        newest.setdefault("image", fallback.get("image"))
        newest.setdefault("imageAlt", fallback.get("imageAlt"))

    arsenal["lastResult"] = newest

    # Guardrail: if trusted result/report news contains a newer completed match
    # than lastResult, fail the refresh instead of silently publishing stale data.
    newest_news = newest_news_result(payload)
    if newest_news:
        current_dt = candidate_dt(arsenal["lastResult"])
        news_dt = candidate_dt(newest_news)
        if current_dt.date() < news_dt.date():
            raise RuntimeError(
                f"Arsenal lastResult is stale: {arsenal['lastResult'].get('dateLabel')} "
                f"but trusted result news has {newest_news.get('dateLabel')} "
                f"vs {newest_news.get('opponent')}"
            )
        if current_dt.date() == news_dt.date():
            same_score = (
                arsenal["lastResult"].get("arsenalScore") == newest_news.get("arsenalScore")
                and arsenal["lastResult"].get("opponentScore") == newest_news.get("opponentScore")
            )
            same_opponent = str(arsenal["lastResult"].get("opponent") or "").lower() == str(newest_news.get("opponent") or "").lower()
            if not (same_score and same_opponent):
                raise RuntimeError(
                    "Arsenal lastResult disagrees with trusted same-day result news"
                )


def main() -> None:
    path = DATA / "pete.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    sections = payload.setdefault("sections", {})
    arsenal_news = [x for x in sections.get("Arsenal news", []) if not betting_item(x)]
    sections["Arsenal news"] = arsenal_news

    interests = []
    for item in payload.get("interests", []):
        if str(item.get("section", "")).lower() == "arsenal" and betting_item(item):
            continue
        interests.append(item)
    if not any(str(x.get("section", "")).lower() == "arsenal" for x in interests) and arsenal_news:
        replacement = dict(arsenal_news[0])
        replacement["section"] = "Arsenal"
        interests.append(replacement)
    payload["interests"] = interests

    arsenal = payload.setdefault("arsenal", {})
    arsenal["news"] = [x for x in arsenal.get("news", arsenal_news) if not betting_item(x)][:5]
    arsenal["transfers"] = sorted([
        x for x in arsenal.get("transfers", [])
        if not betting_item(x) and x.get("contentType") == "transfer-update" and x.get("trust")
    ], key=lambda x: str(x.get("publishedAt") or ""), reverse=True)[:6]
    arsenal["transferRumours"] = sorted([
        x for x in arsenal.get("transferRumours", [])
        if not betting_item(x)
        and x.get("contentType") == "transfer-rumour"
        and x.get("trust") == "Unconfirmed"
        and x.get("sourceType") == "X"
    ], key=lambda x: str(x.get("publishedAt") or ""), reverse=True)[:5]
    arsenal["scope"] = "Arsenal men's first team · all competitions"

    apply_last_result_fallback(payload)

    payload["arsenal"] = arsenal
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "Arsenal finalization complete: "
        f"{arsenal['lastResult'].get('dateLabel')} Arsenal "
        f"{arsenal['lastResult'].get('result')} {arsenal['lastResult'].get('opponent')}"
    )


if __name__ == "__main__":
    main()
