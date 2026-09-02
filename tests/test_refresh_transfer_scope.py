import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from refresh import (
    TRANSFER_EXCLUSIONS,
    official_transfer_is_corroborated,
    scope_transfer_updates,
)


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

    def test_single_invalid_article_is_quarantined_without_blocking(self):
        invalid_official = {
            "title": "Phoenix Blayney joins Arsenal",
            "source": "Arsenal.com",
            "publishedAt": "2026-09-02T05:00:00+01:00",
        }
        valid_report = {
            "title": "Arsenal agree deal for Ezri Konsa",
            "source": "Sky Sports",
            "publishedAt": "2026-09-02T04:00:00+01:00",
        }

        scoped = scope_transfer_updates([invalid_official, valid_report])

        self.assertEqual([item["title"] for item in scoped], [valid_report["title"]])
        self.assertEqual(scoped[0]["trust"], "Trusted report")

    def test_corroborated_official_item_records_its_evidence(self):
        official = {
            "title": "Ezri Konsa signs for Arsenal",
            "source": "Arsenal.com",
            "publishedAt": "2026-09-02T05:00:00+01:00",
        }
        report = {
            "title": "Ezri Konsa transfer news: Arsenal agree deal",
            "source": "Sky Sports",
            "url": "https://www.skysports.com/example",
            "publishedAt": "2026-09-02T04:00:00+01:00",
        }

        scoped = scope_transfer_updates([official, report])
        published_official = next(
            item for item in scoped if item["source"] == "Arsenal.com"
        )

        self.assertEqual(
            published_official["corroboratedBy"]["source"], "Sky Sports"
        )


if __name__ == "__main__":
    unittest.main()
