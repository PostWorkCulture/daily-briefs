from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refresh


def item(title: str, date: str = "2026-10-15", source: str = "Test", url: str | None = None) -> dict:
    return {
        "title": title,
        "source": source,
        "publishedAt": f"{date}T12:00:00+01:00",
        "url": url or f"https://example.com/{abs(hash(title))}",
        "contentType": "article",
    }


class AiDedupeTests(unittest.TestCase):

    def test_same_event_from_two_outlets_appears_once(self) -> None:
        items = [
            item("FTC subpoenas Anthropic and OpenAI over artificial intelligence safety concerns"),
            item("US FTC subpoenas OpenAI and Anthropic over consumer harms, Axios reports"),
            item("Anthropic makes Code Review generally available"),
        ]
        titles = [x["title"] for x in refresh.dedupe_ai_stories(items)]
        self.assertEqual(len(titles), 2)
        self.assertEqual(titles[0], items[0]["title"])

    def test_same_company_valuation_story_within_two_days_appears_once(self) -> None:
        items = [
            item("Anthropic’s valuation could be slashed by $500bn", "2026-10-16"),
            item("Investors temper Anthropic IPO valuation expectations over revenue growth slowdown", "2026-10-15"),
        ]
        self.assertEqual(len(refresh.dedupe_ai_stories(items)), 1)

    def test_different_stories_about_one_company_are_kept(self) -> None:
        items = [
            item("Anthropic makes Code Review generally available, with $50,000 in credits attached"),
            item("Anthropic taps nonprofits METR and SecureBio to help assess risks and safety practices"),
        ]
        self.assertEqual(len(refresh.dedupe_ai_stories(items)), 2)

    def test_same_model_launch_appears_once(self) -> None:
        items = [
            item("Gemini 4 Argon: Built to solve your hardest problems"),
            item("Gemini 4 Argon for Robotics"),
            item("Claude Opus 5.5 release notes"),
            item("Developers react to Claude Opus 5.5"),
            item("Claude Sonnet 5.5: advancing performance"),
        ]
        titles = [x["title"] for x in refresh.dedupe_ai_stories(items)]
        self.assertEqual(titles, [
            "Gemini 4 Argon: Built to solve your hardest problems",
            "Claude Opus 5.5 release notes",
            "Claude Sonnet 5.5: advancing performance",
        ])

    def test_identical_url_is_a_duplicate(self) -> None:
        items = [item("One headline", url="https://x/1"), item("Totally different words", url="https://x/1")]
        self.assertEqual(len(refresh.dedupe_ai_stories(items)), 1)


class AiClassificationTests(unittest.TestCase):

    def test_google_news_redirect_url_does_not_make_a_story_google(self) -> None:
        story = item("Meta releases Muse Spark Open, a new open-weight AI model", url="https://news.google.com/rss/articles/abc")
        self.assertFalse(refresh.is_google_ai(story))
        direct = item("Gemini 4 Argon for Robotics", url="https://deepmind.google/discover/blog/x")
        self.assertTrue(refresh.is_google_ai(direct))


class LiveChineseAiTests(unittest.TestCase):

    def setUp(self) -> None:
        self.original_google_news = refresh.google_news
        self.original_previous = refresh.previous_chinese_ai

    def tearDown(self) -> None:
        refresh.google_news = self.original_google_news
        refresh.previous_chinese_ai = self.original_previous

    def test_chinese_lab_must_be_the_main_subject(self) -> None:
        self.assertTrue(refresh.chinese_ai_item(item("DeepSeek suffers another major outage")))
        self.assertTrue(refresh.chinese_ai_item(item("Alibaba Qwen Releases Qwen-Image-2.1-Turbo")))
        self.assertFalse(refresh.chinese_ai_item(item("Muse Spark Open is Meta's answer to Qwen, GLM, and Kimi")))
        self.assertFalse(refresh.chinese_ai_item(item("Kimi Antonelli wins in Austin")))
        self.assertFalse(refresh.chinese_ai_item(item("Alibaba shares fall 3%")))

    def test_live_slots_rotate_labs_and_collapse_repeats(self) -> None:
        feed = [
            item("DeepSeek suffers another major outage as company offers user refunds", "2026-10-15"),
            item("DeepSeek implements fix after partial outage affects chat and API services", "2026-10-15"),
            item("DeepSeek offers compensation after restoring from service outage", "2026-10-15"),
            item("DeepSeek’s Fundraise Could Hit 100 Billion Yuan In Days", "2026-10-14"),
            item("Alibaba Unveils $450 AI Glasses in Expanding Push Into Gadgets", "2026-10-13"),
            item("Alibaba starts selling its Qwen N1 AI glasses in China from $450", "2026-10-13"),
            item("Kimi K3 on AMD Instinct GPUs with TokenSpeed", "2026-10-09"),
        ]
        refresh.google_news = lambda *args, **kwargs: feed
        refresh.previous_chinese_ai = lambda: []
        picks = refresh.live_chinese_ai()
        self.assertEqual(len(picks), 3)
        labs = [refresh.ai_story_company(x) for x in picks]
        self.assertEqual(labs, ["deepseek", "alibaba", "moonshot"])
        self.assertTrue(all(x.get("liveChineseLab") for x in picks))

    def test_no_hardcoded_chinese_items_when_feed_is_empty(self) -> None:
        refresh.google_news = lambda *args, **kwargs: []
        refresh.previous_chinese_ai = lambda: []
        self.assertEqual(refresh.live_chinese_ai(), [])


if __name__ == "__main__":
    unittest.main()
