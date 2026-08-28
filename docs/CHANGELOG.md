# Daily Briefs Changelog

Newest entries go first.

## 28 August 2026: Accessible newsroom contrast and resilient story media

Status: validated and approved for publication

- Approved contrast change: the Home greeting, page titles, section titles, News group headings, Dida page title, and Birthday month headings now use dark `#142A3D` ink directly on the protected `#78B7E0` canvas. Contrast rises from 2.18:1 to 6.76:1 while the solid blue canvas, dark navigation, cards, imagery, and section identities remain unchanged.
- Editorial rules: title dividers now use the existing navy rule colour instead of a low-contrast white line, strengthening the same lead/support/stream hierarchy without changing content order.
- Mobile density: reduced the gap between News groups and tightened group-heading spacing while preserving the divided paper feed, compact thumbnails, and fixed navigation.
- Story-media resilience: News and Arsenal add media geometry only after the exact publisher image loads, decodes, and confirms the existing 1,200 × 675 minimum. Failed or slow images remain text-only instead of showing an empty dark slab.
- Validation: all 27 unit tests pass; JavaScript syntax, Python compilation and diff hygiene pass; the responsive Chromium suite passes at 390 × 844 and 1,366 × 900; reduced motion, locked routes, media readiness, contrast, section ordering, and protected layouts are covered. Pete and Sofia Home, News, Career, Birthday, Dida, AI, and Arsenal screenshots were generated, and the changed mobile/desktop Home, News, and Birthday views were visually inspected.
- Scope protected: no route, profile, section, control, source, content item, ordering rule, card colour, navigation behaviour, or data refresh logic changes.
- Master brief update: version 3.7 records the approved accessible canvas-title treatment and browser image-readiness guard.

## 28 August 2026: Sky-grade editorial refinement loop

Status: validated and published

- Editorial rail: tightened the Chromebook/desktop reading width to 1,120 px and turned the empty top bar into a useful date, refresh-time, weather, and profile utility masthead without restoring a wordmark.
- News: image-verified leads now use an image-left, copy-right desktop package; text-only leads use a deliberate 7/5 lead-and-support rail; stream cards are flatter and mobile feeds use a single divided paper surface.
- Home: Calendar now uses a concise four-box summary row above a natural-height event list, Around the world vertically centres short facts, and the five-card TV layout no longer creates an orphan at intermediate widths. Weather and all four Coming up cards retain their protected full-width order and single-row Chromebook layout.
- AI and Career: repaired the 900–1,099 px orphan layout and balanced the final four desktop stream cards when ten items are present. AI and Career still use code-native icons and no photography.
- Arsenal, Dida, and Birthday: added lead/support/stream roles to all five club-news cards, gave Dida a consistent page title while preserving exactly three white age-six zones, and made Birthday months use one, two, or three balanced columns according to their item count.
- Correctness and accessibility: direct `profile` query parameters are now authoritative over stale local storage, locked routes occupy no switch space, reduced-motion preferences disable scripted smooth scrolling and visual transitions, and keyboard focus retains a real outline fallback alongside destination glows.
- Career curation: removed a duplicate GDS role attributed to the wrong employer and added a refresh guard against the same employer/title mismatch.
- Validation: the responsive Playwright suite now verifies isolated Pete and Sofia routes, direct locked queries, zero switch geometry, profile-specific Arsenal visibility, reduced motion, News and Arsenal hierarchy roles, and the revised editorial geometry at 390 × 844 and 1,366 × 900.
- Protected contrast: the specified white canvas headings on `#78B7E0` remain unchanged. Raising those headings to WCAG AAA would require Pete to approve a colour or title-backing change.
- Publication: PR #13 passed the responsive workflow and was squash-merged as `aac83e7`.
- Master brief update: version 3.6 records the refined editorial geometry, utility masthead, authoritative locked-profile behaviour, adaptive Birthday grid, and reduced-motion requirement.

## 28 August 2026: Open Horizon newsroom structural overhaul

Status: validated and published

