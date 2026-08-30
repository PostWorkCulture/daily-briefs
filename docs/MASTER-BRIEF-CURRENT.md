# MASTER BRIEF - CURRENT

Version 4.1, 30 August 2026. Owner: Pete.
Repo: PostWorkCulture/daily-briefs
Live: https://postworkculture.github.io/daily-briefs/

This is the single source of truth. Preserve every requirement unless Pete explicitly supersedes it. Never change or remove an unrelated section, route, control, field, data source, link, colour treatment, or responsive behaviour. Flag conflicts before editing. Update this file and CHANGELOG.md after approved specification changes. Run QA-CHECKLIST.md after material work.

## Product

Daily Briefs is an exciting, futuristic daily-use morning brief. Combine FABLE OS structure, Morning Story speed and emotion, and Pete/Sofia family personalisation. Use a solid medium-light blue canvas, dark `#142A3D` ink for main copy on every light surface, restrained luminous accents, rounded cards, bold legible type, and meaningful warm photography. Reserve light text for image-led media cards where a strong dark overlay is required for readability. Preserve header styling during unrelated work.

- Use an `Open Horizon newsroom` hierarchy inspired by premium news homepages without copying their identity: firm section rules, a clear lead/supporting/stream rhythm, intentional desktop grids, and denser mobile scanning. Prominence comes from width, position, type scale, and verified imagery, not fabricated labels or reordered source content. Keep bespoke systems for Arsenal, Dida, Birthday, Weather, Coming up, Calendar, Around the world, and TV Picks.
- Cap the main Chromebook/desktop editorial rail at 1,120 px. Do not use a utility top bar. On locked profile routes, the main brief date must be the first visible line, followed by the greeting; never duplicate the date, weather status, or profile identity above it.
- Text-only news leads are valid and must use a purposeful 7/5 lead-and-support desktop rail rather than reserving an empty image-scale area. Image-verified desktop leads use a prominent image-left, copy-right package. Desktop stream stories share one flat divided paper rail instead of appearing as separate floating tiles. On mobile, only an image-verified lead uses full-width media; supporting and stream stories use compact thumbnails where exact publisher imagery exists, and secondary items form a flat divided paper feed rather than a wall of identical cards.

- The Home greeting and section or page titles that sit directly on the solid blue canvas use dark `#142A3D` ink, giving at least 4.5:1 contrast. Titles inside white or light cards retain the same readable dark ink or a purposeful accessible accent colour. Reserve white text for dark surfaces and strongly overlaid media. Main copy on light surfaces remains dark `#142A3D`.

- Do not show a visible `Daily Briefs` wordmark in page content. Retain the Daily Briefs browser title, bookmark, manifest, icon, and sharing metadata.
- Primary navigation uses a solid dark-navy `#102A43` surface with white text and icons at rest, including the active destination. Each destination uses a brighter version of its existing colour only on hover or keyboard focus so the feedback remains readable against the dark surface.
- Respect `prefers-reduced-motion`: destination changes and in-page controls must not request smooth scrolling, navigation decoration must not animate, and hover/focus transitions must become effectively immediate. Keep a real visible keyboard-focus outline in addition to destination glows.
- On mobile, primary navigation remains fixed, fully visible, and clickable while switching destinations or interacting with content. Use immediate mobile view changes and a stable opaque navigation surface to avoid compositor flicker.
- Home `Coming up` cards retain solid pastel text surfaces with dark `#142A3D` text and use Pete-supplied artwork as a cropped right-side visual where a matched image exists. Keep all live card text inside a dedicated left-side text column on the solid pastel area, with no overlap into the artwork. Recycling, general and garden waste, clocks, Halloween, and Christmas each use their matching supplied image. General-bin weeks must be titled `General & garden waste` with the concise instruction `Put out both bins`; garden waste remains collected on those weeks. Crop out the dates, countdown numbers, and fake controls embedded in the source compositions so the live dynamic card text remains authoritative. Halloween retains pastel orange. From 700 px upwards, all four cards must fit on one compact row.
- Interactive card hover and keyboard-focus feedback must be clearly visible, stationary, and consistent in strength throughout the brief. General cards use cyan, Arsenal cards retain red, and image-led TV cards retain gold.

