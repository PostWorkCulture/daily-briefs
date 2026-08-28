from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