- Structural direction: adopted a premium editorial hierarchy inspired by Sky News UK while retaining Daily Briefs' Open Horizon identity, blue canvas, protected ordering, data rules, and bespoke profile sections.
- Home: replaced the long flat desktop stack with intentional full-width newsroom modules, a concise Calendar treatment, a horizontal fact-and-place package, and a lead-plus-four TV grid. All five TV Picks remain visible.
- News, AI, and Career: added explicit lead, supporting, and stream roles. Text-only leads now adapt without empty media-scale slabs; mobile supporting imagery uses compact right thumbnails; AI and Career retain code-native icons and no photography.
- Navigation: repaired locked profile routes so the switch is genuinely hidden, added active-page accessibility state, and reserved an opaque mobile bottom band behind the fixed navigation.
- Protected areas: preserved Arsenal's identity, strengthened five-card club-news rendering, kept Dida's three white age-six zones, and made Birthday single-entry months retain compact desktop card density.
- Data integrity: replaced the incorrect West Malling weather image with Mark Percy's exact-place Northolt clock tower photograph, cached locally at 1,600 × 900 with Commons source and CC BY-SA 2.0 credit. The refresh now has a verified Northolt fallback.
- Arsenal scope: removed a marketing vacancy and an academy signing from trusted Transfer watch. Future Arsenal.com items without explicit first-team context require separate approved-source player corroboration; job and commercial titles are rejected.
- Validation: 25 unit tests, JavaScript syntax checks, Python compilation, diff hygiene, and the Playwright responsive suite pass. Screenshots cover Pete and Sofia Home, News, and Career plus Pete Arsenal, AI, Dida, and Birthday at 390 × 844 and 1,366 × 900.
- Rollback: preserved pre-overhaul main as `backup/pre-sky-news-overhaul-2026-08-28`.
- Publication: PR #11 was merged and the post-release morning refresh completed successfully.
- Master brief update: version 3.5 records the permanent editorial hierarchy and transfer-scope rules; QA wording now matches the fact-first Around the world order.

## 28 August 2026: Open Horizon Daily Brief identity

Status: selected by Pete for immediate publication; deployment validation required

- Selected concept: minimalist yellow sunrise emerging from layered blue open pages.
- Identity coverage: use the same selected mark for the Home navigation, browser favicon, Apple touch icon, Android saved-page icon, installable-app icons, maskable icon, manifest, and link-preview image.
- Cache protection: every browser-facing icon and manifest uses a new immutable Open Horizon filename, while the origin-level `favicon.ico` and Apple touch fallback are also replaced.
- Scope protected: no content, data, profile, layout, section, Arsenal branding, or navigation behaviour changes.

## 28 August 2026: Newest-first Local News, major-event-only sport and supplied cannon

Status: implemented in draft, not published

- Local News rule: merge the current Molesey, Elmbridge and Kingston-area sources before selecting the 12 newest stories, then render them newest to oldest for both profiles.
- TV sport rule: reject routine sports programmes and coverage. The only sports exceptions are World Cup, UEFA Euros and Wimbledon programmes that otherwise satisfy the existing seven-day episode, artwork and destination rules.
- Arsenal identity: extract the exact supplied white cannon from Pete's red artwork as a transparent asset and use that same file for the Arsenal masthead and navigation mask, preventing the two silhouettes from diverging.
- Validation: 20 unit tests pass, including Local News ordering and allowed/blocked sport cases. Responsive mobile and Chromebook validation remains pending on the draft workflow.
- Scope protected: all other sections, profiles, routes, data rules and Daily Brief favicon branding remain unchanged.

## 27 August 2026: Official-site-inspired Arsenal match centre

Status: implemented in draft, not published

