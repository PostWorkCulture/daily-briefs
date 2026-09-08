from __future__ import annotations

import unittest

from scripts.refresh import (
    editorial_news,
    news_item_is_job_vacancy,
    section_content_type_errors,
)


class SectionContentTypeTests(unittest.TestCase):
    def test_contractor_adverts_are_quarantined_even_when_labelled_article(self) -> None:
        for title in (
            "Cybersecurity Engineer - £495pd - Outside IR35 - Surbiton, Surrey (Hybrid)",
            "Data Analyst - £45ph - Kingston",
            "Software Engineer - £400–500 per day - Surbiton",
            "Support Engineer - £30/hour - Hampton",
            "Business Analyst - Outside IR35 - Kingston",
        ):
            with self.subTest(title=title):
                item = {"title": title, "source": "Kingston Nub News", "contentType": "article"}
                self.assertEqual(editorial_news([item]), [])
                self.assertTrue(section_content_type_errors({"Local news": [item]}))

    def test_publisher_job_path_is_not_an_editorial_article(self) -> None:
        self.assertEqual(editorial_news([{
            "title": "Receptionist in Kingston", "contentType": "article",
            "url": "https://kingston.nub.news/jobs/administration/receptionist-123",
        }]), [])

    def test_employment_reporting_is_not_a_contractor_advert(self) -> None:
        for title in (
            "Council creates 200 new jobs in Kingston",
            "What changes to IR35 mean for local businesses",
            "Kingston engineer wins community award",
        ):
            self.assertFalse(news_item_is_job_vacancy({"title": title}))

    def test_expired_salary_listing_is_a_job_vacancy(self) -> None:
        item = {
            "title": "Business Analyst Surbiton, Surrey - £80,000 plus benefits (EXPIRED)",
            "source": "Kingston Nub News",
        }

        self.assertTrue(news_item_is_job_vacancy(item))
        self.assertEqual(editorial_news([item]), [])

    def test_job_creation_reporting_remains_an_article(self) -> None:
        item = {
            "title": "Thousands of new apprenticeships created across England",
            "source": "BBC News",
            "url": "https://example.com/new-jobs-created",
        }

        self.assertFalse(news_item_is_job_vacancy(item))
        self.assertEqual(editorial_news([item])[0]["contentType"], "article")

    def test_job_board_source_and_job_schema_are_rejected_from_news(self) -> None:
        self.assertTrue(news_item_is_job_vacancy({
            "title": "Responsible AI Lead",
            "source": "Civil Service Jobs",
        }))
        self.assertTrue(news_item_is_job_vacancy({
            "title": "Responsible AI Lead",
            "company": "Cabinet Office",
            "salary": "£80,000",
            "location": "London",
        }))

    def test_section_contract_rejects_both_directions_of_content_bleed(self) -> None:
        sections = {
            "Local news": [{
                "title": "AI vacancy in Surbiton",
                "contentType": "job",
            }],
            "Career": [{
                "title": "Council launches AI service",
                "contentType": "article",
            }],
        }

        errors = section_content_type_errors(sections)

        self.assertTrue(any("Local news" in error and "expected article" in error for error in errors))
        self.assertTrue(any("Career" in error and "expected job" in error for error in errors))

    def test_section_contract_accepts_separated_articles_and_jobs(self) -> None:
        sections = {
            "Local news": [{
                "title": "New family trail opens in Teddington",
                "contentType": "article",
            }],
            "Career": [{
                "title": "Responsible AI Lead",
                "company": "Cabinet Office",
                "salary": "£80,000",
                "location": "London",
                "contentType": "job",
            }],
        }

        self.assertEqual(section_content_type_errors(sections), [])


if __name__ == "__main__":
    unittest.main()
