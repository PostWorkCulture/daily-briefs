from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "story-images.json"
UA = {"User-Agent": "Mozilla/5.0 DailyBriefs/5.0 (+https://github.com/PostWorkCulture/daily-briefs)"}
TARGET_PER_PROFILE_TAB = 4
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

        # Google News wrapper pages commonly expose Google's own generic artwork rather
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
            # Reject Google-hosted wrapper/tracking artwork. Exact-article screenshots
            # are a safer fallback than unrelated or generic publisher imagery.
            if "google" in host or "gstatic" in host:
                continue
            return image, title
        return None, title
    except Exception:
        return None, None


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
    metadata_cache: dict[str, tuple[str | None, str | None]] = {}

    for profile, payload in profiles.items():
        for tab, items in candidates(payload, profile).items():
            count = 0
            used_in_this_profile: set[str] = set()
            for item in items:
                if count >= TARGET_PER_PROFILE_TAB:
                    break
                url = item.get("url", "").strip()
                if not url or url in result:
                    # Existing rule is safe to reuse only for the same article URL.
                    if url in result and norm_url(result[url]["src"]) not in used_in_this_profile:
                        used_in_this_profile.add(norm_url(result[url]["src"]))
                        count += 1
                    continue

                hay = f"{item.get('title','')} {item.get('source','')} {url}".lower()
                rule = None
                # The approved OpenAI treatment: use Sam Altman speaking once, never
                # recycle that photo for another story in the same brief.
                sam_key = norm_url(SAM_ALTMAN["src"])
                if ("openai" in hay or "chatgpt" in hay) and sam_key not in used_images and sam_key not in used_in_this_profile:
                    rule = dict(SAM_ALTMAN)
                else:
                    if url not in metadata_cache:
                        metadata_cache[url] = og_image(url)
                    image, page_title = metadata_cache[url]
                    if image:
                        key = norm_url(image)
                        if key not in used_images and key not in used_in_this_profile:
                            rule = {"src": image, "alt": page_title or item.get("title") or "Story image", "pos": "center"}
                    if not rule:
                        # Exact linked-article screenshot fallback. This is deliberately
                        # preferred to unrelated stock art and is unique per article URL.
                        image = screenshot(url)
                        key = norm_url(image)
                        if key not in used_images and key not in used_in_this_profile:
                            rule = {"src": image, "alt": item.get("title") or "Story image", "pos": "center"}

                if not rule:
                    continue
                key = norm_url(rule["src"])
                if key in used_images or key in used_in_this_profile:
                    continue
                result[url] = rule
                used_images.add(key)
                used_in_this_profile.add(key)
                count += 1

    # Hard publish guard: max one src per article and no image URL reuse across
    # different article URLs in the generated map.
    seen = {}
    for article_url, rule in result.items():
        src = rule.get("src") if isinstance(rule, dict) else None
        if not isinstance(src, str) or not src:
            raise SystemExit(f"invalid story image rule for {article_url}")
        key = norm_url(src)
        if key in seen and seen[key] != article_url:
            raise SystemExit(f"duplicate image assigned to {article_url} and {seen[key]}")
        seen[key] = article_url

    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(result)} unique story image rules to {OUT}")


if __name__ == "__main__":
    main()
