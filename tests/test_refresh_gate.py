from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from scripts.refresh_gate import should_run_refresh


LONDON = ZoneInfo("Europe/London")


class RefreshGateTests(unittest.TestCase):
    def root_with_dates(self, pete: str, sofia: str) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "data").mkdir()
        for profile, date in (("pete", pete), ("sofia", sofia)):
            (root / "data" / f"{profile}.json").write_text(
                json.dumps({"worldFact": {"date": date}}), encoding="utf-8"
            )
        return root

    def test_non_schedule_event_always_runs(self) -> None:
        root = self.root_with_dates("2026-08-29", "2026-08-29")
        should_run, _ = should_run_refresh(
            "workflow_dispatch", datetime(2026, 8, 29, 3, tzinfo=LONDON), root
        )
        self.assertTrue(should_run)

    def test_schedule_waits_until_six_in_london(self) -> None:
        root = self.root_with_dates("2026-08-28", "2026-08-28")
        should_run, reason = should_run_refresh(
            "schedule", datetime(2026, 8, 29, 5, 59, tzinfo=LONDON), root
        )
        self.assertFalse(should_run)
        self.assertIn("before 06:00", reason)

    def test_stale_schedule_runs_at_six(self) -> None:
        root = self.root_with_dates("2026-08-28", "2026-08-28")
        should_run, reason = should_run_refresh(
            "schedule", datetime(2026, 8, 29, 6, tzinfo=LONDON), root
        )
        self.assertTrue(should_run)
        self.assertIn("pete", reason)
        self.assertIn("sofia", reason)

    def test_retry_skips_after_today_is_published(self) -> None:
        root = self.root_with_dates("2026-08-29", "2026-08-29")
        should_run, reason = should_run_refresh(
            "schedule", datetime(2026, 8, 29, 6, 30, tzinfo=LONDON), root
        )
        self.assertFalse(should_run)
        self.assertIn("already published", reason)

    def test_retry_runs_when_one_profile_is_stale(self) -> None:
        root = self.root_with_dates("2026-08-29", "2026-08-28")
        should_run, reason = should_run_refresh(
            "schedule", datetime(2026, 8, 29, 7, 30, tzinfo=LONDON), root
        )
        self.assertTrue(should_run)
        self.assertNotIn("pete", reason)
        self.assertIn("sofia", reason)

    def test_workflow_has_dst_safe_six_am_recovery_window(self) -> None:
        workflow = (
            Path(__file__).resolve().parents[1]
            / ".github"
            / "workflows"
            / "morning-refresh.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("cron: '0,30 5-8 * * *'", workflow)
        self.assertIn("python scripts/refresh_gate.py", workflow)


if __name__ == "__main__":
    unittest.main()
