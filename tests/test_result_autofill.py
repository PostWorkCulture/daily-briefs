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
             patch.object(enrich_arsenal, "bbc_results", return_value=[]), \
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
        self.assertNotIn("summary", finalize_arsenal.with_factual_summary(dict(self.BASE, stadium="TBC")))
        self.assertNotIn("summary", finalize_arsenal.with_factual_summary(dict(self.BASE, stadium="")))
        self.assertNotIn("summary", finalize_arsenal.with_factual_summary(dict(self.BASE, scorers=self.BASE["scorers"][:1])))


def bbc_page(events: list[dict]) -> str:
    import json as _json
    state = {"data": {"x": {"name": "sport-data-scores-fixtures", "data": {"eventGroups": [
        {"secondaryGroups": [{"events": events}]}]}}}}
    return "<script>window.__INITIAL_DATA__=" + _json.dumps(_json.dumps(state)) + ";</script>"


def bbc_goal(name: str, minute: str, kind: str = "Goal") -> dict:
    return {"playerName": name, "actionType": "goal",
            "actions": [{"type": kind, "typeLabel": {"value": kind}, "timeLabel": {"value": minute}}]}


BBC_EVENT = {
    "status": "PostEvent",
    "startDateTime": "2026-11-01T16:30:00+00:00",
    "tournament": {"name": "Premier League"},
    "onwardJourneyLink": "/sport/football/live/abc",
    "home": {"fullName": "Liverpool", "score": "1", "actions": [bbc_goal("M. Salah", "40'", "Penalty")]},
    "away": {"fullName": "Arsenal", "score": "2", "actions": [
        {"playerName": "B. Saka", "actionType": "goal", "actions": [
            {"type": "Goal", "timeLabel": {"value": "12'"}}, {"type": "Goal", "timeLabel": {"value": "77'"}}]},
        {"playerName": "D. Rice", "actionType": "card", "actions": [{"type": "Yellow Card"}]},
    ]},
}


class BbcResultTests(unittest.TestCase):
    def test_completed_bbc_event_yields_scorers(self) -> None:
        rows = enrich_arsenal.parse_bbc_results(bbc_page([BBC_EVENT, dict(BBC_EVENT, status="PreEvent")]), "https://www.bbc.co.uk/sport")
        self.assertEqual(len(rows), 1)
        item = rows[0]
        self.assertEqual((item["opponent"], item["homeAway"], item["arsenalScore"], item["opponentScore"]), ("Liverpool", "away", 2, 1))
        self.assertEqual([(r["name"], r["minute"]) for r in item["scorers"]], [("M. Salah", "40'"), ("B. Saka", "12'"), ("B. Saka", "77'")])
        self.assertTrue(item["scorers"][0]["penalty"])

    def test_bbc_scorers_must_match_date_opponent_and_score(self) -> None:
        bbc = enrich_arsenal.parse_bbc_results(bbc_page([BBC_EVENT]), "https://www.bbc.co.uk/sport")
        result = {"date": "2026-11-01T16:30:00+00:00", "opponent": "Liverpool FC", "arsenalScore": 2, "opponentScore": 1}
        self.assertIsNotNone(enrich_arsenal.bbc_scorers_for(result, bbc))
        self.assertIsNone(enrich_arsenal.bbc_scorers_for(dict(result, arsenalScore=3), bbc))
        self.assertIsNone(enrich_arsenal.bbc_scorers_for(dict(result, opponent="Chelsea"), bbc))
        self.assertIsNone(enrich_arsenal.bbc_scorers_for(dict(result, date="2026-11-02T16:30:00+00:00"), bbc))

    def test_snapshot_fills_scorers_from_bbc_and_stadium_from_prior_fixture(self) -> None:
        sky_completed = {
            "date": "2026-11-01T16:30:00+00:00", "dateLabel": "Sun 1 Nov", "kickoff": "4:30pm",
            "opponent": "Liverpool", "competition": "Premier League", "homeAway": "away",
            "completed": True, "arsenalScore": 2, "opponentScore": 1, "result": "2–1",
            "source": "Sky Sports", "url": "https://www.skysports.com/football/liverpool-vs-arsenal/1",
        }
        existing = {"nextFixture": {"date": "2026-11-01T16:30:00+00:00", "opponent": "Liverpool", "stadium": "Anfield"}}
        bbc = enrich_arsenal.parse_bbc_results(bbc_page([BBC_EVENT]), "https://www.bbc.co.uk/sport")
        with patch.object(enrich_arsenal, "espn_snapshot", return_value=([], 1, 20, 10)), \
             patch.object(enrich_arsenal, "all_sky_matches", return_value=[sky_completed]), \
             patch.object(enrich_arsenal, "all_bbc_matches", return_value=[]), \
             patch.object(enrich_arsenal, "bbc_results", return_value=bbc), \
             patch.object(enrich_arsenal, "official_pl_next_fixture", return_value=None), \
             patch.object(enrich_arsenal, "NOW", enrich_arsenal.NOW.replace(year=2026, month=11, day=2, hour=5, minute=0)):
            last = enrich_arsenal.snapshot([], existing_arsenal=existing)["lastResult"]
        self.assertEqual(last["stadium"], "Anfield")
        self.assertEqual(len(last["scorers"]), 3)
        final = finalize_arsenal.with_factual_summary(last)
        self.assertEqual(final["summary"], "B. Saka scored as Arsenal beat Liverpool 2–1 at Anfield in the Premier League.")


