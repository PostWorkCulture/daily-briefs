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


def verified_community_shield() -> dict:
    return {
        "date": "2026-08-16T15:00:00+01:00",
        "dateLabel": "Sun 16 Aug",
        "kickoff": "3pm",
        "opponent": "Manchester City",
        "competition": "FA Community Shield",
        "homeAway": "neutral",
        "completed": False,
        "arsenalScore": None,
        "opponentScore": None,
        "result": "",
        "url": "https://www.thefa.com/news/2026/jun/04/2026-fa-community-shield",
        "source": "The FA",
    }


def main() -> None:
    path = DATA / "pete.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    sections = payload.setdefault("sections", {})
    arsenal_news = [x for x in sections.get("Arsenal news", []) if not betting_item(x)]
    sections["Arsenal news"] = arsenal_news

    # Prevent betting content leaking through the smaller "For you" Arsenal card as well.
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
    arsenal["scope"] = "Arsenal men's first team · all competitions"

    # Source data currently misses the final pre-season result. Keep a verified fallback only
    # until a newer completed match is available from Sky/ESPN.
    last = arsenal.get("lastResult")
    como = verified_como_result()
    if not last:
        arsenal["lastResult"] = como
    else:
        try:
            if datetime.fromisoformat(last["date"]) < datetime.fromisoformat(como["date"]):
                arsenal["lastResult"] = como
        except Exception:
            arsenal["lastResult"] = como

    # Before kick-off, Community Shield is the next men's first-team fixture regardless of
    # the Premier League fallback. After the match starts, live sources are allowed to take over.
    shield = verified_community_shield()
    shield_dt = datetime.fromisoformat(shield["date"])
    if NOW < shield_dt:
        next_fixture = arsenal.get("nextFixture")
        try:
            next_dt = datetime.fromisoformat(next_fixture["date"]) if next_fixture else None
        except Exception:
            next_dt = None
        if next_dt is None or shield_dt < next_dt:
            arsenal["nextFixture"] = shield

    payload["arsenal"] = arsenal
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Arsenal finalization complete")


if __name__ == "__main__":
    main()
