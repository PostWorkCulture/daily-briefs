from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_refresh():
    spec = importlib.util.spec_from_file_location("refresh_news_order", ROOT / "scripts" / "refresh.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


refresh = load_refresh()


class LocalNewsOrderTests(unittest.TestCase):
    def test_newest_articles_are_first_and_limit_is_applied(self) -> None:
        items = [
            {"title": "Old", "publishedAt": "2026-08-25T09:00:00+01:00"},
            {"title": "Undated", "publishedAt": ""},
            {"title": "Newest", "publishedAt": "2026-08-28T08:00:00+01:00"},
            {"title": "Middle", "publishedAt": "2026-08-27T12:00:00+01:00"},
        ]

        result = refresh.newest_news(items, 3)

        self.assertEqual([item["title"] for item in result], ["Newest", "Middle", "Old"])

    def test_scope_accepts_only_named_or_genuinely_nearby_places(self) -> None:
        accepted = (
            "Hurst Pool refurbishment update",
            "East Molesey residents back riverside plan",
            "Who runs Kingston upon Thames?",
            "Council regrets Hampton Wick parking error",
            "Hampton residents oppose high street closure",
            "Newts in danger at Teddington park pond",
            "Concours of Elegance Hampton Court returns",
            "Walton & Hersham FC fans stage bar boycott",
            "CCTV installed at Thames Ditton open space",
            "Plans revealed for homes beside Esher bypass",
            "New seating area proposed for Surbiton cafe",
            "Hinchley Wood school announces expansion",
            "River warning issued in Sunbury-on-Thames",
        )
        rejected = (
            "Zendaya celebrates her best year yet",
            "Elmbridge publishes borough-wide spending plan",
            "Surrey house prices ranked from highest to lowest",
            "Kingston, Jamaica prepares for tropical storm",
            "New student centre opens at Hampton University",
            "East Hampton mansion sells for record price",
            "Who should I draft: Omarion Hampton or Drake London?",
            "Walton County approves new highway",
            "Kingston upon Hull unveils waterfront plans",
        )

        for title in accepted:
            with self.subTest(title=title):
                self.assertTrue(refresh.local_news_item_is_in_scope({"title": title, "summary": ""}))
        for title in rejected:
            with self.subTest(title=title):
                self.assertFalse(refresh.local_news_item_is_in_scope({"title": title, "summary": ""}))

    def test_local_news_filters_before_sorting_and_limiting(self) -> None:
        accepted = [
            {
                "title": f"Teddington local update {index}",
                "summary": "",
                "publishedAt": f"2026-08-{index + 10:02d}T09:00:00+01:00",
                "url": f"https://example.com/local-{index}",
            }
            for index in range(12)
        ]
        rejected = {
            "title": "National celebrity story with no local place",
            "summary": "",
            "publishedAt": "2026-09-01T10:00:00+01:00",
            "url": "https://example.com/not-local",
        }

        with patch.object(refresh, "google_news", return_value=[rejected, *accepted]):
            result = refresh.local_news()

        self.assertEqual(len(result), 12)
        self.assertNotIn(rejected["title"], {item["title"] for item in result})
        self.assertEqual(
            [item["publishedAt"] for item in result],
            sorted((item["publishedAt"] for item in accepted), reverse=True),
        )


if __name__ == "__main__":
    unittest.main()