class NextFixtureAfterResultTests(unittest.TestCase):
    def test_played_match_is_not_kept_as_next_fixture(self) -> None:
        sky_completed = {
            "date": "2026-11-01T16:30:00+00:00", "dateLabel": "Sun 1 Nov", "kickoff": "4:30pm",
            "opponent": "Liverpool", "competition": "Premier League", "homeAway": "away",
            "completed": True, "arsenalScore": 1, "opponentScore": 0, "result": "1–0",
            "source": "Sky Sports", "url": "https://www.skysports.com/football/liverpool-vs-arsenal/1",
            "scorers": [{"name": "K. Havertz", "team": "Arsenal", "minute": "16'"}], "scorersLabel": "K. Havertz 16'",
        }
        upcoming = {
            "date": "2026-11-04T20:00:00+00:00", "dateLabel": "Wed 4 Nov", "kickoff": "8pm",
            "opponent": "Inter Milan", "competition": "UEFA Champions League", "homeAway": "home",
            "completed": False, "source": "Sky Sports", "url": "https://www.skysports.com/x",
        }
        existing = {"nextFixture": {"date": "2026-11-01T16:30:00+00:00", "opponent": "Liverpool",
                                    "completed": False, "stadium": "Anfield"}}
        with patch.object(enrich_arsenal, "espn_snapshot", return_value=([], 1, 20, 10)), \
             patch.object(enrich_arsenal, "all_sky_matches", return_value=[sky_completed, upcoming]), \
             patch.object(enrich_arsenal, "all_bbc_matches", return_value=[]), \
             patch.object(enrich_arsenal, "bbc_results", return_value=[]), \
             patch.object(enrich_arsenal, "official_pl_next_fixture", return_value=None), \
             patch.object(enrich_arsenal, "NOW", enrich_arsenal.NOW.replace(year=2026, month=11, day=1, hour=18, minute=50)):
            result = enrich_arsenal.snapshot([], existing_arsenal=existing)
        self.assertEqual(result["lastResult"]["opponent"], "Liverpool")
        self.assertEqual(result["nextFixture"]["opponent"], "Inter Milan")
        import json as _json
        _json.dumps(result)  # the snapshot must stay serialisable
        self.assertEqual(result["played"], 10)


class BbcResultsFetchTests(unittest.TestCase):
    def test_results_filter_is_requested_and_duplicates_merged(self) -> None:
        requested = []
        page = bbc_page([BBC_EVENT]).encode()

        class Response:
            content = page
            url = "https://www.bbc.co.uk/sport/x"

            def raise_for_status(self) -> None:
                pass

        def fake_get(url, **kwargs):
            requested.append(url)
            return Response()

        with patch.object(enrich_arsenal.requests, "get", side_effect=fake_get), \
             patch.object(enrich_arsenal, "NOW", enrich_arsenal.NOW.replace(year=2026, month=11, day=5, hour=5, minute=0)):
            rows = enrich_arsenal.bbc_results()
        self.assertIn(enrich_arsenal.BBC_FIXTURES_URL + "/2026-11?filter=results", requested)
        self.assertIn(enrich_arsenal.BBC_FIXTURES_URL + "/2026-10?filter=results", requested)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
