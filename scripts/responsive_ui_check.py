from __future__ import annotations

import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:4173/pete/"
VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1366, "height": 900},
}


def check_viewport(page, name: str) -> None:
    page.set_viewport_size(VIEWPORTS[name])
    page.goto(BASE_URL, wait_until="networkidle")
    page.locator('[data-view-target="arsenal"]').click()
    page.locator('#nextFixtureCard.fixture-detail-card').wait_for(state="visible")

    result = page.evaluate(
        """
        () => {
          const card = document.querySelector('#nextFixtureCard.fixture-detail-card');
          const cardRect = card.getBoundingClientRect();
          const selectors = [
            '#nextFixtureCard.fixture-detail-card > strong',
            '#nextFixtureCard .fixture-fact',
            '#nextFixtureCard .fixture-fact > span',
            '#nextFixtureCard .fixture-fact > b',
            '#nextFixtureCard .fixture-fact > small'
          ];
          const offenders = [];
          for (const selector of selectors) {
            for (const el of document.querySelectorAll(selector)) {
              const r = el.getBoundingClientRect();
              if (r.right > cardRect.right + 1 || r.left < cardRect.left - 1) {
                offenders.push({selector, text: el.textContent.trim(), left: r.left, right: r.right});
              }
            }
          }
          return {
            viewportWidth: window.innerWidth,
            pageScrollWidth: document.documentElement.scrollWidth,
            cardClientWidth: card.clientWidth,
            cardScrollWidth: card.scrollWidth,
            offenders
          };
        }
        """
    )

    failures = []
    if result["pageScrollWidth"] > result["viewportWidth"] + 1:
        failures.append(
            f"page horizontal overflow: {result['pageScrollWidth']} > {result['viewportWidth']}"
        )
    if result["cardScrollWidth"] > result["cardClientWidth"] + 1:
        failures.append(
            f"next fixture card overflow: {result['cardScrollWidth']} > {result['cardClientWidth']}"
        )
    if result["offenders"]:
        failures.append(f"fixture descendants escape card: {result['offenders']}")

    if failures:
        raise AssertionError(f"{name}: " + " | ".join(failures))
    print(f"PASS {name}: next fixture fits viewport and card")


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            for name in VIEWPORTS:
                check_viewport(page, name)
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RESPONSIVE CHECK FAILED: {exc}", file=sys.stderr)
        raise
