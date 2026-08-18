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
UA = {"User-Agent": "Mozilla/5.0 DailyBriefs/7.0 (+https://github.com/PostWorkCulture/daily-briefs)"}
TARGET_PER_PROFILE_TAB = 5
MAX_IMAGE_BYTES = 12_000_000
VISUAL_HASH_DISTANCE = 5
MIN_WIDTH = 1200
MIN_HEIGHT = 675
MIN_AREA = MIN_WIDTH * MIN_HEIGHT
MIN_ASPECT = 0.65
MAX_ASPECT = 3.0
BANNED_IMAGE_HINTS = (
    "favicon", "sprite", "logo", "brandmark", "avatar", "icon-", "/icon/",
    "placeholder", "default-image", "default_image", "generic", "fallback",
)
BANNED_IMAGE_HOSTS = ("image.thum.io", "upload.wikimedia.org", "unsplash.com", "pexels.com")
STOP = {
    "the", "and", "for", "with", "from", "that", "this", "into", "over", "after", "before",
    "about", "says", "say", "new", "latest", "live", "news", "report", "reports", "update",
    "updates", "why", "how", "what", "when", "where", "who", "its", "their", "his", "her",
    "our", "your", "more", "than", "has", "have", "had", "was", "were", "will", "would",
    "could", "should", "not", "out",
}


def norm_url(url: str) -> str:
    try:
        parsed = urlsplit(html.unescape(url or "").strip())
        ignored = {"w", "width", "h", "height", "q", "quality", "fit", "crop", "auto", "format", "fm", "dpr", "v", "ver", "version"}
        pairs = [
            (key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in ignored and not key.lower().startswith("utm_")
        ]
        return urlunsplit((parsed.netloc.lower(), "", parsed.path.rstrip("/"), urlencode(sorted(pairs)), ""))
    except Exception:
        return re.sub(r"[?#].*$", "", str(url or "")).rstrip("/").lower()


def title_tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", (value or "").lower()) if len(token) > 2 and token not in STOP}


def title_relevant(article_title: str, page_title: str | None) -> bool:
    if not page_title:
        return False
    article, page = title_tokens(article_title), title_tokens(page_title)
    if not article or not page:
        return False
    overlap = len(article & page)
    return overlap >= 2 or overlap / max(1, min(len(article), len(page))) >= 0.45


def banned_image_url(url: str) -> bool:
    low = html.unescape(url or "").lower()
    host = urlsplit(low).netloc
    return any(value in host for value in BANNED_IMAGE_HOSTS) or any(value in low for value in BANNED_IMAGE_HINTS)


def meta_content(soup: BeautifulSoup, *keys: str) -> str | None:
    for key in keys:
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            return html.unescape(tag.get("content").strip())
    return None


def publisher_image(url: str, article_title: str) -> tuple[str | None, str | None]:
    """Return only the exact page's publisher-selected social image.

    A matching publisher page is the provenance boundary. There is deliberately no
    topic search, stock library, Wikimedia, personality or tab-level fallback. If a
    publisher does not expose a matching article image, the card stays text-only.
    """
    try:
        response = requests.get(url, headers=UA, timeout=(4, 9), allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text[:2_500_000], "html.parser")
        page_title = meta_content(soup, "og:title", "twitter:title")
        if not page_title:
            page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
        final_host = urlsplit(response.url).netloc.lower()
        if "news.google.com" in final_host or page_title.strip().lower() == "google news":
            return None, page_title
        if not title_relevant(article_title, page_title):
            return None, page_title
        image = meta_content(soup, "og:image", "og:image:secure_url", "twitter:image", "twitter:image:src")
        if not image:
            return None, page_title
        image = urljoin(response.url, image)
        if not image.startswith("https://") or banned_image_url(image):
            return None, page_title
        return image, page_title
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


def hamming(first: int, second: int) -> int:
    return (first ^ second).bit_count()


def image_info(url: str) -> tuple[str, int, int, int] | None:
    try:
        if banned_image_url(url):
            return None
        response = requests.get(
            url,
            headers={**UA, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"},
            timeout=(4, 12),
        )
        response.raise_for_status()
        data = response.content
        if not data or len(data) > MAX_IMAGE_BYTES:
            return None
        with Image.open(io.BytesIO(data)) as image:
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            if width < MIN_WIDTH or height < MIN_HEIGHT or width * height < MIN_AREA:
                return None
            aspect = width / max(height, 1)
            if aspect < MIN_ASPECT or aspect > MAX_ASPECT:
                return None
            visual_hash = dhash(image)
        return hashlib.sha256(data).hexdigest(), visual_hash, width, height
    except Exception:
        return None


def visually_used(info: tuple[str, int, int, int], used: list[tuple[str, int]]) -> bool:
    byte_hash, visual_hash, _, _ = info
    return any(byte_hash == prior_byte or hamming(visual_hash, prior_visual) <= VISUAL_HASH_DISTANCE for prior_byte, prior_visual in used)


def unique(items: list[dict]) -> list[dict]:
    output, seen = [], set()
    for item in items:
        url = str((item or {}).get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        output.append(item)
    return output


def round_robin(groups: list[list[dict]]) -> list[dict]:
    groups = [unique(group) for group in groups if group]
    output, seen, index = [], set(), 0
    while groups:
        next_groups = []
        for group in groups:
            if index < len(group):
                item = group[index]
                url = item.get("url", "")
                if url and url not in seen:
                    seen.add(url)
                    output.append(item)
                next_groups.append(group)
        index += 1
        groups = [group for group in next_groups if index < len(group)]
    return output


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
    profiles = {
        name: json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))
        for name in ("pete", "sofia")
        if (DATA / f"{name}.json").exists()
    }
    profile_tabs = {profile: candidates(payload, profile) for profile, payload in profiles.items()}
    articles = {
        str(item.get("url") or "").strip(): str(item.get("title") or "").strip()
        for tabs in profile_tabs.values()
        for items in tabs.values()
        for item in items
        if str(item.get("url") or "").strip() and str(item.get("title") or "").strip()
    }

    publisher_metadata: dict[str, tuple[str | None, str | None]] = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(publisher_image, url, title): url for url, title in articles.items()}
        for future in as_completed(futures):
            url = futures[future]
            try:
                publisher_metadata[url] = future.result()
            except Exception:
                publisher_metadata[url] = (None, None)

    result: dict[str, dict] = {}
    used_urls: set[str] = set()
    used_fingerprints: list[tuple[str, int]] = []
    info_cache: dict[str, tuple[str, int, int, int] | None] = {}
    for tabs in profile_tabs.values():
        for items in tabs.values():
            count = 0
            for item in items:
                if count >= TARGET_PER_PROFILE_TAB:
                    break
                article_url = str(item.get("url") or "").strip()
                article_title = str(item.get("title") or "").strip()
                if not article_url or not article_title:
                    continue
                if article_url in result:
                    count += 1
                    continue
                image_url, page_title = publisher_metadata.get(article_url, (None, None))
                if not image_url or not page_title:
                    continue
                key = norm_url(image_url)
                if not key or key in used_urls:
                    continue
                if key not in info_cache:
                    info_cache[key] = image_info(image_url)
                info = info_cache[key]
                if not info or visually_used(info, used_fingerprints):
                    continue
                result[article_url] = {
                    "src": image_url,
                    "alt": page_title,
                    "pos": "center",
                    "provenance": "publisher",
                    "matchedPageTitle": page_title,
                }
                used_urls.add(key)
                used_fingerprints.append((info[0], info[1]))
                count += 1

    for article_url, rule in result.items():
        if rule.get("provenance") != "publisher" or not rule.get("matchedPageTitle"):
            raise SystemExit(f"non-publisher story image rule for {article_url}")
        if banned_image_url(str(rule.get("src") or "")):
            raise SystemExit(f"banned story image rule for {article_url}")

    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(result)} exact publisher image rules to {OUT}; unmatched articles remain text-only")


if __name__ == "__main__":
    main()
