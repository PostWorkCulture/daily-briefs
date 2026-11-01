"""Automatic completion of Arsenal's latest result (no hand-written verified_*_result needed)."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


enrich_arsenal = load_script("enrich_arsenal")
finalize_arsenal = load_script("finalize_arsenal")

COMPETITORS = [
    {"homeAway": "home", "score": "1", "team": {"id": "364", "displayName": "Liverpool"}},
    {"homeAway": "away", "score": "2", "team": {"id": "359", "displayName": "Arsenal"}},
]


def espn_summary(key_events: list[dict], venue: str = "Anfield") -> dict:
    return {
        "header": {"competitions": [{"competitors": COMPETITORS}]},
        "gameInfo": {"venue": {"fullName": venue}},
        "keyEvents": key_events,
    }


def goal(name: str, team_id: str, team: str, minute: str, kind: str = "Goal", period: int = 1) -> dict:
    return {
        "type": {"text": kind, "type": kind.lower().replace(" ", "-")},
        "scoringPlay": True,
        "period": {"number": period},
        "clock": {"displayValue": minute},
        "team": {"id": team_id, "displayName": team},
        "participants": [{"athlete": {"displayName": name}}],
    }


ESPN_ITEM = {
    "date": "2026-11-01T16:30:00+00:00",
    "opponent": "Liverpool",
    "competition": "Premier League",
    "completed": True,
    "arsenalScore": 2,
    "opponentScore": 1,
    "result": "2–1",
    "_eventId": "1",
    "_competitionCode": "eng.1",
}


class EspnSummaryTests(unittest.TestCase):
    def test_scorers_and_venue_come_from_key_events_and_game_info(self) -> None:
        summary = espn_summary([
            goal("Bukayo Saka", "359", "Arsenal", "12'"),
            {"type": {"text": "Yellow Card"}, "scoringPlay": False},
            goal("Mohamed Salah", "364", "Liverpool", "40'", kind="Penalty - Scored"),
            goal("Declan Rice", "359", "Arsenal", "77'"),
        ])
        with patch.object(enrich_arsenal, "get_json", return_value=summary):
            result = enrich_arsenal.enrich_completed_result(dict(ESPN_ITEM))
        self.assertEqual(result["stadium"], "Anfield")
        self.assertEqual([row["name"] for row in result["scorers"]], ["Bukayo Saka", "Mohamed Salah", "Declan Rice"])
        self.assertTrue(result["scorers"][1]["penalty"])
        self.assertIn("Mohamed Salah (pen) 40'", result["scorersLabel"])
        self.assertIn("beat Liverpool 2–1 at Anfield", result["summary"])

    def test_shootout_kicks_are_not_counted_as_scorers(self) -> None:
        summary = espn_summary([
            goal("Bukayo Saka", "359", "Arsenal", "12'"),
            goal("Mohamed Salah", "364", "Liverpool", "40'"),
            goal("Declan Rice", "359", "Arsenal", "77'"),
            goal("Martin Odegaard", "359", "Arsenal", "", kind="Shootout Goal", period=5),
        ])
        with patch.object(enrich_arsenal, "get_json", return_value=summary):
            result = enrich_arsenal.enrich_completed_result(dict(ESPN_ITEM))
        self.assertEqual(len(result["scorers"]), 3)

    def test_scorers_that_do_not_add_up_to_the_score_are_dropped(self) -> None:
        summary = espn_summary([goal("Bukayo Saka", "359", "Arsenal", "12'")])
        with patch.object(enrich_arsenal, "get_json", return_value=summary):
            result = enrich_arsenal.enrich_completed_result(dict(ESPN_ITEM))
        self.assertNotIn("scorers", result)
        self.assertNotIn("scorersLabel", result)
        self.assertEqual(result["stadium"], "Anfield")

    def test_previous_next_fixture_supplies_stadium(self) -> None:
        sky_completed = {
            "date": "2026-11-01T16:30:00+00:00", "dateLabel": "Sun 1 Nov", "kickoff": "4:30pm",
            "opponent": "Liverpool", "competition": "Premier League", "homeAway": "away",
            "completed": True, "arsenalScore": 0, "opponentScore": 0, "result": "0–0",
            "source": "Sky Sports", "url": "https://www.skysports.com/football/liverpool-vs-arsenal/1",
        }
        existing = {"nextFixture": {
            "date": "2026-11-01T16:30:00+00:00", "opponent": "Liverpool",
            "completed": False, "stadium": "Anfield",
        }}
        with patch.object(enrich_arsenal, "espn_snapshot", return_value=([], 1, 20, 10)), \
             patch.object(enrich_arsenal, "all_sky_matches", return_value=[sky_completed]), \
             patch.object(enrich_arsenal, "all_bbc_matches", return_value=[]), \
             patch.object(enrich_arsenal, "official_pl_next_fixture", return_value=None), \
             patch.object(enrich_arsenal, "NOW", enrich_arsenal.NOW.replace(year=2026, month=11, day=2, hour=5, minute=0)):
            result = enrich_arsenal.snapshot([], existing_arsenal=existing)
        self.assertEqual(result["lastResult"]["stadium"], "Anfield")


class FactualSummaryTests(unittest.TestCase):
    BASE = {
        "opponent": "Liverpool", "stadium": "Anfield", "competition": "Premier League",
        "arsenalScore": 2, "opponentScore": 1, "result": "2–1",
        "scorers": [
            {"name": "Bukayo Saka", "team": "Arsenal", "minute": "12'"},
            {"name": "Mohamed Salah", "team": "Liverpool", "minute": "40'"},
            {"name": "Declan Rice", "team": "Arsenal", "minute": "77'"},
        ],
    }

    def test_summary_is_built_only_from_verified_fields(self) -> None:
        result = finalize_arsenal.with_factual_summary(dict(self.BASE))
        self.assertEqual(
            result["summary"],
            "Bukayo Saka and Declan Rice scored as Arsenal beat Liverpool 2–1 at Anfield in the Premier League.",
        )

    def test_goalless_draw(self) -> None:
        item = dict(self.BASE, arsenalScore=0, opponentScore=0, result="0–0", scorers=[])
        result = finalize_arsenal.with_factual_summary(item)
        self.assertEqual(result["summary"], "Arsenal drew 0–0 with Liverpool at Anfield in the Premier League.")
        self.assertEqual(result["scorersLabel"], "No scorers")

    def test_existing_summary_is_kept(self) -> None:
        item = dict(self.BASE, summary="Report summary.")
        self.assertEqual(finalize_arsenal.with_factual_summary(item)["summary"], "Report summary.")

    def test_no_summary_without_stadium_or_complete_scorers(self) -> None:
        self.assertNotIn("summary", finalize_arsenal.with_factual_summary(dict(self.BASE, stadium="")))
        self.assertNotIn("summary", finalize_arsenal.with_factual_summary(dict(self.BASE, scorers=self.BASE["scorers"][:1])))


if __name__ == "__main__":
    unittest.main()
