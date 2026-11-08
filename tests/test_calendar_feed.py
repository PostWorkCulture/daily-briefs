"""Calendar: recurring events, edited instances, several calendars, local secrets."""
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from datetime import datetime
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


refresh = load_script("refresh")
NOW = datetime(2026, 11, 8, 5, 0, tzinfo=TZ)

PRIMARY = b"""BEGIN:VCALENDAR
VERSION:2.0
X-WR-TIMEZONE:Europe/London
BEGIN:VEVENT
UID:footy@google.com
DTSTART;VALUE=DATE:20261012
DTEND;VALUE=DATE:20261013
RRULE:FREQ=WEEKLY;UNTIL=20261214;BYDAY=MO
EXDATE;VALUE=DATE:20261123
SUMMARY:Footy - PU 4.15pm (main playground)
END:VEVENT
BEGIN:VEVENT
UID:choir@google.com
DTSTART;VALUE=DATE:20260910
DTEND;VALUE=DATE:20260911
RRULE:FREQ=WEEKLY;BYDAY=TH
SUMMARY:Choir - PU 4pm (reception)
END:VEVENT
BEGIN:VEVENT
UID:choir@google.com
RECURRENCE-ID;VALUE=DATE:20261126
DTSTART;VALUE=DATE:20261126
DTEND;VALUE=DATE:20261127
STATUS:CANCELLED
SUMMARY:Choir - PU 4pm (reception)
END:VEVENT
BEGIN:VEVENT
UID:parents@google.com
DTSTART:20261119T161000Z
DTEND:20261119T163000Z
SUMMARY:Parents Evening
END:VEVENT
BEGIN:VEVENT
UID:old@google.com
DTSTART;VALUE=DATE:20261001
DTEND;VALUE=DATE:20261002
SUMMARY:Already over
END:VEVENT
END:VCALENDAR
"""

KIDS = b"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:kids@google.com
DTSTART;TZID=Europe/London:20260725T100000
DTEND;TZID=Europe/London:20260726T160000
RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=SA
SUMMARY:Pete Kids
END:VEVENT
BEGIN:VEVENT
UID:kids@google.com
RECURRENCE-ID:20261128T100000Z
DTSTART;TZID=Europe/London:20261121T100000
DTEND;TZID=Europe/London:20261122T160000
SUMMARY:Pete Kids
END:VEVENT
END:VCALENDAR
"""


class FakeResponse:
    def __init__(self, content: bytes, status: int = 200):
        self.content, self.status = content, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


def fake_get(feeds: dict[str, bytes | None]):
    def get(url, **_kwargs):
        body = feeds[url]
        return FakeResponse(b"", 503) if body is None else FakeResponse(body)
    return get


class CalendarFeedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        (self.data / "calendar-colors.json").write_text(json.dumps({"eventPalette": {"8": "#e1e1e1"}, "events": {}, "keywords": {"kids": "8"}}))
        patches = [
            patch.object(refresh, "NOW", NOW),
            patch.object(refresh, "DATA", self.data),
            patch.object(refresh, "warn", lambda *a: None),
            patch.dict(refresh.CARRIED_SECTIONS, {}, clear=True),
            patch.dict(os.environ, {"GOOGLE_CALENDAR_COLORS_URL": ""}),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        for key in [k for k in os.environ if k.startswith("GOOGLE_CALENDAR_ICS_URL")]:
            self.addCleanup(os.environ.__setitem__, key, os.environ.pop(key))
        self.addCleanup(self.tmp.cleanup)

    def run_feeds(self, feeds):
        os.environ["GOOGLE_CALENDAR_ICS_URL"] = " ".join(feeds)
        self.addCleanup(os.environ.pop, "GOOGLE_CALENDAR_ICS_URL", None)
        with patch.object(refresh.requests, "get", fake_get(feeds)):
            return refresh.calendar_events()

    def titles_on(self, events, day):
        return sorted(e["title"] for e in events if e["date"] == day)

    def test_weekly_series_started_before_today_is_expanded(self):
        events = self.run_feeds({"https://p": PRIMARY})
        footy = [e["date"] for e in events if e["title"].startswith("Footy")]
        self.assertEqual(footy, ["2026-11-09", "2026-11-16", "2026-11-30", "2026-12-07", "2026-12-14"])

    def test_cancelled_instance_and_exdate_are_skipped(self):
        events = self.run_feeds({"https://p": PRIMARY})
        choir = [e["date"] for e in events if e["title"].startswith("Choir")]
        self.assertIn("2026-11-12", choir)
        self.assertNotIn("2026-11-26", choir)
        self.assertNotIn("2026-11-23", [e["date"] for e in events if e["title"].startswith("Footy")])

    def test_single_timed_event_and_past_event(self):
        events = self.run_feeds({"https://p": PRIMARY})
        parents = [e for e in events if e["title"] == "Parents Evening"]
        self.assertEqual(len(parents), 1)
        self.assertEqual(parents[0]["time"], "4:10pm")
        self.assertFalse(any(e["title"] == "Already over" for e in events))

    def test_second_calendar_with_moved_instance(self):
        events = self.run_feeds({"https://p": PRIMARY, "https://k": KIDS})
        kids = [(e["date"], e["time"]) for e in events if e["title"] == "Pete Kids"]
        # Fortnightly from 25 Jul lands on 14 Nov, 28 Nov (moved to 21 Nov), 12 Dec, 26 Dec.
        self.assertEqual([d for d, _ in kids], ["2026-11-14", "2026-11-21", "2026-12-12", "2026-12-26"])
        self.assertTrue(all(t == "10am" for _, t in kids))  # stays 10am local after the clock change
        self.assertEqual({e["color"] for e in events if e["title"] == "Pete Kids"}, {"#e1e1e1"})

    def test_one_dead_calendar_keeps_its_previous_events(self):
        first = self.run_feeds({"https://p": PRIMARY, "https://k": KIDS})
        (self.data / "pete.json").write_text(json.dumps({"calendar": first}))
        events = self.run_feeds({"https://p": PRIMARY, "https://k": None})
        self.assertEqual(len([e for e in events if e["title"] == "Pete Kids"]), 4)
        self.assertIn("Calendar", refresh.CARRIED_SECTIONS)

    def test_no_url_keeps_previous_calendar_and_flags_it(self):
        (self.data / "pete.json").write_text(json.dumps({"calendar": [{"title": "X", "date": "2026-11-20", "start": "2026-11-20T00:00:00+00:00"}]}))
        self.assertEqual(len(refresh.calendar_events()), 1)
        self.assertIn("no GOOGLE_CALENDAR_ICS_URL", refresh.CARRIED_SECTIONS["Calendar"])

    def test_local_env_file_fills_missing_settings_only(self):
        env = self.data / ".env.local"
        env.write_text('# comment\nGOOGLE_CALENDAR_ICS_URL="https://a https://b"\nOTHER_SETTING=keep-env\n', encoding="utf-8")
        with patch.dict(os.environ, {"OTHER_SETTING": "from-env"}):
            os.environ.pop("GOOGLE_CALENDAR_ICS_URL", None)
            refresh.load_local_env(env)
            self.assertEqual(refresh.calendar_feed_urls(), ["https://a", "https://b"])
            self.assertEqual(os.environ["OTHER_SETTING"], "from-env")
            os.environ.pop("GOOGLE_CALENDAR_ICS_URL", None)


if __name__ == "__main__":
    unittest.main()