- Requested change: use the official Arsenal site's red-led identity and supporting colours to make the brief's Arsenal view more professional, and replace the Premier League table card with the club's current position only.
- Visual system: bright Arsenal red `#E30613`, deep navy `#071D49`, white, and restrained yellow `#FFD51F`. The view now uses a red cannon masthead, white last-result card, navy next-fixture card, compact red position card, clearer club-news hierarchy, and a navy transfer area.
- Position rule: retain the live league-table feed but display only Arsenal's ordinal position. Points and matches played are no longer rendered. The 27 August source refresh returns Arsenal in 2nd.
- Content protected: last result, full next-fixture details, trusted-transfer rules, separate unconfirmed reporter watch, source links, men's-first-team scope, all competitions, and the gambling ban remain unchanged.
- Accessibility: white on red has a 4.88:1 contrast ratio, white on navy 16.39:1, and yellow on navy 11.55:1. All pass WCAG AA for their use.
- Validation: the live data refresh confirmed Arsenal 3–0 Coventry City, Aston Villa away next, and 2nd in the Premier League. Responsive Chromium and visual screenshot checks remain pending on the draft workflow.
- Scope protected: no Home, Weather, Calendar, Around the world, TV Picks, News, AI, Career, Dida, Birthday, navigation, profile, or route change is intended.
- Master brief update: version 3.2 records the permanent Arsenal presentation and position rules.

## 27 August 2026: Dynamic two-week TV Picks

Status: implemented in draft, not published

- Reported defect: the morning TV enrichment rewrote the same five hard-coded programmes, while the browser artwork guard accepted only those same titles. The count-only validator therefore passed even though no new content could appear.
- Eligibility rule: a programme qualifies when any new episode was released during the previous seven days or is scheduled during the next seven days. New episodes count even when the series itself is established.
- Discovery rule: query current UK broadcast schedules and major streaming schedules every morning, rank Pete's existing crime, investigation, documentary, thriller, mystery, science-fiction, football, sport, and history preferences, and exclude news, talk shows, game shows, daily soaps, generic articles, invalid destinations, and programmes without exact artwork.
- Freshness rule: prefer titles not selected during the previous three refresh days, limit over-concentration by service and category, and store 30 days of selection history. Fail before publication if five valid picks cannot be produced.
- Card rule: every pick carries the programme title, episode-specific summary where available, channel or streaming service, available-since or upcoming date, a real programme destination, and exact programme artwork supplied by TVMaze. The old fixed-title browser catalogue is removed.
- Current draft: five picks were generated from 88 eligible programmes for 27 August 2026. Every current destination and artwork URL returned HTTP 200.
- Validation: 17 unit tests pass, including both edges of the previous/next-week window, exact-artwork enforcement, soap/generic-image rejection, rotation before reuse, and the hard stop for too few picks. Responsive browser validation remains pending on the draft workflow.
- Scope protected: no layout, navigation, Weather, Calendar, Around the world, News, Arsenal, AI, Career, Dida, Birthday, profile, or route change is intended.
- Master brief update: version 3.2 records the permanent TV freshness and exact-artwork rules.

## 26 August 2026: Guaranteed weather images and human-first rare facts

Status: validated and published

- Requested changes: never leave the hottest or coldest England card without an image, and replace dull geological facts with much more surprising, little-known facts about people, communities, population, languages, traditions, records, music, and bands around the world.
- Weather image rule: every extreme now receives a locally cached 1,600 × 900 exact-place WebP. Search order is landmark, council or civic building, town centre, then another clearly identifiable exact-place view. The refresh fails before publication if it cannot verify, download, cache, credit, and source both images.
- Current weather repair: Wiggonholt now uses a verified Pulborough Brooks image and Kielder now uses a verified Kielder Water image. Pete and Sofia use the same local, cache-keyed files so a remote image failure cannot leave either card blank.
- Fact rule: new-day selection now chooses an unused `human-first` fact before any general catalogue item. Eight source-verified facts were added across extraordinary people, population and language records, living traditions, record-breaking music culture, indigenous music, and human-animal communication.
- Current fact: the Eye of the Sahara item is replaced by Jeju's haenyeo, women breath-hold divers who continue the tradition into their 80s.
- Validation passed: all 12 unit tests cover known exact-place image fallbacks, human-first selection, and the existing Arsenal guards. The responsive Chromium workflow passed at 390 × 844 and 1,366 × 900, requiring two visible sourced weather images, a human-first current fact, stable mobile navigation, and all protected layouts. Both Home screenshots were visually inspected.
- Scope protected: no layout, navigation, Calendar, News, Arsenal, AI, Career, Dida, Birthday, TV Picks, profile, route, or unrelated content change is intended.
- Publication: Pete approved the preview and PR #7 was published on 26 August 2026. The post-merge morning refresh succeeded. Both profile routes and both local weather-image files returned HTTP 200, and the live Pete and Sofia data retained the Jeju haenyeo fact plus the cached Wiggonholt and Kielder images.
- Master brief update: version 3.1 records both permanent rules.

