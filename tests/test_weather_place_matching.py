import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import enrich_weather_v2 as wx


class FakeResponse:
    def __init__(self, payload=None, text=""):
        self._payload = payload
        self.text = text

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


ST_JAMES_ADDRESS = {
    "leisure": "St James's Park",
    "suburb": "St. James's",
    "city_district": "City of Westminster",
    "city": "London",
    "state_district": "Greater London",
    "state": "England",
    "ISO3166-2-lvl4": "GB-ENG",
    "country": "United Kingdom",
}


class PlacePartsTests(unittest.TestCase):
    def test_title_case_apostrophe_is_tidied(self):
        self.assertEqual(wx.tidy_place_name("St James'S Park"), "St James's Park")

    def test_multi_part_station_is_most_specific_first(self):
        self.assertEqual(wx.place_parts("London, St James'S Park"), ["St James's Park", "London"])
        self.assertEqual(wx.exact_place("London, St James'S Park"), "St James's Park")

    def test_colon_separated_station_is_most_specific_first(self):
        self.assertEqual(wx.place_parts("Wight: St Catherines Point"), ["St Catherines Point", "Wight"])
        self.assertEqual(wx.exact_place("Wight: St Catherines Point"), "St Catherines Point")
        self.assertTrue(wx.place_name_matches("Wight: St Catherines Point", "St Catherine's Point"))
        self.assertEqual(wx.nominatim_queries("Wight: St Catherines Point"),
                         ["St Catherines Point, Wight", "St Catherines Point", "Wight"])

    def test_single_part_station_is_unchanged(self):
        self.assertEqual(wx.place_parts("Spadeadam No 2"), ["Spadeadam"])
        self.assertEqual(wx.exact_place("Spadeadam No 2"), wx.core_place("Spadeadam No 2"))

    def test_source_name_may_match_any_part(self):
        self.assertTrue(wx.place_name_matches("London, St James'S Park", "St James's Park"))
        self.assertTrue(wx.place_name_matches("London, St James'S Park", "London St James's Park"))
        self.assertTrue(wx.place_name_matches("London, St James'S Park", "London"))
        self.assertFalse(wx.place_name_matches("London, St James'S Park", "Heathrow"))


class MetOfficeHeadingTests(unittest.TestCase):
    def test_linked_station_page_accepts_the_exact_site(self):
        page = "<h1>St James's Park (Greater London) last 24 hours weather</h1>"
        with mock.patch.object(wx.requests, "get", return_value=FakeResponse(text=page)):
            place = wx.linked_met_office_place(
                "London, St James'S Park", "https://weather.metoffice.gov.uk/observations/example"
            )
        self.assertEqual(place, ("St James's Park", "Greater London"))

    def test_linked_station_page_accepts_a_colon_separated_site(self):
        page = "<h1>St Catherine's Point (Isle of Wight) last 24 hours weather</h1>"
        with mock.patch.object(wx.requests, "get", return_value=FakeResponse(text=page)):
            place = wx.linked_met_office_place(
                "Wight: St Catherines Point", "https://weather.metoffice.gov.uk/observations/example"
            )
        self.assertEqual(place, ("St Catherine's Point", "Isle of Wight"))

    def test_linked_station_page_for_another_place_is_rejected(self):
        page = "<h1>Heathrow (Greater London) last 24 hours weather</h1>"
        with mock.patch.object(wx.requests, "get", return_value=FakeResponse(text=page)):
            place = wx.linked_met_office_place(
                "London, St James'S Park", "https://weather.metoffice.gov.uk/observations/example"
            )
        self.assertIsNone(place)


class NominatimTests(unittest.TestCase):
    def test_exact_site_is_geocoded_first_and_labelled_with_its_county(self):
        calls = []

        def fake_get(url, params=None, **kwargs):
            calls.append(params["q"])
            return FakeResponse([{"address": ST_JAMES_ADDRESS}])

        with mock.patch.object(wx.requests, "get", side_effect=fake_get):
            place = wx.england_place("London, St James'S Park")
        self.assertEqual(place, ("St James's Park", "Greater London"))
        self.assertEqual(calls[0], "St James's Park, London, United Kingdom")

    def test_falls_back_to_wider_part_when_site_is_not_found(self):
        def fake_get(url, params=None, **kwargs):
            if params["q"].startswith("London"):
                return FakeResponse([{"address": {"city": "London", "state_district": "Greater London",
                                                   "state": "England", "ISO3166-2-lvl4": "GB-ENG"}}])
            return FakeResponse([])

        with mock.patch.object(wx.requests, "get", side_effect=fake_get):
            self.assertEqual(wx.england_place("London, St James'S Park"), ("London", "Greater London"))

    def test_london_without_county_field_is_greater_london(self):
        self.assertEqual(wx.nominatim_county({"city": "London", "state": "England"}), "Greater London")

    def test_place_outside_england_is_rejected(self):
        address = {"town": "Lerwick", "county": "Shetland Islands", "state": "Scotland", "ISO3166-2-lvl4": "GB-SCT"}
        with mock.patch.object(wx.requests, "get", return_value=FakeResponse([{"address": address}])):
            self.assertIsNone(wx.england_place("Lerwick"))

    def test_network_failure_returns_none(self):
        with mock.patch.object(wx.requests, "get", side_effect=OSError("offline")):
            self.assertIsNone(wx.england_place("London, St James'S Park"))


