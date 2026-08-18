from __future__ import annotations

import hashlib
import html
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "story-images.json"
UA = {"User-Agent": "Mozilla/5.0 DailyBriefs/6.0 (+https://github.com/PostWorkCulture/daily-briefs)"}
TARGET_PER_PROFILE_TAB = 5
MAX_IMAGE_BYTES = 12_000_000
VISUAL_HASH_DISTANCE = 5
MIN_WIDTH = 1200
MIN_HEIGHT = 675
MIN_AREA = 900_000
MIN_ASPECT = 1.15
MAX_ASPECT = 2.45
BANNED_IMAGE_HINTS = ("favicon", "sprite", "logo", "brandmark", "avatar", "icon-", "/icon/", "placeholder", "default-image", "default_image")
BANNED_IMAGE_HOSTS = ("image.thum.io",)
STOP = {
    "the", "and", "for", "with", "from", "that", "this", "into", "over", "after", "before", "about", "says", "say", "new", "latest", "live", "news", "report", "reports", "update", "updates", "why", "how", "what", "when", "where", "who", "its", "their", "his", "her", "our", "your", "more", "than", "has", "have", "had", "was", "were", "will", "would", "could", "should", "not", "out"
}
SAM_ALTMAN = {
    "src": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Sam_Altman_speaking_at_TED.jpg/1280px-Sam_Altman_speaking_at_TED.jpg",
    "alt": "OpenAI CEO Sam Altman speaking on stage at TED",
    "pos": "center 32%",
    "credit": "Steve Jurvetson · CC BY 2.0 · Wikimedia Commons",
    "curated": True,
}
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
CURATED_TAB_QUERIES = {
    "news": (
        "Stockholm Sweden waterfront", "London skyline England", "Palace of Westminster London",
        "British newspaper press", "Surrey England landscape", "Sweden city street", "London street scene",
    ),
    "arsenal": (
        "Emirates Stadium Arsenal", "football stadium crowd England", "football pitch goal",
        "association football match England", "football boots ball", "football supporters stadium",
    ),
    "ai": (
        "artificial intelligence computer", "data centre servers", "semiconductor wafer",
        "neural network visualization", "robot technology", "computer circuit board", "machine learning data",
    ),
    "career": (
        "London office team", "business meeting office", "financial data screen",
        "product management whiteboard", "remote work laptop", "Stockholm office", "professional team collaboration",
    ),
}


def clean_text(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        BeautifulSoup(html.unescape(value or ""), "html.parser").get_text(" ", strip=True),
    ).strip()


def norm_url(url: str) -> str:
    try:
        p = urlsplit(html.unescape(url or "").strip())
        ignored = {"w", "width", "h", "height", "q", "quality", "fit", "crop", "auto", "format", "fm", "dpr", "v", "ver", "version"}
        pairs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in ignored and not k.lower().startswith("utm_")]
        return urlunsplit((p.netloc.lower(), "", p.path.rstrip("/"), urlencode(sorted(pairs)), ""))
    except Exception:
        return re.sub(r"[?#].*$", "", str(url or "")).rstrip("/").lower()


def title_tokens(value: str) -> set[str]:
    return {x for x in re.findall(r"[a-z0-9]+", (value or "").lower()) if len(x) > 2 and x not in STOP}


def title_relevant(article_title: str, page_title: str | None) -> bool:
    if not page_title:
        return False
    a, b = title_tokens(article_title), title_tokens(page_title)
    if not a or not b:
        return False
    overlap = len(a & b)
    return overlap >= 2 or overlap / max(1, min(len(a), len(b))) >= 0.45


def banned_image_url(url: str) -> bool:
    low = html.unescape(url or "").lower()
    host = urlsplit(low).netloc
    return any(x in host for x in BANNED_IMAGE_HOSTS) or any(x in low for x in BANNED_IMAGE_HINTS)


def og_image(url: str, article_title: str) -> tuple[str | None, str | None]:
    try:
        r = requests.get(url, headers=UA, timeout=(4, 8), allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text[:2_500_000], "html.parser")
        title = None
        for key in ("og:title", "twitter:title"):
            tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
            if tag and tag.get("content"):
                title = tag.get("content").strip()
                break
        if not title:
            title = clean = (soup.title.get_text(" ", strip=True) if soup.title else "")
        final_host = urlsplit(r.url).netloc.lower()
        if "news.google.com" in final_host or (title and title.strip().lower() == "google news"):
            return None, title
        if not title_relevant(article_title, title):
            return None, title
        for key in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"):
            tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
            if not tag or not tag.get("content"):
                continue
            image = urljoin(r.url, html.unescape(tag.get("content").strip()))
            if not image.startswith("https://") or banned_image_url(image):
                continue
            return image, title
        return None, title
    except Exception:
        return None, None


