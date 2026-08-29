from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


LONDON = ZoneInfo("Europe/London")
PROFILES = ("pete", "sofia")


def published_date(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return ""
    return str((data.get("worldFact") or {}).get("date") or "")


def should_run_refresh(event_name: str, now: datetime, root: Path) -> tuple[bool, str]:
    if event_name != "schedule":
        return True, f"{event_name or 'manual'} event"

    london_now = now.astimezone(LONDON)
    if london_now.hour < 6:
        return False, f"before 06:00 Europe/London ({london_now:%H:%M})"

    today = london_now.date().isoformat()
    stale = [
        profile
        for profile in PROFILES
        if published_date(root / "data" / f"{profile}.json") != today
    ]
    if stale:
        return True, f"stale profiles for {today}: {', '.join(stale)}"
    return False, f"today's {today} brief is already published"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    now = datetime.now(LONDON)
    should_run, reason = should_run_refresh(os.environ.get("EVENT_NAME", ""), now, root)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as handle:
            handle.write(f"should_run={'true' if should_run else 'false'}\n")
    print(f"Refresh gate: {'run' if should_run else 'skip'} because {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
