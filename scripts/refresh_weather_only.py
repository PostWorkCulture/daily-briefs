from __future__ import annotations

import json
from pathlib import Path

from enrich_weather_metoffice import met_weather

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def main() -> None:
    fresh_weather = met_weather()

    for name in ("pete", "sofia"):
        path = DATA / f"{name}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))

        # Preserve the separately enriched "Yesterday in the UK" block so the
        # lightweight weather refresh only replaces live/current forecast data.
        existing_weather = payload.get("weather") or {}
        yesterday_extremes = existing_weather.get("yesterdayExtremes")
        if yesterday_extremes:
            fresh_weather["yesterdayExtremes"] = yesterday_extremes

        payload["weather"] = fresh_weather
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Met Office live weather refreshed for Pete and Sofia")


if __name__ == "__main__":
    main()
