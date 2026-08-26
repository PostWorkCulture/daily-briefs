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


if __name__ == "__main__":
    unittest.main()
