import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from refresh import (
    TRANSFER_EXCLUSIONS,
    base_google_uid,
    dedupe_transfer_updates,
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

    def test_duplicate_player_transfer_stories_are_deduplicated(self):
        newer_story = {
            "title": "Arsenal boss Mikel Arteta refuses to rule out loan move for Max Dowman",
            "source": "Sky Sports",
            "publishedAt": "2026-09-18T22:37:32+01:00",
        }
        older_duplicate = {
            "title": "Max Dowman: Mikel Arteta admits 16-year-old Arsenal wonderkid could go out on loan in the future",
            "source": "Sky Sports",
            "publishedAt": "2026-09-18T22:32:05+01:00",
        }
        unrelated_story = {
            "title": "Arsenal latest: Mikel Arteta relaxed about new contract",
            "source": "Sky Sports",
            "publishedAt": "2026-09-18T09:35:26+01:00",
        }

        deduped = dedupe_transfer_updates([newer_story, older_duplicate, unrelated_story])
        self.assertEqual(len(deduped), 2)
        self.assertEqual(deduped[0]["title"], newer_story["title"])
        self.assertEqual(deduped[1]["title"], unrelated_story["title"])

    def test_recurring_calendar_uid_normalization(self):
        self.assertEqual(
            base_google_uid("1nnb47dr2n0np88mfiugnjidfp_R20261012"),
            "1nnb47dr2n0np88mfiugnjidfp"
        )
        self.assertEqual(
            base_google_uid("event123_20261012T080000Z"),
            "event123"
        )
        self.assertEqual(
            base_google_uid("standalone_uid"),
            "standalone_uid"
        )

    def test_calendar_colour_data_reads_local_file(self):
        from refresh import calendar_colour_data
        data = calendar_colour_data()
        self.assertIn("eventPalette", data)
        self.assertIn("events", data)


if __name__ == "__main__":
    unittest.main()
