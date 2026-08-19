import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from enrich_weather_v2 import england_place, met_office_heading_place


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


if __name__ == "__main__":
    unittest.main()
