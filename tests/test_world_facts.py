import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import refresh


def fact(fact_id: str, priority: str | None = None) -> dict:
    item = {
        "id": fact_id,
        "category": "Test category",
        "country": "Test country",
        "locationContext": "Test region · Test continent",
        "place": "Test place",
        "source": "Test source",
        "sourceUrl": "https://example.com/source",
        "image": "https://example.com/image.jpg",
        "imagePage": "https://example.com/image-page",
        "photoCredit": "Test credit",
        "fact": f"Unique fact text for {fact_id}.",
    }
    if priority:
        item["editorialPriority"] = priority
    return item


class WorldFactTests(unittest.TestCase):
    def test_catalog_has_broad_human_first_range(self):
        catalog = json.loads((ROOT / "data" / "fact-catalog.json").read_text(encoding="utf-8"))
        human_first = [item for item in catalog if item.get("editorialPriority") == "human-first"]
        self.assertGreaterEqual(len(human_first), 8)
        categories = " ".join(item["category"].lower() for item in human_first)
        for topic in ("people", "population", "tradition", "music", "record"):
            self.assertIn(topic, categories)

    def test_low_stock_warns_without_blocking_publication(self):
        from fact_reserve import reserve_report
        for count in (0, 1, 6, 7, 21):
            catalog = [fact(f'human-{i}', 'human-first') for i in range(count)]
            report = reserve_report(catalog, {'used': []})
            self.assertEqual(report['remaining'], count)
            self.assertEqual(report['needsReplenishment'], count < 7)

    def test_every_catalogue_fact_has_wider_location_context(self):
        catalog = json.loads((ROOT / "data" / "fact-catalog.json").read_text(encoding="utf-8"))
        for item in catalog:
            with self.subTest(item=item["id"]):
                self.assertTrue(str(item.get("locationContext") or "").strip())
                self.assertIn("·", item["locationContext"])

    def test_retired_fact_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            history_path = root / "history.json"
            retired = fact("retired-human", "human-first")
            retired["editorialStatus"] = "retired"
            catalog_path.write_text(
                json.dumps([retired, fact("fresh-human", "human-first")]),
                encoding="utf-8",
            )
            history_path.write_text('{"version": 1, "used": []}', encoding="utf-8")

            original_catalog = refresh.FACT_CATALOG
            original_history = refresh.FACT_HISTORY
            original_now = refresh.NOW
            try:
                refresh.FACT_CATALOG = catalog_path
                refresh.FACT_HISTORY = history_path
                refresh.NOW = datetime(2026, 8, 30, tzinfo=ZoneInfo("Europe/London"))
                selected = refresh.world_fact_for_today()
            finally:
                refresh.FACT_CATALOG = original_catalog
                refresh.FACT_HISTORY = original_history
                refresh.NOW = original_now

            self.assertEqual(selected["id"], "fresh-human")

    def test_new_day_prefers_unused_human_first_fact(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            history_path = root / "history.json"
            catalog_path.write_text(
                json.dumps([fact("ordinary"), fact("remarkable-human", "human-first")]),
                encoding="utf-8",
            )
            history_path.write_text('{"version": 1, "used": []}', encoding="utf-8")

            original_catalog = refresh.FACT_CATALOG
            original_history = refresh.FACT_HISTORY
            original_now = refresh.NOW
            try:
                refresh.FACT_CATALOG = catalog_path
                refresh.FACT_HISTORY = history_path
                refresh.NOW = datetime(2026, 8, 27, tzinfo=ZoneInfo("Europe/London"))
                selected = refresh.world_fact_for_today()
            finally:
                refresh.FACT_CATALOG = original_catalog
                refresh.FACT_HISTORY = original_history
                refresh.NOW = original_now

            self.assertEqual(selected["id"], "remarkable-human")
            self.assertEqual(selected["editorialPriority"], "human-first")

    def _select(self, catalog, used=None, day=(2026, 10, 17)):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            history_path = root / "history.json"
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            history_path.write_text(json.dumps({"version": 1, "used": used or []}), encoding="utf-8")
            original = (refresh.FACT_CATALOG, refresh.FACT_HISTORY, refresh.NOW)
            try:
                refresh.FACT_CATALOG = catalog_path
                refresh.FACT_HISTORY = history_path
                refresh.NOW = datetime(*day, tzinfo=ZoneInfo("Europe/London"))
                return refresh.world_fact_for_today()
            finally:
                refresh.FACT_CATALOG, refresh.FACT_HISTORY, refresh.NOW = original

    def test_wild_facts_are_chosen_before_ordinary_human_first_facts(self):
        gentle = fact("gentle-craft", "human-first")
        wild = fact("wild-ritual", "human-first")
        wild["editorialBoost"] = "wild"
        self.assertEqual(self._select([gentle, wild])["id"], "wild-ritual")

    def test_consecutive_days_avoid_the_same_category_when_possible(self):
        yesterday = fact("yesterday-record", "human-first")
        yesterday["category"] = "World record"
        same = fact("another-record", "human-first")
        same["category"] = "World record"
        same["editorialBoost"] = "wild"
        different = fact("a-tribe", "human-first")
        different["category"] = "Living tribe"
        different["editorialBoost"] = "wild"
        selected = self._select(
            [yesterday, same, different],
            used=[{"date": "2026-10-16", "id": "yesterday-record"}],
        )
        self.assertEqual(selected["id"], "a-tribe")

    def test_catalogue_wild_facts_are_complete_and_sourced(self):
        catalog = json.loads((ROOT / "data" / "fact-catalog.json").read_text(encoding="utf-8"))
        wild = [item for item in catalog if item.get("editorialBoost") == "wild"]
        self.assertGreaterEqual(len(wild), 14)
        for item in wild:
            with self.subTest(item=item["id"]):
                self.assertEqual(item.get("editorialPriority"), "human-first")
                self.assertTrue(item["sourceUrl"].startswith("https://"))
                self.assertTrue(item["image"].startswith("https://commons.wikimedia.org/"))
                self.assertIn("·", item["locationContext"])

    def test_new_day_fails_when_human_first_queue_is_exhausted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            catalog_path = root / "catalog.json"
            history_path = root / "history.json"
            catalog_path.write_text(json.dumps([fact("ordinary")]), encoding="utf-8")
            history_path.write_text('{"version": 1, "used": []}', encoding="utf-8")

            original_catalog = refresh.FACT_CATALOG
            original_history = refresh.FACT_HISTORY
            original_now = refresh.NOW
            try:
                refresh.FACT_CATALOG = catalog_path
                refresh.FACT_HISTORY = history_path
                refresh.NOW = datetime(2026, 9, 4, tzinfo=ZoneInfo("Europe/London"))
                with self.assertRaisesRegex(RuntimeError, "Human-first fact catalogue exhausted"):
                    refresh.world_fact_for_today()
            finally:
                refresh.FACT_CATALOG = original_catalog
                refresh.FACT_HISTORY = original_history
                refresh.NOW = original_now


if __name__ == "__main__":
    unittest.main()