## 25 August 2026: Dark-navy navigation and separated Coming up text

Status: validated and published

- Requested changes: replace the dark-grey navigation surface with dark navy, and keep all Coming up text on the coloured left side of each artwork card so it never runs over the picture.
- Approved scope: navigation surface and shadow, Coming up text and artwork geometry, CSS cache keys, responsive validation, master brief, QA checklist, and changelog only.
- Navigation rule: use solid dark navy `#102A43` on mobile and desktop while retaining white resting labels and icons, the active treatment, brighter per-destination hover and focus colours, the aurora edge, and fixed mobile stability.
- Coming up rule: reserve a 55% left text column and a 42% right artwork column, leaving separation between their layout boxes. Keep the pastel card identities, dark text, dynamic dates and countdowns, current supplied artwork, crops, hover feedback, mobile stacking, and compact four-card Chromebook row.
- Validation passed: all eight unit tests and the full responsive Chromium workflow verified the exact dark-navy surface, white resting navigation, destination hover colours, stable mobile switching, left-only Coming up text geometry, right-side artwork, mobile stacking, and the compact four-card Chromebook row. Mobile and Chromebook screenshots were visually inspected.
- Publication: Pete approved the preview and PR #6 was published on 25 August 2026.
- Master brief update: version 3.0 records both requested rules.

## 25 August 2026: Supplied artwork for Coming up cards

Status: validated and published

- Requested change: publish Pete's newly uploaded recycling, normal-bin, clocks, Halloween, and Christmas images on their matching Home `Coming up` cards.
- Approved scope: those five supplied source images, optimised display crops, Coming up rendering and layout, cache keys, responsive validation, master brief, QA checklist, and changelog only.
- Artwork rule: show the supplied subject artwork on the right side of its matching card while keeping the existing solid pastel surface and current dynamic text on the left. The display crops omit the obsolete 2025 dates, fixed countdown numbers, and decorative `View calendar` controls embedded in the source compositions.
- Performance rule: use compact WebP display crops totalling less than 210 KB rather than loading the five source files, which total more than 6 MB.
- Requirements protected: four cards on one Chromebook row, mobile stacking and navigation visibility, dark readable text, existing pastel card identities, live countdown calculations, stationary cyan hover, Birthday card treatment, both profiles, all routes, and every unrelated section.
- Validation passed: all eight unit tests and the full responsive browser workflow verified the correct live mapping, decoded image dimensions, full-height crop, no overflow, pastel backgrounds, dark text, compact Chromebook row, mobile stacking, navigation visibility, and all existing protected behaviour. Mobile and Chromebook screenshots were visually inspected.
- Unexpected changes: none intended.
- Publication: published after Pete's approval on 25 August 2026. Pete, Sofia, the cache-keyed renderer, and all five display images returned HTTP 200 from the live GitHub Pages site.
- Master brief update: version 2.9 records the approved supplied-artwork rule.

## 24 August 2026: Dark-grey navigation with white resting labels

Status: validated and approved for publication

- Requested change: make the primary navigation dark grey with white text so it stands out more.
- Approved scope: navigation surface, resting text and icon colours, brighter destination hover colours, cache key, responsive regression coverage, master brief, and changelog only.
- Navigation rule: use solid dark grey `#343A40` on mobile and desktop. Every label and code-native icon is white at rest, including the active destination; the existing destination identities appear only through brighter, readable hover and keyboard-focus colours.
- Requirements protected: mobile fixed-bar stability, desktop vertical rail, 44 px controls, active-state clarity, aurora outline, Birthday balloon, Arsenal cannon, hover-only destination colour behaviour, Pete and Sofia profiles, all content, data, sources, routes, and unrelated styling.
- Validation passed: all eight unit tests and the responsive Chromium workflow require the exact dark-grey surface, white resting labels and icons, every brighter destination hover colour, stable repeated mobile navigation switching, and all existing protected responsive behaviour. Mobile and Chromebook screenshots were visually inspected.
- Unexpected changes: none intended.
- Master brief update: version 2.8 replaces the previous light navigation and dark resting-text rule.
- Publication: Pete approved publication on 24 August 2026.

