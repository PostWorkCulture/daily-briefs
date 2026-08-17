from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Programme-first TV Picks. Every entry must name the actual programme and have
# a matching genuine artwork/still in js/tv-picks-artwork.js. Do not add vague
# article headlines here. The frontend will reject anything it cannot match.
PICKS = [
    {
        "title": "Silo",
        "summary": "Season three is currently rolling out weekly on Apple TV.",
        "meta": "Apple TV · Season 3",
        "source": "Apple TV",
        "url": "https://www.apple.com/uk/tv-pr/originals/silo/",
        "preferenceScore": 150,
    },
    {
        "title": "Murder Trial: Death of a Dog Walker",
        "summary": "BBC true-crime documentary following the Brian Low murder case and trial.",
        "meta": "BBC · True crime",
        "source": "BBC",
        "url": "https://www.womanandhome.com/life/news-entertainment/death-of-a-dog-walker-david-campbell-now/",
        "preferenceScore": 145,
    },
    {
        "title": "Spy Next Door: The Anna Chapman Story",
        "summary": "Channel 4 documentary about Russian spy Anna Chapman and the people caught in her orbit.",
        "meta": "Channel 4 · Documentary",
        "source": "Channel 4",
        "url": "https://www.theguardian.com/tv-and-radio/2026/aug/12/tv-tonight-fascinating-documentary-explores-the-rise-and-fall-of-a-russian-spy",
        "preferenceScore": 140,
    },
    {
        "title": "Mourinho",
        "summary": "New three-part Netflix documentary series on José Mourinho's career and contradictions.",
        "meta": "Netflix · 3 episodes",
        "source": "Netflix",
        "url": "https://about.netflix.com/en/news/limited-netflix-documentary-series-mourinho-reveals-trailer",
        "preferenceScore": 135,
    },
    {
        "title": "Conversations with a Killer: The Charles Manson Tapes",
        "summary": "Three-part Netflix docuseries built around rare audio and the Manson Family story.",
        "meta": "Netflix · True crime",
        "source": "Netflix",
        "url": "https://decider.com/2026/08/12/the-charles-manson-tapes-netflix-review/",
        "preferenceScore": 130,
    },
]


def main() -> None:
    for profile in ("pete", "sofia"):
        path = DATA / f"{profile}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["watch"] = [dict(item) for item in PICKS]
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("TV Picks: wrote 5 programme-first recommendations with exact programme identities")


if __name__ == "__main__":
    main()