def dhash(image: Image.Image) -> int:
    image = ImageOps.exif_transpose(image).convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    pixels = list(image.getdata())
    value = 0
    for row in range(8):
        base = row * 9
        for col in range(8):
            value = (value << 1) | int(pixels[base + col] > pixels[base + col + 1])
    return value


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def image_info(url: str) -> tuple[str, int, int, int] | None:
    try:
        if banned_image_url(url):
            return None
        r = requests.get(url, headers={**UA, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"}, timeout=(4, 12))
        r.raise_for_status()
        data = r.content
        if not data or len(data) > MAX_IMAGE_BYTES:
            return None
        with Image.open(io.BytesIO(data)) as im:
            im = ImageOps.exif_transpose(im)
            width, height = im.size
            if width < MIN_WIDTH or height < MIN_HEIGHT or width * height < MIN_AREA:
                return None
            aspect = width / max(height, 1)
            if aspect < MIN_ASPECT or aspect > MAX_ASPECT:
                return None
            visual_hash = dhash(im)
        return hashlib.sha256(data).hexdigest(), visual_hash, width, height
    except Exception:
        return None


def commons_images(query: str) -> list[dict]:
    try:
        response = requests.get(
            COMMONS_API,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": query,
                "gsrnamespace": 6,
                "gsrlimit": 6,
                "prop": "imageinfo",
                "iiprop": "url|size|extmetadata",
                "iiurlwidth": 1600,
                "format": "json",
                "origin": "*",
            },
            headers=UA,
            timeout=(4, 12),
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages", {})
    except Exception:
        return []

    results = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        width, height = int(info.get("width") or 0), int(info.get("height") or 0)
        if width < MIN_WIDTH or height < MIN_HEIGHT:
            continue
        src = info.get("thumburl") or info.get("url")
        if not src or banned_image_url(src):
            continue
        meta = info.get("extmetadata") or {}
        artist = clean_text((meta.get("Artist") or {}).get("value", ""))
        licence = clean_text((meta.get("LicenseShortName") or {}).get("value", ""))
        credit = " · ".join(x for x in (artist, licence, "Wikimedia Commons") if x)
        title = clean_text(page.get("title", "").removeprefix("File:"))
        results.append({"src": src, "alt": f"Supporting image: {title}", "pos": "center", "credit": credit})
    return results


def visually_used(info: tuple[str, int, int, int] | None, used: list[tuple[str, int]]) -> bool:
    if not info:
        return False
    byte_hash, visual_hash, _, _ = info
    return any(byte_hash == prior_byte or hamming(visual_hash, prior_visual) <= VISUAL_HASH_DISTANCE for prior_byte, prior_visual in used)


def unique(items: list[dict]) -> list[dict]:
    out, seen = [], set()
    for item in items:
        url = (item or {}).get("url", "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(item)
    return out


def round_robin(groups: list[list[dict]]) -> list[dict]:
    groups = [unique(g) for g in groups if g]
    out, seen, i = [], set(), 0
    while groups:
        next_groups = []
        for group in groups:
            if i < len(group):
                item = group[i]
                url = item.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    out.append(item)
                next_groups.append(group)
        i += 1
        groups = [g for g in next_groups if i < len(g)]
    return out


def candidates(payload: dict, profile: str) -> dict[str, list[dict]]:
    sections = payload.get("sections") or {}
    news_groups = []
    if profile == "sofia":
        news_groups.append(sections.get("Sweden") or [])
    news_groups.extend([sections.get("Local news") or [], sections.get("UK news") or []])
    arsenal = []
    if profile == "pete":
        arsenal.extend((payload.get("arsenal") or {}).get("news") or [])
        arsenal.extend(sections.get("Arsenal news") or [])
    return {
        "news": round_robin(news_groups),
        "arsenal": unique(arsenal),
        "ai": unique(sections.get("AI") or []),
        "career": unique(sections.get("Career") or []),
    }


def main() -> None:
    profiles = {}
    for name in ("pete", "sofia"):
        path = DATA / f"{name}.json"
        if path.exists():
            profiles[name] = json.loads(path.read_text(encoding="utf-8"))

    result: dict[str, dict] = {}
    used_images: set[str] = set()
    used_fingerprints: list[tuple[str, int]] = []
    metadata_cache: dict[str, tuple[str | None, str | None]] = {}
    info_cache: dict[str, tuple[str, int, int, int] | None] = {}
    commons_cache: dict[str, list[dict]] = {}

    profile_tabs = {profile: candidates(payload, profile) for profile, payload in profiles.items()}
    article_lookups = {
        item.get("url", "").strip(): item.get("title", "").strip()
        for tabs in profile_tabs.values()
        for items in tabs.values()
        for item in items
        if item.get("url", "").strip() and item.get("title", "").strip()
    }
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(og_image, url, title): url for url, title in article_lookups.items()}
        for future in as_completed(futures):
            url = futures[future]
            try:
                metadata_cache[url] = future.result()
            except Exception:
                metadata_cache[url] = (None, None)

    all_queries = sorted({query for queries in CURATED_TAB_QUERIES.values() for query in queries})
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(commons_images, query): query for query in all_queries}
        for future in as_completed(futures):
            query = futures[future]
            try:
                commons_cache[query] = future.result()
            except Exception:
                commons_cache[query] = []

    def acceptable(rule: dict, profile_used: set[str]) -> tuple[bool, str, tuple[str, int, int, int] | None]:
        src = rule.get("src", "")
        key = norm_url(src)
        if not key or key in used_images or key in profile_used or banned_image_url(src):
            return False, key, None
        if key not in info_cache:
            info_cache[key] = image_info(src)
        info = info_cache[key]
        if not info or visually_used(info, used_fingerprints):
            return False, key, info
        return True, key, info

    for profile, tabs in profile_tabs.items():
        for tab, items in tabs.items():
            count = 0
            used_in_this_profile: set[str] = set()
            for item in items:
                if count >= TARGET_PER_PROFILE_TAB:
                    break
                url = item.get("url", "").strip()
                title = item.get("title", "").strip()
                if not url or not title:
                    continue
                if url in result:
                    key = norm_url(result[url]["src"])
                    if key not in used_in_this_profile:
                        used_in_this_profile.add(key)
                        count += 1
                    continue

                hay = f"{title} {item.get('source','')} {url}".lower()
                proposals: list[dict] = []
                if "openai" in hay or "chatgpt" in hay:
                    proposals.append(dict(SAM_ALTMAN))

                image, page_title = metadata_cache.get(url, (None, None))
                if image:
                    proposals.append({"src": image, "alt": page_title or title, "pos": "center"})

                for query in CURATED_TAB_QUERIES.get(tab, ()):
                    proposals.extend(commons_cache.get(query, ()))

                chosen = None
                chosen_key = ""
                chosen_info = None
                for rule in proposals:
                    ok, key, info = acceptable(rule, used_in_this_profile)
                    if ok:
                        chosen, chosen_key, chosen_info = rule, key, info
                        break
                if not chosen:
                    continue

                chosen.pop("curated", None)
                result[url] = chosen
                used_images.add(chosen_key)
                used_in_this_profile.add(chosen_key)
                if chosen_info:
                    used_fingerprints.append((chosen_info[0], chosen_info[1]))
                count += 1

    seen_urls = {}
    seen_fps: list[tuple[str, str, int]] = []
    for article_url, rule in result.items():
        src = rule.get("src") if isinstance(rule, dict) else None
        if not isinstance(src, str) or not src or banned_image_url(src):
            raise SystemExit(f"invalid or banned story image rule for {article_url}")
        key = norm_url(src)
        if key in seen_urls and seen_urls[key] != article_url:
            raise SystemExit(f"duplicate image URL assigned to {article_url} and {seen_urls[key]}")
        seen_urls[key] = article_url
        info = info_cache.get(key)
        if not info:
            raise SystemExit(f"story image failed quality validation for {article_url}")
        byte_hash, visual_hash, _, _ = info
        for prior_article, prior_byte, prior_visual in seen_fps:
            if byte_hash == prior_byte or hamming(visual_hash, prior_visual) <= VISUAL_HASH_DISTANCE:
                raise SystemExit(f"visually duplicate image assigned to {article_url} and {prior_article}")
        seen_fps.append((article_url, byte_hash, visual_hash))

    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(result)} premium unique article image rules, targeting {TARGET_PER_PROFILE_TAB} per profile tab, to {OUT}")


if __name__ == "__main__":
    main()
