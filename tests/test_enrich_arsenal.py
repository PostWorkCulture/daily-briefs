from __future__ import annotations

import importlib.util
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


enrich_arsenal = load_script("enrich_arsenal")
enrich_next_fixture = load_script("enrich_next_fixture")


class UpcomingFixtureTests(unittest.TestCase):
    def test_updated_official_fixture_date_time_and_broadcaster_are_parsed(self) -> None:
        html = """
        <main>
          <p>Monday 31 August</p>
          <p>20:00 Aston Villa v Arsenal (Sky Sports)</p>
          <p>Sunday 6 September</p>
          <p>16:30 Arsenal v Chelsea (Sky Sports)</p>
        </main>
        """
        now = datetime(2026, 8, 24, 9, 0, tzinfo=ZoneInfo("Europe/London"))
        fixtures = enrich_arsenal.parse_official_pl_fixtures(
            html, enrich_arsenal.OFFICIAL_PL_FIXTURE_URLS[0], now
        )

        self.assertEqual(len(fixtures), 2)
        self.assertEqual(fixtures[0]["dateLabel"], "Mon 31 Aug")
        self.assertEqual(fixtures[0]["kickoff"], "8pm")
        self.assertEqual(fixtures[0]["opponent"], "Aston Villa")
        self.assertEqual(fixtures[0]["homeAway"], "away")
        self.assertEqual(fixtures[0]["tvChannel"], "Sky Sports")

    def test_official_reschedule_replaces_stale_same_opponent_fixture(self) -> None:
        stale = {
            "date": "2026-08-29T00:00:00+01:00",
            "opponent": "Aston Villa",
            "competition": "Premier League",
            "completed": False,
        }
        cup_fixture = {
            "date": "2026-08-27T20:00:00+01:00",
            "opponent": "Chelsea",
            "competition": "League Cup",
            "completed": False,
        }
        official = {
            "date": "2026-08-31T20:00:00+01:00",
            "opponent": "Aston Villa",
            "competition": "Premier League",
            "completed": False,
        }

        fixtures = enrich_arsenal.reconcile_official_fixture(
            [stale, cup_fixture], official
        )

        self.assertIn(cup_fixture, fixtures)
        self.assertIn(official, fixtures)
        self.assertNotIn(stale, fixtures)

    def test_verified_aston_villa_details_are_complete(self) -> None:
        fixture = enrich_next_fixture.enrich_fixture(
            {
                "date": "2026-08-31T20:00:00+01:00",
                "dateLabel": "Mon 31 Aug",
                "kickoff": "8pm",
                "opponent": "Aston Villa",
                "competition": "Premier League",
                "homeAway": "away",
            }
        )

        self.assertEqual(fixture["stadium"], "Villa Park")
        self.assertEqual(fixture["kickoff"], "8:00pm")
        self.assertEqual(fixture["tvChannel"], "Sky Sports")
        self.assertEqual(
            fixture["previousMeeting"]["score"], "Arsenal 4–1 Aston Villa"
        )


if __name__ == "__main__":
    unittest.main()