- Use Pete's selected minimalist Open Horizon artwork, a yellow sunrise emerging from layered blue open pages, as the dedicated Daily Brief icon across favicon, Apple touch, Android saved-page, installable-app, link-preview, and Home navigation metadata. Use new immutable filenames when changing icon artwork so mobile favourites cannot reuse an old cached identity. Keep Daily Brief branding separate from Bomberfan and Arsenal.
- Primary navigation uses a single code-native balloon for Birthdays and the exact same supplied cannon silhouette used in the Arsenal masthead. Birthday navigation uses vivid bright pink on hover or keyboard focus. Keep the aurora edge restrained and do not use stars, sparkles, twinkles, or sparkle glyphs in the navigation.
- The Birthday destination and navigation label are both `Birthday`. Do not repeat a generic Birthdays subheading beneath the page title.
- Birthday and anniversary cards use solid white surfaces with vivid bright-pink outlines and highlights. The Birthday page title and month headings use dark `#142A3D` ink on the blue canvas. Group cards under month headings, and place cards from the same month on one line where the viewport allows. Keep the colourful balloon artwork, dark readable text, unique entries, and a minimum 4.5:1 text contrast. The Home birthday reminder retains its solid pastel-pink surface.
- Birthday and anniversary cards, including the Home birthday reminder, use the same visible cyan edge-glow as Calendar summary boxes on hover and keyboard focus, without movement.

## Boundaries

- Use only PostWorkCulture/daily-briefs. The old Claude/API repo is obsolete.
- No Anthropic/OpenAI API dependency or paid API credits.
- Static responsive GitHub Pages app with JSON data and Python/GitHub Actions refresh.
- Target the full morning refresh for 06:00 `Europe/London` every day. Use GMT/BST-safe UTC triggers, retry at 30-minute intervals while today's edition is still stale, and skip the remaining retries as soon as both profiles carry today's publication date.
- Never commit private calendar credentials.
- Mobile first. Chromebook/desktop must have an intentional larger-screen layout.
- Always use real, clickable links. Never invent data, URLs, sources, or test results.

## Profiles

Pete and Sofia each have a personal brief. Root switch contains Pete and Sofia only. Keep /pete/ and /sofia/ routes and data/pete.json and data/sofia.json consistent. Never restore the obsolete Us profile.

- A valid `profile=pete` or `profile=sofia` query parameter is authoritative over local storage. Locked profile routes hide the switch and must not reserve any geometry for it. Pete routes show Arsenal; Sofia routes do not.

- The Home greeting is `Hey Pete` for Pete and `Hey Sofia` for Sofia, without trailing punctuation.
- Keep the greeting deliberately smaller than the previous headline: 36–52 px below 900 px and 52–68 px from 900 px upwards.
- Do not display the `Daily Briefs` wordmark in page content.
- Place the greeting slightly lower in the hero so it sits comfortably between the date and the Weather panel.

## Current structure

Primary views: Home, News, Arsenal, AI, Career, Dida, Birthday.
Home: Weather, Coming up, Calendar, Around the world, TV Picks.
Do not remove, duplicate, or silently reorder them. Calendar stays above Arsenal in any shared flow.

## Protected requirements

**Weather**
- Met Office only for home area, currently KT8 2LE.
- Daily weather only. No advice or best-time content.
- Visual must match wording. Rain icon only for actual rain/showers, not rain probability.
- Sunny intervals, partly cloudy, and light cloud must be distinguishable.
- Yesterday's warmest and coldest cards must use Met Office observations from England only. Never select Scotland, Wales, Northern Ireland, or another country.
- Both extreme cards must display the verified town and English county in `Town, County` form.
- Both extreme cards must always display a locally cached 1,600 × 900 image of the exact place. Source a landmark first, then a council or civic building, town centre, or another clearly identifiable exact-place view. Retain its source and credit. If no verified image can be found or cached, fail the morning refresh instead of publishing a blank card.

**Calendar**
- Real content refreshed every morning through GOOGLE_CALENDAR_ICS_URL.
- Real links, no duplication, no Soon or For you groups.
- No duplicate Today/Tomorrow pills. Keep numbered controls.
- Today, Tomorrow, This week, and This month summary boxes use a visible cyan edge-glow on hover and keyboard focus, without moving the box.
- On Chromebook/desktop, show the four summary boxes in one concise row above a natural-height event list; a short list must never stretch into a dead white slab.

