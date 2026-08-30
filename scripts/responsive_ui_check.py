from __future__ import annotations

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:4173/?profile=pete"
LOCKED_URL = "http://127.0.0.1:4173/?profile=pete&locked=1"
VIEWPORTS = {
    "mobile": {"width": 390, "height": 844},
    "desktop": {"width": 1366, "height": 900},
}
ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ICON_PATHS = {
    "shortcut": "assets/icons/daily-brief-open-horizon-favicon-v2.ico",
    "ico": "assets/icons/daily-brief-open-horizon-favicon-v2.ico",
    "small": "assets/icons/daily-brief-open-horizon-favicon-32-v2.png",
    "large": "assets/icons/daily-brief-open-horizon-192-v2.png",
    "touch": "assets/icons/daily-brief-open-horizon-touch-v2.png",
    "manifest": "daily-brief-open-horizon-v2.webmanifest",
}
HOME_LOGO_PATH = "assets/icons/daily-brief-open-horizon-master-v2.png"
COMPANY_LOGO_PATHS = {
    "OpenAI": "assets/company-logos/openai.svg",
    "Google": "assets/company-logos/google.svg",
    "Google Gemini": "assets/company-logos/google-gemini.svg",
    "Anthropic": "assets/company-logos/anthropic.svg",
}


def check_icon_metadata_files() -> None:
    expected_root = tuple(ICON_PATHS.values())
    root_html = (ROOT / "index.html").read_text(encoding="utf-8")
    if 'class="brand hero-brand"' in root_html:
        raise AssertionError("visible Daily Briefs wordmark remains in the hero")
    if "Rare facts · wild places" in root_html:
        raise AssertionError("Around the world still shows the removed Rare facts subtitle")
    for value in expected_root:
        if value not in root_html:
            raise AssertionError(f"root icon metadata is missing {value}")
    if "searchParams.set('icon','v2')" not in root_html:
        raise AssertionError("root page does not apply the v2 bookmark cache key")
    if HOME_LOGO_PATH not in root_html:
        raise AssertionError("Home navigation does not use the selected Open Horizon mark")
    if "daily-brief-open-horizon-512-v2.png" not in root_html:
        raise AssertionError("Open Graph metadata does not use the selected Open Horizon mark")
    fallback_touch = ROOT / "apple-touch-icon.png"
    explicit_touch = ROOT / ICON_PATHS["touch"]
    if not fallback_touch.is_file() or fallback_touch.read_bytes() != explicit_touch.read_bytes():
        raise AssertionError("origin-level Apple touch fallback does not match Open Horizon")
    fallback_favicon = ROOT / "favicon.ico"
    if not fallback_favicon.is_file() or fallback_favicon.stat().st_size < 5_000:
        raise AssertionError("origin-level favicon fallback is missing or empty")

    for profile in ("pete", "sofia"):
        profile_html = (ROOT / profile / "index.html").read_text(encoding="utf-8")
        for value in expected_root:
            if f"../{value}" not in profile_html:
                raise AssertionError(f"{profile} icon metadata is missing ../{value}")
        if f"profile={profile}&locked=1&icon=v2" not in profile_html:
            raise AssertionError(f"{profile} route does not use the v2 bookmark cache key")

        profile_data = json.loads((ROOT / "data" / f"{profile}.json").read_text(encoding="utf-8"))
        if profile == "pete":
            for job in (profile_data.get("sections") or {}).get("Career") or []:
                title = str(job.get("title") or "").casefold()
                company = str(job.get("company") or "").casefold()
                if "government digital service" in title and "government digital service" not in company:
                    raise AssertionError("Pete Career includes a mismatched GDS aggregator duplicate")
        current_fact = profile_data.get("worldFact") or {}
        if current_fact.get("editorialPriority") != "human-first":
            raise AssertionError(f"{profile} current world fact is not human-first")
        extremes = (profile_data.get("weather") or {}).get("yesterdayExtremes") or {}
        for kind in ("hot", "cold"):
            photo = ((extremes.get(kind) or {}).get("photo") or {})
            source = str(photo.get("src") or "")
            expected_prefix = f"assets/weather-extremes/{kind}.webp?v="
            if not source.startswith(expected_prefix):
                raise AssertionError(f"{profile} {kind} weather card has no local image")
            image_path = ROOT / source.split("?", 1)[0]
            if not image_path.is_file() or image_path.stat().st_size < 20_000:
                raise AssertionError(f"{profile} {kind} weather image is missing or empty")
            if not str(photo.get("page") or "").startswith("https://commons.wikimedia.org/wiki/File:"):
                raise AssertionError(f"{profile} {kind} weather image lacks a verified source")

    manifest = json.loads((ROOT / ICON_PATHS["manifest"]).read_text(encoding="utf-8"))
    manifest_icons = {item.get("src") for item in manifest.get("icons", [])}
    expected_manifest_icons = {
        "assets/icons/daily-brief-open-horizon-192-v2.png",
        "assets/icons/daily-brief-open-horizon-512-v2.png",
        "assets/icons/daily-brief-open-horizon-maskable-512-v2.png",
    }
    if manifest.get("name") != "Daily Briefs" or manifest_icons != expected_manifest_icons:
        raise AssertionError(f"bookmark manifest metadata is incorrect: {manifest}")
    if any(manifest.get(key) != "/daily-briefs/" for key in ("id", "start_url", "scope")):
        raise AssertionError(f"bookmark manifest is not scoped to the Daily Briefs project: {manifest}")
    fallback_manifest = json.loads((ROOT / "site.webmanifest").read_text(encoding="utf-8"))
    if {item.get("src") for item in fallback_manifest.get("icons", [])} != expected_manifest_icons:
        raise AssertionError("origin-level manifest fallback does not use Open Horizon")

    tabs_script = (ROOT / "js" / "tabs-dida.js").read_text(encoding="utf-8")
    for company, relative_path in COMPANY_LOGO_PATHS.items():
        logo_path = ROOT / relative_path
        if not logo_path.is_file() or logo_path.stat().st_size < 250:
            raise AssertionError(f"AI company logo is missing or empty: {company}")
        if relative_path not in tabs_script:
            raise AssertionError(f"AI company logo is not mapped by the renderer: {company}")

    reminders = (ROOT / "js" / "home-reminders.js").read_text(encoding="utf-8")
    theme = (ROOT / "css" / "light-theme.css").read_text(encoding="utf-8")
    if "theme: 'halloween'" not in reminders or ".home-reminder-card.festive.halloween{background:#ffc27a}" not in theme:
        raise AssertionError("Halloween does not have its dedicated solid pastel orange treatment")
    reminder_art = {
        "clocks-card.webp",
        "halloween-card.webp",
        "normal-bins-card.webp",
        "recycling-card.webp",
        "xmas-card.webp",
    }
    for filename in reminder_art:
        path = ROOT / "assets" / "icons" / filename
        if not path.is_file() or path.stat().st_size < 10_000:
            raise AssertionError(f"Coming up artwork is missing or empty: {filename}")
        if filename not in reminders:
            raise AssertionError(f"Coming up renderer does not reference {filename}")


