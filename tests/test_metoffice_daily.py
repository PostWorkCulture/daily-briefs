from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "enrich_weather_metoffice", ROOT / "scripts" / "enrich_weather_metoffice.py"
)
metoffice = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(metoffice)

# Structure observed on the Met Office forecast page on 15 October 2026:
# short "Fri 16" tab labels, <time datetime>, condition only in the symbol alt
# text, and rain chance only in the per-day hourly precipitation rows.
DAYS = [
    ("Today", "2026-10-15", "Sunny intervals;", 21, 10, "20% 40% 30% 10% <5%"),
    ("Fri 16", "2026-10-16", "Sunny intervals;", 16, 7, "<5% 30% ≥95% 40% <5%"),
    ("Sat 17", "2026-10-17", "Sunny day;", 14, 7, "<5% 10% 40% 30% <5%"),
    ("Sun 18", "2026-10-18", "Sunny intervals;", 14, 9, "20% 50% 40% 30% 20%"),
    ("Mon 19", "2026-10-19", "Overcast;", 15, 9, "40% 30% 20% 10% <5%"),
    ("Tue 20", "2026-10-20", "Sunny intervals;", 15, 9, "<5% <5% 10% 10% <5%"),
    ("Wed 21", "2026-10-21", "Sunny intervals;", 16, 11, "<5% 10% 20% 10% <5%"),
    ("Thu 22", "2026-10-22", "Sunny intervals;", 15, 10, "<5% <5% <5% <5% <5%"),
]


def fixture_html() -> str:
    tabs = []
    hourly = []
    for label, date, alt, high, low, rain in DAYS:
        tabs.append(
            f'<li><div class="link-display heading-s">'
            f'<h3 class="tab-day" aria-label="{label}"><time datetime="{date}">'
            f'<span class="heading-s">{label}</span></time></h3>'
            f'<div class="weather-day-elements"><div class="weather-symbol">'
            f'<img alt="{alt}"></div>'
            f'<div class="tab-temp temperature-data">'
            f'<span class="tab-temp-high"><span aria-hidden="true">{high}°</span>'
            f'<span class="visually-hidden">Maximum daytime temperature: {high} degrees Celsius;</span></span>'
            f'<span class="tab-temp-low"><span aria-hidden="true">{low}°</span>'
            f'<span class="visually-hidden">Minimum nighttime temperature: {low} degrees Celsius;</span></span>'
            f'</div></div></div></li>'
        )
        cells = "".join(f"<td>{value}</td>" for value in rain.split())
        hourly.append(
            f'<div data-date="{date}"><table><tr class="precipitation-chance-row hourly-table">'
            f"<th>Chance of precipitation</th>{cells}</tr></table></div>"
        )
    return (
        "<html><body><h2>Forecast days</h2><ul>" + "".join(tabs) + "</ul>"
        + "".join(hourly) + "</body></html>"
    )


class MetOfficeDailyForecastTests(unittest.TestCase):

    def test_short_day_labels_produce_seven_days(self) -> None:
        daily = metoffice.daily_blocks(BeautifulSoup(fixture_html(), "html.parser"))
        self.assertEqual(len(daily), 7)
        self.assertEqual(
            [day["date"] for day in daily],
            [d[1] for d in DAYS[:7]],
        )

    def test_conditions_temperatures_and_peak_rain_are_read(self) -> None:
        daily = metoffice.daily_blocks(BeautifulSoup(fixture_html(), "html.parser"))
        self.assertEqual(daily[1]["condition"], "Sunny intervals")
        self.assertEqual(daily[2]["condition"], "Sunny")
        self.assertEqual(daily[4]["condition"], "Overcast")
        self.assertEqual((daily[1]["high"], daily[1]["low"]), (16, 7))
        self.assertEqual(daily[1]["rainChance"], 95)
        self.assertEqual(daily[5]["rainChance"], 10)
        self.assertNotIn("Forecast", [day["condition"] for day in daily])


if __name__ == "__main__":
    unittest.main()