**Around the world**
- Lead with one genuinely astonishing, obscure, source-verified fact each day, then show its precisely matched place image beneath it.
- Show only the `Around the world` title above the fact. Do not display the old `Rare facts · wild places` subtitle.
- Prioritise genuinely rare human stories from different countries: extraordinary people and communities, population and language records, indigenous traditions, unusual customs, record-breaking achievements, and surprising music or band culture. Wild places and planet facts remain occasional variety, not the default.
- Keep a curated human-first queue large enough to prevent dull fallback. New-day selection must choose an unused human-first fact before any general catalogue item.
- Track every published fact ID in a committed permanent history. Never reuse an ID or duplicate fact text; if the catalogue is exhausted, fail the refresh instead of repeating.
- Every fact must display a useful wider location line in `place/area · country/region` form so an unfamiliar location is understandable without prior knowledge. Retire an item from future selection when Pete rejects it as dull; keep its ID only for permanent history integrity.
- Use curated, place-matched images at least 2,200 pixels wide and 1,000 pixels high. Never display a low-resolution fallback.
- On Chromebook/desktop, short fact copy may be vertically centred beside its image so the 4/8 package uses its whitespace intentionally; fact-first DOM order remains mandatory.

**TV Picks**
- Show five current, named programmes per profile. An eligible pick has released a new episode within the previous seven days or will release one within the next seven days; a new episode qualifies even when the series itself is not new.
- Refresh the selection every morning from current UK broadcast and major-streaming schedules. Prioritise documentaries—especially murder, scandal, corruption, fraud, cult, prison, and other dark investigations—plus thrillers, mysteries, `Silo`, science fiction, and strong new Apple TV+ series or season premieres. Prefer BBC iPlayer, Channel 4, and Netflix, followed by Apple TV+, when equally strong current programmes are available. Exclude every reality programme, including misclassified Gary Barlow or celebrity-travel shows, as well as routine sport, news, talk shows, game shows, daily soaps, generic articles, and programmes without a real destination. The only sports exceptions are World Cup, UEFA Euros and Wimbledon programmes.
- Give every card the exact programme artwork supplied by the schedule source, a service or channel, and a clear available-since or upcoming date. Never use generic streaming art, logos, screenshots, placeholders, or a fixed title allowlist.
- Prefer titles not used during the previous three refresh days, keep source and category variety, and fail before publication if five valid current picks cannot be produced. Keep a committed 30-day selection history so freshness is testable.

**Arsenal**
- Use an official-site-inspired Arsenal visual system: bright red `#E30613`, deep navy `#071D49`, white, and restrained yellow `#FFD51F`. The section opens with a red masthead using Pete's supplied white cannon, and the nav uses that exact same silhouette. Use strong match-centre hierarchy, white and navy match cards, a red league-position card, clean club-news cards, and a navy transfer area. Keep it professional, high-contrast, stationary on hover, and responsive.
- Do not show a Premier League table, points total, or matches-played total. Show only Arsenal's current ordinal league position, refreshed from the live table source.
- No betting, odds, gambling promotion, or gambling information.
- Men's first team, all competitions.
- Latest completed and nearest upcoming fixtures.
- The latest completed match must always show score, scorers, competition, a concise factual game summary, actual kickoff time, and stadium. If any required result field cannot be verified, fail the refresh instead of publishing an incomplete result.
- Preserve opponent, stadium, kickoff, competition, TV channel, and previous-meeting details for the upcoming fixture when available.
- Put Transfer watch at the bottom of the Arsenal view and always order it newest first. Its trusted list includes only official announcements or reports from Arsenal.com, BBC Sport, Sky Sports, The Athletic/The New York Times, The Guardian, Reuters, or ESPN. Reject rumour roundups, gossip, paper talk, betting, odds, job vacancies, commercial roles, academy, and women's-team items from this trusted list. An Arsenal.com item without explicit first-team context must be corroborated by a separate approved source identifying the same player before it can appear.
- Beneath the trusted list, show a separate Reporter watch for early, speculative public X posts. Mark every item `Unconfirmed · X`; never mix it into trusted reporting. Allow only David Ornstein, Fabrizio Romano, Charles Watts, and James Benge. Order it newest first and reject betting, gambling, women's-team, academy, U21, U18, youth, and girls' items.
- Discover allowlisted public X posts through Google News indexing so the brief does not require a paid X API, credentials, scraping proxy, or new morning-refresh secret.
- Apply the red edge-glow hover/focus treatment to every Arsenal card, including fixtures, league position, news, and transfer updates.
- Render the five Club news items with explicit lead, two-support, and two-stream roles while preserving source order and exact-image eligibility.

