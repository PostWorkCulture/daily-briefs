from __future__ import annotations

import html
import hashlib
import json
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

from enrich_weather_metoffice import met_weather, UA

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EXTREMES_URL = "https://weather.metoffice.gov.uk/observations/weather-extremes"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA_ENTITY = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
WEATHER_IMAGE_DIR = ROOT / "assets" / "weather-extremes"

# Known, manually verified exact-place photos from the approved Daily Briefs build.
KNOWN_PHOTOS = {
    "northolt": {
        "src": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Northolt_clock_tower_-_geograph.org.uk_-_7246077.jpg?width=1600",
        "page": "https://commons.wikimedia.org/wiki/File:Northolt_clock_tower_-_geograph.org.uk_-_7246077.jpg",
        "credit": "Mark Percy · CC BY-SA 2.0",
        "alt": "Northolt clock tower on Northolt Village Green, Greater London",
    },
    "teddington": {
        "src": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Diana_Fountain%2C_Bushy_Park.jpeg?width=1600",
        "page": "https://commons.wikimedia.org/wiki/File:Diana_Fountain,_Bushy_Park.jpeg",
        "credit": "Jonathan Cardy · CC BY 3.0",
        "alt": "Diana Fountain in Bushy Park, Teddington, Greater London",
    },
    "sennybridge": {
        "src": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Bridge_over_the_River_Usk_at_Sennybridge_-_geograph.org.uk_-_3953802.jpg?width=1600",
        "page": "https://commons.wikimedia.org/wiki/File:Bridge_over_the_River_Usk_at_Sennybridge_-_geograph.org.uk_-_3953802.jpg",
        "credit": "Rod Allday · CC BY-SA 2.0",
        "alt": "Bridge over the River Usk at Sennybridge",
    },
    "warcop": {
        "src": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Warcop_-_geograph.org.uk_-_30200.jpg?width=1600",
        "page": "https://commons.wikimedia.org/wiki/File:Warcop_-_geograph.org.uk_-_30200.jpg",
        "credit": "Carl Bendelow · CC BY-SA 2.0",
        "alt": "Warcop village in Cumbria near the Warcop Training Area",
    },
    "wiggonholt": {
        "src": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Pulborough_Brooks.JPG?width=1600",
        "page": "https://commons.wikimedia.org/wiki/File:Pulborough_Brooks.JPG",
        "credit": "Charlesdrakew · public domain",
        "alt": "Pulborough Brooks nature reserve in Wiggonholt, West Sussex",
    },
    "topcliffe": {
        "src": "https://upload.wikimedia.org/wikipedia/commons/4/4c/Church_Street_from_above_-_geograph.org.uk_-_6179037.jpg",
        "page": "https://commons.wikimedia.org/wiki/File:Church_Street_from_above_-_geograph.org.uk_-_6179037.jpg",
        "credit": "Gordon Hatton · CC BY-SA 2.0",
        "alt": "Church Street in Topcliffe, North Yorkshire",
    },
    "kielder": {
        "src": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Kielder_water_uk_-_panoramio.jpg?width=1600",
        "page": "https://commons.wikimedia.org/wiki/File:Kielder_water_uk_-_panoramio.jpg",
        "credit": "Jim Walton · CC BY 3.0",
        "alt": "Kielder Water in Kielder, Northumberland",
    },
    "spadeadam": {
        "src": "https://commons.wikimedia.org/wiki/Special:Redirect/file/Entrance_to_RAF_Spadeadam%2C_1989_-_geograph.org.uk_-_4292063.jpg?width=1600",
        "page": "https://commons.wikimedia.org/wiki/File:Entrance_to_RAF_Spadeadam,_1989_-_geograph.org.uk_-_4292063.jpg",
        "credit": "Ben Brooksbank · CC BY-SA 2.0",
        "alt": "Entrance to RAF Spadeadam in Cumberland, England",
    },
}