## 24 August 2026: Compact reminders, stronger hover feedback, simplified Dida, and month-grouped Birthday cards

Status: validated and approved for publication

- Requested changes: remove the visible `Daily Briefs` text; use consistent dark ink for main copy; make the Home greeting and blue-canvas titles white; remove the Around the world subtitle; keep navigation neutral until hover and prevent it disappearing temporarily on mobile; give Home `Coming up` cards solid pastel surfaces with Halloween in orange; fit all four reminders on one Chromebook row; strengthen hover feedback consistently; remove Dida's top section and extra header copy; and simplify Birthday into white cards grouped by month.
- Wordmark rule: the visible hero wordmark is removed. Browser titles, bookmark metadata, manifest identity, icons, and sharing metadata retain the Daily Briefs name.
- Text rule: readable copy on light surfaces uses `#142A3D`. The Home greeting and titles sitting directly on the blue canvas use white; titles inside light cards retain a contrasting dark or purposeful accent. Text over dark photographic media remains light to preserve contrast. The old `Rare facts · wild places` subtitle is removed.
- Navigation rule: all navigation text and code-native icons use `#142A3D` at rest, including the active destination. The existing per-destination colours appear only on hover or keyboard focus.
- Mobile navigation stability: destination changes scroll to the new view immediately on mobile instead of starting a smooth-scroll compositor transition. The fixed bar uses an opaque surface, safe-area-aware bottom position, forced visibility, and a higher stable stacking level.
- Coming up rule: bin day uses pastel mint, clocks use pastel lavender, birthdays use pastel pink, and seasonal reminders use a dedicated solid pastel palette. Halloween uses pastel orange `#FFC27A`. At Chromebook widths, the four cards use a shorter four-column row.
- Hover rule: Calendar, News, AI, Career, Coming up, Birthday, Dida, Weather, and Around the world cards use one stronger stationary cyan glow. Arsenal retains an equally visible red treatment, TV artwork retains gold, and navigation keeps its destination colour.
- Dida rule: the hero and duplicate mini-navigation are removed. The three independent boxes remain, and each header now contains only `This week`, `Seasonal missions`, or `Reference library`. The age-six source moves into Reference library without removing any ideas or guides.
- Birthday rule: the destination is labelled `Birthday` once, the static-family subtitle and repeated generic heading are removed, cards are de-duplicated, grouped beneath white month headings, arranged on the same row per month when space allows, and use solid white surfaces. Bright pink remains for outlines, highlights, and navigation hover; the Home reminder remains pastel pink.
- Validation passed: all eight unit tests and the responsive browser workflow cover the compact four-card reminder row, stronger hover parity, repeated mobile navigation switching and viewport visibility, simplified three-zone Dida structure, month grouping, solid-white Birthday cards, unique entries, responsive layouts, contrast, and all previously protected content.
- Requirements protected: solid blue canvas, Pete and Sofia profiles, Daily Brief bookmark identity, colourful Birthday balloons, Dida green titles and outlines, image-overlay contrast, navigation geometry, links, content, and data sources.
- Unexpected changes: none intended.
- Master brief update: version 2.7 records the wordmark, text, navigation, compact Coming up, hover, Dida, and Birthday rules.
- Publication: Pete approved publication on 24 August 2026.

## 24 August 2026: Solid blue canvas, white Dida cards, bright Birthday pink, and current Arsenal fixture

Status: implemented, awaiting preview approval

