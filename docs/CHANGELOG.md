# Daily Briefs Changelog

Newest entries go first.

## 22 August 2026: Cleaner content icons, Dida zones, and navigation marks

Status: implemented

- Requested change: Remove Career and AI pictures in favour of stylish generic icons; reorganise the overloaded Dida view; use a single balloon for Birthdays; and replace the Arsenal navigation mark with a proper cannon.
- Approved scope: AI/Career presentation only, Dida information layout only, the two requested navigation icons, responsive regression coverage, cache keys, master brief, and changelog.
- Files changed: index.html, js/story-images-enhance.js, js/tabs-dida.js, css/tabs-dida.css, js/home-reminders.js, css/home-reminders.css, css/nav-cannon.css, scripts/responsive_ui_check.py, docs/MASTER-BRIEF-CURRENT.md, and docs/CHANGELOG.md.
- AI/Career rule: suppress article photography and use decorative code-native icon sets while preserving every item, metadata field, and real destination link.
- Dida rule: preserve all content but divide it into This week, Seasonal missions, and Reference library; keep the four detailed reference groups collapsed until opened.
- Navigation rule: Birthdays uses one balloon; Arsenal uses a clean side-on cannon with a filled barrel and spoked wheel.
- Requirements protected: Pete/Sofia profile behaviour, mobile horizontal and desktop vertical navigation, 44 px targets, Dida lime styling, Arsenal red treatment and content rules, all data sources, and every unrelated view.
- Validation prepared: mobile and desktop checks assert the icon-only AI/Career cards, balloon/cannon marks, three Dida zones, collapsed reference library, navigation geometry, and existing protected rules.
- Unexpected changes: none intended.
- Master brief update: version 1.9 records the approved image, Dida structure, and navigation-icon rules.
- Follow-up: run responsive, refresh, Pages, and live-route verification.

## 22 August 2026: Shorter Hey greetings

Status: implemented

- Requested change: Replace the morning greeting with `Hey Pete`, make it smaller, and apply the same treatment to Sofia.
- Approved scope: shared greeting copy, responsive greeting typography, cache keys, Pete/Sofia responsive regression coverage, master brief, and changelog.
- Files changed: index.html, js/app.js, css/app.css, scripts/responsive_ui_check.py, docs/MASTER-BRIEF-CURRENT.md, and docs/CHANGELOG.md.
- Greeting rule: show `Hey Pete` and `Hey Sofia` without trailing punctuation.
- Typography rule: use a 36–52 px responsive range below 900 px and a 52–68 px range from 900 px upwards.
- Validation prepared: both names and both viewport size ceilings are asserted by the responsive UI check; JavaScript syntax and exact bounded replacements were checked before publication.
- QA discovery: the existing Birthdays destination made the old six-button Pete navigation assertion stale. The check now protects all seven existing destinations in order without changing the UI.
- Unexpected changes: none intended; profiles, routes, sections, controls, data, colours, links, content feeds, and unrelated responsive behaviour remain unchanged.
- Master brief update: version 1.8 records the approved greeting wording and smaller responsive scale.
- Follow-up: run the responsive workflow and verify both live profile routes after deployment.

## 19 August 2026: Repair England weather-extremes county resolution

Status: validated

- Failure: the scheduled morning refresh generated valid data but publication was blocked because the county resolver could not verify the Met Office station `Albemarle`.
- Root cause: the extremes parser discarded the official Met Office station link and relied on a small manual mapping plus a third-party geocoder for unknown stations.
- Fix: add the verified `Albemarle, Northumberland` mapping and resolve future unknown linked stations from the county in their official Met Office observation-page heading before using the existing fallback.
- Safety: accept only HTTPS links on `weather.metoffice.gov.uk`, require the linked station name to match the extremes-table location, and retain the hard failure when town, county, or England status cannot be verified.
- Tests: three regression tests pass; a live Met Office extremes parse returned `Hurn, Bournemouth, Christchurch and Poole` and `Albemarle, Northumberland`, both marked England with no resolver error. The fresh Morning refresh passed and committed `21907a5`; GitHub Pages serves both 19 August profiles with identical 21-event calendars, 12 Local News items, 12 UK News items, and the verified England extreme locations.
- Scope: weather-extremes enrichment and its regression tests only. No layout, profile, calendar, news, Arsenal, Career, AI, TV Picks, Dida, or image behaviour changed.

