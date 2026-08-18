# Daily Briefs Changelog

Newest entries go first.

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
