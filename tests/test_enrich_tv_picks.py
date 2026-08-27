from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import enrich_tv_picks as tv


def episode(
    title: str,
    *,
    episode_id: int,
    airdate: str = "2026-08-27",
    show_type: str = "Documentary",
    genres: list[str] | None = None,
    source: str = "BBC One",
    number: int = 1,
) -> dict:
    return {
        "id": episode_id,
        "airdate": airdate,
        "airtime": "21:00",
        "number": number,
        "summary": f"A new investigation in {title}.",
        "show": {
            "id": episode_id + 1000,
            "name": title,
            "type": show_type,
            "language": "English",
            "genres": genres or ["Crime"],
            "weight": 80,
            "officialSite": f"https://example.com/{episode_id}",
            "network": {"name": source, "country": {"code": "GB"}},
            "webChannel": None,
            "image": {
                "original": f"https://static.tvmaze.com/uploads/images/original_untouched/1/{episode_id}.jpg"
            },
        },
    }


class TvPickTests(unittest.TestCase):
    def test_candidate_contains_current_schedule_and_exact_artwork(self) -> None:
        item = tv.candidate(episode("The New Murder File", episode_id=1), date(2026, 8, 27))
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item["contentType"], "tv-pick")
        self.assertEqual(item["generatedDate"], "2026-08-27")
        self.assertEqual(item["badge"], "True crime")
        self.assertTrue(item["artwork"].startswith("https://static.tvmaze.com/uploads/images/original_untouched/"))

    def test_candidate_rejects_generic_artwork_and_daily_soap(self) -> None:
        generic = episode("A New Documentary", episode_id=2)
        generic["show"]["image"]["original"] = "https://example.com/placeholder.jpg"
        self.assertIsNone(tv.candidate(generic, date(2026, 8, 27)))
        self.assertIsNone(tv.candidate(episode("EastEnders", episode_id=3), date(2026, 8, 27)))

    def test_new_episode_is_eligible_across_previous_and_next_week(self) -> None:
        last_week = tv.candidate(
            episode("Last Week Series", episode_id=30, airdate="2026-08-20", number=6),
            date(2026, 8, 27),
        )
        next_week = tv.candidate(
            episode("Next Week Series", episode_id=31, airdate="2026-09-03", number=4),
            date(2026, 8, 27),
        )
        too_old = tv.candidate(
            episode("Old Series", episode_id=32, airdate="2026-08-19", number=8),
            date(2026, 8, 27),
        )
        self.assertIsNotNone(last_week)
        self.assertIsNotNone(next_week)
        self.assertIsNone(too_old)
        assert last_week is not None and next_week is not None
        self.assertIn("Available since", last_week["meta"])
        self.assertIn("Thu 3 Sep", next_week["meta"])

    def test_selection_rolls_forward_before_reusing_recent_titles(self) -> None:
        candidates = [tv.candidate(episode(f"Fresh Programme {i}", episode_id=i), date(2026, 8, 27)) for i in range(1, 7)]
        old = tv.candidate(episode("Yesterday's Pick", episode_id=20), date(2026, 8, 27))
        items = [item for item in [old, *candidates] if item]
        history = [{"date": "2026-08-26", "titles": ["Yesterday's Pick"]}]
        selected = tv.select_picks(items, date(2026, 8, 27), history)
        self.assertEqual(len(selected), 5)
        self.assertNotIn("Yesterday's Pick", {item["title"] for item in selected})

    def test_selection_fails_instead_of_publishing_too_few_picks(self) -> None:
        items = [tv.candidate(episode(f"Programme {i}", episode_id=i), date(2026, 8, 27)) for i in range(1, 4)]
        with self.assertRaisesRegex(RuntimeError, "Only 3 current TV Picks"):
            tv.select_picks([item for item in items if item], date(2026, 8, 27), [])


if __name__ == "__main__":
    unittest.main()
