from __future__ import annotations

import html as html_lib
import importlib.util
import json
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
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
    def test_transient_standings_outage_keeps_last_verified_position(self) -> None:
        enriched = {"leaguePosition": None}
        existing = {"leaguePosition": 2}

        result = enrich_arsenal.retain_verified_league_position(enriched, existing)

        self.assertEqual(result["leaguePosition"], 2)

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

    def test_current_sky_embedded_state_is_parsed_without_localised_copy(self) -> None:
        state = {
            "start": {"date": "Sunday 6th September", "time": "16:30", "time12hr": "4.30pm"},
            "competition": {"name": {"full": "Premier League"}},
            "teams": {
                "home": {"name": {"full": "Arsenal"}, "score": {"current": 0}},
                "away": {"name": {"full": "Chelsea"}, "score": {"current": 0}},
            },
            "matchState": "pre", "isFixture": True, "isResult": False,
            "matchURL": "/football/arsenal-vs-chelsea/7193893630913215232",
            "channel": {"description": "Sky Sports Premier League"},
        }
        women = dict(state)
        women["teams"] = {
            "home": {"name": {"full": "Arsenal Women"}, "score": {"current": 0}},
            "away": {"name": {"full": "Chelsea Women"}, "score": {"current": 0}},
        }
        html = "".join(
            f'<div data-component-name="ui-sport-match-score" data-state="{html_lib.escape(json.dumps(item), quote=True)}"></div>'
            for item in (state, women)
        )

        fixtures = enrich_arsenal.parse_sky_state_matches(
            html,
            "https://www.skysports.com/arsenal-scores-fixtures/2026-09-01",
            datetime(2026, 9, 1, tzinfo=ZoneInfo("Europe/London")),
        )

        self.assertEqual(len(fixtures), 1)
        self.assertEqual(fixtures[0]["date"], "2026-09-06T16:30:00+01:00")
        self.assertEqual(fixtures[0]["opponent"], "Chelsea")
        self.assertEqual(fixtures[0]["competition"], "Premier League")
        self.assertEqual(fixtures[0]["tvChannel"], "Sky Sports Premier League")
        self.assertEqual(
            fixtures[0]["url"],
            "https://www.skysports.com/football/arsenal-vs-chelsea/7193893630913215232",
        )

    def test_current_bbc_embedded_state_is_parsed_as_independent_fallback(self) -> None:
        event = {
            "home": {"fullName": "Napoli"},
            "away": {"fullName": "Arsenal"},
            "startDateTime": "2026-09-09T19:00:00Z",
            "date": {"iso": "2026-09-09T19:00:00Z"},
            "periodLabel": {"value": "Scheduled"},
            "status": "PreEvent",
            "tournament": {
                "name": "UEFA Champions League",
                "disambiguatedName": "UEFA Champions League",
            },
            "onwardJourneyLink": "/sport/football/live/c6z9zywpj3l5t",
        }
        women = dict(event)
        women["away"] = {"fullName": "Arsenal Women"}
        state = {
            "data": {
                "fixtures": {
                    "name": "sport-data-scores-fixtures",
                    "data": {
                        "eventGroups": [{
                            "secondaryGroups": [{"events": [event, women]}],
                        }],
                    },
                },
            },
        }
        html = (
            "<script>window.__INITIAL_DATA__="
            + json.dumps(json.dumps(state))
            + ";</script>"
        )

        fixtures = enrich_arsenal.parse_bbc_state_matches(
            html,
            "https://www.bbc.co.uk/sport/football/teams/arsenal/scores-fixtures",
        )

        self.assertEqual(len(fixtures), 1)
        self.assertEqual(fixtures[0]["date"], "2026-09-09T20:00:00+01:00")
        self.assertEqual(fixtures[0]["opponent"], "Napoli")
        self.assertEqual(fixtures[0]["competition"], "UEFA Champions League")
        self.assertEqual(fixtures[0]["source"], "BBC Sport")

    def test_nearest_sky_fixture_beats_later_official_fallback(self) -> None:
        chelsea = {
            "date": "2026-09-06T16:30:00+01:00", "opponent": "Chelsea",
            "competition": "Premier League", "completed": False,
        }
        leeds = {
            "date": "2026-10-10T12:30:00+01:00", "opponent": "Leeds United",
            "competition": "Premier League", "completed": False,
        }
        with (
            patch.object(enrich_arsenal, "NOW", datetime(2026, 9, 1, 9, 0, tzinfo=ZoneInfo("Europe/London"))),
            patch.object(enrich_arsenal, "espn_snapshot", return_value=([], 2, None, None)),
            patch.object(enrich_arsenal, "all_sky_matches", return_value=[chelsea]),
            patch.object(enrich_arsenal, "all_bbc_matches", return_value=[]),
            patch.object(enrich_arsenal, "official_pl_next_fixture", return_value=leeds),
        ):
            result = enrich_arsenal.snapshot([])

        self.assertEqual(result["nextFixture"]["opponent"], "Chelsea")
        self.assertEqual(result["nextFixture"]["date"], "2026-09-06T16:30:00+01:00")

    def test_still_upcoming_fixture_survives_a_transient_sky_failure(self) -> None:
        chelsea = {
            "date": "2026-09-06T16:30:00+01:00", "opponent": "Chelsea",
            "competition": "Premier League", "completed": False,
        }
        leeds = {
            "date": "2026-10-10T12:30:00+01:00", "opponent": "Leeds United",
            "competition": "Premier League", "completed": False,
        }
        with (
            patch.object(enrich_arsenal, "NOW", datetime(2026, 9, 4, 14, 0, tzinfo=ZoneInfo("Europe/London"))),
            patch.object(enrich_arsenal, "espn_snapshot", return_value=([], 2, None, None)),
            patch.object(enrich_arsenal, "all_sky_matches", return_value=[]),
            patch.object(enrich_arsenal, "all_bbc_matches", return_value=[]),
            patch.object(enrich_arsenal, "official_pl_next_fixture", return_value=leeds),
        ):
            result = enrich_arsenal.snapshot([], {"nextFixture": chelsea})

        self.assertEqual(result["nextFixture"]["opponent"], "Chelsea")
        self.assertEqual(result["nextFixture"]["date"], "2026-09-06T16:30:00+01:00")

    def test_bbc_fixture_prevents_jump_to_later_league_fallback(self) -> None:
        napoli = {
            "date": "2026-09-09T20:00:00+01:00",
            "opponent": "Napoli",
            "competition": "UEFA Champions League",
            "completed": False,
            "source": "BBC Sport",
        }
        leeds = {
            "date": "2026-10-10T12:30:00+01:00",
            "opponent": "Leeds United",
            "competition": "Premier League",
            "completed": False,
        }
        with (
            patch.object(enrich_arsenal, "NOW", datetime(2026, 9, 9, 6, 0, tzinfo=ZoneInfo("Europe/London"))),
            patch.object(enrich_arsenal, "espn_snapshot", return_value=([], 2, None, None)),
            patch.object(enrich_arsenal, "all_sky_matches", return_value=[]),
            patch.object(enrich_arsenal, "all_bbc_matches", return_value=[napoli]),
            patch.object(enrich_arsenal, "official_pl_next_fixture", return_value=leeds),
        ):
            result = enrich_arsenal.snapshot([])

        self.assertEqual(result["nextFixture"]["opponent"], "Napoli")
        self.assertEqual(result["nextFixture"]["source"], "BBC Sport")

    def test_expired_fixture_and_missing_sky_bbc_fail_closed(self) -> None:
        leeds = {
            "date": "2026-10-10T12:30:00+01:00",
            "opponent": "Leeds United",
            "competition": "Premier League",
            "completed": False,
        }
        with (
            patch.object(enrich_arsenal, "NOW", datetime(2026, 9, 9, 6, 0, tzinfo=ZoneInfo("Europe/London"))),
            patch.object(enrich_arsenal, "espn_snapshot", return_value=([], 2, None, None)),
            patch.object(enrich_arsenal, "all_sky_matches", return_value=[]),
            patch.object(enrich_arsenal, "all_bbc_matches", return_value=[]),
            patch.object(enrich_arsenal, "official_pl_next_fixture", return_value=leeds),
        ):
            result = enrich_arsenal.snapshot([])

        self.assertIsNone(result["nextFixture"])

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


    def test_completed_result_includes_all_required_match_details(self) -> None:
        event = {
            "id": "2645195",
            "date": "2026-08-21T19:00:00Z",
            "status": {"type": {"completed": True}},
            "links": [{"href": "https://example.com/report"}],
            "competitions": [{
                "venue": {"fullName": "Emirates Stadium"},
                "competitors": [
                    {"homeAway": "home", "score": {"value": 3}, "team": {"id": "359", "displayName": "Arsenal"}},
                    {"homeAway": "away", "score": {"value": 0}, "team": {"id": "388", "displayName": "Coventry City"}},
                ],
                "details": [
                    {"scoringPlay": True, "team": {"id": "359"}, "clock": {"displayValue": "15"}, "participants": [{"athlete": {"displayName": "Kai Havertz"}}]},
                    {"scoringPlay": True, "team": {"id": "359"}, "clock": {"displayValue": "23"}, "participants": [{"athlete": {"displayName": "Bukayo Saka"}}]},
                    {"scoringPlay": True, "team": {"id": "359"}, "clock": {"displayValue": "49"}, "participants": [{"athlete": {"displayName": "Martin Ødegaard"}}]},
                ],
            }],
        }

        result = enrich_arsenal.parse_fixture(event, "Premier League", "eng.1")

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["result"], "3–0")
        self.assertEqual(result["scorersLabel"], "Kai Havertz 15', Bukayo Saka 23', Martin Ødegaard 49'")
        self.assertEqual(result["competition"], "Premier League")
        self.assertIn("beat Coventry City 3–0", result["summary"])
        self.assertEqual(result["kickoff"], "8pm")
        self.assertEqual(result["stadium"], "Emirates Stadium")

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

    def test_verified_chelsea_details_are_complete(self) -> None:
        fixture = enrich_next_fixture.enrich_fixture(
            {
                "date": "2026-09-06T16:30:00+01:00",
                "dateLabel": "Sun 6 Sep",
                "kickoff": "4:30pm",
                "opponent": "Chelsea",
                "competition": "Premier League",
                "homeAway": "home",
                "tvChannel": "Sky Sports Premier League",
            }
        )

        self.assertEqual(fixture["stadium"], "Emirates Stadium")
        self.assertEqual(fixture["kickoff"], "4:30pm")
        self.assertEqual(fixture["tvChannel"], "Sky Sports Premier League")
        self.assertEqual(fixture["previousMeeting"]["score"], "Arsenal 2–1 Chelsea")

    def test_verified_napoli_details_are_complete(self) -> None:
        fixture = enrich_next_fixture.enrich_fixture({
            "date": "2026-09-09T20:00:00+01:00",
            "dateLabel": "Wed 9 Sep",
            "kickoff": "8pm",
            "opponent": "Napoli",
            "competition": "UEFA Champions League",
            "homeAway": "away",
            "source": "BBC Sport",
        })

        self.assertEqual(fixture["stadium"], "Stadio Diego Armando Maradona")
        self.assertEqual(fixture["kickoff"], "8:00pm")
        self.assertEqual(fixture["source"], "Sky Sports / Arsenal.com / BBC Sport")


        self.assertEqual(fixture["previousMeeting"]["score"], "Napoli 0–1 Arsenal")
        self.assertEqual(fixture["previousMeeting"]["date"], "18 Apr 2019")
        self.assertEqual(fixture["previousMeeting"]["competition"], "Europa League")

    def test_empty_verified_meeting_does_not_bypass_lookup(self) -> None:
        key = ("2026-09-09", "napoli")
        verified = {**enrich_next_fixture.VERIFIED_FIXTURES[key],
                    "previousMeeting": {"score": "No previous meeting found", "date": ""}}
        meeting = enrich_next_fixture.HISTORICAL_MEETINGS["napoli"]
        with patch.dict(enrich_next_fixture.VERIFIED_FIXTURES, {key: verified}), \
             patch.object(enrich_next_fixture, "latest_recent_meeting", return_value=meeting) as lookup:
            fixture = enrich_next_fixture.enrich_fixture({"date": "2026-09-09T20:00:00+01:00", "opponent": "Napoli"})
        lookup.assert_called_once_with("Napoli")
        self.assertEqual(fixture["previousMeeting"], meeting)


if __name__ == "__main__":
    unittest.main()