KNOWN_ENGLISH_PLACES = {
    "albemarle": ("Albemarle", "Northumberland"),
    "northolt": ("Northolt", "Greater London"),
    "teddington": ("Teddington", "Greater London"),
    "wiggonholt": ("Wiggonholt", "West Sussex"),
    "topcliffe": ("Topcliffe", "North Yorkshire"),
    "pershore": ("Pershore", "Worcestershire"),
    "writtle": ("Writtle", "Essex"),
    "warcop": ("Warcop", "Cumbria"),
    "holbeach": ("Holbeach", "Lincolnshire"),
    "shobdon": ("Shobdon", "Herefordshire"),
    "boscombe down": ("Boscombe Down", "Wiltshire"),
    "south newington": ("South Newington", "Oxfordshire"),
    "benson": ("Benson", "Oxfordshire"),
    "brize norton": ("Brize Norton", "Oxfordshire"),
    "exeter": ("Exeter", "Devon"),
    "langdon bay": ("Langdon Bay", "Kent"),
    "heathrow": ("Heathrow", "Greater London"),
    "kew": ("Kew", "Greater London"),
    "spadeadam": ("Spadeadam", "Cumberland"),
}

ENGLAND_REGION_IDS = {
    "region-ne",  # North East England
    "region-yh",  # Yorkshire & Humber
    "region-nw",  # North West England
    "region-em",  # East Midlands
    "region-wm",  # West Midlands
    "region-ee",  # East of England
    "region-se",  # London & South East England
    "region-sw",  # South West England
}


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def plain(value: str) -> str:
    return clean(BeautifulSoup(html.unescape(value or ""), "html.parser").get_text(" ", strip=True))


def core_place(location: str) -> str:
    value = re.sub(r"\bNo\s*\d+\b", "", location, flags=re.I)
    value = re.sub(r"\bNumber\s*\d+\b", "", value, flags=re.I)
    return clean(value.split(",", 1)[0])


NAMED_SITE = re.compile(r"\b(?:park|gardens?|common|heath|green|reservoir|airport)\b", re.I)
MUSEUM_OBJECT = re.compile(r"findid|portable antiquities|\b(?:token|coin|mould|artefact|artifact|museum number)\b", re.I)
TRANSPORT_STOP = re.compile(r"\b(?:station|underground|tube|platform)\b", re.I)


def tidy_place_name(value: str) -> str:
    """Undo title-case artefacts in Met Office names, e.g. "St James'S Park"."""
    return re.sub(r"(\w)(['\u2019])S\b", r"\1\2s", clean(value))


def place_parts(location: str) -> list[str]:
    """Comma-separated parts of a Met Office location, most specific first.

    The Met Office writes some stations as "City, Spot" (e.g. "London, St James's Park"),
    so the last part names the exact site and the first names the wider town or city.
    """
    value = re.sub(r"\bNo\s*\d+\b", "", location, flags=re.I)
    value = re.sub(r"\bNumber\s*\d+\b", "", value, flags=re.I)
    parts = [tidy_place_name(part) for part in value.split(",")]
    parts = [part for part in parts if part]
    return list(reversed(parts))


def exact_place(location: str) -> str:
    parts = place_parts(location)
    return parts[0] if parts else core_place(location)


def squash(value: str) -> str:
    return re.sub(r"\W+", "", (value or "").lower())


def place_name_matches(location: str, name: str) -> bool:
    """True when a source's place name is the Met Office location or one of its parts."""
    actual = squash(name)
    if not actual:
        return False
    parts = place_parts(location)
    options = {squash(part) for part in parts}
    options.add(squash(" ".join(reversed(parts))))
    options.add(squash(" ".join(parts)))
    return actual in options


def met_office_heading_place(heading: str) -> tuple[str, str] | None:
    match = re.match(
        r"^(.+?)\s+\(([^()]+)\)\s+(?:last 24 hours weather|weather)\b",
        clean(heading),
        flags=re.I,
    )
    if not match:
        return None
    town, county = clean(match.group(1)), clean(match.group(2))
    if not town or not county or town.lower() == county.lower():
        return None
    return town, county


def linked_met_office_place(location: str, location_url: str) -> tuple[str, str] | None:
    if not location_url:
        return None
    url = urljoin(EXTREMES_URL, location_url)
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.netloc != "weather.metoffice.gov.uk":
        return None
    try:
        r = requests.get(url, headers=UA, timeout=15)
        r.raise_for_status()
        heading = BeautifulSoup(r.text, "html.parser").find("h1")
        place = met_office_heading_place(heading.get_text(" ", strip=True) if heading else "")
        if not place:
            return None
        if not place_name_matches(location, place[0]):
            return None
        return tidy_place_name(place[0]), place[1]
    except Exception:
        return None