- Requested changes: keep UK News directly below Local News; correct the stale upcoming Arsenal match; replace the pale gradient canvas with a solid blue that is not too dark; make every Dida card and icon surface white with a brighter green only for titles and outlines; and replace the muted Birthday colour and navigation treatment with bright pink.
- News status: the existing draft already stacks UK News directly beneath Local News for Pete and Sofia, with Sweden retained above Local News for Sofia.
- Arsenal correction: the next men’s first-team fixture is Aston Villa away at Villa Park on Monday 31 August 2026 at 8:00pm, live on Sky Sports. The previous meeting is Arsenal 4–1 Aston Villa on 30 December 2025. The fixture now links to the updated Premier League schedule.
- Arsenal refresh repair: the official fallback now reads the Premier League’s maintained all-380-fixtures page before the original club-release page, captures broadcaster data, and replaces a stale same-opponent league fixture without displacing an earlier fixture from another competition.
- Canvas: the root, body, and top bar now use one solid medium-light blue, `#78B7E0`, with no gradient or decorative wash.
- Dida: the hero, three independent zones, inner cards, navigation boxes, and icon surfaces are white. Fresh green `#00823B` is restricted to titles and outlines; body text and icons remain neutral. The approved cyan hover/focus glow is retained.
- Birthdays: the section heading, card outlines, cards, Home reminder, milestone card, and navigation state now use a vivid pink treatment. Darker ink is used for card details so text contrast remains at least 4.5:1.
- Validation: fixture parser and stale-schedule regression tests added; responsive checks now require the exact solid canvas, updated fixture details, bright Birthday treatment, white Dida surfaces, fresh green titles/outlines, existing hover effects, News order, and mobile/desktop layout. The preview workflow now exports screenshots for review before publication.
- Requirements protected: Pete and Sofia profiles, real links and sources, all sections and content, Dida age-six copy and three-box spacing, colourful birthday balloons, responsive behaviour, and unrelated card treatments.
- Unexpected changes: none intended.
- Master brief update: version 2.5 records the approved canvas, Dida, and Birthday colour rules.
- Publication: draft only. Do not merge or publish until Pete approves the screenshots.

## 23 August 2026: Bookmark icon cache repair

Status: implemented, awaiting preview approval

- Requested change: Stop newly saved Daily Brief bookmarks from showing the obsolete Bomberfan logo.
- Root cause: the committed artwork is the approved Daily Brief rising-sun and layered-news-card design, but bookmark metadata still reused the original origin-level icon filenames. Chrome can retain that earlier Bomberfan association in its favicon database despite query-string cache keys.
- Fix: publish the approved artwork under entirely new immutable filenames for shortcut icon, ICO favicon, 32 px favicon, Apple touch icon, 192 px icon, 512 px icon, and maskable icon. Root, Pete, Sofia, Open Graph, and manifest metadata now use those new paths.
- Requirements protected: the approved Daily Brief artwork is reused without alteration; no page layout, profile, content, navigation, data source, or unrelated branding changes.
- Validation prepared: static checks require the new filenames in root and both profile routes, verify the new manifest identity and icon set, and retain mobile and desktop browser coverage.
- Unexpected changes: none intended.
- Master brief update: none. This repairs the existing dedicated-icon requirement without changing the specification.
- Follow-up: after publication, remove any existing Bomberfan bookmark once and save the Daily Brief again so Chrome creates a new bookmark record from the new icon URLs.

## 23 August 2026: Tidier News, corrected Arsenal result, independent Dida boxes, and Birthday glow

Status: implemented, awaiting preview approval

- Requested change: Put UK News underneath Local News, correct the Arsenal result, restyle Dida as three independent blue/neutral boxes, and give Birthday, Career, and Dida cards the same hover treatment as Calendar Today/Tomorrow.
- Approved scope: News group layout, Arsenal first-team result validation and current data, Dida surfaces and separation, Birthday hover/focus states, cache keys, responsive and refresh regression coverage, safe preview-branch workflow routing, master brief, and changelog.
- Arsenal correction: the under-21 Crystal Palace report is no longer eligible for the men’s first-team result. The latest result is Arsenal 3–0 Coventry City, Premier League, Friday 21 August 2026. Academy, youth, women’s-team, and girls’ stories are now excluded from first-team Arsenal news and result parsing at collection, enrichment, and finalisation.
- News layout: News groups stack vertically in profile order, placing UK News directly below Local News while retaining Sweden above Local News for Sofia. Article cards keep their existing responsive grid.
- Dida layout: the shared green outer container is removed. This week, Seasonal missions, and Reference library are independent blue/neutral cards with their existing 28 px mobile and 36 px desktop gaps. Lime is reserved for occasional icons, labels, badges, links, and interactive highlights.
- Birthday interaction: every Birthday card and the Home birthday reminder uses the Calendar cyan edge-glow on mouse hover and keyboard focus, with no movement and no replacement of the existing pastel card backgrounds.
- Career and Dida interaction: Career story cards and Dida’s hero and three zone cards use the same Calendar cyan edge-glow, with no movement. Career also retains keyboard-focus parity, while a Dida zone glows when its interactive content receives keyboard focus.
- Requirements protected: Pete/Sofia profiles, news content and links, age-six Dida copy and source, all existing Dida ideas and collapsed reference groups, birthday artwork and contrast, and unrelated views.
- Release safety: script changes on a preview branch can no longer start a refresh job that resets to and writes into main; the refresh push trigger is explicitly main-only.
- Validation prepared: Python regression tests reject youth result stories and prefer the correct first-team report; morning validation rejects ineligible Arsenal news; responsive checks compare Birthday and Calendar computed hover shadows, verify no movement, assert News order, and verify the independent neutral Dida surfaces.
- Unexpected changes: none intended.
- Master brief update: version 2.4 records the approved News ordering, Dida surface rules, and Birthday, Career, and Dida interaction treatments.
- Follow-up: complete local QA, stage the preview, and publish only after Pete approves it.

## 23 August 2026: Clearer Dida zones and age-six content

Status: validated

- Requested change: Separate the three Dida sections more clearly, use neutral readable text with green reserved for boxes and highlights, and change the content for a six-year-old.
- Approved scope: Dida spacing, Dida light-theme text colour, age-specific Dida copy and source, cache keys, responsive regression coverage, master brief, and changelog.
- Files changed: js/tabs-dida.js, css/tabs-dida.css, css/light-theme.css, index.html, scripts/responsive_ui_check.py, docs/MASTER-BRIEF-CURRENT.md, and docs/CHANGELOG.md.
- Spacing rule: keep the three existing zones and add 28 px between them on mobile and 36 px on Chromebook/desktop.
- Colour rule: use neutral dark ink and blue-grey body text; keep lime green for containers, borders, icons, badges, links, and interactive highlights.
- Age rule: update the hero, development guide, teaching ideas, games, seasonal quantities, and birthday runway from age five to age six. Replace the old age-five CDC link with the real CDC ages 6–8 guide.
- Requirements protected: the approved light sky-blue and lavender app background, all three Dida zones, every Dida idea and guide, four collapsed reference groups, both profiles, all routes, and every unrelated view and feed.
- Validation prepared: mobile and desktop checks require three zones, 28/36 px gaps, neutral Dida body text, age-six wording, the real age-six source, lime accents, and the existing collapsed reference library.
- Publication: published after Pete's approval on 23 August 2026.
- Unexpected changes: none intended.
- Master brief update: version 2.2 records the approved age-six, spacing, and neutral-text rules.
- Validation result: Responsive UI check, Morning refresh, and Pages deployment passed. Pete and Sofia returned HTTP 200; the deployed Dida assets contain the age-six copy, 28/36 px zone gaps, neutral body text, new cache keys, and no preview-only redirect.

## 23 August 2026: Light-theme Birthday cards

Status: validated

