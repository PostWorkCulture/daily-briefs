from __future__ import annotations

import hashlib
import html
import io
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "story-images.json"
NEWS_IMAGE_DIR = ROOT / "assets" / "news-images"
NEWS_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
}
TARGET_PER_PROFILE_TAB = 30
MAX_IMAGE_BYTES = 15_000_000
MIN_WIDTH = 600
MIN_HEIGHT = 338
MIN_ASPECT = 1.15
MAX_ASPECT = 2.40

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

_GARTURLREQ_CTX = [
    ["X", "X", ["X", "X"], None, None, 1, 1, "US:en", None, 1, None, None, None, None, None, 0, 1],
    "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0,
]

SESSION = requests.Session()
SESSION.headers.update(UA)
SESSION.cookies.set("SOCS", "CAESHAgBEhJnd3NfMjAyNDA5MjQtMF9SQzEaAmVuIAEaBgiA_L22Bg", domain=".google.com")


def decode_google_news_url(url: str) -> str | None:
    """Resolve an opaque Google News redirect URL to its direct publisher source URL."""
    if "news.google.com" not in url:
        return url
    try:
        art_id = url.split("/articles/")[1].split("?")[0]
    except Exception:
        return None
    try:
        r = SESSION.get(url, allow_redirects=True, timeout=8)
        sg_m = re.search(r'data-n-a-sg="([^"]+)"', r.text)
        ts_m = re.search(r'data-n-a-ts="([^"]+)"', r.text)
        if not sg_m or not ts_m:
            return None
        sg, ts = sg_m.group(1), ts_m.group(1)
        inner = ["garturlreq", _GARTURLREQ_CTX, art_id, int(ts) if str(ts).isdigit() else ts, sg]
        envelope = [["Fbv4je", json.dumps(inner, separators=(",", ":")), None, "0"]]
        body = f"f.req={quote(json.dumps([envelope], separators=(',', ':')))}"
        headers = {
            "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
            "User-Agent": UA["User-Agent"],
        }
        resp = SESSION.post("https://news.google.com/_/DotsSplashUi/data/batchexecute", headers=headers, data=body, timeout=8)
        text = resp.text
        if "\n\n" in text:
            text = text.split("\n\n", 1)[1]
        text = text.lstrip()
        if text.startswith(")]}'"):
            text = text.split("\n", 1)[1] if "\n" in text else text[4:]
            text = text.lstrip()
        rows = json.loads(text)
        for row in rows:
            if isinstance(row, list) and len(row) >= 3 and (row[0] == "wrb.fr" or row[1] == "Fbv4je"):
                payload = row[2]
                if isinstance(payload, str):
                    payload = json.loads(payload)
                if isinstance(payload, list) and payload and payload[0] == "garturlres":
                    return payload[1]
    except Exception:
        return None
    return None


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
    return overlap >= 2 or overlap / max(1, min(len(article), len(page))) >= 0.35


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


def publisher_image(url: str, article_title: str) -> tuple[str | None, str | None, str | None]:
    """Return only the exact page's publisher-selected social image."""
    try:
        real_url = decode_google_news_url(url) or url
        final_host = urlsplit(real_url).netloc.lower()
        if "news.google.com" in final_host:
            return None, None, None
        response = SESSION.get(real_url, timeout=(4, 9), allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text[:2_500_000], "html.parser")
        page_title = meta_content(soup, "og:title", "twitter:title")
        if not page_title:
            page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
        if not title_relevant(article_title, page_title):
            return None, page_title, real_url
        image = meta_content(soup, "og:image", "og:image:secure_url", "twitter:image", "twitter:image:src")
        if not image:
            return None, page_title, real_url
        image = urljoin(response.url, image)
        if not image.startswith("https://") or banned_image_url(image):
            return None, page_title, real_url
        return image, page_title, real_url
    except Exception:
        return None, None, None


def optimize_and_cache_image(image_url: str, title: str) -> str | None:
    """Fetch, validate high quality landscape framing, and format to 1200x675 WebP."""
    try:
        if banned_image_url(image_url):
            return None
        response = SESSION.get(
            image_url,
            headers={"Accept": "image/avif,image/webp,image/*,*/*;q=0.8"},
            timeout=(4, 12),
        )
        response.raise_for_status()
        data = response.content
        if not data or len(data) > MAX_IMAGE_BYTES:
            return None
        with Image.open(io.BytesIO(data)) as raw_image:
            image = ImageOps.exif_transpose(raw_image)
            width, height = image.size
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                return None
            aspect = width / max(height, 1)
            if aspect < MIN_ASPECT or aspect > MAX_ASPECT:
                return None
            fitted = ImageOps.fit(
                image.convert("RGB"),
                (1200, 675),
                method=Image.Resampling.LANCZOS,
                centering=(0.5, 0.5),
            )
            buf = io.BytesIO()
            fitted.save(buf, format="WEBP", quality=85, method=6)
            webp_bytes = buf.getvalue()

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:45]
        digest = hashlib.sha256(webp_bytes).hexdigest()[:12]
        filename = f"{slug}-{digest[:8]}.webp"
        filepath = NEWS_IMAGE_DIR / filename
        filepath.write_bytes(webp_bytes)
        return f"assets/news-images/{filename}?v={digest}"
    except Exception:
        return None


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
    }


def main() -> None:
    profiles = {
        name: json.loads((DATA / f"{name}.json").read_text(encoding="utf-8"))
        for name in ("pete", "sofia")
        if (DATA / f"{name}.json").exists()
    }
    existing_map = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}

    all_current_articles = {
        str(item.get("url") or "").strip(): str(item.get("title") or "").strip()
        for payload in profiles.values()
        for group_name, items in (payload.get("sections") or {}).items()
        for item in (items or [])
        if str(item.get("url") or "").strip() and str(item.get("title") or "").strip()
    }
    for payload in profiles.values():
        for item in (payload.get("arsenal") or {}).get("news") or []:
            url = str(item.get("url") or "").strip()
            title = str(item.get("title") or "").strip()
            if url and title:
                all_current_articles[url] = title

    profile_tabs = {profile: candidates(payload, profile) for profile, payload in profiles.items()}
    articles = {
        str(item.get("url") or "").strip(): str(item.get("title") or "").strip()
        for tabs in profile_tabs.values()
        for items in tabs.values()
        for item in items
        if str(item.get("url") or "").strip() and str(item.get("title") or "").strip()
    }

    publisher_metadata: dict[str, tuple[str | None, str | None, str | None]] = {}
    pending_articles = {}
    for url, title in articles.items():
        if url in existing_map:
            rule = existing_map[url]
            src = rule.get("src", "").split("?")[0]
            if (ROOT / src).is_file() or src.startswith("http"):
                continue
        pending_articles[url] = title

    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {executor.submit(publisher_image, url, title): url for url, title in pending_articles.items()}
        for future in as_completed(futures):
            url = futures[future]
            try:
                publisher_metadata[url] = future.result()
            except Exception:
                publisher_metadata[url] = (None, None, None)

    result: dict[str, dict] = {}
    used_images: set[str] = set()

    for tabs in profile_tabs.values():
        for tab_name, items in tabs.items():
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

                if article_url in existing_map:
                    prior = existing_map[article_url]
                    src = prior.get("src", "").split("?")[0]
                    if ((ROOT / src).is_file() or src.startswith("http")) and src not in used_images:
                        result[article_url] = prior
                        used_images.add(src)
                        count += 1
                        continue

                image_url, page_title, real_url = publisher_metadata.get(article_url, (None, None, None))
                if not image_url or not page_title:
                    continue

                cached_src = optimize_and_cache_image(image_url, article_title)
                if not cached_src:
                    continue
                clean_src = cached_src.split("?")[0]
                if clean_src in used_images:
                    continue

                rule = {
                    "src": cached_src,
                    "alt": page_title,
                    "pos": "center",
                    "provenance": "publisher",
                    "matchedPageTitle": page_title,
                }
                result[article_url] = rule
                used_images.add(clean_src)
                count += 1

    # Prune any rules for articles that no longer exist in current edition
    valid_result = {
        url: rule for url, rule in result.items()
        if url in all_current_articles and rule.get("provenance") == "publisher"
    }

    OUT.write_text(json.dumps(valid_result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(valid_result)} exact publisher image rules to {OUT}; unmatched articles remain text-only")


if __name__ == "__main__":
    main()
