from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_refresh():
    spec = importlib.util.spec_from_file_location("refresh_uk_positive_news", ROOT / "scripts" / "refresh.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


refresh = load_refresh()


class PositiveUKNewsTests(unittest.TestCase):
    def test_positive_filter_accepts_only_constructive_or_uplifting_stories(self) -> None:
        accepted = (
            "NHS bladder cancer test spots nine in 10 cases in promising trial",
            "British wildlife charity celebrates record-breaking return of beavers",
            "Community raises £2m to reopen village theatre",
            "UK scientists make breakthrough that could save lives",
            "Restored railway station reopens to passengers",
            "Thousands of new apprenticeships created across England",
        )
        rejected = (
            "Iran attacks US bases after reports strike killed five",
            "Murder suspect pleads not guilty ahead of death penalty trial",
            "Rising numbers of children in mental health crisis",
            "Families hit by long waits for dementia diagnosis",
            "Charity warns funding crisis could force closures",
            "Community mourns victims after fatal crash",
        )

        for title in accepted:
            with self.subTest(title=title):
                self.assertTrue(refresh.positive_uk_news_item_is_in_scope({"title": title, "summary": ""}))
        for title in rejected:
            with self.subTest(title=title):
                self.assertFalse(refresh.positive_uk_news_item_is_in_scope({"title": title, "summary": ""}))

    def test_uk_news_filters_before_sorting_and_limiting(self) -> None:
        positive = [
            {
                "title": f"New community service opens in Britain {index}",
                "summary": "",
                "publishedAt": f"2026-08-{index + 10:02d}T09:00:00+01:00",
                "url": f"https://example.com/positive-{index}",
            }
            for index in range(12)
        ]
        negative = {
            "title": "UK crisis deepens after wave of closures",
            "summary": "",
            "publishedAt": "2026-09-01T10:00:00+01:00",
            "url": "https://example.com/negative",
        }

        with (
            patch.object(refresh, "rss", return_value=[negative]),
            patch.object(refresh, "google_news", return_value=positive),
        ):
            result = refresh.uk_news()

        self.assertEqual(len(result), 12)
        self.assertNotIn(negative["title"], {item["title"] for item in result})
        self.assertTrue(all(refresh.positive_uk_news_item_is_in_scope(item) for item in result))
        self.assertEqual(
            [item["publishedAt"] for item in result],
            sorted((item["publishedAt"] for item in positive), reverse=True),
        )


if __name__ == "__main__":
    unittest.main()