## 18 August 2026: Dedicated Daily Brief icon

Status: validated

- Requested change: Replace the incorrectly shared Bomberfan image with Pete's approved colourful Daily Brief icon, showing the concept before publication.
- Approved scope: derived favicon, Apple touch, installable-app and maskable icon files; explicit root/Pete/Sofia metadata; web app manifest; cache-busting URLs; responsive checks; master brief; and changelog.
- Files changed: favicon.ico, assets/icons/apple-touch-icon.png, assets/icons/daily-brief-192.png, assets/icons/daily-brief-512.png, assets/icons/daily-brief-maskable-512.png, assets/icons/favicon-32.png, site.webmanifest, index.html, pete/index.html, sofia/index.html, scripts/responsive_ui_check.py, docs/MASTER-BRIEF-CURRENT.md, and docs/CHANGELOG.md.
- Branding rule: use the approved colourful rising-sun and layered-news-card design for Daily Brief favicon, touch, installable-app, and preview metadata; never reuse Bomberfan imagery.
- Validation performed: PNG and multi-size ICO dimensions, manifest JSON and file references, explicit root/Pete/Sofia metadata, Python syntax, successful mobile/desktop Responsive UI workflow, successful Morning refresh, successful Pages deployments, exact Git blob hashes for both full-quality 512px assets, cache-busted live URLs, and live Chrome decoding of 32px, 512px, and maskable 512px images.
- Unexpected changes: none intended; Bomberfan and all Daily Brief content, routes, profiles, sections, data, sources, and interactions remain unchanged.
- Master brief update: version 1.7 records the dedicated Daily Brief icon and separation from Bomberfan branding.
- Follow-up: none.

## 18 August 2026: Newest-first transfers and X reporter watch

Status: validated

- Requested change: Order Arsenal transfers newest first and add useful speculative transfer signals from Twitter/X.
- Approved scope: transfer timestamps and sorting, allowlisted public X reporter discovery, separate unconfirmed presentation, preservation through Arsenal enrichment, protected workflow checks, cache versions, master brief, and changelog.
- Files changed: scripts/refresh.py, scripts/enrich_arsenal.py, scripts/finalize_arsenal.py, scripts/responsive_ui_check.py, .github/workflows/morning-refresh.yml, js/app.js, css/features.css, index.html, docs/MASTER-BRIEF-CURRENT.md, and docs/CHANGELOG.md.
- Trusted-list rule: official and established-media transfers remain separate and are ordered by machine-readable publication time, newest first.
- Speculation rule: Reporter watch accepts only public X posts from David Ornstein, Fabrizio Romano, Charles Watts, and James Benge, marks every item unconfirmed, orders them newest first, and excludes betting, gambling, women's-team, academy, U21, U18, youth, and girls' content.
- Reliability decision: use Google News indexing of the four verified X profiles. Direct X recent-search access requires authenticated, pay-per-use API access, which conflicts with the brief's no-paid-API boundary.
- Validation performed: Python and JavaScript syntax, workflow validation code, synthetic filters, live source discovery, responsive Chrome at mobile and desktop widths, successful Morning refresh, successful Pages deployment, generated-feed ordering and allowlist checks, and live Chrome rendering of both lists.
- Unexpected changes: none intended; fixtures, trusted-source rules, the gambling ban, profiles, Calendar, News, AI, Career, Dida, Weather, Around the World, and TV Picks remain unchanged.
- Master brief update: version 1.6 records newest-first ordering and the separate unconfirmed X Reporter watch.
- Follow-up: monitor indexing coverage; an empty Reporter watch is valid when no qualifying recent post is indexed.

## 18 August 2026: News depth, trusted Arsenal transfers, exact imagery, and lime Dida

Status: validated