- Requested change: Reject option D, retain the current approved light background, and improve the Birthday card backgrounds so they match it.
- Approved scope: Birthday and anniversary list cards, the Home Birthday reminder card, Birthday balloon-card enhancement styles, cache keys, responsive regression coverage, master brief, and changelog.
- Files changed: js/home-reminders.js, js/hq-birthday-balloons.js, js/calendar-cleanup.js, index.html, scripts/responsive_ui_check.py, docs/MASTER-BRIEF-CURRENT.md, and docs/CHANGELOG.md.
- Card rule: replace the inherited dark purple Birthday surfaces with pale pink, blue, lavender, mint, and gold-tinted gradients while preserving the existing individual balloon palettes.
- Readability rule: Birthday names, dates, countdowns, and reminder text must retain at least 4.5:1 contrast against every gradient stop.
- Requirements protected: the approved light sky-blue and lavender app background, both profiles and greetings, Birthday navigation balloon, all Birthday data, every route, every unrelated view, and all content feeds.
- Validation prepared: mobile and desktop checks now inspect Birthday cards for both Pete and Sofia, require light surfaces, require balloon artwork, and calculate text contrast against every rendered gradient stop.
- Publication: published after Pete's approval on 23 August 2026.
- Unexpected changes: none intended.
- Master brief update: version 2.1 records the approved light Birthday-card rule.
- QA discovery: the first responsive run exposed an over-broad Pete profile selector in the new test, which matched both the profile button and navigation container. The selector was narrowed to the profile switch without changing the interface.
- Validation result: the corrected responsive workflow passed at 390 × 844 and 1,366 × 900 for Pete and Sofia. Morning refresh and Pages deployment passed, both live profile routes returned HTTP 200, and the deployed Birthday asset and cache keys match the approved light-card build.

## 22 August 2026: Lighter theme and permanent rare-fact history

Status: validated

- Requested change: Make the dark-blue interface much lighter and easier to read; remove navigation stars and sparkles; move the Pete/Sofia greeting down slightly; and make Fact of the Day genuinely rare, fact-first, image-second, and permanently non-repeating.
- Theme rule: use a light sky-blue and soft-lavender canvas with dark ink text, pale cards, restrained coloured accents, and deliberate dark overlays only on image-led media.
- Navigation rule: preserve the clean aurora edge but remove every star field, twinkle layer, sparkle pseudo-element, and sparkle glyph. Dida now uses an open-book mark.
- Wordmark rule: move `Daily Briefs` out of the sticky top bar and place it directly above the date without duplication.
- Greeting rule: retain `Hey Pete` and `Hey Sofia` at the smaller approved scale, with extra spacing below the date so the greeting sits more naturally before Weather.
- Fact rule: the verified fact card now appears before its matched image. The first fact explains how Antarctica’s Blood Falls turns red only after clear iron-rich brine meets air.
- No-repeat rule: a committed fact history records each published ID forever. Duplicate catalogue text, duplicate IDs, duplicate history IDs, or two facts on one date fail validation. Catalogue exhaustion fails the refresh instead of recycling.
- Editorial range: the curated catalogue prioritises wild places and also covers extreme life, human origins, population-scale planet facts, impossible landscapes, and unique travel.
- Image rule: each fact includes a matching, attributed image of at least 2,200 × 1,000; no low-resolution or generic fallback is displayed.
- Requirements protected: profile routes, calendar, Met Office weather, Arsenal content rules, Career/AI icon treatment, three-zone Dida structure, birthday balloon, cannon mark, navigation geometry, links, and all unrelated data feeds.
- Validation added: mobile and desktop checks cover light-theme brightness, fact-before-image order, verified fact loading, greeting spacing, and complete navigation sparkle removal; Morning refresh validates the permanent fact ledger.
- QA discoveries resolved: a legacy birthday-card enhancement was replacing the requested single nav balloon with a three-balloon graphic, so its nav override was removed while preserving its card artwork. The responsive workflow now runs automatically for every HTML, CSS, JavaScript, profile-page, or test change, and the Calendar assertion returns to the visible Home view before checking hover behaviour.
- Validation result: the final responsive workflow passed at 390 × 844 and 1,366 × 900, including both greetings, the single balloon, Arsenal cannon, light theme, fact-first layout, navigation geometry, Career/AI icons, three-zone Dida structure, Calendar glow, and Arsenal content.
- Unexpected changes: none intended.

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
