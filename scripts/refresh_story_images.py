from __future__ import annotations

import hashlib
import html
import io
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "story-images.json"
UA = {"User-Agent": "Mozilla/5.0 DailyBriefs/5.0 (+https://github.com/PostWorkCulture/daily-briefs)"}
TARGET_PER_PROFILE_TAB = 4
MAX_IMAGE_BYTES = 12_000_000
VISUAL_HASH_DISTANCE = 5
SAM_ALTMAN = {
    "src": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Sam_Altman_speaking_at_TED.jpg/1280px-Sam_Altman_speaking_at_TED.jpg",
    "alt": "OpenAI CEO Sam Altman speaking on stage at TED",
    "pos": "center 32%",
    "credit": "Steve Jurvetson · CC BY 2.0 · Wikimedia Commons",
}


def norm_url(url: str) -> str:
    try:
        p = urlsplit(html.unescape(url or "").strip())
        ignored = {"w", "width", "h", "height", "q", "quality", "fit", "crop", "auto", "format", "fm", "dpr", "v", "ver", "version"}
        pairs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k.lower() not in ignored and not k.lower().startswith("utm_")]
        return urlunsplit((p.netloc.lower(), "", p.path.rstrip("/"), urlencode(sorted(pairs)), ""))
    except Exception:
        return re.sub(r"[?#].*$", "", str(url or "")).rstrip("/").lower()


def screenshot(url: str) -> str:
    return "https://image.thum.io/get/width/1200/crop/720/noanimate/" + url


def og_image(url: str) -> tuple[str | None, str | None]:
    try:
        r = requests.get(url, headers=UA, timeout=20, allow_redirects=True)
        r.raise_for_status()
        soup = BeautifulSoup(r.text[:2_500_000], "html.parser")
        title = None
        for key in ("og:title", "twitter:title"):
            tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
            if tag and tag.get("content"):
                title = tag.get("content").strip()
                break

        # Google News wrapper pages often expose Google's own generic artwork rather
        # than the publisher's story image. Never use that as an article image.
        final_host = urlsplit(r.url).netloc.lower()
        if "news.google.com" in final_host or (title and title.strip().lower() == "google news"):
            return None, title

        for key in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"):
            tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
            if not tag or not tag.get("content"):
                continue
            image = urljoin(r.url, html.unescape(tag.get("content").strip()))
            if not image.startswith("https://"):
                continue
            host = urlsplit(image).netloc.lower()
            if "google" in host or "gstatic" in host:
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


def image_fingerprint(url: str) -> tuple[str, int] | None:
    try:
        r = requests.get(url, headers={**UA, "Accept": "image/avif,image/webp,image/*,*/*;q=0.8"}, timeout=24)
        r.raise_for_status()
        data = r.content
        if not data or len(data) > MAX_IMAGE_BYTES:
            return None
        byte_hash = hashlib.sha256(data).hexdigest()
        with Image.open(io.BytesIO(data)) as im:
            visual_hash = dhash(im)
        return byte_hash, visual_hash
    except Exception:
        return None


def visually_used(fp: tuple[str, int] | None, used: list[tuple[str, int]]) -> bool:
    if not fp:
        return False
    byte_hash, visual_hash = fp
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
    fingerprint_cache: dict[str, tuple[str, int] | None] = {}

    def acceptable(rule: dict, profile_used: set[str]) -> tuple[bool, str, tuple[str, int] | None]:
        src = rule.get("src", "")
        key = norm_url(src)
        if not key or key in used_images or key in profile_used:
            return False, key, None
        if key not in fingerprint_cache:
            fingerprint_cache[key] = image_fingerprint(src)
        fp = fingerprint_cache[key]
        if visually_used(fp, used_fingerprints):
            return False, key, fp
        return True, key, fp

    for profile, payload in profiles.items():
        for tab, items in candidates(payload, profile).items():
            count = 0
            used_in_this_profile: set[str] = set()
            for item in items:
                if count >= TARGET_PER_PROFILE_TAB:
                    break
                url = item.get("url", "").strip()
                if not url:
                    continue
                if url in result:
                    # The same article may appear in both personal briefs. That is not
                    # image reuse across different articles, so keep the one canonical rule.
                    key = norm_url(result[url]["src"])
                    if key not in used_in_this_profile:
                        used_in_this_profile.add(key)
                        count += 1
                    continue

                hay = f"{item.get('title','')} {item.get('source','')} {url}".lower()
                proposals: list[dict] = []
                if "openai" in hay or "chatgpt" in hay:
                    proposals.append(dict(SAM_ALTMAN))

                if url not in metadata_cache:
                    metadata_cache[url] = og_image(url)
                image, page_title = metadata_cache[url]
                if image:
                    proposals.append({"src": image, "alt": page_title or item.get("title") or "Story image", "pos": "center"})

                # Exact linked-article screenshot is the final safe fallback: it can never
                # silently substitute an unrelated stock image for the story.
                proposals.append({"src": screenshot(url), "alt": item.get("title") or "Story image", "pos": "center"})

                chosen = None
                chosen_key = ""
                chosen_fp = None
                for rule in proposals:
                    ok, key, fp = acceptable(rule, used_in_this_profile)
                    if ok:
                        chosen, chosen_key, chosen_fp = rule, key, fp
                        break
                if not chosen:
                    continue

                result[url] = chosen
                used_images.add(chosen_key)
                used_in_this_profile.add(chosen_key)
                if chosen_fp:
                    used_fingerprints.append(chosen_fp)
                count += 1

    # Hard publish guards: one image field per article, no repeated normalised URLs,
    # and no visually duplicated image files where fingerprints are available.
    seen_urls = {}
    seen_fps: list[tuple[str, str, int]] = []
    for article_url, rule in result.items():
        src = rule.get("src") if isinstance(rule, dict) else None
        if not isinstance(src, str) or not src:
            raise SystemExit(f"invalid story image rule for {article_url}")
        key = norm_url(src)
        if key in seen_urls and seen_urls[key] != article_url:
            raise SystemExit(f"duplicate image URL assigned to {article_url} and {seen_urls[key]}")
        seen_urls[key] = article_url
        fp = fingerprint_cache.get(key)
        if fp:
            byte_hash, visual_hash = fp
            for prior_article, prior_byte, prior_visual in seen_fps:
                if byte_hash == prior_byte or hamming(visual_hash, prior_visual) <= VISUAL_HASH_DISTANCE:
                    raise SystemExit(f"visually duplicate image assigned to {article_url} and {prior_article}")
            seen_fps.append((article_url, byte_hash, visual_hash))

    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(result)} unique story image rules to {OUT}")


if __name__ == "__main__":
    main()