- Requested change: Add Calendar edge glow; keep at least 10 UK and 10 Local stories; add a trusted Arsenal transfer section; extend Arsenal's red hover to every box; remove generic AI and brief imagery; and make Dida lime, colourful, and icon-led.
- Approved scope: Calendar and Arsenal interaction styling, news collection and protected counts, Arsenal transfer sourcing and filtering, article-image provenance, Dida presentation, cache versions, responsive checks, master brief, and changelog.
- Files changed: scripts/refresh.py, scripts/enrich_arsenal.py, scripts/finalize_arsenal.py, scripts/refresh_story_images.py, scripts/responsive_ui_check.py, .github/workflows/morning-refresh.yml, js/app.js, js/tabs-dida.js, js/story-images-enhance.js, css/app.css, css/features.css, css/tabs-dida.css, css/aurora-nav.css, data/story-images.json, index.html, docs/MASTER-BRIEF-CURRENT.md, and docs/CHANGELOG.md.
- News rule: collect and de-duplicate broader local and national sources, with workflow failure if either profile has fewer than 10 Local News or 10 UK News items.
- Arsenal rule: show Transfer watch at the bottom; accept only approved first-team transfer updates from Arsenal.com, BBC Sport, Sky Sports, The Athletic, The Guardian, Reuters, or ESPN; reject rumour, gossip, paper-talk, betting, academy, and women's-team items.
- Image rule: remove every generic fallback and legacy generic mapping. Use only a high-resolution image selected by the exact matching publisher article page; otherwise keep the card text-only.
- Dida rule: lime-green treatment with playful, relevant code-native icons. No Dida photograph was added because Dida photos must come from Pete and remain exactly as supplied.
- Validation performed: Python and JavaScript syntax, synthetic source and transfer filters, live source breadth, local Chrome at 390px and 1366px, Calendar and Arsenal hover-state checks, Dida visual inspection, successful Responsive UI and Morning refresh workflows, successful Pages deployment, and live Pete/Sofia data and layout inspection.
- Unexpected changes: none intended; existing profiles, shared Calendar content, weather, careers, TV Picks, and Around the World behaviour remain protected.
- Master brief update: version 1.5 records the protected hover, news-count, trusted-transfer, exact-image, and Dida rules.
- Follow-up: monitor the scheduled 5:30am BST refresh; its protected validation will stop publication if either 10-item news threshold or any exact-image/trusted-transfer rule is breached.

## 18 August 2026: England extremes, Chrome navigation, and image coverage

Status: validated

- Requested change: Restrict the warmest and coldest cards to England, always show town and county, repair the Chrome navigation, replace the low-quality Death Valley scenery image, and add more pictures to every article tab without exceeding one picture per article.
- Approved scope: Met Office extremes selection and validation, navigation layout and responsive regression checks, curated Around the World imagery, article-image sourcing and coverage, cache versions, master brief, and changelog.
- Files changed: scripts/enrich_weather_v2.py, scripts/responsive_ui_check.py, scripts/refresh_story_images.py, .github/workflows/morning-refresh.yml, css/tabs-dida.css, js/weather-extremes.js, js/scenery-facts.js, js/story-images-enhance.js, data/story-images.json, index.html, docs/MASTER-BRIEF-CURRENT.md, docs/CHANGELOG.md.
- Weather rule: aggregate only the eight Met Office England regional tables, then choose England's highest maximum and lowest minimum. Reject output unless both locations resolve to an English town and county.
- Navigation fix: restore the intended vertical six-item rail on desktop while preserving the single-row mobile navigation; add minimum button-size and orientation assertions.
- Image rule: replace uncontrolled Wikipedia summary images with curated 2,400px Wikimedia Commons images and reject any loaded source below 2,200 × 1,000 pixels.
- Article-image rule: target five unique images in every populated News, Arsenal, AI, and Career tab for both profiles, keep no more than one per article, require at least 1,200 × 675 pixels, and use relevant Wikimedia Commons fallbacks with API-verified dimensions when a story page has no verifiable high-resolution image.
- Validation performed: live Met Office parsing, synthetic country/county checks, JavaScript and Python syntax, local route checks, Chrome desktop/mobile layout checks, protected workflow validation, production refresh, deployment, and live-page verification.
- Unexpected changes: none intended; profiles, calendars, careers, news, Arsenal, AI, Dida, and TV Picks remain unchanged except for their normal morning data refresh.
- Master brief update: version 1.4 protects the England-only, town/county, high-resolution scenery, and per-tab article-image rules.
- Follow-up: none.