**News, AI, Career, Dida**
- Keep each destination working and independent.
- Use current content and real source links.
- Keep at least 10 current items in Local News and at least 10 current items in UK News for both profiles.
- Merge Local News candidates across all configured local searches before selecting the newest items, and always render Local News strictly newest to oldest.
- Stack News groups vertically, with UK News directly underneath Local News. Sofia keeps Sweden above Local News.
- Show up to five unique, high-resolution article images in each News and Arsenal view, with no more than one image per article, but only when the exact matching publisher page supplies that image. Keep the article text-only when exact publisher provenance cannot be verified.
- Add an article media block in the browser only after its exact publisher image has loaded, decoded, and met the 1,200 × 675 minimum. A failed or slow image must leave the story text-only instead of reserving an empty dark media slab.
- AI and Career never show article photography. AI uses the exact company mark when OpenAI or ChatGPT, Google or Gemini, Google DeepMind, Anthropic, or Claude is unambiguous in the story metadata; use the generic code-native AI symbol as fallback. Career retains stylish code-native section icons. Preserve the current article and job content, metadata, and real links.
- Career cards use the same cyan edge-glow as Calendar summary boxes on hover and keyboard focus, without movement.
- Never use stock, topic-level, personality, search-library, Wikimedia, tab-level, generic, inferred, or guessed article-image fallbacks. This exact-relevance rule supersedes the earlier five-image minimum.
- Article images must be at least 1,200 × 675 pixels. Reject logos, icons, placeholders, low-resolution sources, duplicate sources, and near-duplicate publisher imagery.
- Do not change them as a side effect of other work.
- Sofia's Career section shows current senior non-software product roles suited to her 17 years in product development at Strategic Insight, a B2B financial-data company.
- Sofia's roles must be fully remote or explicitly offer at least three work-from-home days per week. Generic hybrid roles do not qualify without evidence of that working pattern.
- Favour UK- and Sweden-based roles for Sofia; Europe-wide remote roles are a lower-priority fallback.
- Pete's Career section shows current UK roles in Civil Service, public sector, AI, digital, data, and automation, using the same multi-site search pool as Sofia.
- Career searches include LinkedIn, Arbeitnow, Remote OK, Remotive, Jobicy, and Sweden's official JobTech feed. Reject duplicates, listings older than 30 days, inactive listings when detectable, and links that are not real HTTP(S) job pages.
- Reject job listings whose title names Government Digital Service but whose listed employer is a different organisation; this is treated as a mismatched aggregator duplicate.
- Dida is for a six-year-old. Use age-six development guidance, learning ideas, games, seasonal missions, and birthday activities, with a real age-appropriate source link.
- Dida has a single page-level `Dida` title but no hero or duplicate section-navigation block. It then opens directly with three independent boxes: This week, Seasonal missions, and Reference library. Each box header contains only that title, without a number, kicker, or description. Use white backgrounds for every zone, inner card, and icon surface; fresh bright green only for titles and box outlines; and neutral icons and body copy. Keep at least 28 px between zones on mobile and 36 px on Chromebook/desktop, keep weekly quick wins first, preserve every existing idea and the real age-six source, and keep all four reference groups collapsed by default on mobile and desktop.
- Dida’s three independent zone cards use the strong Calendar cyan edge-glow on hover or when they contain keyboard focus, without movement.
- Dida photographs must be supplied by Pete and kept exactly as supplied. Never source, invent, crop, or substitute a Dida photo.

## Morning Story target

A swipeable seven-beat story: greeting; Weather; Calendar/free time; family/local idea; viewing; important stories; closing link to full brief. Use current profile data and every protected rule. Pete still needs to choose whether it is default, optional, or inside Home.

## Required workflow

Read this file and CHANGELOG.md; inspect current code/data; bound the scope; identify requirements at risk; implement only that scope; test feature plus mobile and desktop; run QA-CHECKLIST.md; report missing, unexpected, new, conflicting, and passed items; update documentation.

If blocked, state why, what is complete, what remains, and the exact next step. Missing historical detail is never permission to remove current behaviour.
