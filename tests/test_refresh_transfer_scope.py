import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from refresh import TRANSFER_EXCLUSIONS, official_transfer_is_corroborated


class ArsenalTransferScopeTests(unittest.TestCase):
    def test_job_vacancy_is_excluded(self):
        self.assertIsNotNone(
            TRANSFER_EXCLUSIONS.search(
                "Creative - Partner Marketing (12 Month Fixed Term Contract)"
            )
        )

    def test_official_first_team_transfer_needs_player_corroboration(self):
        official = {"title": "Ezri Konsa signs for Arsenal"}
        reports = [
            {
                "title": (
                    "Ezri Konsa transfer news: Arsenal agree deal with Aston Villa "
                    "to sign England defender"
                )
            }
        ]
        self.assertTrue(official_transfer_is_corroborated(official, reports))

    def test_uncorroborated_academy_signing_is_rejected(self):
        official = {"title": "Phoenix Blayney joins Arsenal"}
        reports = [{"title": "Arsenal agree deal for Ezri Konsa"}]
        self.assertFalse(official_transfer_is_corroborated(official, reports))

    def test_current_transfer_watch_obeys_scope(self):
        payload = json.loads((ROOT / "data" / "pete.json").read_text(encoding="utf-8"))
        transfers = payload["arsenal"]["transfers"]
        trusted_reports = [
            item for item in transfers
            if "arsenal.com" not in item.get("source", "").lower()
        ]
        for item in transfers:
            self.assertIsNone(TRANSFER_EXCLUSIONS.search(item["title"]))
            if "arsenal.com" in item.get("source", "").lower():
                self.assertTrue(
                    official_transfer_is_corroborated(item, trusted_reports),
                    item["title"],
                )


if __name__ == "__main__":
    unittest.main()