## 17 August 2026: Expanded UK and Sweden career search

Status: validated

- Requested change: Search harder across LinkedIn and other job sites, favour UK or Sweden roles for Sofia, and add more UK roles to Pete's Career section from the same sources.
- Approved scope: Career source collection, profile-specific filtering and ranking, Career validation, generated profile data, master brief, and changelog only.
- Files changed: scripts/refresh.py, data/pete.json, data/sofia.json, .github/workflows/morning-refresh.yml, docs/MASTER-BRIEF-CURRENT.md, docs/CHANGELOG.md.
- Requirements affected: Sofia's senior non-software product and work-pattern rules; Pete's UK Civil Service, public-sector, AI, digital, data, and automation focus; real links; morning reliability.
- Sources: LinkedIn public job listings, Arbeitnow, Remote OK, Remotive, Jobicy, and Sweden's official JobTech feed.
- Reliability: added shared fetching, UK/Sweden preference scoring, 30-day freshness checks, inactive-listing checks, de-duplication, and last-good Career fallback when all live sources fail temporarily.
- Validation performed: filter unit checks, live multi-source integration, full profile refresh, protected workflow assertions, JSON and JavaScript syntax checks, local route checks, and live deployment checks.
- Unexpected changes: none intended; calendar and all non-Career sections remain unchanged except for their normal live refresh.
- Master brief update: version 1.2 records the approved multi-site Career behaviour for both profiles.
- Follow-up: review the first deployed morning refresh and refine Pete's target role profile if he supplies narrower seniority, function, or salary criteria.

## 17 August 2026: Sofia career job matching

Status: validated

- Requested change: Focus Sofia's Career section on posted remote roles or roles with at least three work-from-home days.
- Approved scope: Sofia's Career refresh logic and its protected validation only.
- Files changed: scripts/refresh.py, data/sofia.json, .github/workflows/morning-refresh.yml, docs/MASTER-BRIEF-CURRENT.md, docs/CHANGELOG.md.
- Requirements affected: Sofia profile personalisation, current Career content, real job links, and morning validation.
- Matching profile: senior non-software product development; 17 years at Strategic Insight in B2B financial data.
- Work-pattern rule: fully remote, or explicit evidence of three or more WFH days; generic hybrid wording is rejected.
- Sources: current listings from the public Arbeitnow and Remote OK feeds, with no paid API dependency.
- Validation performed: filter unit checks, live source integration, full profile build, protected workflow assertions, JSON and JavaScript syntax checks, local route checks, and a live-link response check for the current match.
- Unexpected changes: none intended; Pete's Career feed and all unrelated sections remain unchanged.
- Master brief update: added the approved Sofia Career specification.
- Follow-up: validate the first deployed refresh and adjust title coverage only if genuine relevant roles are being missed.

## 17 August 2026

### Master brief v1.0 created

Status: complete

- Consolidated retrievable Brief project decisions into MASTER-BRIEF-CURRENT.md.
- Separated approved intent from the verified implementation baseline.
- Added PROJECT-INSTRUCTIONS.md and QA-CHECKLIST.md.
- Confirmed that /pete/ and /sofia/ routes exist.
- Confirmed that the root profile switch contains Pete and Sofia only.
- Corrected the README reference to the obsolete shared Us view.
- No feature code, layout, content logic, or refresh logic changed.

### Evidence used

- Retrievable Brief project conversation decisions.
- Four Fable Daily Brief UI Concepts.png.
- Four Smartphone UI Concepts Compared.png.
- Current default branch and GitHub Actions workflows.

### Remaining uncertainty

Some older requirements may remain in unretrieved conversation history. Items marked Needs confirmation must not be guessed.

## Entry template

### YYYY-MM-DD: Short change title

Status: proposed | approved | implemented | validated | reverted

- Requested change:
- Approved scope:
- Files changed:
- Requirements affected:
- Validation performed:
- Unexpected changes:
- Master brief update:
- Follow-up:
