import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from refresh import pete_job_item


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
            "description": "Current public-sector data leadership vacancy.",
            "url": "https://example.com/jobs/gds",
        }
        self.assertIsNotNone(pete_job_item(job, "LinkedIn"))


if __name__ == "__main__":
    unittest.main()
