import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from refresh import pete_job_item, public_ai_career_jobs


class PeteCareerScopeTests(unittest.TestCase):
    def test_gds_title_rejects_mismatched_employer(self):
        job = {
            "title": "Head of Applied Data Governance and Capability - Government Digital Service - G6",
            "company_name": "Manchester Digital",
            "location": "Manchester, England, United Kingdom",
            "description": "Current public-sector data leadership vacancy.",
            "url": "https://example.com/jobs/gds-mismatch",
        }
        self.assertIsNone(pete_job_item(job, "LinkedIn"))

    def test_gds_title_accepts_gds_employer(self):
        job = {
            "title": "Head of Applied Data Governance and Capability",
            "company_name": "Government Digital Service",
            "location": "England, United Kingdom",
            "description": "Lead responsible AI governance and assurance across government services.",
            "url": "https://example.com/jobs/gds",
            "date": "2026-09-03",
        }
        self.assertIsNotNone(pete_job_item(job, "LinkedIn"))

    def test_private_sector_ai_role_is_rejected(self):
        job = {
            "title": "AI Director",
            "company_name": "Private Technology Limited",
            "location": "London, United Kingdom",
            "description": "Lead the company's artificial intelligence strategy.",
            "url": "https://example.com/jobs/private-ai",
            "date": "2026-09-03",
        }
        self.assertIsNone(pete_job_item(job, "Official site"))

    def test_public_sector_role_without_ai_relevance_is_rejected(self):
        job = {
            "title": "Digital Delivery Manager",
            "company_name": "Cabinet Office",
            "location": "London, United Kingdom",
            "description": "Lead a website transformation programme.",
            "url": "https://example.com/jobs/public-digital",
            "date": "2026-09-03",
        }
        self.assertIsNone(pete_job_item(job, "Official site"))

    def test_output_has_every_requested_field_in_order(self):
        job = {
            "title": "Responsible AI Lead",
            "company_name": "NHS England",
            "location": "Leeds, United Kingdom",
            "description": "Lead responsible AI assurance for national health services. Salary £85,000 per annum.",
            "url": "https://example.com/jobs/nhs-ai",
            "date": "2026-09-03",
        }

        result = pete_job_item(job, "NHS Jobs")

        self.assertIsNotNone(result)
        item = result[2]
        requested = ["title", "company", "description", "salary", "postedDate", "source", "location"]
        self.assertEqual([key for key in item if key in requested], requested)
        self.assertEqual(item["salary"], "£85,000 per annum")
        self.assertEqual(item["postedDate"], "3 September 2026")

    def test_jobs_are_sorted_strictly_newest_first(self):
        candidates = [
            ({
                "title": "AI Policy Lead",
                "company_name": "Cabinet Office",
                "location": "London, United Kingdom",
                "description": "Set artificial intelligence policy across public services.",
                "url": "https://example.com/jobs/older",
                "date": "2026-09-01",
            }, "Official site"),
            ({
                "title": "Machine Learning Programme Manager",
                "company_name": "NHS England",
                "location": "Leeds, United Kingdom",
                "description": "Lead machine learning delivery for national health services.",
                "url": "https://example.com/jobs/newer",
                "date": "2026-09-03",
            }, "NHS Jobs"),
        ]

        result = public_ai_career_jobs(candidates)

        self.assertEqual([item["title"] for item in result], [
            "Machine Learning Programme Manager",
            "AI Policy Lead",
        ])


if __name__ == "__main__":
    unittest.main()