def check_profile_routes(browser) -> None:
    cases = (
        ("http://127.0.0.1:4173/pete/", "pete"),
        ("http://127.0.0.1:4173/sofia/", "sofia"),
        ("http://127.0.0.1:4173/?profile=pete&locked=1", "pete"),
        ("http://127.0.0.1:4173/?profile=sofia&locked=1", "sofia"),
    )
    for url, profile in cases:
        context = browser.new_context(viewport={"width": 390, "height": 844})
        page = context.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_function(
                f"document.querySelector('#greeting')?.textContent === 'Hey {profile.title()}' && "
                f"document.querySelector('#primaryNav')?.dataset.profile === '{profile}'"
            )
            route_state = page.evaluate(
                """
                () => {
                  const switcher=document.querySelector('#profileSwitch');
                  const rect=switcher.getBoundingClientRect();
                  const arsenal=document.querySelector('[data-view-target="arsenal"]');
                  return {
                    profile: state.profile,
                    navProfile: document.querySelector('#primaryNav')?.dataset.profile,
                    switchHidden: switcher.hidden,
                    switchWidth: rect.width,
                    switchHeight: rect.height,
                    arsenalVisible: getComputedStyle(arsenal).display !== 'none'
                  };
                }
                """
            )
            if route_state["profile"] != profile or route_state["navProfile"] != profile:
                raise AssertionError(f"{url}: loaded the wrong profile identity: {route_state}")
            if "icon=v2" not in page.url:
                raise AssertionError(f"{url}: did not apply the v2 bookmark cache key")
            if not route_state["switchHidden"] or route_state["switchWidth"] or route_state["switchHeight"]:
                raise AssertionError(f"{url}: locked switch still occupies space: {route_state}")
            if route_state["arsenalVisible"] != (profile == "pete"):
                raise AssertionError(f"{url}: Arsenal visibility does not match profile: {route_state}")
        finally:
            context.close()


