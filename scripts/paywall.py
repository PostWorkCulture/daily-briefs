"""Reject articles from publishers that lock stories behind a subscription paywall.

Pete's rule (28 October 2026): no article that appears anywhere in the brief may be
paywalled. Google News items only carry the publisher name (their URL is a
news.google.com redirect), so both the publisher name and the destination domain
are checked. Keep this list in sync with PAYWALLED_* in js/app.js.
"""
from __future__ import annotations

import re
from urllib.parse import urlparse

# Publisher names as they appear in Google News / RSS "source" fields (lower case).
PAYWALLED_PUBLISHERS = frozenset({
    "financial times", "ft", "ft.com", "ft adviser", "sifted",
    "the times", "times", "the sunday times", "the times & the sunday times", "thetimes.com", "thetimes.co.uk",
    "the telegraph", "telegraph", "the daily telegraph", "daily telegraph", "telegraph.co.uk",
    "the wall street journal", "wall street journal", "wsj", "wsj.com", "barron's", "barrons", "marketwatch",
    "bloomberg", "bloomberg.com", "bloomberg law", "bloomberg businessweek", "businessweek",
    "the economist", "economist",
    "the information",
    "the athletic", "the new york times", "new york times", "nytimes", "nytimes.com",
    "the washington post", "washington post",
    "breakingviews", "reuters breakingviews", "reuters", "reuters.com",
    "business insider", "insider", "fortune", "harvard business review", "hbr",
    "the atlantic", "the new yorker", "wired", "wired uk",
    "nikkei asia", "nikkei", "south china morning post", "scmp",
    "handelsblatt", "le monde", "les echos", "le figaro",
    "the australian", "australian financial review", "afr", "the globe and mail",
    "the spectator", "new statesman", "haaretz", "foreign policy", "foreign affairs",
    "investor's business daily", "seeking alpha", "puck", "stratechery", "mlex",
    "politico pro", "axios pro",
    "dagens nyheter", "dn", "svenska dagbladet", "svd", "göteborgs-posten", "goteborgs-posten",
    "dagens industri", "di", "sydsvenskan",
})

# Registrable domains whose articles are paywalled. Subdomains match too.
PAYWALLED_DOMAINS = (
    "ft.com", "sifted.eu", "reuters.com", "thetimes.com", "thetimes.co.uk", "telegraph.co.uk",
    "wsj.com", "barrons.com", "marketwatch.com", "bloomberg.com", "economist.com",
    "theinformation.com", "theathletic.com", "nytimes.com", "washingtonpost.com",
    "businessinsider.com", "insider.com", "fortune.com", "hbr.org", "theatlantic.com",
    "newyorker.com", "wired.com", "wired.co.uk", "nikkei.com", "scmp.com",
    "handelsblatt.com", "lemonde.fr", "lesechos.fr", "lefigaro.fr", "theaustralian.com.au",
    "afr.com", "theglobeandmail.com", "spectator.co.uk", "newstatesman.com", "haaretz.com",
    "foreignpolicy.com", "foreignaffairs.com", "investors.com", "seekingalpha.com",
    "puck.news", "stratechery.com", "mlex.com", "dn.se", "svd.se", "gp.se", "di.se", "sydsvenskan.se",
)
# Paywalled sections of otherwise free sites.
PAYWALLED_URL_PATHS = (
    re.compile(r"^https?://(?:www\.)?reuters\.com/breakingviews/", re.I),
    re.compile(r"^https?://(?:www\.)?nytimes\.com/athletic/", re.I),
    re.compile(r"^https?://(?:www\.)?nationalgeographic\.com/(?:magazine|premium)/", re.I),
)
PAYWALL_TITLE_MARKERS = re.compile(
    r"\((?:paywall|subscription required|subscriber[s]? only|premium)\)|\b(?:subscriber[- ]only|for subscribers)\b",
    re.I,
)
# Publishers sometimes append their name to the headline: "Headline - Financial Times".
TITLE_SUFFIX = re.compile(r"\s+[-|–]\s+([^-|–]{2,60})$")


def _normal(name: str) -> str:
    return re.sub(r"\s+", " ", str(name or "").replace("’", "'")).strip().casefold()


def paywalled_url(url: str) -> bool:
    url = str(url or "").strip()
    if not url:
        return False
    if any(pattern.search(url) for pattern in PAYWALLED_URL_PATHS):
        return True
    host = (urlparse(url).hostname or "").casefold()
    return any(host == domain or host.endswith("." + domain) for domain in PAYWALLED_DOMAINS)


def is_paywalled(item: dict) -> bool:
    """True when an article comes from a subscription-paywalled publisher or page."""
    if not isinstance(item, dict):
        return False
    if _normal(item.get("source")) in PAYWALLED_PUBLISHERS:
        return True
    for key in ("url", "link", "sourceUrl"):
        if paywalled_url(item.get(key)):
            return True
    title = str(item.get("title") or "")
    if PAYWALL_TITLE_MARKERS.search(title):
        return True
    suffix = TITLE_SUFFIX.search(title)
    return bool(suffix and _normal(suffix.group(1)) in PAYWALLED_PUBLISHERS - {"ft", "dn", "di", "insider", "times"})


def without_paywalled(items: list[dict] | None) -> list[dict]:
    return [item for item in (items or []) if not is_paywalled(item)]
