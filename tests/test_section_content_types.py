from __future__ import annotations

import unittest

from scripts.refresh import (
    editorial_news,
    anthropic_first,
    local_news_item_is_in_scope,
    news_item_is_job_vacancy,
    section_content_type_errors,
)



class SectionContentTypeTests(unittest.TestCase):
    def test_job_directories_and_roundups_rejected_in_every_editorial_section(self) -> None:
        for title in (
            "Jobs in Teddington | Sales", "Jobs in Kingston", "Latest jobs in Hampton",
            "Local jobs: Sales", "Jobs of the week in Surbiton",
            "Teddington jobs roundup", "Browse local jobs", "Job listings in Kingston",
        ):
            item = {"title": title, "contentType": "article", "source": "Teddington Nub News",
                    "url": "https://news.google.com/rss/articles/opaque-id"}
            with self.subTest(title=title):
                self.assertEqual(editorial_news([item]), [])
                for section in ("Local news", "UK news", "Sweden", "AI", "Arsenal news"):
                    self.assertTrue(section_content_type_errors({section: [item]}))

    def test_job_directory_root_paths_rejected_without_title_clues(self) -> None:
        for suffix in ("/jobs", "/jobs/", "/jobs?category=sales", "/careers#roles", "/vacancies"):
            with self.subTest(suffix=suffix):
                self.assertTrue(news_item_is_job_vacancy({
                    "title": "Sales", "url": "https://teddington.nub.news" + suffix,
                }))

    def test_genuine_employment_and_careers_reporting_remains_news(self) -> None:
        for title in ("Kingston Council boosts support for youth jobs and careers",
                      "Council creates 200 new jobs in Kingston",
                      "Jobs saved as Kingston factory reopens"):
            with self.subTest(title=title):
                self.assertFalse(news_item_is_job_vacancy({"title": title}))

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

    def test_bare_role_and_place_vacancy_titles_are_quarantined(self) -> None:
        for title in (
            "Mobile Vehicle Technician - Esher",
            "Care Assistant - Kingston upon Thames",
            "Receptionist – Teddington",
            "Delivery Driver - West Molesey",
        ):
            with self.subTest(title=title):
                item = {"title": title, "source": "Teddington Nub News", "contentType": "article",
                        "url": "https://news.google.com/rss/articles/opaque-id"}
                self.assertTrue(news_item_is_job_vacancy(item))
                self.assertFalse(local_news_item_is_in_scope(item))
                self.assertTrue(section_content_type_errors({"Local news": [item]}))

    def test_role_words_in_editorial_headlines_remain_news(self) -> None:
        for title in (
            "Kingston engineer wins community award",
            "Bus driver praised for saving passenger - Surbiton",
            "Delicious new food stalls to join Teds Market as it celebrates two years in Teddington",
            "Hampton chef opens new restaurant on Station Road",
            "Police officer honoured for bravery in Kingston",
        ):
            with self.subTest(title=title):
                self.assertFalse(news_item_is_job_vacancy({"title": title}))

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

    def test_anthropic_always_leads_ai_and_google_keeps_only_major_announcements(self) -> None:
        items = [
            {"title": "OpenAI announces model", "source": "OpenAI", "url": "https://openai.com/1", "publishedAt": "2026-10-14T10:00:00+01:00"},
            {"title": "Gemini 4 Argon: Built to solve your hardest problems", "source": "Google DeepMind", "url": "https://deepmind.google/1", "publishedAt": "2026-10-13T10:00:00+01:00"},
            {"title": "Developing Gemini 4 Argon responsibly and safely", "source": "Google DeepMind", "url": "https://deepmind.google/2", "publishedAt": "2026-10-13T11:00:00+01:00"},
            {"title": "Google DeepMind and Singapore Government collaborate on scam model", "source": "Google DeepMind", "url": "https://deepmind.google/3", "publishedAt": "2026-10-14T09:00:00+01:00"},
            {"title": "5 tips for using Gemini in Gmail", "source": "Google", "url": "https://blog.google/1", "publishedAt": "2026-10-14T12:00:00+01:00"},
            {"title": "Google launches new AI Mode in Search", "source": "Google", "url": "https://blog.google/2", "publishedAt": "2026-10-12T12:00:00+01:00"},
            {"title": "Gemini 4 Argon for Robotics", "source": "Google DeepMind", "url": "https://deepmind.google/4", "publishedAt": "2026-10-11T12:00:00+01:00"},
            {"title": "Anthropic expands Claude Code to teams", "source": "Reuters", "url": "https://reuters.com/2", "publishedAt": "2026-10-10T10:00:00+01:00"},
            {"title": "Claude Opus 5.5 release notes", "source": "Anthropic", "url": "https://www.anthropic.com/news/opus", "publishedAt": "2026-10-12T10:00:00+01:00"},
        ]
        ordered = anthropic_first(items)
        titles = [item["title"] for item in ordered]
        self.assertEqual(titles[:2], ["Claude Opus 5.5 release notes", "Anthropic expands Claude Code to teams"])
        self.assertEqual(titles[2:4], [
            "Gemini 4 Argon: Built to solve your hardest problems",
            "Google launches new AI Mode in Search",
        ])
        self.assertEqual(titles[4:], ["OpenAI announces model"])
        for minor in (
            "Developing Gemini 4 Argon responsibly and safely",
            "Google DeepMind and Singapore Government collaborate on scam model",
            "5 tips for using Gemini in Gmail",
        ):
            self.assertNotIn(minor, titles)

    def test_whats_on_and_whats_going_on_items_rejected_from_local_news(self) -> None:
        for title in (
            "What's on near Teddington this weekend: Tango and Cake",
            "What's on in Kingston this weekend: Cultural celebrations",
            "What's going on in Surbiton this week",
            "Things to do in Hampton Court this weekend",
        ):
            item = {
                "title": title,
                "summary": "Local listings",
                "source": "Kingston Nub News",
                "contentType": "article",
                "url": "https://kingston.nub.news/whats-on",
            }
            with self.subTest(title=title):
                self.assertFalse(
                    local_news_item_is_in_scope(item),
                    f"{title} should be rejected from Local News"
                )

    def test_whats_on_activities_belong_in_fun_section(self) -> None:
        sections = {
            "Fun": [{
                "title": "Bushy Park Charity Day & Family Fun Morning",
                "location": "Bushy Park · Teddington",
                "summary": "Family activities and stalls",
                "when": "Saturday 3 & Sunday 4 October",
                "ages": "All ages",
                "cost": "Free",
                "source": "Teddington Nub News",
                "url": "https://teddington.nub.news/whats-on",
                "tags": ["Events", "What's on"],
                "contentType": "activity",
            }],
        }
        self.assertEqual(section_content_type_errors(sections), [])


if __name__ == "__main__":
    unittest.main()

