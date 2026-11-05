"""One failing component must not stop the brief: carry-forward orchestration."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
TZ = ZoneInfo("Europe/London")


def load_script(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


run_refresh = load_script("run_refresh")
refresh = load_script("refresh")

NOW = datetime(2026, 11, 5, 5, 0, tzinfo=TZ)


def previous_edition(tmp: Path) -> run_refresh.Previous:
    fixture_date = (NOW + timedelta(days=3)).isoformat()
    arsenal = {
        "lastResult": {
            "date": "2026-11-04T20:00:00+00:00", "dateLabel": "Wed 4 Nov", "opponent": "Slavia Prague",
            "result": "2–1", "scorersLabel": "Madueke 9', Gyokeres 38'", "competition": "Champions League",
            "summary": "Arsenal beat Slavia Prague 2–1.", "kickoff": "8pm", "stadium": "Fortuna Arena",
            "scorers": [{"name": "Madueke"}, {"name": "Gyokeres"}],
        },
        "nextFixture": {
            "date": fixture_date, "opponent": "Sunderland", "stadium": "Emirates Stadium", "kickoff": "4:30pm",
            "competition": "Premier League", "tvChannel": "Sky Sports", "source": "Sky Sports",
            "previousMeeting": {"score": "2–0"},
        },
        "leaguePosition": 1, "points": 25, "played": 10,
        "news": [{"title": "Old Arsenal story", "url": "https://example.com/arsenal-old", "contentType": "article"}],
        "transfers": [], "transferRumours": [],
    }
    sections = {
        "Local news": [{"title": f"Local {i}", "url": f"https://example.com/local-{i}", "publishedAt": f"2026-11-0{4 - i % 3}T0{i}:00:00+00:00", "contentType": "article"} for i in range(12)],
        "UK news": [{"title": f"UK {i}", "url": f"https://example.com/uk-{i}", "contentType": "article"} for i in range(11)],
        "Arsenal news": list(arsenal["news"]),
    }
    weather = {"source": "Met Office", "temp": "9°", "daily": [{"date": "2026-11-05"}],
               "yesterdayExtremes": {"source": "Met Office", "hot": {"town": "Topcliffe"}}}
    watch = [{"title": f"Pick {i}", "generatedDate": "2026-11-04"} for i in range(5)]
    for name in ("pete", "sofia"):
        payload = {"worldFact": {"date": "2026-11-04"}, "weather": weather, "watch": watch, "watchAlternatives": [],
                   "sections": sections, "arsenal": arsenal if name == "pete" else {}}
        (tmp / f"{name}.json").write_text(json.dumps(payload), encoding="utf-8")
    (tmp / "story-images.json").write_text(json.dumps({
        "https://example.com/local-1": {"src": "https://img.example.com/a.jpg", "provenance": "publisher", "matchedPageTitle": "Local 1"},
        "https://example.com/gone": {"src": "https://img.example.com/b.jpg", "provenance": "publisher", "matchedPageTitle": "Gone"},
    }), encoding="utf-8")
    (tmp / "tv-picks-history.json").write_text(json.dumps({"days": [{"date": "2026-11-04", "titles": [p["title"] for p in watch]}]}), encoding="utf-8")
    return run_refresh.Previous(tmp)


class CarryForwardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.previous = previous_edition(self.tmp)
        self.status = run_refresh.Status("2026-11-05")
        self.data_patch = patch.object(run_refresh, "DATA", self.tmp)
        self.data_patch.start()

    def tearDown(self) -> None:
        self.data_patch.stop()

    def fresh_profiles(self) -> dict:
        return {
            "pete": {"worldFact": {"date": "2026-11-05"}, "weather": {"temp": "—", "daily": []}, "watch": [],
                     "sections": {"Local news": [], "UK news": [], "Arsenal news": []},
                     "arsenal": {"lastResult": {"date": "2026-11-04T20:00:00+00:00", "opponent": "Slavia Prague", "result": "2–1"},
                                 "nextFixture": None, "leaguePosition": None, "news": []}},
            "sofia": {"worldFact": {"date": "2026-11-05"}, "weather": {"temp": "—", "daily": []}, "watch": [], "sections": {}},
        }

    def test_incomplete_arsenal_block_is_carried_from_last_edition(self) -> None:
        profiles = self.fresh_profiles()
        run_refresh.check_arsenal(profiles, self.previous, self.status, NOW)
        arsenal = profiles["pete"]["arsenal"]
        self.assertEqual(arsenal["lastResult"]["stadium"], "Fortuna Arena")
        self.assertEqual(arsenal["nextFixture"]["opponent"], "Sunderland")
        self.assertEqual(arsenal["leaguePosition"], 1)
        self.assertEqual(set(self.status.carried), {"arsenal.lastResult", "arsenal.nextFixture", "arsenal.leaguePosition"})

    def test_complete_fresh_arsenal_block_is_left_alone(self) -> None:
        profiles = self.fresh_profiles()
        profiles["pete"]["arsenal"] = json.loads(json.dumps(self.previous.arsenal()))
        profiles["pete"]["arsenal"]["lastResult"]["opponent"] = "Sunderland"
        run_refresh.check_arsenal(profiles, self.previous, self.status, NOW)
        self.assertEqual(profiles["pete"]["arsenal"]["lastResult"]["opponent"], "Sunderland")
        self.assertEqual(self.status.carried, {})

    def test_expired_previous_fixture_is_not_carried(self) -> None:
        profiles = self.fresh_profiles()
        profiles["pete"]["arsenal"]["nextFixture"] = {"date": (NOW + timedelta(days=2)).isoformat(), "opponent": "Chelsea"}
        self.previous.profiles["pete"]["arsenal"]["nextFixture"]["date"] = (NOW - timedelta(days=2)).isoformat()
        run_refresh.check_arsenal(profiles, self.previous, self.status, NOW)
        self.assertEqual(profiles["pete"]["arsenal"]["nextFixture"]["opponent"], "Chelsea")
        self.assertIn("arsenal.nextFixture", self.status.carried)

    def test_tv_picks_carried_with_their_history(self) -> None:
        profiles = self.fresh_profiles()
        run_refresh.check_watch(profiles, self.previous, self.status)
        self.assertEqual(len(profiles["pete"]["watch"]), 5)
        self.assertEqual(len(profiles["sofia"]["watch"]), 5)
        self.assertIn("watch", self.status.carried)
        history = json.loads((self.tmp / "tv-picks-history.json").read_text(encoding="utf-8"))
        self.assertEqual(history["days"][-1]["date"], "2026-11-04")

    def test_weather_carried_when_met_office_extremes_fail(self) -> None:
        profiles = self.fresh_profiles()
        profiles["pete"]["weather"] = {"source": "Met Office", "temp": "8°", "daily": [1],
                                      "yesterdayExtremes": {"source": "Met Office", "error": "table missing"}}
        with patch.object(run_refresh, "run_script", return_value=(False, "offline")):
            run_refresh.check_weather(profiles, self.previous, self.status)
        self.assertEqual(profiles["pete"]["weather"]["yesterdayExtremes"]["hot"]["town"], "Topcliffe")
        self.assertEqual(profiles["pete"]["weather"]["temp"], "9°")
        self.assertIn("weather", self.status.carried)

    def test_story_images_pruned_to_current_articles(self) -> None:
        profiles = self.fresh_profiles()
        profiles["pete"]["sections"]["Local news"] = [{"url": "https://example.com/local-1", "title": "Local 1"}]
        run_refresh.restore_story_images(profiles, self.previous)
        rules = json.loads((self.tmp / "story-images.json").read_text(encoding="utf-8"))
        self.assertEqual(list(rules), ["https://example.com/local-1"])

    def test_validator_messages_map_to_components(self) -> None:
        cases = {
            "pete: stale TV Picks": "watch",
            "pete: hot extreme missing town": "weather",
            "Arsenal last result missing stadium": "arsenal.lastResult",
            "Arsenal next fixture is already stale": "arsenal.nextFixture",
            "Arsenal current Premier League position is unavailable": "arsenal.leaguePosition",
            "Reporter watch is not newest first": "arsenal.transferRumours",
            "Arsenal trusted transfers are not newest first": "arsenal.transfers",
            "pete: section content bleed: Local news item 3 has contentType job": "sections.Local news",
            "sofia: fewer than 10 UK News items": "sections.UK news",
            "image rule is not tied to a current article: https://x": "storyImages",
            "Fact history is empty": None,
        }
        for message, component in cases.items():
            self.assertEqual(run_refresh.component_for_validation_error(message), component, message)

    def test_restore_section_covers_both_profiles(self) -> None:
        profiles = self.fresh_profiles()
        self.assertTrue(run_refresh.restore_component("sections.Local news", profiles, self.previous))
        self.assertEqual(len(profiles["pete"]["sections"]["Local news"]), 12)
        self.assertEqual(len(profiles["sofia"]["sections"]["Local news"]), 12)
        self.assertTrue(run_refresh.restore_component("sections.Arsenal news", profiles, self.previous))
        self.assertEqual(profiles["pete"]["arsenal"]["news"][0]["title"], "Old Arsenal story")
        self.assertFalse(run_refresh.restore_component("facts", profiles, self.previous))

    def test_validation_loop_repairs_then_passes(self) -> None:
        profiles = self.fresh_profiles()
        answers = iter(["pete: stale TV Picks", None])
        with patch.object(run_refresh, "validation_error", side_effect=lambda: next(answers)):
            run_refresh.validate_with_repairs(profiles, self.previous, self.status)
        self.assertIn("watch", self.status.carried)
        self.assertEqual(len(profiles["pete"]["watch"]), 5)
        status = json.loads((self.tmp / "refresh-status.json").read_text(encoding="utf-8"))
        self.assertTrue(status["degraded"])
        self.assertEqual(profiles["pete"]["refreshStatus"]["carriedForward"], status["carriedForward"])

    def test_validation_loop_stops_on_unrepairable_rule(self) -> None:
        profiles = self.fresh_profiles()
        with patch.object(run_refresh, "validation_error", return_value="Fact history is empty"):
            with self.assertRaises(SystemExit):
                run_refresh.validate_with_repairs(profiles, self.previous, self.status)


class ResilientSectionTests(unittest.TestCase):
    def setUp(self) -> None:
        refresh.CARRIED_SECTIONS.clear()
        self.previous = [
            {"title": f"Kept {i}", "url": f"https://example.com/{i}", "publishedAt": f"2026-11-0{1 + i % 4}T08:00:00+00:00", "contentType": "article"}
            for i in range(12)
        ]

    def test_dead_feed_is_topped_up_from_previous_edition(self) -> None:
        def build():
            raise ConnectionError("feed down")
        with patch.object(refresh, "previous_section", return_value=self.previous), \
                patch.object(refresh, "is_paywalled", return_value=False), \
                patch.dict(refresh.SECTION_SCOPE_CHECKS, {"UK news": lambda item: True}):
            items = refresh.resilient_section("UK news", build)
        self.assertEqual(len(items), 12)
        self.assertIn("UK news", refresh.CARRIED_SECTIONS)
        self.assertIn("feed down", refresh.CARRIED_SECTIONS["UK news"])

    def test_short_feed_keeps_fresh_items_first_and_dedupes(self) -> None:
        fresh = [{"title": "Kept 0", "url": "https://example.com/0", "publishedAt": "2026-11-05T08:00:00+00:00", "contentType": "article"},
                 {"title": "Brand new", "url": "https://example.com/new", "publishedAt": "2026-11-05T09:00:00+00:00", "contentType": "article"}]
        with patch.object(refresh, "previous_section", return_value=self.previous), \
                patch.object(refresh, "is_paywalled", return_value=False), \
                patch.dict(refresh.SECTION_SCOPE_CHECKS, {"Local news": lambda item: True}):
            items = refresh.resilient_section("Local news", lambda: fresh)
        urls = [item["url"] for item in items]
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(len(items), 13)
        dates = [item["publishedAt"] for item in items]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_full_feed_is_untouched(self) -> None:
        fresh = [{"title": f"Fresh {i}", "url": f"https://example.com/f{i}", "contentType": "article"} for i in range(10)]
        with patch.object(refresh, "previous_section", side_effect=AssertionError("must not read previous edition")):
            items = refresh.resilient_section("UK news", lambda: fresh)
        self.assertEqual(items, fresh)
        self.assertEqual(refresh.CARRIED_SECTIONS, {})

    def test_carried_items_still_obey_scope_and_paywall(self) -> None:
        with patch.object(refresh, "previous_section", return_value=self.previous), \
                patch.object(refresh, "is_paywalled", side_effect=lambda item: item["title"] == "Kept 1"), \
                patch.dict(refresh.SECTION_SCOPE_CHECKS, {"UK news": lambda item: item["title"] != "Kept 2"}):
            items = refresh.resilient_section("UK news", lambda: [])
        titles = {item["title"] for item in items}
        self.assertNotIn("Kept 1", titles)
        self.assertNotIn("Kept 2", titles)
        self.assertEqual(len(items), 10)


if __name__ == "__main__":
    unittest.main()
