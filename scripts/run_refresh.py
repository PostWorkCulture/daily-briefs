"""Resilient morning refresh orchestrator.

Runs the same pipeline as before (refresh.py, weather, Arsenal, next fixture,
TV Picks, story images) but no single component can stop publication. When a
step fails, or the protected-rule validator rejects the data it produced, that
component alone is carried forward from the last published edition and the
rest of the brief is published fresh. Every carried component is recorded in
``refreshStatus`` (both profiles) and ``data/refresh-status.json`` so the
failure is visible and the validator can waive only that component's
same-day freshness rule.

Hard failures remain only where carrying forward would itself break a
protected rule: the Around-the-world fact history (no repeats) and a previous
edition that is missing or unreadable.

Usage: python scripts/run_refresh.py [--skip-validate]
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCRIPTS = ROOT / "scripts"
TZ = ZoneInfo("Europe/London")
PROFILES = ("pete", "sofia")
STEP_TIMEOUT = int(os.getenv("REFRESH_STEP_TIMEOUT", "600"))
MAX_VALIDATION_REPAIRS = 8

LAST_RESULT_FIELDS = ("result", "scorersLabel", "competition", "summary", "kickoff", "stadium")
NEXT_FIXTURE_FIELDS = ("opponent", "stadium", "kickoff", "competition", "tvChannel")

# Validator assertion text -> component to carry forward. Order matters: the
# first matching pattern wins.
VALIDATION_COMPONENT_PATTERNS = (
    (r"TV Pick", "watch"),
    (r"extreme|weather", "weather"),
    (r"Arsenal last result|lastResult", "arsenal.lastResult"),
    (r"Arsenal next fixture", "arsenal.nextFixture"),
    (r"Premier League position", "arsenal.leaguePosition"),
    (r"Reporter watch|X reporter", "arsenal.transferRumours"),
    (r"transfer", "arsenal.transfers"),
    (r"Arsenal first-team news", "sections.Arsenal news"),
    (r"section content bleed: (?P<section>[^:]+?):", "sections.{section}"),
    (r"Local News", "sections.Local news"),
    (r"UK News", "sections.UK news"),
    (r"family activity", "sections.Fun"),
    (r"\bimage\b|\bstory image", "storyImages"),
)


def log(message: str) -> None:
    print(f"[run_refresh] {message}", flush=True)


def notice(title: str, message: str) -> None:
    # GitHub Actions annotation; harmless plain text elsewhere.
    print(f"::notice title={title}::{message}", flush=True)


def warning(title: str, message: str) -> None:
    print(f"::warning title={title}::{message}", flush=True)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_profiles() -> dict[str, dict]:
    return {name: read_json(DATA / f"{name}.json") for name in PROFILES}


def save_profiles(profiles: dict[str, dict]) -> None:
    for name, payload in profiles.items():
        write_json(DATA / f"{name}.json", payload)


class Previous:
    """The last published edition, captured before anything is rewritten."""

    def __init__(self, data_dir: Path = DATA) -> None:
        self.profiles = {name: read_json(data_dir / f"{name}.json") for name in PROFILES}
        images = data_dir / "story-images.json"
        self.story_images = read_json(images) if images.exists() else {}
        history = data_dir / "tv-picks-history.json"
        self.tv_history = read_json(history) if history.exists() else {"days": []}

    def arsenal(self) -> dict:
        return deepcopy(self.profiles["pete"].get("arsenal") or {})


class Status:
    def __init__(self, today: str) -> None:
        self.today = today
        self.carried: dict[str, str] = {}
        self.topped_up: dict[str, str] = {}
        self.failed_steps: dict[str, str] = {}

    def carry(self, component: str, reason: str) -> None:
        reason = re.sub(r"\s+", " ", str(reason)).strip()[:400]
        if component not in self.carried:
            self.carried[component] = reason
            warning("Carried forward", f"{component}: {reason}")

    def as_dict(self) -> dict:
        return {
            "date": self.today,
            "degraded": bool(self.carried),
            "carriedForward": dict(self.carried),
            "toppedUpSections": dict(self.topped_up),
            "failedSteps": dict(self.failed_steps),
        }


def run_script(name: str, env_extra: dict | None = None) -> tuple[bool, str]:
    """Run a pipeline script in its own interpreter; return (ok, error text)."""
    env = {**os.environ, "PYTHONUTF8": "1", **(env_extra or {})}
    try:
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / name)],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=STEP_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, f"{name} timed out after {STEP_TIMEOUT}s"
    if proc.stdout.strip():
        print(proc.stdout.rstrip(), flush=True)
    if proc.returncode == 0:
        return True, ""
    tail = "\n".join((proc.stderr or "").strip().splitlines()[-6:])
    return False, f"{name} exited {proc.returncode}: {tail or 'no error output'}"


# --------------------------------------------------------------------------
# Carry-forward restores. Each takes the fresh profiles and the previous
# edition and puts one component back the way it was last published.
# --------------------------------------------------------------------------

def restore_weather(profiles: dict[str, dict], previous: Previous) -> None:
    for name in PROFILES:
        prev = previous.profiles[name].get("weather")
        if prev:
            profiles[name]["weather"] = deepcopy(prev)


def restore_arsenal_key(profiles: dict[str, dict], previous: Previous, key: str) -> None:
    arsenal = profiles["pete"].setdefault("arsenal", {})
    prev = previous.arsenal()
    if key == "leaguePosition":
        for field in ("leaguePosition", "points", "played"):
            if prev.get(field) is not None:
                arsenal[field] = prev[field]
        return
    if prev.get(key) is not None:
        arsenal[key] = deepcopy(prev[key])


def restore_section(profiles: dict[str, dict], previous: Previous, section: str) -> None:
    for name in PROFILES:
        prev_sections = previous.profiles[name].get("sections") or {}
        if section in prev_sections:
            profiles[name].setdefault("sections", {})[section] = deepcopy(prev_sections[section])
    if section == "Arsenal news":
        prev_news = previous.arsenal().get("news")
        if prev_news is not None:
            profiles["pete"].setdefault("arsenal", {})["news"] = deepcopy(prev_news)


def restore_watch(profiles: dict[str, dict], previous: Previous) -> None:
    for name in PROFILES:
        for key in ("watch", "watchAlternatives"):
            prev = previous.profiles[name].get(key)
            if prev is not None:
                profiles[name][key] = deepcopy(prev)
    write_json(DATA / "tv-picks-history.json", previous.tv_history)


def current_article_urls(profiles: dict[str, dict]) -> set[str]:
    urls: set[str] = set()
    for payload in profiles.values():
        for items in (payload.get("sections") or {}).values():
            urls.update(str(item.get("url") or "").strip() for item in items or [])
        urls.update(str(item.get("url") or "").strip() for item in (payload.get("arsenal") or {}).get("news") or [])
    urls.discard("")
    return urls


def restore_story_images(profiles: dict[str, dict], previous: Previous) -> None:
    """Keep only previous publisher image rules that still point at a current article."""
    current = current_article_urls(profiles)
    seen: set[str] = set()
    kept = {}
    for url, rule in previous.story_images.items():
        src = str((rule or {}).get("src") or "")
        key = src.split("#", 1)[0]
        if url in current and rule.get("provenance") == "publisher" and src and key not in seen:
            if not src.startswith("http") and not (ROOT / src.split("?")[0]).is_file():
                continue
            kept[url] = rule
            seen.add(key)
    write_json(DATA / "story-images.json", kept)


def restore_component(component: str, profiles: dict[str, dict], previous: Previous) -> bool:
    if component == "weather":
        restore_weather(profiles, previous)
    elif component.startswith("arsenal."):
        restore_arsenal_key(profiles, previous, component.split(".", 1)[1])
    elif component.startswith("sections."):
        restore_section(profiles, previous, component.split(".", 1)[1])
    elif component == "watch":
        restore_watch(profiles, previous)
    elif component == "storyImages":
        restore_story_images(profiles, previous)
    else:
        return False
    return True


# --------------------------------------------------------------------------
# Component checks run after each step, so a step that exits 0 but leaves a
# component incomplete is caught before the validator.
# --------------------------------------------------------------------------

def incomplete_fields(record: dict | None, fields: tuple[str, ...]) -> list[str]:
    record = record or {}
    return [key for key in fields if not str(record.get(key) or "").strip()]


def fixture_is_current(fixture: dict | None, now: datetime) -> bool:
    try:
        return datetime.fromisoformat(str((fixture or {}).get("date") or "")) >= now - timedelta(hours=3)
    except ValueError:
        return False


def check_arsenal(profiles: dict[str, dict], previous: Previous, status: Status, now: datetime) -> None:
    arsenal = profiles["pete"].get("arsenal") or {}
    last = arsenal.get("lastResult") or {}
    missing = incomplete_fields(last, LAST_RESULT_FIELDS)
    if not isinstance(last.get("scorers"), list):
        missing.append("scorers")
    if missing:
        status.carry("arsenal.lastResult", f"latest result incomplete ({', '.join(missing)})")
        restore_arsenal_key(profiles, previous, "lastResult")

    fixture = arsenal.get("nextFixture")
    missing = incomplete_fields(fixture, NEXT_FIXTURE_FIELDS)
    if not fixture or missing or not fixture_is_current(fixture, now):
        prev_fixture = previous.arsenal().get("nextFixture")
        if prev_fixture and fixture_is_current(prev_fixture, now) and not incomplete_fields(prev_fixture, NEXT_FIXTURE_FIELDS):
            status.carry("arsenal.nextFixture", f"next fixture unavailable or incomplete ({', '.join(missing) or 'stale'})")
            restore_arsenal_key(profiles, previous, "nextFixture")
        elif not fixture and prev_fixture:
            # Nothing fresh at all: keep the last known card rather than an empty one.
            status.carry("arsenal.nextFixture", "no fixture from any source; showing last known fixture")
            restore_arsenal_key(profiles, previous, "nextFixture")
        elif missing:
            status.carry("arsenal.nextFixture", f"next fixture missing {', '.join(missing)}; no verified previous card")

    position = arsenal.get("leaguePosition")
    if not (isinstance(position, int) and 1 <= position <= 20):
        status.carry("arsenal.leaguePosition", "league table unavailable")
        restore_arsenal_key(profiles, previous, "leaguePosition")


def check_watch(profiles: dict[str, dict], previous: Previous, status: Status) -> None:
    picks = profiles["pete"].get("watch") or []
    fresh = len(picks) == 5 and all(p.get("generatedDate") == status.today for p in picks)
    if not fresh:
        status.carry("watch", "TV Picks could not be rebuilt for today")
        restore_watch(profiles, previous)


def check_weather(profiles: dict[str, dict], previous: Previous, status: Status) -> None:
    wx = profiles["pete"].get("weather") or {}
    ext = wx.get("yesterdayExtremes") or {}
    ok = wx.get("source") == "Met Office" and ext.get("source") == "Met Office" and not ext.get("error")
    if ok:
        return
    status.carry("weather", f"Met Office data incomplete ({ext.get('error') or 'forecast or extremes missing'})")
    restore_weather(profiles, previous)
    save_profiles(profiles)
    # Second source for the live forecast: the lightweight Met Office refresh,
    # which keeps the previous day's extremes block intact.
    ok2, err = run_script("refresh_weather_only.py")
    refreshed = load_profiles() if ok2 else {}
    live = (refreshed.get("pete") or {}).get("weather") or {}
    if ok2 and live.get("temp") not in (None, "", "—") and live.get("daily"):
        for name in PROFILES:
            profiles[name]["weather"] = refreshed[name].get("weather") or profiles[name]["weather"]
        log("live Met Office forecast refreshed; yesterday's extremes carried forward")
    else:
        log(f"forecast fallback unavailable ({err or 'blank forecast'}); previous forecast kept")
        save_profiles(profiles)


# --------------------------------------------------------------------------
# Core edition fallback when refresh.py itself cannot run.
# --------------------------------------------------------------------------

def core_fallback(previous: Previous, status: Status, now: datetime) -> dict[str, dict]:
    sys.path.insert(0, str(ROOT))
    from scripts import refresh as core  # noqa: WPS433 (deliberate late import)

    world_fact = core.world_fact_for_today()
    core.cache_world_fact_image(world_fact)
    calendar = core.calendar_events()
    stamp = core.safe_strftime(now, "%A, %-d %B %Y · refreshed %-I:%M%p").replace("AM", "am").replace("PM", "pm")
    profiles = {}
    for name in PROFILES:
        payload = deepcopy(previous.profiles[name])
        payload["updatedLabel"] = stamp
        payload["worldFact"] = world_fact
        if calendar:
            payload["calendar"] = calendar
        profiles[name] = payload
    for section in sorted({s for p in profiles.values() for s in (p.get("sections") or {})}):
        status.carry(f"sections.{section}", "refresh.py failed; previous edition's stories kept")
    return profiles


# --------------------------------------------------------------------------
# Validator loop: any component the validator rejects is carried forward and
# the validator runs again, until it passes or nothing more can be carried.
# --------------------------------------------------------------------------

def component_for_validation_error(message: str) -> str | None:
    for pattern, component in VALIDATION_COMPONENT_PATTERNS:
        match = re.search(pattern, message, re.I)
        if match:
            return component.format(**{k: v.strip() for k, v in match.groupdict().items()})
    return None


def validation_error() -> str | None:
    ok, err = run_script("validate_brief.py")
    if ok:
        return None
    match = re.search(r"AssertionError: (.*)$", err, re.M)
    return match.group(1).strip() if match else err


def write_status(profiles: dict[str, dict], status: Status) -> None:
    snapshot = status.as_dict()
    for payload in profiles.values():
        payload["refreshStatus"] = snapshot
    save_profiles(profiles)
    write_json(DATA / "refresh-status.json", snapshot)


def validate_with_repairs(profiles: dict[str, dict], previous: Previous, status: Status) -> None:
    for _ in range(MAX_VALIDATION_REPAIRS):
        write_status(profiles, status)
        message = validation_error()
        if message is None:
            return
        component = component_for_validation_error(message)
        if component is None or component in status.carried:
            raise SystemExit(f"Validation failed and cannot be repaired by carrying forward: {message}")
        log(f"validator rejected {component}: {message}")
        if not restore_component(component, profiles, previous):
            raise SystemExit(f"Validation failed: {message}")
        status.carry(component, f"validator: {message}")
    raise SystemExit("Validation still failing after the maximum number of repairs")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    now = datetime.now(TZ)
    status = Status(now.date().isoformat())
    previous = Previous()
    log(f"previous edition: pete {previous.profiles['pete'].get('worldFact', {}).get('date')}")

    ok, err = run_script("refresh.py")
    if ok:
        profiles = load_profiles()
        # refresh.py records sections it topped up from the previous edition.
        for section, reason in ((profiles["pete"].get("refreshStatus") or {}).get("carriedSections") or {}).items():
            status.topped_up[section] = reason
            warning("Section topped up", f"{section}: {reason}")
    else:
        status.failed_steps["refresh.py"] = err
        warning("refresh.py failed", err)
        profiles = core_fallback(previous, status, now)
    save_profiles(profiles)

    # Weather
    ok, err = run_script("enrich_weather_v2.py")
    if not ok:
        status.failed_steps["enrich_weather_v2.py"] = err
    profiles = load_profiles()
    check_weather(profiles, previous, status)
    save_profiles(profiles)

    # Arsenal chain
    for script in ("enrich_arsenal.py", "finalize_arsenal.py", "enrich_next_fixture.py"):
        ok, err = run_script(script)
        if not ok:
            status.failed_steps[script] = err
    profiles = load_profiles()
    check_arsenal(profiles, previous, status, now)
    save_profiles(profiles)

    # TV Picks
    ok, err = run_script("enrich_tv_picks.py")
    if not ok:
        status.failed_steps["enrich_tv_picks.py"] = err
    profiles = load_profiles()
    check_watch(profiles, previous, status)
    save_profiles(profiles)

    # Story images (already per-article tolerant; only a crash needs handling)
    ok, err = run_script("refresh_story_images.py")
    if not ok:
        status.failed_steps["refresh_story_images.py"] = err
        status.carry("storyImages", err)
        restore_story_images(profiles, previous)

    for script, err in status.failed_steps.items():
        warning("Step failed", f"{script}: {err}")

    if "--skip-validate" in argv:
        write_status(profiles, status)
    else:
        validate_with_repairs(profiles, previous, status)

    summary = status.as_dict()
    if summary["degraded"]:
        notice("Refresh published with carried-forward components", json.dumps(summary["carriedForward"], ensure_ascii=False))
    else:
        notice("Refresh complete", "all components fresh")
    log(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