def check_reduced_motion(browser) -> None:
    context = browser.new_context(
        viewport={"width": 1366, "height": 900}, reduced_motion="reduce"
    )
    page = context.new_page()
    try:
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        page.locator("#greeting").wait_for(state="visible", timeout=10000)
        page.evaluate("window.scrollTo(0, 900)")
        page.locator('[data-view-target="news"]').click()
        motion = page.evaluate(
            """
            () => ({
              scrollY: window.scrollY,
              navAnimation: getComputedStyle(document.querySelector('.bottom-nav'),'::before').animationName,
              cardTransition: getComputedStyle(document.querySelector('#view-news .tab-story')).transitionDuration
            })
            """
        )
        if motion["scrollY"] != 0 or motion["navAnimation"] != "none":
            raise AssertionError(f"reduced motion still animates navigation: {motion}")
        durations = [float(value.rstrip("s")) for value in motion["cardTransition"].split(", ")]
        if any(value > 0.001 for value in durations):
            raise AssertionError(f"reduced motion retains long transitions: {motion}")
    finally:
        context.close()


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
        home_logo = page.locator('[data-view-target="home"] .nav-home-logo')
        if home_logo.count() != 1 or home_logo.get_attribute("src") != HOME_LOGO_PATH:
            raise AssertionError(f"{name}: Home nav does not use the Open Horizon logo")
        home_logo_size = home_logo.evaluate(
            "el => ({width: el.naturalWidth, height: el.naturalHeight})"
        )
        if home_logo_size != {"width": 1024, "height": 1024}:
            raise AssertionError(f"{name}: Home nav logo failed to decode: {home_logo_size}")
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
        nav_cannon_mask = arsenal_cannon.evaluate(
            "el => getComputedStyle(el).maskImage || getComputedStyle(el).webkitMaskImage || ''"
        )
        if "arsenal-cannon-white-v1.png" not in nav_cannon_mask:
            raise AssertionError(f"{name}: Arsenal nav cannon does not use the supplied silhouette")

        page.locator('[data-view-target="news"]').click()
        page.wait_for_timeout(500)
        unsafe_story_media = page.evaluate(
            """
            () => [...document.querySelectorAll('#view-news .story-media')]
              .filter(media =>
                media.dataset.imageReady !== '1'
                || Number(media.dataset.imageWidth) < 1200
                || Number(media.dataset.imageHeight) < 675
              )
              .map(media => ({
                ready: media.dataset.imageReady || '',
                width: media.dataset.imageWidth || '',
                height: media.dataset.imageHeight || '',
                background: getComputedStyle(media).backgroundImage
              }))
            """
        )
        if unsafe_story_media:
            raise AssertionError(
                f"{name}: News contains an undecoded or undersized media slab: {unsafe_story_media}"
            )
        local_news_order = page.evaluate(
            """
            () => {
              const expected = [...(state.data?.sections?.['Local news'] || [])]
                .sort((a,b) => (Date.parse(b.publishedAt || '') || 0) - (Date.parse(a.publishedAt || '') || 0))
                .map(item => item.title);
              const group = [...document.querySelectorAll('#newsTabGroups .tab-group')]
                .find(section => section.querySelector('h3')?.textContent.trim() === 'Local News');
              const actual = [...(group?.querySelectorAll('h4') || [])].map(node => node.textContent.trim());
              return {expected, actual};
            }
            """
        )
        if local_news_order["actual"] != local_news_order["expected"]:
            raise AssertionError(f"{name}: Local News is not rendered newest first: {local_news_order}")

        hierarchy = page.evaluate(
            """
            () => [...document.querySelectorAll('#newsTabGroups .tab-group')].map(group =>
              [...group.querySelectorAll('.tab-story')].map(card => ({
                lead:card.classList.contains('story-lead'),
                support:card.classList.contains('story-support'),
                stream:card.classList.contains('story-stream')
              })))
            """
        )
        for roles in hierarchy:
            for index, role in enumerate(roles):
                expected = "lead" if index == 0 else "support" if index < 3 else "stream"
                if not role[expected] or sum(role.values()) != 1:
                    raise AssertionError(f"{name}: invalid News hierarchy at {index}: {role}")

        stream_feeds = page.evaluate(
            """
            () => [...document.querySelectorAll('#newsTabGroups .tab-group')].map(group => {
              const feed=group.querySelector('.story-stream-grid');
              const streamCards=[...group.querySelectorAll('.story-stream')];
              const textLead=[...group.querySelectorAll('.story-lead')]
                .find(card => !card.classList.contains('has-image'));
              const title=textLead?.querySelector('h4');
              const meta=textLead?.querySelector('.meta');
              return {
                streamCount:streamCards.length,
                feedCount:feed?1:0,
                feedDisplay:feed?getComputedStyle(feed).display:'',
                feedGap:feed?getComputedStyle(feed).gap:'',
                feedBackground:feed?getComputedStyle(feed).backgroundColor:'',
                streamRadii:streamCards.map(card => getComputedStyle(card).borderRadius),
                streamShadows:streamCards.map(card => getComputedStyle(card).boxShadow),
                titleBeforeMeta:!textLead || !title || !meta || title.getBoundingClientRect().top < meta.getBoundingClientRect().top
              };
            })
            """
        )
        for feed in stream_feeds:
            if feed["streamCount"] and feed["feedCount"] != 1:
                raise AssertionError(f"{name}: News stream is not grouped into one feed: {feed}")
            expected_display = "contents" if name == "mobile" else "grid"
            if feed["streamCount"] and feed["feedDisplay"] != expected_display:
                raise AssertionError(f"{name}: News stream feed has the wrong layout: {feed}")
            if name == "desktop" and feed["streamCount"]:
                if feed["feedGap"] != "1px" or feed["feedBackground"] == "rgba(0, 0, 0, 0)":
                    raise AssertionError(f"{name}: News stream lacks a shared divided surface: {feed}")
                if any(value != "0px" for value in feed["streamRadii"]):
                    raise AssertionError(f"{name}: News stream still looks like floating tiles: {feed}")
                if any(value != "none" for value in feed["streamShadows"]):
                    raise AssertionError(f"{name}: News stream retains individual tile shadows: {feed}")
            if not feed["titleBeforeMeta"]:
                raise AssertionError(f"{name}: News lead metadata appears before its headline: {feed}")

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
            if target == "ai":
                company_icons = page.locator('#view-ai .section-story-icon-company')
                if company_icons.count() < 1:
                    raise AssertionError(f"{name}: AI has no recognised company logos")
                if company_icons.count() != page.locator('#view-ai .section-company-logo').count():
                    raise AssertionError(f"{name}: an AI company icon is missing its logo image")
                failed_logos = page.locator('#view-ai .section-company-logo').evaluate_all(
                    "els => els.filter(el => !el.complete || !el.naturalWidth).map(el => el.src)"
                )
                if failed_logos:
                    raise AssertionError(f"{name}: AI company logos failed to decode: {failed_logos}")

        page.locator('[data-view-target="home"]').click()
        reminder_text = page.locator('#homeReminders').inner_text()
        reminder_copy = reminder_text.casefold()
        if 'general & garden waste' not in reminder_copy or 'put out both bins' not in reminder_copy:
            raise AssertionError(f"{name}: Garden Waste reminder copy is unclear: {reminder_text}")
        location_text = page.locator('#sceneryCountry').inner_text()
        location_copy = location_text.casefold()
        if '·' not in location_text or not any(region in location_copy for region in ('europe', 'oceania', 'africa', 'asia', 'america', 'antarctica')):
            raise AssertionError(f"{name}: Fact location lacks wider country/region context: {location_text}")
        calendar_cards = page.locator('#calendarSummaryCards button')
        if calendar_cards.count() != 4:
            raise AssertionError(f"{name}: expected four Calendar summary cards")
        calendar_cards.first.hover()
        page.wait_for_timeout(250)
        calendar_shadow = calendar_cards.first.evaluate("el => getComputedStyle(el).boxShadow")
        if calendar_shadow == "none":
            raise AssertionError(f"{name}: Calendar card has no edge-glow hover")

        for selector in ('#homeReminders .home-reminder-card', '#sceneryFact', '#sceneryCard', '.uk-extreme'):
            card = page.locator(selector).first
            card.hover()
            page.wait_for_timeout(250)
            shadow = card.evaluate("el => getComputedStyle(el).boxShadow")
            transform = card.evaluate("el => getComputedStyle(el).transform")
            if shadow != calendar_shadow or transform != "none":
                raise AssertionError(
                    f"{name}: {selector} hover does not match the visible Calendar glow or moves: "
                    f"shadow={shadow}, transform={transform}"
                )

        tv_cards = page.locator('#watchStrip .watch-card.artwork')
        if tv_cards.count() != 5:
            raise AssertionError(f"{name}: expected five exact-artwork TV Picks, found {tv_cards.count()}")
        for index in range(tv_cards.count()):
            card = tv_cards.nth(index)
            artwork = card.get_attribute('data-artwork') or ''
            background = card.evaluate("el => getComputedStyle(el).backgroundImage")
            if not artwork.startswith('https://static.tvmaze.com/uploads/images/original_untouched/') or 'static.tvmaze.com' not in background:
                raise AssertionError(f"{name}: TV Pick {index + 1} does not render exact programme artwork")
            text = card.inner_text().casefold()
            if not any(marker in text for marker in ('available since', 'today', 'tomorrow', 'mon ', 'tue ', 'wed ', 'thu ', 'fri ', 'sat ', 'sun ')):
                raise AssertionError(f"{name}: TV Pick {index + 1} has no availability date")
            sports = __import__('re').search(
                r'\b(?:sports?|football|soccer|premier league|champions league|fa cup|carabao cup|rugby|cricket|tennis|golf|boxing|formula\s*(?:one|1)|f1|motorsport|grand prix|athletics?|olympics?|basketball|nfl|super bowl|baseball|nhl|ice hockey|cycling|darts|snooker|horse racing|wrestling|wwe|ufc)\b',
                text,
                __import__('re').I,
            )
            allowed_sport = __import__('re').search(
                r'\b(?:world cup|uefa euro(?:s|\s*20\d{2})?|uefa european championship|wimbledon)\b',
                text,
                __import__('re').I,
            )
            if sports and not allowed_sport:
                raise AssertionError(f"{name}: routine sport appeared in TV Picks: {text}")

        tv_card = tv_cards.first
        if tv_card.count():
            tv_card.hover()
            page.wait_for_timeout(250)
            tv_shadow = tv_card.evaluate("el => getComputedStyle(el).boxShadow")
            tv_transform = tv_card.evaluate("el => getComputedStyle(el).transform")
            if "255, 212, 119" not in tv_shadow or tv_transform != "none":
                raise AssertionError(
                    f"{name}: TV hover is not a strong stationary gold glow: "
                    f"shadow={tv_shadow}, transform={tv_transform}"
                )

        page.locator('[data-view-target="career"]').click()
        page.wait_for_function("window.scrollY < 2")
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
        last_result_text = page.locator('#lastResultCard').inner_text()
        last_result_copy = last_result_text.casefold()
        for required in ('arsenal 3–0 coventry city', 'kai havertz', 'premier league', '8pm', 'emirates stadium'):
            if required not in last_result_copy:
                raise AssertionError(f"{name}: Arsenal last result is missing {required}: {last_result_text}")
        if len(page.locator('#lastResultCard .match-summary').inner_text().strip()) < 40:
            raise AssertionError(f"{name}: Arsenal quick game summary is missing or too thin")
        page.locator('#arsenalTransfers').wait_for(state="visible", timeout=10000)
        page.locator('.arsenal-rumour-head').wait_for(state="visible", timeout=10000)
        page.locator('#arsenalTransferRumours').wait_for(state="visible", timeout=10000)
        arsenal_roles = page.evaluate(
            """
            () => [...document.querySelectorAll('#arsenalNews .arsenal-news-item')].map(card => ({
              lead:card.classList.contains('arsenal-news-lead'),
              support:card.classList.contains('arsenal-news-support'),
              stream:card.classList.contains('arsenal-news-stream')
            }))
            """
        )
        for index, role in enumerate(arsenal_roles):
            expected = "lead" if index == 0 else "support" if index < 3 else "stream"
            if not role[expected] or sum(role.values()) != 1:
                raise AssertionError(f"{name}: invalid Arsenal news hierarchy at {index}: {role}")
        arsenal_hero = page.locator('.arsenal-hero')
        hero_background = arsenal_hero.evaluate("el => getComputedStyle(el).backgroundImage")
        if 'rgb(227, 6, 19)' not in hero_background:
            raise AssertionError(f"{name}: Arsenal masthead does not use the approved official-site red: {hero_background}")
        if arsenal_hero.locator('.arsenal-hero-cannon').count() != 1:
            raise AssertionError(f"{name}: Arsenal masthead cannon is missing")
        cannon_asset = page.evaluate(
            """
            () => {
              const hero = document.querySelector('.arsenal-hero-cannon');
              const nav = document.querySelector('.nav-cannon');
              const navStyle = getComputedStyle(nav);
              return {
                heroTag: hero?.tagName || '',
                heroSrc: hero?.getAttribute('src') || '',
                heroWidth: hero?.naturalWidth || 0,
                heroHeight: hero?.naturalHeight || 0,
                navMask: navStyle.maskImage || navStyle.webkitMaskImage || ''
              };
            }
            """
        )
        if (
            cannon_asset["heroTag"] != "IMG"
            or cannon_asset["heroSrc"] != "assets/icons/arsenal-cannon-white-v1.png"
            or cannon_asset["heroWidth"] < 800
            or cannon_asset["heroHeight"] < 300
            or "arsenal-cannon-white-v1.png" not in cannon_asset["navMask"]
        ):
            raise AssertionError(
                f"{name}: supplied cannon is not shared by the Arsenal masthead and nav: {cannon_asset}"
            )
        transfer_background = page.locator('.arsenal-transfers').evaluate("el => getComputedStyle(el).backgroundImage")
        if 'rgb(7, 29, 73)' not in transfer_background:
            raise AssertionError(f"{name}: Arsenal transfer area does not use the approved navy: {transfer_background}")
        fixture_copy_colours = page.evaluate(
            """
            () => ({
              primary: getComputedStyle(document.querySelector('#nextFixtureCard .fixture-fact>b')).color,
              supporting: getComputedStyle(document.querySelector('#nextFixtureCard .fixture-fact>small')).color
            })
            """
        )
        if fixture_copy_colours["primary"] != "rgb(255, 255, 255)":
            raise AssertionError(
                f"{name}: Arsenal fixture copy is not white on navy: {fixture_copy_colours}"
            )
        if not fixture_copy_colours["supporting"].startswith("rgba(255, 255, 255,"):
            raise AssertionError(
                f"{name}: Arsenal supporting fixture copy is not light on navy: {fixture_copy_colours}"
            )
        league_text = page.locator('#leagueCard').inner_text()
        if not __import__('re').search(r'\b(?:1st|2nd|3rd|(?:[4-9]|1[0-9]|20)th)\b', league_text):
            raise AssertionError(f"{name}: Arsenal current league position is missing: {league_text}")
        if __import__('re').search(r'\b(?:pts?|points?|played|matches)\b', league_text, __import__('re').I):
            raise AssertionError(f"{name}: Arsenal position card still shows table details: {league_text}")
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

        page.locator('[data-view-target="home"]').click()
        # Clear interaction state before checking the resting-state colour.
        # Desktop retains :hover and touch emulation can retain focus.
        page.evaluate("document.activeElement?.blur()")
        page.mouse.move(1, 1)
        page.wait_for_timeout(250)
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
              const weatherCards = [...document.querySelectorAll('#yesterdayExtremes .uk-extreme')];
              const parseRgb = value => value.match(/\d+(?:\.\d+)?/g)?.slice(0,3).map(Number) || [0,0,0];
              const luminance = values => {
                const rgbValues = values.map(value => value / 255).map(
                  value => value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4
                );
                return 0.2126 * rgbValues[0] + 0.7152 * rgbValues[1] + 0.0722 * rgbValues[2];
              };
              const contrast = (left, right) => {
                const values = [luminance(left), luminance(right)].sort((a, b) => b - a);
                return (values[0] + 0.05) / (values[1] + 0.05);
              };
              const canvasTitleSelectors = [
                '#greeting',
                '#homeRemindersSection .section-head h2',
                '#calendarSection .section-head h2',
                '#sceneryPanel .section-head h2',
                '.tonight-block > .section-head h2',
                '#view-news > .tab-panel > .section-head h2',
                '#view-news .tab-group > h3',
                '#view-ai .section-head h2',
                '#view-career .section-head h2',
                '#view-dida > .tab-panel > .section-head h2',
                '.birthday-panel .section-head h2',
                '.occasion-month h3'
              ];
              const canvasTitles = canvasTitleSelectors
                .map(selector => document.querySelector(selector))
                .filter(Boolean);
              return {
                bodyRgb: rgb,
                bodyBackgroundImage: bodyStyle.backgroundImage,
                bodyBackgroundColor: bodyStyle.backgroundColor,
                topbarBackgroundColor: topbarStyle.backgroundColor,
                factBeforeImage: Boolean(fact.compareDocumentPosition(image) & Node.DOCUMENT_POSITION_FOLLOWING),
                factText: document.querySelector('#sceneryFactText')?.textContent?.trim() || '',
                factHref: fact?.getAttribute('href') || '',
                factLabel: document.querySelector('#sceneryFactLabel')?.textContent?.trim() || '',
                weatherCards: weatherCards.map(card => ({
                  classes: card.className,
                  backgroundImage: getComputedStyle(card.querySelector('.uk-extreme-photo')).backgroundImage,
                  sourceHref: card.querySelector('.uk-extreme-photo-credit a')?.href || '',
                  text: card.textContent.trim()
                })),
                greetingMarginTop: parseFloat(getComputedStyle(greeting).marginTop),
                greetingColour: getComputedStyle(greeting).color,
                dateColour: getComputedStyle(date).color,
                canvasTitleColours: canvasTitles.map(node => getComputedStyle(node).color),
                canvasTitleContrasts: canvasTitles.map(node => contrast(parseRgb(getComputedStyle(node).color), rgb)),
                weatherTitleColour: getComputedStyle(document.querySelector('#weatherPanel .section-head h2')).color,
                heroBrandCount: document.querySelectorAll('.hero .hero-brand').length,
                topbarBrandCount: document.querySelectorAll('.topbar .brand').length,
                navBackgroundColour: getComputedStyle(nav).backgroundColor,
                navDefaultColours: buttons.map(button => getComputedStyle(button).color),
                mainCopyColours: [
                  '.section-kicker',
                  '.forecast-day small',
                  '.calendar-row p',
                  '#sceneryFactText'
                ].map(selector => ({
                  selector,
                  colour: document.querySelector(selector)
                    ? getComputedStyle(document.querySelector(selector)).color
                    : null
                })),
                reminderCards: reminderCards.map(card => ({
                  classes: card.className,
                  text: card.textContent.trim(),
                  backgroundImage: getComputedStyle(card).backgroundImage,
                  backgroundColour: getComputedStyle(card).backgroundColor,
                  top: card.getBoundingClientRect().top,
                  left: card.getBoundingClientRect().left,
                  right: card.getBoundingClientRect().right,
                  height: card.getBoundingClientRect().height,
                  clientWidth: card.clientWidth,
                  scrollWidth: card.scrollWidth,
                  copyRight: card.querySelector('.home-reminder-copy')?.getBoundingClientRect().right || null,
                  artwork: [...card.querySelectorAll('.home-reminder-art')].map(image => ({
                    src: image.getAttribute('src'),
                    naturalWidth: image.naturalWidth,
                    naturalHeight: image.naturalHeight,
                    left: image.getBoundingClientRect().left,
                    width: image.getBoundingClientRect().width,
                    height: image.getBoundingClientRect().height
                  })),
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
        if len(visual["weatherCards"]) != 2:
            failures.append(f"hottest and coldest weather image cards are not both present: {visual['weatherCards']}")
        for card in visual["weatherCards"]:
            if "no-photo" in card["classes"].split():
                failures.append(f"weather card fell back to a blank image: {card}")
            if "assets/weather-extremes/" not in card["backgroundImage"]:
                failures.append(f"weather card does not use its cached exact-place image: {card}")
            if not card["sourceHref"].startswith("https://commons.wikimedia.org/wiki/File:"):
                failures.append(f"weather card image credit is not linked to its source: {card}")
        if visual["greetingMarginTop"] < 16:
            failures.append(f"greeting was not moved down: margin {visual['greetingMarginTop']}")
        if visual["heroBrandCount"] != 0 or visual["topbarBrandCount"] != 0:
            failures.append("visible Daily Briefs wordmark remains")
        approved_ink = "rgb(20, 42, 61)"
        if visual["greetingColour"] != approved_ink or visual["dateColour"] != approved_ink:
            failures.append(
                f"greeting or date does not use the approved ink: {visual}"
            )
        if any(colour != approved_ink for colour in visual["canvasTitleColours"]):
            failures.append(f"titles on the blue canvas do not use the approved ink: {visual['canvasTitleColours']}")
        if any(ratio < 4.5 for ratio in visual["canvasTitleContrasts"]):
            failures.append(f"titles on the blue canvas fall below 4.5:1 contrast: {visual['canvasTitleContrasts']}")
        if visual["weatherTitleColour"] != approved_ink:
            failures.append(f"Weather title is not readable on its light card: {visual['weatherTitleColour']}")
        if visual["navBackgroundColour"] != "rgb(16, 42, 67)":
            failures.append(f"navigation is not solid dark navy: {visual['navBackgroundColour']}")
        if any(colour != "rgb(255, 255, 255)" for colour in visual["navDefaultColours"]):
            failures.append(f"navigation text and icons are not white before hover: {visual['navDefaultColours']}")
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
        for card in visual["reminderCards"]:
            classes = card["classes"].split()
            expected_art = None
            if "bin" in classes:
                expected_art = "recycling-card.webp" if "recycling" in card["text"].lower() else "normal-bins-card.webp"
            elif "clocks" in classes:
                expected_art = "clocks-card.webp"
            elif "halloween" in classes:
                expected_art = "halloween-card.webp"
            elif "christmas" in classes:
                expected_art = "xmas-card.webp"
            if expected_art:
                if len(card["artwork"]) != 1 or not card["artwork"][0]["src"].endswith(expected_art):
                    failures.append(f"Coming up {expected_art} artwork is not mapped correctly: {card}")
                elif (
                    card["artwork"][0]["naturalWidth"] < 500
                    or card["artwork"][0]["naturalHeight"] < 600
                    or abs(card["artwork"][0]["height"] - card["height"]) > 3
                ):
                    failures.append(f"Coming up {expected_art} artwork did not load or fill its card: {card}")
                elif card["copyRight"] > card["artwork"][0]["left"] + 1:
                    failures.append(f"Coming up text overlaps {expected_art} artwork: {card}")
            elif card["artwork"]:
                failures.append(f"Coming up card has unexpected artwork: {card}")
            if expected_art and card["scrollWidth"] > card["clientWidth"] + 1:
                failures.append(f"Coming up artwork causes horizontal overflow: {card}")
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
        reminder_tops = {round(card["top"]) for card in visual["reminderCards"]}
        if name == "desktop":
            if len(reminder_tops) != 1:
                failures.append(f"Coming up cards do not fit on one Chromebook row: {visual['reminderCards']}")
            if any(card["height"] > 150 for card in visual["reminderCards"]):
                failures.append(f"Coming up cards remain too tall for the compact row: {visual['reminderCards']}")
        elif len(reminder_tops) != len(visual["reminderCards"]):
            failures.append(f"Coming up cards overlap on mobile: {visual['reminderCards']}")
        if visual["navAfter"] not in {"none", '""'}:
            failures.append(f"navigation star layer remains: {visual['navAfter']}")
        if any(content not in {"none", '""'} for content in visual["buttonAfter"]):
            failures.append(f"navigation button sparkle remains: {visual['buttonAfter']}")
        if any(mark in visual["navText"] for mark in ("✦", "★", "☆", "✨")):
            failures.append("navigation still contains a star or sparkle glyph")

        expected_nav_hover_colours = {
            "home": "rgb(108, 232, 255)",
            "news": "rgb(140, 185, 255)",
            "arsenal": "rgb(255, 155, 160)",
            "ai": "rgb(235, 170, 255)",
            "career": "rgb(255, 211, 92)",
            "dida": "rgb(155, 224, 83)",
            "birthdays": "rgb(255, 150, 205)",
        }
        for target, expected_colour in expected_nav_hover_colours.items():
            nav_button = page.locator(f'[data-view-target="{target}"]')
            nav_button.hover()
            page.wait_for_timeout(220)
            actual_colour = nav_button.evaluate("el => getComputedStyle(el).color")
            if actual_colour != expected_colour:
                failures.append(
                    f"{target} navigation colour does not appear on hover: "
                    f"{actual_colour} != {expected_colour}"
                )

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
            for target in ("home", "news", "dida", "birthday", "career", "home"):
                target_name = "birthdays" if target == "birthday" else target
                page.locator(f'[data-view-target="{target_name}"]').click()
                page.wait_for_timeout(60)
                nav_state = page.evaluate(
                    """
                    () => {
                      const nav = document.querySelector('#primaryNav');
                      const rect = nav.getBoundingClientRect();
                      const style = getComputedStyle(nav);
                      return {
                        display: style.display,
                        visibility: style.visibility,
                        opacity: Number(style.opacity),
                        top: rect.top,
                        bottom: rect.bottom,
                        height: rect.height,
                        viewportHeight: window.innerHeight,
                        zIndex: Number(style.zIndex)
                      };
                    }
                    """
                )
                if (
                    nav_state["display"] == "none"
                    or nav_state["visibility"] != "visible"
                    or nav_state["opacity"] != 1
                    or nav_state["height"] < 44
                    or nav_state["top"] < 0
                    or nav_state["bottom"] > nav_state["viewportHeight"] + 1
                    or nav_state["zIndex"] < 1000
                ):
                    failures.append(
                        f"mobile nav disappeared or left the viewport after selecting {target_name}: {nav_state}"
                    )

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
            news_card = page.locator('#newsTabGroups .tab-story').first
            news_card.hover()
            page.wait_for_timeout(250)
            news_shadow = news_card.evaluate("el => getComputedStyle(el).boxShadow")
            news_transform = news_card.evaluate("el => getComputedStyle(el).transform")
            if news_shadow != calendar_shadow or news_transform != "none":
                failures.append(
                    f"{profile} News hover does not match the visible Calendar glow or moves: "
                    f"shadow={news_shadow}, transform={news_transform}"
                )
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
                  const lineCount = node => {
                    if (!node) return 0;
                    const style = getComputedStyle(node);
                    const parsedLineHeight = parseFloat(style.lineHeight);
                    const fallbackLineHeight = parseFloat(style.fontSize) * 1.2;
                    const lineHeight = Number.isFinite(parsedLineHeight) ? parsedLineHeight : fallbackLineHeight;
                    return Math.round(node.getBoundingClientRect().height / lineHeight);
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
                      minimumContrast: ratios.length ? Math.min(...ratios) : 0,
                      nameLines: lineCount(card.querySelector('strong')),
                      detailLines: lineCount(card.querySelector('small'))
                    };
                  };
                  const cards = [...document.querySelectorAll('.birthday-card')];
                  const homeCard = document.querySelector('.home-reminder-card.birthday');
                  return {
                    cards: cards.map(inspect),
                    homeCard: homeCard ? inspect(homeCard) : null,
                    title: document.querySelector('.birthday-panel .section-head h2')?.textContent.trim() || '',
                    kickerCount: document.querySelectorAll('.birthday-panel .section-head .section-kicker').length,
                    navLabel: document.querySelector('[data-view-target="birthdays"]')?.innerText.trim() || '',
                    names: cards.map(card => card.querySelector('strong')?.textContent.trim() || ''),
                    monthGroups: [...document.querySelectorAll('.occasion-month')].map(group => ({
                      month: group.querySelector('h3')?.textContent.trim() || '',
                      cardCount: group.querySelectorAll('.birthday-card').length,
                      tops: [...group.querySelectorAll('.birthday-card')].map(card => Math.round(card.getBoundingClientRect().top))
                    })),
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
                surface["backgroundStops"]
                or surface["backgroundColour"] != [255, 255, 255]
                for surface in birthday["cards"]
            ):
                failures.append(f"{profile} birthday cards are not solid white: {birthday}")
            if birthday["homeCard"]["backgroundStops"] or birthday["homeCard"]["backgroundColour"] != [255, 193, 220]:
                failures.append(f"{profile} Home birthday reminder is not solid pastel pink: {birthday}")
            birthday_surfaces = birthday["cards"] + [birthday["homeCard"]]
            if any(surface["minimumContrast"] < 4.5 for surface in birthday_surfaces):
                failures.append(f"{profile} birthday card text contrast is below 4.5:1: {birthday}")
            if birthday["balloonCards"] < 1:
                failures.append(f"{profile} birthday cards lost their balloon artwork")
            if birthday["title"] != "Birthday" or birthday["kickerCount"] != 0 or birthday["navLabel"] != "Birthday":
                failures.append(f"{profile} Birthday heading remains duplicated or misnamed: {birthday}")
            if len(birthday["names"]) != len(set(birthday["names"])):
                failures.append(f"{profile} Birthday list contains duplicate cards: {birthday['names']}")
            grouped_count = sum(group["cardCount"] for group in birthday["monthGroups"])
            if grouped_count != len(birthday["cards"]) or not birthday["monthGroups"]:
                failures.append(f"{profile} Birthday cards are not grouped by month: {birthday}")
            if name == "desktop" and any(
                group["cardCount"] <= 3 and len(set(group["tops"])) != 1
                for group in birthday["monthGroups"]
            ):
                failures.append(f"{profile} same-month Birthday cards do not share a row: {birthday['monthGroups']}")
            if name == "desktop" and any(
                surface["nameLines"] > 2 or surface["detailLines"] > 2
                for surface in birthday["cards"]
            ):
                failures.append(f"{profile} desktop Birthday copy wraps too deeply: {birthday['cards']}")
            if birthday["navPink"] != "255,150,205" or birthday["headingColour"] != approved_ink:
                failures.append(f"{profile} Birthday heading is not readable ink or navigation hover is not bright pink: {birthday}")
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
        page.locator('.dida-zone').first.wait_for(state="visible", timeout=10000)
        dida = page.evaluate(
            r"""
            () => {
              const zoneRects = [...document.querySelectorAll('.dida-zone')]
                .map(zone => zone.getBoundingClientRect());
              const textSelectors = [
                '.dida-source',
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
                heroes: document.querySelectorAll('.dida-hero').length,
                heroIcons: document.querySelectorAll('.dida-hero-icons span').length,
                quickIcons: document.querySelectorAll('.dida-quick-icon').length,
                foldIcons: document.querySelectorAll('.dida-fold-icon').length,
                zones: document.querySelectorAll('.dida-zone').length,
                zoneBackgrounds: [...document.querySelectorAll('.dida-zone')].map(zone => getComputedStyle(zone).backgroundImage),
                zoneBackgroundColours: [...document.querySelectorAll('.dida-zone')].map(zone => getComputedStyle(zone).backgroundColor),
                zoneBorders: [...document.querySelectorAll('.dida-zone')].map(zone => getComputedStyle(zone).borderColor),
                innerBackgroundColours: [...document.querySelectorAll('.dida-quick,.dida-season,.dida-season-item,.dida-fold,.dida-ref-card,.dida-quick-icon,.dida-fold-icon')].map(item => getComputedStyle(item).backgroundColor),
                titleColours: [...document.querySelectorAll('.dida-zone-head h3,.dida-quick h4,.dida-season h4,.dida-fold summary h4,.dida-ref-card h5')].map(item => getComputedStyle(item).color),
                zoneGaps: zoneRects.slice(1).map((rect, index) => rect.top - zoneRects[index].bottom),
                sectionLinks: document.querySelectorAll('.dida-section-nav a').length,
                zoneHeaders: [...document.querySelectorAll('.dida-zone-head')].map(head => ({
                  text: head.textContent.trim(),
                  h3Count: head.querySelectorAll(':scope > h3').length,
                  extraCount: head.querySelectorAll(':scope > :not(h3), small, p, .dida-zone-number').length
                })),
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
        if dida["heroes"] != 0 or dida["heroIcons"] != 0 or dida["sectionLinks"] != 0:
            failures.append(f"Dida top section or duplicate section navigation remains: {dida}")
        if dida["quickIcons"] < 3 or dida["foldIcons"] < 4:
            failures.append(f"Dida fun icon treatment is incomplete: {dida}")
        if dida["zones"] != 3:
            failures.append(f"Dida is not split into three clear sections: {dida}")
        expected_zone_titles = ["This week", "Seasonal missions", "Reference library"]
        if [head["text"] for head in dida["zoneHeaders"]] != expected_zone_titles or any(
            head["h3Count"] != 1 or head["extraCount"] != 0
            for head in dida["zoneHeaders"]
        ):
            failures.append(f"Dida zone headers contain more than their title: {dida['zoneHeaders']}")
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
        if "Age-six development" not in dida["copy"]:
            failures.append("Dida age-six reference content is missing")
        removed_dida_copy = (
            "DIDA · AGE 6",
            "What matters now",
            "START HERE",
            "Three focused ideas. Do one, not everything.",
            "EXPLORE & PLAY",
            "KEEP FOR LATER",
        )
        if any(value in dida["copy"] for value in removed_dida_copy):
            failures.append(f"Dida still renders removed top or header copy: {dida['copy']}")
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
        for target in ("home", "news", "arsenal", "ai", "career", "dida", "birthdays"):
            page.locator(f'[data-view-target="{target}"]').click()
            page.wait_for_timeout(250)
            page.screenshot(
                path=str(ARTIFACTS / f"preview-{name}-{target}.png"),
                full_page=True,
            )

        page.locator('[data-profile="sofia"]').click()
        page.wait_for_function(
            "document.querySelector('#greeting')?.textContent === 'Hey Sofia'"
        )
        for target in ("home", "news", "career"):
            page.locator(f'[data-view-target="{target}"]').click()
            page.wait_for_timeout(250)
            page.screenshot(
                path=str(ARTIFACTS / f"preview-{name}-sofia-{target}.png"),
                full_page=True,
            )

        page.goto(LOCKED_URL, wait_until="domcontentloaded", timeout=15000)
        page.locator("#greeting").wait_for(state="visible", timeout=10000)
        if page.locator("#profileSwitch").is_visible():
            failures.append("locked profile route exposes the profile switch")

        if failures:
            raise AssertionError(f"{name}: " + " | ".join(failures))
        print(f"PASS {name}: sourced weather images, human-first fact, compact Coming up row, visible card glows, Birthday, Dida, navigation and protected content are usable")
    finally:
        page.close()


def main() -> int:
    check_icon_metadata_files()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            check_profile_routes(browser)
            check_reduced_motion(browser)
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
