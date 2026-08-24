from __future__ import annotations

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:4173/?profile=pete&locked=1"
VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1366, "height": 900},
}
ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ICON_PATHS = {
    "shortcut": "assets/icons/daily-brief-favicon-v2.ico",
    "ico": "assets/icons/daily-brief-favicon-v2.ico",
    "small": "assets/icons/daily-brief-favicon-32-v2.png",
    "large": "assets/icons/daily-brief-192-v2.png",
    "touch": "assets/icons/daily-brief-touch-v2.png",
    "manifest": "daily-brief-v2.webmanifest",
}


def check_icon_metadata_files() -> None:
    expected_root = tuple(ICON_PATHS.values())
    root_html = (ROOT / "index.html").read_text(encoding="utf-8")
    if 'class="brand hero-brand"' in root_html:
        raise AssertionError("visible Daily Briefs wordmark remains in the hero")
    for value in expected_root:
        if value not in root_html:
            raise AssertionError(f"root icon metadata is missing {value}")

    for profile in ("pete", "sofia"):
        profile_html = (ROOT / profile / "index.html").read_text(encoding="utf-8")
        for value in expected_root:
            if f"../{value}" not in profile_html:
                raise AssertionError(f"{profile} icon metadata is missing ../{value}")

    manifest = json.loads((ROOT / ICON_PATHS["manifest"]).read_text(encoding="utf-8"))
    manifest_icons = {item.get("src") for item in manifest.get("icons", [])}
    expected_manifest_icons = {
        "assets/icons/daily-brief-192-v2.png",
        "assets/icons/daily-brief-512-v2.png",
        "assets/icons/daily-brief-maskable-512-v2.png",
    }
    if manifest.get("name") != "Daily Briefs" or manifest_icons != expected_manifest_icons:
        raise AssertionError(f"bookmark manifest metadata is incorrect: {manifest}")

    reminders = (ROOT / "js" / "home-reminders.js").read_text(encoding="utf-8")
    theme = (ROOT / "css" / "light-theme.css").read_text(encoding="utf-8")
    if "theme: 'halloween'" not in reminders or ".home-reminder-card.festive.halloween{background:#ffc27a}" not in theme:
        raise AssertionError("Halloween does not have its dedicated solid pastel orange treatment")


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
        expected_links = {
            'link[rel="shortcut icon"]': ICON_PATHS["shortcut"],
            'link[rel="icon"][type="image/x-icon"]': ICON_PATHS["ico"],
            'link[rel="icon"][sizes="32x32"]': ICON_PATHS["small"],
            'link[rel="icon"][sizes="192x192"]': ICON_PATHS["large"],
            'link[rel="apple-touch-icon"]': ICON_PATHS["touch"],
            'link[rel="manifest"]': ICON_PATHS["manifest"],
        }
        for selector, expected_href in expected_links.items():
            link = page.locator(selector)
            if link.count() != 1 or link.get_attribute("href") != expected_href:
                raise AssertionError(
                    f"{name}: bookmark metadata {selector} does not use {expected_href}"
                )
            asset_url = page.evaluate(
                "path => new URL(path, document.baseURI).href", expected_href
            )
            response = page.request.get(asset_url)
            if not response.ok or not response.body():
                raise AssertionError(
                    f"{name}: bookmark asset did not load from {expected_href}"
                )

        decoded_icons = page.evaluate(
            """
            paths => Promise.all(paths.map(path => new Promise(resolve => {
              const image = new Image();
              image.onload = () => resolve({
                path,
                width: image.naturalWidth,
                height: image.naturalHeight,
              });
              image.onerror = () => resolve({path, width: 0, height: 0});
              image.src = path;
            })))
            """,
            [ICON_PATHS["small"], ICON_PATHS["large"], ICON_PATHS["touch"]],
        )
        expected_dimensions = {
            ICON_PATHS["small"]: (32, 32),
            ICON_PATHS["large"]: (192, 192),
            ICON_PATHS["touch"]: (180, 180),
        }
        for icon in decoded_icons:
            if (icon["width"], icon["height"]) != expected_dimensions[icon["path"]]:
                raise AssertionError(f"{name}: bookmark icon failed to decode: {icon}")
        icon_links = page.locator('link[rel="icon"]')
        if icon_links.count() < 3:
            raise AssertionError(f"{name}: expected ICO, 32px and 192px Daily Brief icons")
        if page.locator('link[rel="apple-touch-icon"][sizes="180x180"]').count() != 1:
            raise AssertionError(f"{name}: Daily Brief Apple touch icon is missing")
        if page.locator('link[rel="manifest"]').count() != 1:
            raise AssertionError(f"{name}: Daily Brief web app manifest is missing")
        birthday_balloon = page.locator('[data-view-target="birthdays"] .nav-balloon')
        balloon_count = birthday_balloon.count()
        if balloon_count != 1:
            nav_html = page.locator('#primaryNav').evaluate('el => el.outerHTML')
            raise AssertionError(
                f"{name}: Birthdays nav does not use one balloon icon "
                f"(found {balloon_count}); nav DOM: {nav_html}"
            )
        arsenal_cannon = page.locator('[data-view-target="arsenal"] .nav-cannon')
        if arsenal_cannon.count() != 1:
            raise AssertionError(f"{name}: Arsenal nav cannon is missing")
        if arsenal_cannon.locator('.cannon-barrel').count() != 1 or arsenal_cannon.locator('.cannon-wheel').count() != 1:
            raise AssertionError(f"{name}: Arsenal nav cannon is not the approved barrel-and-wheel mark")

        for target in ("ai", "career"):
            page.locator(f'[data-view-target="{target}"]').click()
            cards = page.locator(f'#view-{target} .tab-story')
            icons = page.locator(f'#view-{target} .section-story-icon')
            if cards.count() < 1 or icons.count() != cards.count():
                raise AssertionError(
                    f"{name}: {target} cards do not consistently use section icons"
                )
            if page.locator(f'#view-{target} .story-media').count() != 0:
                raise AssertionError(f"{name}: {target} still shows article photography")

        page.locator('[data-view-target="home"]').click()
        calendar_cards = page.locator('#calendarSummaryCards button')
        if calendar_cards.count() != 4:
            raise AssertionError(f"{name}: expected four Calendar summary cards")
        calendar_cards.first.hover()
        page.wait_for_timeout(250)
        calendar_shadow = calendar_cards.first.evaluate("el => getComputedStyle(el).boxShadow")
        if calendar_shadow == "none":
            raise AssertionError(f"{name}: Calendar card has no edge-glow hover")

        page.locator('[data-view-target="career"]').click()
        career_card = page.locator('#view-career .tab-story').first
        career_card.hover()
        page.wait_for_timeout(250)
        career_shadow = career_card.evaluate("el => getComputedStyle(el).boxShadow")
        career_transform = career_card.evaluate("el => getComputedStyle(el).transform")
        if career_shadow != calendar_shadow or career_transform != "none":
            raise AssertionError(
                f"{name}: Career hover does not match Calendar glow or moves: "
                f"shadow={career_shadow}, transform={career_transform}"
            )

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
                .map(button => ({
                  text: button.innerText.trim(),
                  target: button.dataset.viewTarget || null,
                  rect: button.getBoundingClientRect()
                }))
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
                fixtureText: card.innerText,
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
                    target: item.target
                  }))
                }
              };
            }
            """
        )

        failures = []
        visual = page.evaluate(
            r"""
            () => {
              const htmlStyle = getComputedStyle(document.documentElement);
              const bodyStyle = getComputedStyle(document.body);
              const topbarStyle = getComputedStyle(document.querySelector('.topbar'));
              const rgb = htmlStyle.backgroundColor.match(/\d+(?:\.\d+)?/g)?.slice(0, 3).map(Number) || [0, 0, 0];
              const fact = document.querySelector('#sceneryFact');
              const image = document.querySelector('#sceneryCard');
              const greeting = document.querySelector('#greeting');
              const date = document.querySelector('#briefDate');
              const nav = document.querySelector('#primaryNav');
              const buttons = [...nav.querySelectorAll('button')];
              const reminderCards = [...document.querySelectorAll('#homeReminders .home-reminder-card')];
              return {
                bodyRgb: rgb,
                bodyBackgroundImage: bodyStyle.backgroundImage,
                bodyBackgroundColor: bodyStyle.backgroundColor,
                topbarBackgroundColor: topbarStyle.backgroundColor,
                factBeforeImage: Boolean(fact.compareDocumentPosition(image) & Node.DOCUMENT_POSITION_FOLLOWING),
                factText: document.querySelector('#sceneryFactText')?.textContent?.trim() || '',
                factHref: fact?.getAttribute('href') || '',
                factLabel: document.querySelector('#sceneryFactLabel')?.textContent?.trim() || '',
                greetingMarginTop: parseFloat(getComputedStyle(greeting).marginTop),
                greetingColour: getComputedStyle(greeting).color,
                dateColour: getComputedStyle(date).color,
                heroBrandCount: document.querySelectorAll('.hero .hero-brand').length,
                topbarBrandCount: document.querySelectorAll('.topbar .brand').length,
                navDefaultColours: buttons.map(button => getComputedStyle(button).color),
                mainCopyColours: [
                  '.section-kicker',
                  '.forecast-day small',
                  '.calendar-row p',
                  '#sceneryFactText',
                  '#nextFixtureCard .fixture-fact>b',
                  '#nextFixtureCard .fixture-fact>small'
                ].map(selector => ({
                  selector,
                  colour: document.querySelector(selector)
                    ? getComputedStyle(document.querySelector(selector)).color
                    : null
                })),
                reminderCards: reminderCards.map(card => ({
                  classes: card.className,
                  backgroundImage: getComputedStyle(card).backgroundImage,
                  backgroundColour: getComputedStyle(card).backgroundColor,
                  textColours: [...card.querySelectorAll('.home-reminder-top,strong,b,small')]
                    .map(node => getComputedStyle(node).color)
                })),
                navAfter: getComputedStyle(nav, '::after').content,
                buttonAfter: buttons.map(button => getComputedStyle(button, '::after').content),
                navText: nav.textContent
              };
            }
            """
        )
        if visual["bodyRgb"] != [120, 183, 224]:
            failures.append(f"solid blue canvas changed: {visual['bodyRgb']}")
        if visual["bodyBackgroundImage"] != "none":
            failures.append(
                f"page canvas is not solid: {visual['bodyBackgroundImage']}"
            )
        if visual["bodyBackgroundColor"] != "rgb(120, 183, 224)" or visual["topbarBackgroundColor"] != "rgb(120, 183, 224)":
            failures.append(
                "body or topbar does not use the solid blue canvas: "
                f"body={visual['bodyBackgroundColor']}, topbar={visual['topbarBackgroundColor']}"
            )
        if not visual["factBeforeImage"]:
            failures.append("insane fact does not appear before its image")
        if not visual["factText"] or visual["factText"].startswith("Loading"):
            failures.append("daily world fact did not render")
        if not visual["factHref"].startswith("https://"):
            failures.append("daily world fact has no verified source link")
        if not visual["factLabel"].startswith("Insane fact of the day"):
            failures.append(f"fact lead label changed: {visual['factLabel']}")
        if visual["greetingMarginTop"] < 16:
            failures.append(f"greeting was not moved down: margin {visual['greetingMarginTop']}")
        if visual["heroBrandCount"] != 0 or visual["topbarBrandCount"] != 0:
            failures.append("visible Daily Briefs wordmark remains")
        approved_ink = "rgb(20, 42, 61)"
        if visual["greetingColour"] != approved_ink or visual["dateColour"] != approved_ink:
            failures.append(
                f"greeting or date does not use the approved ink: {visual}"
            )
        if any(colour != approved_ink for colour in visual["navDefaultColours"]):
            failures.append(f"navigation is coloured before hover: {visual['navDefaultColours']}")
        wrong_main_copy = [
            item for item in visual["mainCopyColours"]
            if item["colour"] is not None and item["colour"] != approved_ink
        ]
        if wrong_main_copy:
            failures.append(f"main copy does not match the greeting ink: {wrong_main_copy}")
        if len(visual["reminderCards"]) < 4:
            failures.append(f"Coming up cards are missing: {visual['reminderCards']}")
        expected_reminder_colours = {
            "bin": "rgb(216, 242, 230)",
            "clocks": "rgb(228, 225, 248)",
            "new-year": "rgb(214, 234, 248)",
            "midsummer": "rgb(255, 240, 168)",
            "halloween": "rgb(255, 194, 122)",
            "bonfire": "rgb(255, 214, 176)",
            "christmas": "rgb(244, 213, 221)",
            "birthday": "rgb(255, 193, 220)",
        }
        for required_theme in ("bin", "clocks", "birthday"):
            if not any(required_theme in card["classes"].split() for card in visual["reminderCards"]):
                failures.append(f"Coming up {required_theme} card is missing: {visual['reminderCards']}")
        festive_cards = [card for card in visual["reminderCards"] if "festive" in card["classes"].split()]
        if len(festive_cards) != 1:
            failures.append(f"Coming up festive card is missing or duplicated: {visual['reminderCards']}")
        for theme, expected_colour in expected_reminder_colours.items():
            matching = [card for card in visual["reminderCards"] if theme in card["classes"].split()]
            if not matching:
                continue
            if len(matching) != 1:
                failures.append(f"Coming up {theme} card is duplicated: {visual['reminderCards']}")
                continue
            card = matching[0]
            if card["backgroundImage"] != "none" or card["backgroundColour"] != expected_colour:
                failures.append(f"Coming up {theme} card is not solid pastel {expected_colour}: {card}")
            if any(colour != approved_ink for colour in card["textColours"]):
                failures.append(f"Coming up {theme} text does not match the greeting: {card}")
        if visual["navAfter"] not in {"none", '""'}:
            failures.append(f"navigation star layer remains: {visual['navAfter']}")
        if any(content not in {"none", '""'} for content in visual["buttonAfter"]):
            failures.append(f"navigation button sparkle remains: {visual['buttonAfter']}")
        if any(mark in visual["navText"] for mark in ("✦", "★", "☆", "✨")):
            failures.append("navigation still contains a star or sparkle glyph")

        news_nav = page.locator('[data-view-target="news"]')
        news_nav.hover()
        page.wait_for_timeout(250)
        if news_nav.evaluate("el => getComputedStyle(el).color") != "rgb(38, 91, 187)":
            failures.append("News navigation colour does not appear on hover")

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
        required_fixture_copy = (
            "Aston Villa",
            "Mon 31 Aug",
            "8:00pm",
            "Villa Park",
            "Sky Sports",
            "Arsenal 4–1 Aston Villa",
        )
        if any(value not in result["fixtureText"] for value in required_fixture_copy):
            failures.append(
                f"upcoming Arsenal fixture is stale or incomplete: {result['fixtureText']}"
            )

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

        for profile in ("pete", "sofia"):
            page.locator(f'.profile-switch [data-profile="{profile}"]').click()
            page.wait_for_function(
                f"document.querySelector('#greeting')?.textContent === 'Hey {profile.title()}'"
            )
            page.locator('[data-view-target="news"]').click()
            news_groups = page.evaluate(
                """
                () => [...document.querySelectorAll('#newsTabGroups .tab-group')].map(group => ({
                  title: group.querySelector('h3')?.textContent.trim() || '',
                  top: group.getBoundingClientRect().top,
                  bottom: group.getBoundingClientRect().bottom
                }))
                """
            )
            news_titles = [group["title"] for group in news_groups]
            news_copy_colours = page.evaluate(
                """
                () => [...document.querySelectorAll('#newsTabGroups .tab-story h4,#newsTabGroups .tab-story p,#newsTabGroups .tab-story .meta')]
                  .map(node => getComputedStyle(node).color)
                """
            )
            if any(colour != approved_ink for colour in news_copy_colours):
                failures.append(f"{profile} News copy does not match the greeting ink: {news_copy_colours}")
            try:
                local_index = news_titles.index("Local News")
                uk_index = news_titles.index("UK News")
            except ValueError:
                failures.append(f"{profile} News is missing Local News or UK News: {news_titles}")
            else:
                if uk_index != local_index + 1 or news_groups[uk_index]["top"] < news_groups[local_index]["bottom"]:
                    failures.append(f"{profile} UK News is not directly underneath Local News: {news_groups}")
            page.locator('[data-view-target="birthdays"]').click()
            page.locator('.birthday-card').first.wait_for(state="visible", timeout=10000)
            birthday = page.evaluate(
                r"""
                () => {
                  const parseRgb = value => value.match(/\d+(?:\.\d+)?/g)?.slice(0,3).map(Number) || [0,0,0];
                  const stops = value => [...value.matchAll(/rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)/g)]
                    .map(match => match.slice(1,4).map(Number));
                  const luminance = rgb => {
                    const values = rgb.map(value => value / 255).map(
                      value => value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
                    );
                    return 0.2126 * values[0] + 0.7152 * values[1] + 0.0722 * values[2];
                  };
                  const contrast = (a, b) => {
                    const values = [luminance(a), luminance(b)].sort((x, y) => y - x);
                    return (values[0] + 0.05) / (values[1] + 0.05);
                  };
                  const inspect = card => {
                    const backgroundStops = stops(getComputedStyle(card).backgroundImage);
                    const backgroundColour = parseRgb(getComputedStyle(card).backgroundColor);
                    const surfaces = backgroundStops.length ? backgroundStops : [backgroundColour];
                    const textNodes = [card.querySelector('strong'), card.querySelector('small'), card.querySelector('b')].filter(Boolean);
                    const ratios = textNodes.flatMap(node => surfaces.map(stop => contrast(parseRgb(getComputedStyle(node).color), stop)));
                    return {
                      backgroundStops,
                      backgroundColour,
                      minimumContrast: ratios.length ? Math.min(...ratios) : 0
                    };
                  };
                  const cards = [...document.querySelectorAll('.birthday-card')];
                  const homeCard = document.querySelector('.home-reminder-card.birthday');
                  return {
                    cards: cards.map(inspect),
                    homeCard: homeCard ? inspect(homeCard) : null,
                    balloonCards: document.querySelectorAll('.birthday-card.hq-colour .hq-balloon').length,
                    navPink: getComputedStyle(document.querySelector('[data-view-target="birthdays"]')).getPropertyValue('--nav-rgb').trim(),
                    headingColour: getComputedStyle(document.querySelector('.birthday-panel .section-head h2')).color
                  };
                }
                """
            )
            if not birthday["cards"] or birthday["homeCard"] is None:
                failures.append(f"{profile} birthday cards did not render")
                continue
            if any(
                not surface["backgroundStops"]
                or not any(
                    stop[0] >= 245 and stop[1] <= 190 and stop[2] >= 180
                    for stop in surface["backgroundStops"]
                )
                for surface in birthday["cards"]
            ):
                failures.append(f"{profile} birthday cards are not using bright pink surfaces: {birthday}")
            if birthday["homeCard"]["backgroundStops"] or birthday["homeCard"]["backgroundColour"] != [255, 193, 220]:
                failures.append(f"{profile} Home birthday reminder is not solid pastel pink: {birthday}")
            birthday_surfaces = birthday["cards"] + [birthday["homeCard"]]
            if any(surface["minimumContrast"] < 4.5 for surface in birthday_surfaces):
                failures.append(f"{profile} birthday card text contrast is below 4.5:1: {birthday}")
            if birthday["balloonCards"] < 1:
                failures.append(f"{profile} birthday cards lost their balloon artwork")
            if birthday["navPink"] != "217,0,119" or birthday["headingColour"] != "rgb(217, 0, 119)":
                failures.append(f"{profile} Birthday accent is not bright pink: {birthday}")
            birthday_card = page.locator('.birthday-card').first
            birthday_card.hover()
            page.wait_for_timeout(250)
            birthday_shadow = birthday_card.evaluate("el => getComputedStyle(el).boxShadow")
            birthday_transform = birthday_card.evaluate("el => getComputedStyle(el).transform")
            if birthday_shadow != calendar_shadow or birthday_transform != "none":
                failures.append(
                    f"{profile} Birthday hover does not match Calendar glow or moves: "
                    f"shadow={birthday_shadow}, transform={birthday_transform}"
                )
            page.locator('[data-view-target="home"]').click()
            home_birthday = page.locator('.home-reminder-card.birthday')
            home_birthday.hover()
            page.wait_for_timeout(250)
            home_birthday_shadow = home_birthday.evaluate("el => getComputedStyle(el).boxShadow")
            if home_birthday_shadow != calendar_shadow:
                failures.append(f"{profile} Home Birthday hover does not match Calendar glow")

        page.locator('.profile-switch [data-profile="pete"]').click()
        page.wait_for_function(
            "document.querySelector('#greeting')?.textContent === 'Hey Pete'"
        )
        page.locator('[data-view-target="dida"]').click()
        page.locator('.dida-hero').wait_for(state="visible", timeout=10000)
        dida = page.evaluate(
            r"""
            () => {
              const zoneRects = [...document.querySelectorAll('.dida-zone')]
                .map(zone => zone.getBoundingClientRect());
              const textSelectors = [
                '.dida-hero p',
                '.dida-source',
                '.dida-zone-head p',
                '.dida-quick p',
                '.dida-season-title p',
                '.dida-season-item',
                '.dida-fold summary p',
                '.dida-ref-card p'
              ];
              return {
                accent: getComputedStyle(document.querySelector('.dida-shell')).getPropertyValue('--dida').trim(),
                shellBackground: getComputedStyle(document.querySelector('.dida-shell')).backgroundImage,
                shellShadow: getComputedStyle(document.querySelector('.dida-shell')).boxShadow,
                heroIcons: document.querySelectorAll('.dida-hero-icons span').length,
                quickIcons: document.querySelectorAll('.dida-quick-icon').length,
                foldIcons: document.querySelectorAll('.dida-fold-icon').length,
                zones: document.querySelectorAll('.dida-zone').length,
                zoneBackgrounds: [...document.querySelectorAll('.dida-zone')].map(zone => getComputedStyle(zone).backgroundImage),
                zoneBackgroundColours: [...document.querySelectorAll('.dida-zone')].map(zone => getComputedStyle(zone).backgroundColor),
                zoneBorders: [...document.querySelectorAll('.dida-zone')].map(zone => getComputedStyle(zone).borderColor),
                innerBackgroundColours: [...document.querySelectorAll('.dida-quick,.dida-season,.dida-season-item,.dida-fold,.dida-ref-card,.dida-hero-icons span,.dida-quick-icon,.dida-fold-icon')].map(item => getComputedStyle(item).backgroundColor),
                titleColours: [...document.querySelectorAll('.dida-hero h2,.dida-zone-head h3,.dida-quick h4,.dida-season h4,.dida-fold summary h4,.dida-ref-card h5')].map(item => getComputedStyle(item).color),
                zoneGaps: zoneRects.slice(1).map((rect, index) => rect.top - zoneRects[index].bottom),
                sectionLinks: document.querySelectorAll('.dida-section-nav a').length,
                folds: document.querySelectorAll('.dida-fold').length,
                openFolds: document.querySelectorAll('.dida-fold[open]').length,
                bodyTextColours: textSelectors.map(selector => ({
                  selector,
                  colour: getComputedStyle(document.querySelector(selector)).color
                })),
                copy: document.querySelector('#didaContent').textContent,
                sourceHref: document.querySelector('.dida-source a')?.href || ''
              };
            }
            """
        )
        dida_accent = dida["accent"].lower()
        if dida_accent != "#00823b":
            failures.append(f"Dida accent is not the approved bright green: {dida['accent']}")
        if dida["heroIcons"] < 3 or dida["quickIcons"] < 3 or dida["foldIcons"] < 4:
            failures.append(f"Dida fun icon treatment is incomplete: {dida}")
        if dida["zones"] != 3 or dida["sectionLinks"] != 3:
            failures.append(f"Dida is not split into three clear sections: {dida}")
        if dida["shellBackground"] != "none" or dida["shellShadow"] != "none":
            failures.append(f"Dida still has a shared outer container: {dida}")
        if any(value != "none" for value in dida["zoneBackgrounds"]):
            failures.append(f"Dida zones still use gradient backgrounds: {dida}")
        if any(value != "rgb(255, 255, 255)" for value in dida["zoneBackgroundColours"] + dida["innerBackgroundColours"]):
            failures.append(f"Dida card or icon surfaces are not white: {dida}")
        if any("0, 130, 59" not in value for value in dida["zoneBorders"]):
            failures.append(f"Dida zone outlines do not use the bright green: {dida}")
        if any(value != "rgb(0, 130, 59)" for value in dida["titleColours"]):
            failures.append(f"Dida titles do not use the bright green: {dida}")
        minimum_zone_gap = 28 if name == "mobile" else 36
        if len(dida["zoneGaps"]) != 2 or any(
            gap < minimum_zone_gap - 1 for gap in dida["zoneGaps"]
        ):
            failures.append(
                f"Dida zone gaps are below {minimum_zone_gap}px: {dida['zoneGaps']}"
            )
        if dida["folds"] != 4 or dida["openFolds"] != 0:
            failures.append(f"Dida reference library is not compact by default: {dida}")
        expected_text_colour = "rgb(20, 42, 61)"
        non_neutral_text = [
            item for item in dida["bodyTextColours"]
            if item["colour"] != expected_text_colour
        ]
        if non_neutral_text:
            failures.append(f"Dida body text is not consistently neutral: {non_neutral_text}")
        if "DIDA · AGE 6" not in dida["copy"] or "Age-six development" not in dida["copy"]:
            failures.append("Dida did not switch fully to the age-six presentation")
        if any(old_copy in dida["copy"] for old_copy in ("AGE 5", "Five-year-old", "turning five")):
            failures.append("Dida still renders age-five wording")
        if dida["sourceHref"] != "https://stacks.cdc.gov/view/cdc/155268":
            failures.append(f"Dida age-six source changed or is not real: {dida['sourceHref']}")
        dida_zone = page.locator('.dida-zone').first
        dida_zone.hover()
        page.wait_for_timeout(250)
        dida_hover_shadow = dida_zone.evaluate("el => getComputedStyle(el).boxShadow")
        dida_hover_transform = dida_zone.evaluate("el => getComputedStyle(el).transform")
        if dida_hover_shadow != calendar_shadow or dida_hover_transform != "none":
            failures.append(
                "Dida hover does not match Calendar glow or moves: "
                f"shadow={dida_hover_shadow}, transform={dida_hover_transform}"
            )

        ARTIFACTS.mkdir(parents=True, exist_ok=True)
        for target in ("home", "arsenal", "dida", "birthdays"):
            page.locator(f'[data-view-target="{target}"]').click()
            page.wait_for_timeout(250)
            page.screenshot(
                path=str(ARTIFACTS / f"preview-{name}-{target}.png"),
                full_page=True,
            )

        if failures:
            raise AssertionError(f"{name}: " + " | ".join(failures))
        print(f"PASS {name}: greetings, Calendar-matched Birthday, Career and Dida glows, AI/Career icons, balloon and cannon nav marks, spaced age-six Dida zones with neutral text, fixture, navigation and Arsenal content are usable")
    finally:
        page.close()


def main() -> int:
    check_icon_metadata_files()
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
