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

    def test_catalog_keeps_a_seven_day_human_first_reserve(self):
        catalog = json.loads((ROOT / "data" / "fact-catalog.json").read_text(encoding="utf-8"))
        history = json.loads((ROOT / "data" / "fact-history.json").read_text(encoding="utf-8"))
        used_ids = {item["id"] for item in history["used"]}
        available = [
            item
            for item in catalog
            if item.get("editorialPriority") == "human-first"
            and item.get("editorialStatus") != "retired"
            and item["id"] not in used_ids
        ]
        self.assertGreaterEqual(
            len(available),
            7,
            "Replenish the verified human-first queue before the morning refresh can exhaust it",
        )


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
