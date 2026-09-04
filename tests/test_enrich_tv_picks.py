from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import enrich_tv_picks as tv


def episode(
    title: str,
    *,
    episode_id: int,
    airdate: str = "2026-08-27",
    show_type: str = "Documentary",
    genres: list[str] | None = None,
    source: str = "BBC One",
    number: int = 1,
    summary: str | None = None,
) -> dict:
    return {
        "id": episode_id,
        "airdate": airdate,
        "airtime": "21:00",
        "number": number,
        "summary": summary if summary is not None else f"A new investigation in {title}.",
        "show": {
            "id": episode_id + 1000,
            "name": title,
            "type": show_type,
            "language": "English",
            "genres": genres if genres is not None else ["Crime"],
            "weight": 80,
            "officialSite": f"https://example.com/{episode_id}",
            "network": None if source in tv.STREAMING_SERVICES else {"name": source, "country": {"code": "GB"}},
            "webChannel": {"name": source} if source in tv.STREAMING_SERVICES else None,
            "image": {
                "original": f"https://static.tvmaze.com/uploads/images/original_untouched/1/{episode_id}.jpg"
            },
        },
    }


class TvPickTests(unittest.TestCase):
    def test_candidate_contains_current_schedule_and_exact_artwork(self) -> None:
        item = tv.candidate(episode("The New Murder File", episode_id=1), date(2026, 8, 27))
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item["contentType"], "tv-pick")
        self.assertEqual(item["generatedDate"], "2026-08-27")
        self.assertEqual(item["badge"], "True crime")
        self.assertTrue(item["artwork"].startswith("https://static.tvmaze.com/uploads/images/original_untouched/"))

    def test_candidate_rejects_generic_artwork_and_daily_soap(self) -> None:
        generic = episode("A New Documentary", episode_id=2)
        generic["show"]["image"]["original"] = "https://example.com/placeholder.jpg"
        self.assertIsNone(tv.candidate(generic, date(2026, 8, 27)))
        self.assertIsNone(tv.candidate(episode("EastEnders", episode_id=3), date(2026, 8, 27)))

    def test_sport_is_limited_to_world_cup_euros_and_wimbledon(self) -> None:
        routine = episode(
            "Premier League Highlights",
            episode_id=40,
            show_type="Sports",
            genres=["Sports"],
        )
        self.assertIsNone(tv.candidate(routine, date(2026, 8, 27)))

        allowed = (
            "FIFA World Cup Review",
            "UEFA Euro 2028 Preview",
            "Wimbledon Centre Court",
        )
        for index, title in enumerate(allowed, start=41):
            with self.subTest(title=title):
                item = tv.candidate(
                    episode(title, episode_id=index, show_type="Sports", genres=["Sports"]),
                    date(2026, 8, 27),
                )
                self.assertIsNotNone(item)


    def test_reality_and_gary_barlow_are_never_eligible(self) -> None:
        self.assertIsNone(
            tv.candidate(
                episode("Island Contest", episode_id=70, show_type="Reality", genres=["Reality"]),
                date(2026, 8, 27),
            )
        )
        self.assertIsNone(
            tv.candidate(
                episode("Gary Barlow's Wine Tour", episode_id=71, show_type="Documentary", genres=["Travel"]),
                date(2026, 8, 27),
            )
        )

    def test_off_topic_documentaries_are_ineligible(self) -> None:
        dark = tv.candidate(
            episode("Silo: The New Mystery", episode_id=72, show_type="Scripted", genres=["Science-Fiction"], source="Apple TV+"),
            date(2026, 8, 27),
        )
        preferred = tv.candidate(
            episode("A Murder Investigation", episode_id=73, source="BBC iPlayer"),
            date(2026, 8, 27),
        )
        travel = tv.candidate(
            episode(
                "A Gentle Travel Programme",
                episode_id=74,
                show_type="Documentary",
                genres=["Travel"],
                source="ITV1",
                summary="A relaxed journey through scenic villages and gardens.",
            ),
            date(2026, 8, 27),
        )
        nature = tv.candidate(
            episode(
                "Europe's Wild Kingdoms",
                episode_id=75,
                show_type="Documentary",
                genres=["Nature"],
                source="Sky Nature",
                summary="Wildlife thrives around famous European heritage sites.",
            ),
            date(2026, 8, 27),
        )
        cultural = tv.candidate(
            episode(
                "Cultural Journeys",
                episode_id=79,
                show_type="Documentary",
                genres=[],
                source="BBC Two",
                summary="A celebration of literary cultures and traditional cultivation.",
            ),
            date(2026, 8, 27),
        )
        routine_enforcement = tv.candidate(
            episode(
                "Fare Dodgers: At War with the Law",
                episode_id=80,
                show_type="Documentary",
                genres=[],
                source="Channel 5",
                summary="Revenue protection officers inspect tickets across London.",
            ),
            date(2026, 8, 27),
        )
        assert dark is not None and preferred is not None
        self.assertIsNone(travel)
        self.assertIsNone(nature)
        self.assertIsNone(cultural)
        self.assertIsNone(routine_enforcement)
        self.assertEqual(dark["programmeType"], "Scripted")
        self.assertEqual(dark["genres"], ["Science-Fiction"])

    def test_generic_and_comedy_programmes_cannot_fill_the_list(self) -> None:
        generic_drama = episode(
            "Ordinary Family Drama",
            episode_id=76,
            show_type="Scripted",
            genres=["Drama"],
            source="BBC iPlayer",
            summary="A family faces a difficult week together.",
        )
        comedy_crime = episode(
            "Light Detective Comedy",
            episode_id=77,
            show_type="Scripted",
            genres=["Comedy", "Crime"],
            source="BBC iPlayer",
            summary="An eccentric amateur detective prepares for a wedding.",
        )
        self.assertIsNone(tv.candidate(generic_drama, date(2026, 8, 27)))
        self.assertIsNone(tv.candidate(comedy_crime, date(2026, 8, 27)))

    def test_new_apple_tv_premiere_is_eligible(self) -> None:
        item = tv.candidate(
            episode(
                "A New Apple Original",
                episode_id=78,
                show_type="Scripted",
                genres=["Drama"],
                source="Apple TV+",
                number=1,
                summary="A new original drama premieres this week.",
            ),
            date(2026, 8, 27),
        )
        self.assertIsNotNone(item)
        assert item is not None
        self.assertEqual(item["interestLane"], "apple-premiere")

    def test_new_episode_is_eligible_across_previous_and_next_week(self) -> None:
        last_week = tv.candidate(
            episode("Last Week Series", episode_id=30, airdate="2026-08-20", number=6),
            date(2026, 8, 27),
        )
        next_week = tv.candidate(
            episode("Next Week Series", episode_id=31, airdate="2026-09-03", number=4),
            date(2026, 8, 27),
        )
        too_old = tv.candidate(
            episode("Old Series", episode_id=32, airdate="2026-08-19", number=8),
            date(2026, 8, 27),
        )
        self.assertIsNotNone(last_week)
        self.assertIsNotNone(next_week)
        self.assertIsNone(too_old)
        assert last_week is not None and next_week is not None
        self.assertIn("Available since", last_week["meta"])
        self.assertIn("Thu 3 Sep", next_week["meta"])

    def test_selection_rolls_forward_before_reusing_recent_titles(self) -> None:
        candidates = [tv.candidate(episode(f"Fresh Programme {i}", episode_id=i), date(2026, 8, 27)) for i in range(1, 7)]
        old = tv.candidate(episode("Yesterday's Pick", episode_id=20), date(2026, 8, 27))
        items = [item for item in [old, *candidates] if item]
        history = [{"date": "2026-08-26", "titles": ["Yesterday's Pick"]}]
        selected = tv.select_picks(items, date(2026, 8, 27), history)
        self.assertEqual(len(selected), 5)
        self.assertNotIn("Yesterday's Pick", {item["title"] for item in selected})

    def test_selection_is_documentary_led_when_strong_options_exist(self) -> None:
        documentaries = [
            tv.candidate(episode(f"Murder Investigation {i}", episode_id=i), date(2026, 8, 27))
            for i in range(1, 5)
        ]
        scripted = [
            tv.candidate(
                episode(
                    f"Dark Thriller {i}",
                    episode_id=20 + i,
                    show_type="Scripted",
                    genres=["Drama", "Thriller"],
                ),
                date(2026, 8, 27),
            )
            for i in range(1, 4)
        ]
        selected = tv.select_picks([item for item in [*documentaries, *scripted] if item], date(2026, 8, 27), [])
        documentary_count = sum(item["interestLane"] == "dark-documentary" for item in selected)
        self.assertGreaterEqual(documentary_count, 3)
        self.assertLessEqual(documentary_count, 4)

    def test_selection_fails_instead_of_publishing_too_few_picks(self) -> None:
        items = [tv.candidate(episode(f"Programme {i}", episode_id=i), date(2026, 8, 27)) for i in range(1, 4)]
        with self.assertRaisesRegex(RuntimeError, "Only 3 current TV Picks"):
            tv.select_picks([item for item in items if item], date(2026, 8, 27), [])

    def test_selection_fails_without_three_qualifying_documentaries(self) -> None:
        documentaries = [
            tv.candidate(episode(f"Murder File {i}", episode_id=i), date(2026, 8, 27))
            for i in range(1, 3)
        ]
        scripted = [
            tv.candidate(
                episode(
                    f"Dark Thriller {i}",
                    episode_id=40 + i,
                    show_type="Scripted",
                    genres=["Drama", "Thriller"],
                ),
                date(2026, 8, 27),
            )
            for i in range(1, 5)
        ]
        with self.assertRaisesRegex(RuntimeError, "Only 2 dark or investigative documentaries"):
            tv.select_picks([item for item in [*documentaries, *scripted] if item], date(2026, 8, 27), [])


if __name__ == "__main__":
    unittest.main()