class NamedSitePhotoTests(unittest.TestCase):
    def commons_page(self, title, desc):
        return {
            "title": title,
            "imageinfo": [{
                "mime": "image/jpeg", "width": 2000, "height": 1300,
                "url": "https://upload.wikimedia.org/x/" + title.replace(" ", "_"),
                "extmetadata": {"ImageDescription": {"value": desc}, "Artist": {"value": "A Photographer"},
                                "LicenseShortName": {"value": "CC BY-SA 2.0"}},
            }],
        }

    def test_park_site_photo_skips_the_station_named_after_it(self):
        pages = {
            "1": self.commons_page("File:Entrance, St. James's Park Station.jpg", "Entrance, St. James's Park Station"),
            "2": self.commons_page("File:St James's Park lake.jpg", "The lake in St James's Park, London"),
        }
        with mock.patch.object(wx.requests, "get", return_value=FakeResponse({"query": {"pages": pages}})):
            photo = wx.exact_commons_photo("London, St James'S Park", "St James's Park", "Greater London")
        self.assertIn("St_James's_Park_lake", photo["src"])

    def test_only_station_photos_means_no_photo(self):
        pages = {"1": self.commons_page("File:St James's Park tube station.jpg", "St James's Park tube station")}
        with mock.patch.object(wx.requests, "get", return_value=FakeResponse({"query": {"pages": pages}})):
            self.assertIsNone(wx.exact_commons_photo("London, St James'S Park", "St James's Park", "Greater London"))


class WikidataSitePhotoTests(unittest.TestCase):
    def fake_get(self, url, params=None, **kwargs):
        if url == wx.NOMINATIM:
            return FakeResponse([{"address": ST_JAMES_ADDRESS, "extratags": {"wikidata": "Q123"}}])
        if url.startswith("https://www.wikidata.org/"):
            return FakeResponse({"entities": {"Q123": {"claims": {"P18": [
                {"mainsnak": {"datavalue": {"value": "St James's Park Lake.jpg"}}}]}}}})
        if url == wx.COMMONS_API:
            self.assertEqual(params["titles"], "File:St James's Park Lake.jpg")
            return FakeResponse({"query": {"pages": {"1": {"title": "File:St James's Park Lake.jpg", "imageinfo": [{
                "mime": "image/jpeg", "width": 3000, "height": 2000,
                "thumburl": "https://upload.wikimedia.org/thumb/St_James's_Park_Lake.jpg",
                "extmetadata": {"Artist": {"value": "A Photographer"}, "LicenseShortName": {"value": "CC BY-SA 4.0"}},
            }]}}}})
        raise AssertionError(f"unexpected request {url}")

    def test_named_site_uses_the_image_wikidata_records_for_it(self):
        with mock.patch.object(wx.requests, "get", side_effect=self.fake_get):
            photo = wx.exact_commons_photo("London, St James'S Park", "St James's Park", "Greater London")
        self.assertEqual(photo["page"], "https://commons.wikimedia.org/wiki/File:St_James%27s_Park_Lake.jpg")
        self.assertEqual(photo["alt"], "St James's Park, Greater London")
        self.assertIn("CC BY-SA 4.0", photo["credit"])

    def test_wikidata_site_in_another_county_is_ignored(self):
        with mock.patch.object(wx.requests, "get", side_effect=self.fake_get):
            self.assertEqual(wx.osm_wikidata_id("London, St James'S Park", "Kent"), "")

    def test_museum_objects_are_not_place_photos(self):
        page = {"title": "File:Mould of a token, Westminster (FindID 857094).jpg", "imageinfo": [{
            "mime": "image/jpeg", "width": 2000, "height": 1300, "url": "https://upload.wikimedia.org/x.jpg",
            "extmetadata": {"ImageDescription": {"value": "Token from St James's Park, Westminster"}}}]}
        with mock.patch.object(wx, "wikidata_place_photo", return_value=None), \
             mock.patch.object(wx.requests, "get", return_value=FakeResponse({"query": {"pages": {"1": page}}})):
            self.assertIsNone(wx.exact_commons_photo("London, St James'S Park", "St James's Park", "Greater London"))


if __name__ == "__main__":
    unittest.main()
