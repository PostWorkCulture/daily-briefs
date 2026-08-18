from __future__ import annotations

import json
import re
from datetime import datetime
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
    # Current Daily Briefs news feed contains Arsenal.com's report of the 3-0 result.
    # Keep this verified result until a still-newer completed men's first-team match is available.
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
    arsenal["transfers"] = [
        x for x in arsenal.get("transfers", [])
        if not betting_item(x) and x.get("contentType") == "transfer-update" and x.get("trust")
    ][:6]
    arsenal["scope"] = "Arsenal men's first team · all competitions"

    # Choose the newest verified completed fallback only when the live source has not
    # already supplied a newer completed result.
    fallback = verified_community_shield_result() if NOW >= datetime.fromisoformat("2026-08-16T15:00:00+01:00") else verified_como_result()
    last = arsenal.get("lastResult")
    if not last:
        arsenal["lastResult"] = fallback
    else:
        try:
            last_dt = datetime.fromisoformat(last["date"])
            fallback_dt = datetime.fromisoformat(fallback["date"])
            if last_dt < fallback_dt:
                arsenal["lastResult"] = fallback
            elif last_dt == fallback_dt and last.get("opponent") == "Manchester City":
                # Preserve the approved result image even if another source supplied the score.
                last.setdefault("image", fallback["image"])
                last.setdefault("imageAlt", fallback["imageAlt"])
                arsenal["lastResult"] = last
        except Exception:
            arsenal["lastResult"] = fallback

    payload["arsenal"] = arsenal
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Arsenal finalization complete")


if __name__ == "__main__":
    main()
