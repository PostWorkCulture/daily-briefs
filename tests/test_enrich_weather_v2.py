import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from enrich_weather_v2 import england_place, exact_commons_photo, met_office_heading_place


class EnglandPlaceTests(unittest.TestCase):
    def test_albemarle_has_verified_county(self):
        self.assertEqual(england_place("Albemarle"), ("Albemarle", "Northumberland"))

    def test_met_office_observation_heading_supplies_county(self):
        self.assertEqual(
            met_office_heading_place("Albemarle (Northumberland) last 24 hours weather"),
            ("Albemarle", "Northumberland"),
        )

    def test_heading_without_county_is_rejected(self):
        self.assertIsNone(met_office_heading_place("Albemarle last 24 hours weather"))

    def test_kielder_has_verified_exact_place_photo(self):
        photo = exact_commons_photo("Kielder Castle", "Kielder", "Northumberland")
        self.assertEqual(
            photo["page"],
            "https://commons.wikimedia.org/wiki/File:Kielder_water_uk_-_panoramio.jpg",
        )
        self.assertIn("Kielder", photo["alt"])

    def test_northolt_has_verified_exact_place_photo(self):
        photo = exact_commons_photo("Northolt", "Northolt", "Greater London")
        self.assertEqual(
            photo["page"],
            "https://commons.wikimedia.org/wiki/File:Northolt_clock_tower_-_geograph.org.uk_-_7246077.jpg",
        )
        self.assertIn("Northolt", photo["alt"])

    def test_warcop_range_has_verified_place_and_photo(self):
        self.assertEqual(england_place("Warcop Range"), ("Warcop", "Cumbria"))
        photo = exact_commons_photo("Warcop Range", "Warcop", "Cumbria")
        self.assertEqual(
            photo["page"],
            "https://commons.wikimedia.org/wiki/File:Warcop_-_geograph.org.uk_-_30200.jpg",
        )
        self.assertIn("Warcop", photo["alt"])

    def test_wiggonholt_has_verified_exact_place_photo(self):
        photo = exact_commons_photo("Wiggonholt", "Wiggonholt", "West Sussex")
        self.assertEqual(
            photo["page"],
            "https://commons.wikimedia.org/wiki/File:Pulborough_Brooks.JPG",
        )
        self.assertIn("Wiggonholt", photo["alt"])


if __name__ == "__main__":
    unittest.main()
