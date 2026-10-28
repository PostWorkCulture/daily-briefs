from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refresh
from paywall import is_paywalled, without_paywalled


def item(title: str, source: str = "", url: str = "https://news.google.com/rss/articles/x") -> dict:
    return {"title": title, "source": source, "url": url, "publishedAt": "2026-10-28T08:00:00+00:00", "contentType": "article"}


class PaywallTests(unittest.TestCase):

    def test_paywalled_publishers_are_rejected_by_name(self) -> None:
        for source in ("Financial Times", "The Telegraph", "The Times", "Bloomberg", "The Wall Street Journal",
                       "The Economist", "The Information", "The Athletic", "Breakingviews", "Barron’s",
                       "South China Morning Post", "Business Insider", "Dagens Nyheter", "Reuters"):
            with self.subTest(source=source):
                self.assertTrue(is_paywalled(item("Anthropic news", source)))

    def test_free_publishers_are_kept(self) -> None:
        for source in ("BBC", "CNBC", "TechCrunch", "Sky Sports", "Arsenal.com", "Surrey Comet",
                       "Teddington Nub News", "The Guardian", "London Evening Standard", "Anthropic"):
            with self.subTest(source=source):
                self.assertFalse(is_paywalled(item("Story", source)))

    def test_paywalled_urls_and_sections(self) -> None:
        self.assertTrue(is_paywalled(item("x", "Unknown", "https://www.ft.com/content/abc")))
        self.assertTrue(is_paywalled(item("x", "Unknown", "https://markets.ft.com/data")))
        self.assertTrue(is_paywalled(item("x", "Reuters", "https://www.reuters.com/breakingviews/abc")))
        self.assertTrue(is_paywalled(item("x", "NYT", "https://www.nytimes.com/athletic/123")))
        self.assertTrue(is_paywalled(item("x", "Unknown", "https://www.reuters.com/technology/abc")))
        self.assertFalse(is_paywalled(item("x", "Yahoo Finance", "https://finance.yahoo.com/news/abc")))
        self.assertFalse(is_paywalled(item("x", "Unknown", "https://www.notft.com/abc")))

    def test_title_suffix_and_markers(self) -> None:
        self.assertTrue(is_paywalled(item("Anthropic founders tighten grip - Financial Times")))
        self.assertTrue(is_paywalled(item("Big interview (subscription required)", "Some Site")))
        self.assertFalse(is_paywalled(item("Teddington gets new bridge - Teddington Nub News")))

    def test_editorial_pipeline_drops_paywalled_and_reference_pages(self) -> None:
        items = [
            item("Anthropic’s seven founders tighten grip ahead of blockbuster IPO", "Financial Times"),
            item("Anthropic | History, Controversies, & Claude AI", "Britannica"),
            item("Chart: Anthropic's cash pile towers over nearly every U.S. company", "CNBC"),
        ]
        kept = [x["source"] for x in refresh.editorial_news(items)]
        self.assertEqual(kept, ["CNBC"])

    def test_transfer_watch_and_local_news_drop_paywalled(self) -> None:
        transfer = item("Arsenal agree deal to sign striker", "The Athletic")
        self.assertEqual(refresh.scope_transfer_updates([transfer]), [])
        self.assertFalse(refresh.local_news_item_is_in_scope(item("Kingston bridge to reopen", "The Times")))

    def test_without_paywalled_helper(self) -> None:
        self.assertEqual(len(without_paywalled([item("a", "FT"), item("b", "BBC")])), 1)


if __name__ == "__main__":
    unittest.main()
