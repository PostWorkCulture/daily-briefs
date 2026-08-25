import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("refresh", ROOT / "scripts" / "refresh.py")
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)


class PeteCommuteTests(unittest.TestCase):
    def job(self, location, **extra):
        item = {
            "title": "Head of Data and Automation",
            "company_name": "Public Service Employer",
            "location": location,
            "description": "A current UK public-sector data role.",
            "url": "https://example.com/jobs/head-of-data",
        }
        item.update(extra)
        return item

    def test_nearby_role_is_kept_and_labelled(self):
        result = refresh.pete_job_item(
            self.job("Kingston upon Thames, England, United Kingdom"),
            "LinkedIn",
        )
        self.assertIsNotNone(result)
        item = result[2]
        self.assertEqual(item["commuteFrom"], "KT8 2LE")
        self.assertEqual(item["commuteEligibility"], "within-1-hour")
        self.assertIn("Within 1 hour of KT8 2LE", item["meta"])

    def test_central_london_role_is_kept_and_labelled(self):
        result = refresh.pete_job_item(
            self.job("London, England, United Kingdom"),
            "LinkedIn",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[2]["commuteEligibility"], "within-1-hour")
        self.assertIn("Within 1 hour of KT8 2LE", result[2]["meta"])

    def test_uk_remote_role_is_kept(self):
        result = refresh.pete_job_item(
            self.job("United Kingdom", remote=True),
            "Remote OK",
        )
        self.assertIsNotNone(result)
        self.assertEqual(result[2]["commuteEligibility"], "remote")

    def test_distant_role_is_rejected(self):
        self.assertIsNone(
            refresh.pete_job_item(
                self.job("Manchester, England, United Kingdom"),
                "LinkedIn",
            )
        )

    def test_unspecified_greater_london_role_is_rejected(self):
        self.assertIsNone(
            refresh.pete_job_item(
                self.job("Greater London, England, United Kingdom"),
                "LinkedIn",
            )
        )


if __name__ == "__main__":
    unittest.main()