def england_place(location: str, location_url: str = "") -> tuple[str, str] | None:
    low = location.lower()
    for key, place in KNOWN_ENGLISH_PLACES.items():
        if key in low:
            return place
    official_place = linked_met_office_place(location, location_url)
    if official_place:
        return official_place
    return nominatim_england_place(location)


def nominatim_queries(location: str) -> list[str]:
    parts = place_parts(location)
    queries = []
    if len(parts) > 1:
        queries.append(", ".join(parts))  # "St James's Park, London": most specific first
    queries.extend(parts)
    seen, unique = set(), []
    for query in queries:
        if query.lower() not in seen:
            seen.add(query.lower())
            unique.append(query)
    return unique


def nominatim_county(address: dict) -> str:
    county = clean(address.get("county") or address.get("state_district") or "")
    if not county and clean(address.get("city") or "").lower() == "london":
        county = "Greater London"
    return county


def nominatim_england_place(location: str) -> tuple[str, str] | None:
    """Geocode with OpenStreetMap, trying the exact site first, then each wider part.

    A multi-part station such as "London, St James's Park" is labelled with the exact
    site ("St James's Park, Greater London"), matching Heathrow, Kew and Northolt.
    """
    parts = place_parts(location)
    multi_part = len(parts) > 1
    for query in nominatim_queries(location):
        try:
            r = requests.get(
                NOMINATIM,
                params={"q": f"{query}, United Kingdom", "format": "jsonv2", "addressdetails": 1, "limit": 1},
                headers={**UA, "Accept-Language": "en-GB,en"},
                timeout=15,
            )
            r.raise_for_status()
            hits = r.json()
        except Exception:
            continue
        if not hits:
            continue
        address = hits[0].get("address", {})
        in_england = address.get("ISO3166-2-lvl4") == "GB-ENG" or "england" in " ".join(
            str(x) for x in address.values()
        ).lower()
        if not in_england:
            continue
        county = nominatim_county(address)
        if multi_part and query.lower() != parts[-1].lower():
            town = parts[0]
        else:
            town = clean(
                address.get("town") or address.get("city") or address.get("village") or
                address.get("hamlet") or address.get("locality") or address.get("suburb") or
                query
            )
        if town and county and town.lower() != county.lower():
            return tidy_place_name(town), county
    return None


def display_location(location: str) -> str:
    place = england_place(location)
    return f"{place[0]}, {place[1]}" if place else location


def osm_wikidata_id(location: str, county: str = "") -> str:
    """Wikidata ID OpenStreetMap links to the exact site (most specific part first, England only)."""
    for query in nominatim_queries(location):
        try:
            r = requests.get(
                NOMINATIM,
                params={"q": f"{query}, United Kingdom", "format": "jsonv2", "addressdetails": 1,
                        "extratags": 1, "limit": 1},
                headers={**UA, "Accept-Language": "en-GB,en"},
                timeout=15,
            )
            r.raise_for_status()
            hits = r.json()
        except Exception:
            continue
        if not isinstance(hits, list) or not hits:
            continue
        hit = hits[0]
        address = hit.get("address", {})
        if address.get("ISO3166-2-lvl4") != "GB-ENG":
            continue
        if county and nominatim_county(address).lower() != county.lower():
            continue
        qid = str((hit.get("extratags") or {}).get("wikidata") or "")
        if re.fullmatch(r"Q\d+", qid):
            return qid
    return ""


