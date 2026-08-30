from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "finalize_arsenal", ROOT / "scripts" / "finalize_arsenal.py"
)
finalize_arsenal = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(finalize_arsenal)


def news_item(title: str, published_at: str) -> dict:
    return {
        "title": title,
        "summary": "",
        "source": "Arsenal.com",
        "publishedAt": published_at,
        "url": "https://www.arsenal.com/news",
    }


class FirstTeamResultTests(unittest.TestCase):
    def test_youth_results_are_rejected(self) -> None:
        for title in (
            "U21 report: Arsenal 1-1 Crystal Palace",
            "U18s report: Arsenal 1-3 Ipswich Town",
            "Academy highlights: Arsenal 2-0 Chelsea",
            "Women’s report: Arsenal 3-1 Brighton",
        ):
            with self.subTest(title=title):
                self.assertIsNone(
                    finalize_arsenal.parse_news_result(
                        news_item(title, "2026-08-22T15:00:00+01:00")
                    )
                )


    def test_verified_latest_result_has_all_six_requested_fields(self) -> None:
        result = finalize_arsenal.verified_coventry_result()
        for key in ("result", "scorersLabel", "competition", "summary", "kickoff", "stadium"):
            with self.subTest(key=key):
                self.assertTrue(str(result.get(key) or "").strip())
        self.assertEqual(len(result["scorers"]), 3)

    def test_incomplete_new_result_fails_closed(self) -> None:
        payload = {
            "sections": {"Arsenal news": []},
            "arsenal": {
                "lastResult": {
                    "date": "2026-08-29T15:00:00+01:00",
                    "dateLabel": "Sat 29 Aug",
                    "opponent": "Incomplete FC",
                    "completed": True,
                    "arsenalScore": 1,
                    "opponentScore": 0,
                    "result": "1–0",
                    "source": "ESPN",
                },
                "news": [],
            },
        }
        with self.assertRaisesRegex(RuntimeError, "lastResult is incomplete"):
            finalize_arsenal.apply_last_result_fallback(payload)

    def test_first_team_result_wins_over_newer_youth_report(self) -> None:
        payload = {
            "sections": {
                "Arsenal news": [
                    news_item("U21 report: Arsenal 1-1 Crystal Palace", "2026-08-22T15:00:00+01:00"),
                    news_item("Report: Arsenal 3-0 Coventry City", "2026-08-21T22:03:53+01:00"),
                ]
            },
            "arsenal": {"news": []},
        }
        result = finalize_arsenal.newest_news_result(payload)
        self.assertIsNotNone(result)
        self.assertEqual(result["opponent"], "Coventry City")
        self.assertEqual(result["result"], "3–0")


if __name__ == "__main__":
    unittest.main()
