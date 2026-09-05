from __future__ import annotations

import json
import argparse
from copy import deepcopy
from pathlib import Path

from enrich_weather_metoffice import met_weather

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def merge_weather(fresh_weather: dict) -> None:
    for name in ("pete", "sofia"):
        path = DATA / f"{name}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))

        # Preserve the separately enriched "Yesterday in the UK" block so the
        # lightweight weather refresh only replaces live/current forecast data.
        existing_weather = payload.get("weather") or {}
        yesterday_extremes = existing_weather.get("yesterdayExtremes")
        weather = deepcopy(fresh_weather)
        weather.pop('yesterdayExtremes', None)
        if yesterday_extremes:
            weather["yesterdayExtremes"] = yesterday_extremes
        payload["weather"] = weather
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Met Office live weather refreshed for Pete and Sofia")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--apply', type=Path)
    args = parser.parse_args()
    if args.apply:
        merge_weather(json.loads(args.apply.read_text()))
        return
    fresh_weather = met_weather()
    if args.snapshot:
        args.snapshot.write_text(json.dumps(fresh_weather))
    merge_weather(fresh_weather)


if __name__ == "__main__":
    main()
