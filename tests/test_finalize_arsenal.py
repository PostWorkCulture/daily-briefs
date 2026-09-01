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

    def test_match_report_prefix_is_not_part_of_opponent_name(self) -> None:
        result = finalize_arsenal.parse_news_result(
            news_item(
                "Match Report: Aston Villa 0-1 Arsenal",
                "2026-09-01T00:20:00+01:00",
            )
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["opponent"], "Aston Villa")
        self.assertEqual(result["result"], "1–0")

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


    def test_verified_villa_result_has_all_requested_fields(self) -> None:
        result = finalize_arsenal.verified_aston_villa_result()
        for key in ("result", "scorersLabel", "competition", "summary", "kickoff", "stadium"):
            with self.subTest(key=key):
                self.assertTrue(str(result.get(key) or "").strip())
        self.assertEqual(result["scorers"], [
            {"name": "Bukayo Saka", "team": "Arsenal", "minute": "59'"}
        ])

    def test_incomplete_new_result_fails_closed(self) -> None:
        payload = {
            "sections": {"Arsenal news": []},
            "arsenal": {
                "lastResult": {
                    "date": "2026-09-02T15:00:00+01:00",
                    "dateLabel": "Wed 2 Sep",
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

    def test_after_midnight_report_keeps_structured_match_details(self) -> None:
        structured = {
            "date": "2026-08-31T20:00:00+01:00",
            "dateLabel": "Mon 31 Aug",
            "kickoff": "8pm",
            "opponent": "Example United",
            "competition": "Premier League",
            "homeAway": "away",
            "completed": True,
            "arsenalScore": 2,
            "opponentScore": 1,
            "result": "2–1",
            "scorers": [
                {"name": "Player One", "team": "Arsenal", "minute": "24'"},
                {"name": "Player Two", "team": "Arsenal", "minute": "71'"},
            ],
            "scorersLabel": "Player One 24', Player Two 71'",
            "stadium": "Example Stadium",
            "summary": "Arsenal beat Example United 2–1 in the Premier League.",
            "source": "ESPN",
        }
        late_report = {
            "date": "2026-09-01T12:00:00+01:00",
            "opponent": "Example United",
            "arsenalScore": 2,
            "opponentScore": 1,
            "result": "2–1",
            "url": "https://www.arsenal.com/news/example-result",
            "source": "Arsenal.com",
        }

        result = finalize_arsenal.reconcile_news_result_with_structured(
            late_report, structured
        )

        self.assertEqual(result["date"], "2026-08-31T20:00:00+01:00")
        self.assertEqual(result["stadium"], "Example Stadium")
        self.assertEqual(len(result["scorers"]), 2)
        self.assertEqual(result["source"], "Arsenal.com")

if __name__ == "__main__":
    unittest.main()
