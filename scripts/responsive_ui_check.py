from __future__ import annotations

import sys
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:4173/?profile=pete&locked=1"
VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1366, "height": 900},
}


def check_viewport(browser, name: str) -> None:
    page = browser.new_page(viewport=VIEWPORTS[name])
    page.set_default_timeout(10000)
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        page.locator("#greeting").wait_for(state="visible", timeout=10000)
        greeting = page.locator("#greeting")
        if greeting.inner_text() != "Hey Pete":
            raise AssertionError(f"{name}: Pete greeting is not 'Hey Pete'")
        max_greeting_px = 52 if name == "mobile" else 68
        greeting_size = float(greeting.evaluate("el => parseFloat(getComputedStyle(el).fontSize)"))
        if greeting_size > max_greeting_px:
            raise AssertionError(
                f"{name}: greeting is too large ({greeting_size}px > {max_greeting_px}px)"
            )
        page.locator('[data-profile="sofia"]').click()
        page.wait_for_function(
            "document.querySelector('#greeting')?.textContent === 'Hey Sofia'"
        )
        page.locator('[data-profile="pete"]').click()
        page.wait_for_function(
            "document.querySelector('#greeting')?.textContent === 'Hey Pete'"
        )
        page.wait_for_timeout(1200)
        icon_links = page.locator('link[rel="icon"]')
        if icon_links.count() < 3:
            raise AssertionError(f"{name}: expected ICO, 32px and 192px Daily Brief icons")
        if page.locator('link[rel="apple-touch-icon"][sizes="180x180"]').count() != 1:
            raise AssertionError(f"{name}: Daily Brief Apple touch icon is missing")
        if page.locator('link[rel="manifest"]').count() != 1:
            raise AssertionError(f"{name}: Daily Brief web app manifest is missing")
        calendar_cards = page.locator('#calendarSummaryCards button')
        if calendar_cards.count() != 4:
            raise AssertionError(f"{name}: expected four Calendar summary cards")
        calendar_cards.first.hover()
        calendar_shadow = calendar_cards.first.evaluate("el => getComputedStyle(el).boxShadow")
        if calendar_shadow == "none":
            raise AssertionError(f"{name}: Calendar card has no edge-glow hover")

        page.locator('[data-view-target="arsenal"]').click()
        page.locator('#nextFixtureCard.fixture-detail-card').wait_for(state="visible", timeout=10000)
        page.locator('#arsenalTransfers').wait_for(state="visible", timeout=10000)
        page.locator('.arsenal-rumour-head').wait_for(state="visible", timeout=10000)
        page.locator('#arsenalTransferRumours').wait_for(state="visible", timeout=10000)
        for selector in ('#lastResultCard', '#nextFixtureCard', '#leagueCard', '.arsenal-news-item'):
            locator = page.locator(selector).first
            if locator.count():
                locator.hover()
                if locator.evaluate("el => getComputedStyle(el).boxShadow") == "none":
                    raise AssertionError(f"{name}: {selector} has no Arsenal red edge glow")

        result = page.evaluate(
            """
            () => {
              const card = document.querySelector('#nextFixtureCard.fixture-detail-card');
              const cardRect = card.getBoundingClientRect();
              const nav = document.querySelector('#primaryNav');
              const navRect = nav.getBoundingClientRect();
              const navButtons = [...nav.querySelectorAll('button')]
                .map(button => ({text: button.innerText.trim(), rect: button.getBoundingClientRect()}))
                .filter(item => item.rect.width > 0 && item.rect.height > 0);
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
                offenders,
                nav: {
                  width: navRect.width,
                  height: navRect.height,
                  buttons: navButtons.map(item => ({
                    text: item.text,
                    left: item.rect.left,
                    right: item.rect.right,
                    top: item.rect.top,
                    bottom: item.rect.bottom,
                    width: item.rect.width,
                    target: button.dataset.viewTarget || null
                  }))
                }
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

        nav = result["nav"]
        buttons = nav["buttons"]
        expected_nav_targets = [
            "home",
            "news",
            "arsenal",
            "ai",
            "career",
            "dida",
            "birthdays",
        ]
        actual_nav_targets = [button["target"] for button in buttons]
        if actual_nav_targets != expected_nav_targets:
            failures.append(
                f"Pete nav targets changed: {actual_nav_targets} != {expected_nav_targets}"
            )
        if any(button["width"] < 44 for button in buttons):
            failures.append(f"nav buttons squeezed below 44px: {buttons}")
        if name == "desktop":
            if len({round(button["left"]) for button in buttons}) != 1:
                failures.append(f"desktop nav is not a single vertical column: {buttons}")
            if len({round(button["top"]) for button in buttons}) != len(buttons):
                failures.append(f"desktop nav buttons overlap vertically: {buttons}")
        else:
            if len({round(button["top"]) for button in buttons}) != 1:
                failures.append(f"mobile nav is not a single horizontal row: {buttons}")

        page.locator('[data-view-target="dida"]').click()
        page.locator('.dida-hero').wait_for(state="visible", timeout=10000)
        dida = page.evaluate(
            """
            () => ({
              accent: getComputedStyle(document.querySelector('.dida-shell')).getPropertyValue('--dida').trim(),
              heroIcons: document.querySelectorAll('.dida-hero-icons span').length,
              quickIcons: document.querySelectorAll('.dida-quick-icon').length,
              foldIcons: document.querySelectorAll('.dida-fold-icon').length
            })
            """
        )
        if dida["accent"].lower() != "#b7ff3c":
            failures.append(f"Dida accent is not lime green: {dida['accent']}")
        if dida["heroIcons"] < 3 or dida["quickIcons"] < 3 or dida["foldIcons"] < 4:
            failures.append(f"Dida fun icon treatment is incomplete: {dida}")

        if failures:
            raise AssertionError(f"{name}: " + " | ".join(failures))
        print(f"PASS {name}: Pete/Sofia greetings, Daily Brief icons, fixture, navigation, Calendar glow, Arsenal trusted/reporter-watch lists and lime Dida treatment are usable")
    finally:
        page.close()


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for name in VIEWPORTS:
                check_viewport(browser, name)
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"RESPONSIVE CHECK FAILED: {exc}", file=sys.stderr)
        raise