def commons_file_photo(filename: str, place: str, county: str) -> dict | None:
    params = {
        "action": "query",
        "titles": "File:" + filename,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": 1600,
        "format": "json",
        "origin": "*",
    }
    r = requests.get(COMMONS_API, params=params, headers=UA, timeout=20)
    r.raise_for_status()
    for page in ((r.json().get("query") or {}).get("pages") or {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        if info.get("mime") not in {"image/jpeg", "image/png", "image/webp"}:
            return None
        if int(info.get("width") or 0) < 640 or int(info.get("height") or 0) < 360:
            return None
        meta = info.get("extmetadata") or {}
        title = page.get("title", "File:" + filename)
        artist = plain((meta.get("Artist") or {}).get("value", "")) or "Wikimedia Commons contributor"
        licence = plain((meta.get("LicenseShortName") or {}).get("value", ""))
        name = title.removeprefix("File:")
        return {
            "src": info.get("thumburl") or info.get("url"),
            "page": "https://commons.wikimedia.org/wiki/File:" + quote(name.replace(" ", "_"), safe="()_,.-"),
            "credit": " · ".join(x for x in (artist, licence) if x),
            "alt": f"{place}, {county}",
        }
    return None


def wikidata_place_photo(location: str, town: str = "", county: str = "") -> dict | None:
    """The image Wikidata records for the exact site OpenStreetMap identifies (P18)."""
    try:
        qid = osm_wikidata_id(location, county)
        if not qid:
            return None
        r = requests.get(WIKIDATA_ENTITY.format(qid=qid), headers=UA, timeout=20)
        r.raise_for_status()
        entity = (r.json().get("entities") or {}).get(qid) or {}
        claims = (entity.get("claims") or {}).get("P18") or []
        filename = str((((claims[0] if claims else {}).get("mainsnak") or {}).get("datavalue") or {}).get("value") or "")
        if not filename:
            return None
        return commons_file_photo(filename, town or exact_place(location), county or "England")
    except Exception:
        return None


def exact_commons_photo(location: str, town: str = "", county: str = "") -> dict | None:
    low = location.lower()
    for key, photo in KNOWN_PHOTOS.items():
        if key in low:
            return dict(photo)

    place = exact_place(location)
    if len(place) < 3:
        return None
    if len(place_parts(location)) > 1 or NAMED_SITE.search(place):
        site_photo = wikidata_place_photo(location, town, county)
        if site_photo:
            return site_photo
    named_site = bool(NAMED_SITE.search(place))
    station_site = bool(TRANSPORT_STOP.search(place))
    exact_needles = {
        re.sub(r"\W+", "", value.lower())
        for value in (place, town)
        if len(clean(value)) >= 3
    }
    searches = (
        f'"{place}" "{county}" landmark',
        f'"{town or place}" "{county}" council offices',
        f'"{town or place}" "{county}" town centre',
        f'"{town or place}" "{county}" England',
    )
    candidates = []
    for search_rank, search in enumerate(searches):
        try:
            params = {
                "action": "query",
                "generator": "search",
                "gsrsearch": search,
                "gsrnamespace": 6,
                "gsrlimit": 20,
                "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata",
                "iiurlwidth": 1600,
                "format": "json",
                "origin": "*",
            }
            r = requests.get(COMMONS_API, params=params, headers=UA, timeout=20)
            r.raise_for_status()
            pages = (r.json().get("query") or {}).get("pages", {})
            for page in pages.values():
                info = (page.get("imageinfo") or [{}])[0]
                if info.get("mime") not in {"image/jpeg", "image/png", "image/webp"}:
                    continue
                width, height = int(info.get("width") or 0), int(info.get("height") or 0)
                if width < 640 or height < 360:
                    continue
                if not (info.get("thumburl") or info.get("url")):
                    continue
                meta = info.get("extmetadata") or {}
                title = page.get("title", "")
                desc = plain((meta.get("ImageDescription") or {}).get("value", ""))
                hay_text = f"{title} {desc}".lower()
                hay = re.sub(r"\W+", "", hay_text)
                if not any(needle in hay for needle in exact_needles):
                    continue
                if MUSEUM_OBJECT.search(hay_text):
                    continue  # finds, coins and catalogue objects are not views of the place
                if named_site and not station_site and TRANSPORT_STOP.search(hay_text):
                    continue  # e.g. "St James's Park Station" is not St James's Park itself
                landmark_bonus = 2 if re.search(
                    r"\b(?:castle|church|landmark|town centre|council|civic|market|high street|harbour|park|station|street)\b",
                    hay_text,
                    flags=re.I,
                ) else 0
                landscape_bonus = 1 if width >= height else 0
                candidates.append((10 - search_rank + landmark_bonus + landscape_bonus, width * height, page, info, desc))
        except Exception:
            continue

    if candidates:
        _, _, page, info, desc = max(candidates, key=lambda row: (row[0], row[1]))
        meta = info.get("extmetadata") or {}
        title = page.get("title", "")
        artist = plain((meta.get("Artist") or {}).get("value", "")) or "Wikimedia Commons contributor"
        licence = plain((meta.get("LicenseShortName") or {}).get("value", ""))
        filename = title.removeprefix("File:")
        return {
            "src": info.get("thumburl") or info.get("url"),
            "page": "https://commons.wikimedia.org/wiki/File:" + quote(filename.replace(" ", "_"), safe="()_,.-"),
            "credit": " · ".join(x for x in (artist, licence) if x),
            "alt": desc or f"{town or place}, {county or 'England'}",
        }
    return None


def localise_weather_photo(photo: dict, kind: str) -> dict:
    src = str(photo.get("src") or "")
    if not src.startswith("https://"):
        raise ValueError(f"{kind} extreme has no downloadable place photo")
    response = requests.get(
        src,
        headers={**UA, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"},
        timeout=30,
    )
    response.raise_for_status()
    image = ImageOps.exif_transpose(Image.open(BytesIO(response.content))).convert("RGB")
    image = ImageOps.fit(image, (1600, 900), method=Image.Resampling.LANCZOS)
    WEATHER_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    output = WEATHER_IMAGE_DIR / f"{kind}.webp"
    image.save(output, "WEBP", quality=82, method=6)
    digest = hashlib.sha256(output.read_bytes()).hexdigest()[:12]
    result = dict(photo)
    result["src"] = f"assets/weather-extremes/{kind}.webp?v={digest}"
    result["width"] = 1600
    result["height"] = 900
    return result


def parse_extremes() -> dict | None:
    try:
        r = requests.get(EXTREMES_URL, headers=UA, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        headings = [h for h in soup.find_all(["h2", "h3", "h4"]) if h.get("id") in ENGLAND_REGION_IDS]
        if len(headings) != len(ENGLAND_REGION_IDS):
            raise ValueError("not all England regional extremes tables were found")

        hot_candidates, cold_candidates = [], []
        for heading in headings:
            table = heading.find_next("table")
            if not table:
                raise ValueError(f"England extremes table missing for {heading.get('id')}")
            values = {}
            for row in table.find_all("tr"):
                cell_nodes = row.find_all(["th", "td"])
                cells = [clean(c.get_text(" ", strip=True)) for c in cell_nodes]
                if len(cells) >= 3:
                    location_link = cell_nodes[1].find("a", href=True)
                    values[cells[0].lower()] = {
                        "location": cells[1],
                        "locationUrl": urljoin(EXTREMES_URL, location_link["href"]) if location_link else "",
                        "value": cells[2],
                    }
            if values.get("highest maximum temperature"):
                hot_candidates.append(values["highest maximum temperature"])
            if values.get("lowest minimum temperature"):
                cold_candidates.append(values["lowest minimum temperature"])

        def temperature(item: dict) -> float:
            match = re.search(r"-?\d+(?:\.\d+)?", item.get("value", ""))
            if not match:
                raise ValueError(f"temperature missing for {item.get('location', 'England location')}")
            return float(match.group())

        if not hot_candidates or not cold_candidates:
            raise ValueError("required England temperature extremes not found")
        hot = max(hot_candidates, key=temperature)
        cold = min(cold_candidates, key=temperature)

        date_heading = headings[0].find_previous("h2")
        date_label = clean(date_heading.get_text(" ", strip=True)) if date_heading else "Yesterday"

        def enrich(item: dict, kind: str) -> dict:
            loc = clean(item["location"])
            place = england_place(loc, item.get("locationUrl", ""))
            if not place:
                raise ValueError(f"England town/county could not be verified for {loc}")
            town, county = place
            remote_photo = exact_commons_photo(loc, town, county)
            if not remote_photo:
                raise ValueError(
                    f"No verified landmark, civic, town-centre or exact-place photo found for {town}, {county}"
                )
            return {
                "location": loc,
                "town": town,
                "county": county,
                "country": "England",
                "displayLocation": f"{town}, {county}",
                "value": clean(item["value"]).replace(" °C", "°C"),
                "photo": localise_weather_photo(remote_photo, kind),
            }

        return {
            "dateLabel": date_label,
            "source": "Met Office",
            "sourceUrl": EXTREMES_URL,
            "hot": enrich(hot, "hot"),
            "cold": enrich(cold, "cold"),
        }
    except Exception as exc:
        return {"source": "Met Office", "sourceUrl": EXTREMES_URL, "error": str(exc)}


def main() -> None:
    wx = met_weather()
    wx["yesterdayExtremes"] = parse_extremes()
    for name in ("pete", "sofia"):
        path = DATA / f"{name}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["weather"] = wx
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Met Office weather + England-only yesterday extremes applied to Pete and Sofia")


if __name__ == "__main__":
    main()
