# MASTER BRIEF - CURRENT

Version 5.8, 28 September 2026. Owner: Pete.
Repo: PostWorkCulture/daily-briefs
Live: https://postworkculture.github.io/daily-briefs/

This is the single source of truth. Preserve every requirement unless Pete explicitly supersedes it. Never change or remove an unrelated section, route, control, field, data source, link, colour treatment, or responsive behaviour. Flag conflicts before editing. Update this file and CHANGELOG.md after approved specification changes. Run QA-CHECKLIST.md after material work.

## Product

- Do not add branding, labels, taglines, sections or other unrequested interface elements without Pete’s explicit approval. Remove the previously specified Open Horizon / Live briefing navigation text. Keep every desktop navigation destination,  inside the navigation box; scroll within the box on short screens.

Daily Briefs is an exciting, futuristic daily-use morning brief. Combine FABLE OS structure, Morning Story speed and emotion, and Pete/Sofia family personalisation. Use the selected `Signal Grid` direction: a near-black `#030504` canvas, graphite modules, warm-white `#F4F7F2` copy, thin technical rules, clean neutral dividers with lime green horizontal accent lines removed under headings, bold legible type, and meaningful photography. Keep the grid extremely faint and functional rather than decorative. Around the world and TV Picks always retain full-colour source imagery. Preserve header styling during unrelated work.

- Use an `Open Horizon newsroom` hierarchy inspired by premium news homepages without copying their identity: firm section rules, a clear lead/supporting/stream rhythm, intentional desktop grids, and denser mobile scanning. Both News and AI share the same simple, softened typography and reading measure (medium headline weights, relaxed line heights). Prominence comes from width, position, type scale, and verified imagery, not fabricated labels or reordered source content. Keep bespoke systems for Arsenal, Dida, Birthday, Weather, Coming up, Calendar, Around the world, and TV Picks.
- Keep the Chromebook layout intentionally compact, then expand the main editorial rail fluidly on widescreen displays up to 1,920 px. Wider rails must use responsive editorial and card grids so content uses the available space without stretching readable copy into uncontrolled line lengths. Do not use a utility top bar. On locked profile routes, the main brief date must be the first visible line, followed by the greeting; never duplicate the date, weather status, or profile identity above it.
- Text-only news leads are valid and must use a purposeful 7/5 lead-and-support desktop rail rather than reserving an empty image-scale area. Image-verified desktop leads use a prominent image-left, copy-right package. Desktop stream stories share one flat divided paper rail instead of appearing as separate floating tiles. On mobile, only an image-verified lead uses full-width media; supporting and stream stories use compact thumbnails where exact publisher imagery exists, and secondary items form a flat divided paper feed rather than a wall of identical cards.

- The Home greeting and section or page titles on the black canvas use warm-white `#F4F7F2`, giving at least 4.5:1 contrast. The main date uses signal green `#7CF46A`. Main copy on graphite surfaces remains warm white, with muted grey reserved for secondary metadata.

- Do not show a visible `Daily Briefs` wordmark in page content. Retain the Daily Briefs browser title, bookmark, manifest, icon, and sharing metadata.
- Primary navigation uses solid near-black `#070908` with clean white text only (all menu icons removed). Desktop uses the wider labelled rail with clean text buttons; mobile keeps the stable compact horizontal bar with text-only buttons. Each destination uses a brighter version of its existing colour only on hover or keyboard focus so the feedback remains readable against the dark surface.
- Respect `prefers-reduced-motion`: destination changes and in-page controls must not request smooth scrolling, navigation decoration must not animate, and hover/focus transitions must become effectively immediate. Keep a real visible keyboard-focus outline in addition to destination glows.
- On mobile, primary navigation remains fixed, fully visible, and clickable while switching destinations or interacting with content. Use immediate mobile view changes and a stable opaque navigation surface to avoid compositor flicker.
- Home `Coming up` cards use graphite surfaces with a slim section-specific colour signal and Pete-supplied artwork as a cropped right-side visual where a matched image exists. Keep all live card text inside a dedicated left-side text column with no overlap into the artwork. Recycling, general and garden waste, clocks, Halloween, and Christmas each use their matching supplied image. General-bin weeks must be titled `General & garden waste` with the concise instruction `Put out both bins`; garden waste remains collected on those weeks. Crop out the dates, countdown numbers, and fake controls embedded in the source compositions so the live dynamic card text remains authoritative. Halloween retains orange as its accent. From 700 px upwards, all four cards must fit on one compact row.
- Interactive card hover and keyboard-focus feedback must be clearly visible, stationary, and consistent in strength throughout the brief. General cards use cyan, Arsenal cards retain red, and image-led TV cards retain gold.

- Use Pete's selected icon artwork, an ultra-simple solid bright lime green background (`#7CF46A`) with bold white **DB** lettering, as the dedicated Daily Brief icon across favicon, Apple touch, Android saved-page, installable-app, link-preview, and Home navigation metadata. Use new immutable filenames when changing icon artwork so mobile favourites cannot reuse an old cached identity. Keep Daily Brief branding separate from Bomberfan and Arsenal.
- Primary navigation uses a single code-native balloon for Birthdays and the exact same supplied cannon silhouette used in the Arsenal masthead. Birthday navigation uses vivid bright pink on hover or keyboard focus. Keep the aurora edge restrained and do not use stars, sparkles, twinkles, or sparkle glyphs in the navigation.
- The Birthday destination and navigation label are both `Birthday`. Do not repeat a generic Birthdays subheading beneath the page title.
- Birthday and anniversary cards use clean, minimal dark Signal Grid surfaces (`#0b0e0c`) with no dividing lines or borders; all pink card backgrounds, pink borders, and decorative badges are eliminated. Each birthday card formats information on separate lines: Line 1 `Name`, Line 2 `Birthdate - Day` (e.g. `12th December - Saturday`), and Line 3 `Turns...` (e.g. `Turns 1!` or `X years!` for anniversaries). Balloons use high-definition glossy triple-balloon cluster artwork in Pete's selected style (tied with curled ribbons) with gender-specific color palettes: girls receive festive combinations of pink, yellow, and purple; boys receive combinations of boy colours (blues, cyans, and greens). The Home birthday reminder uses the same clean dark surface and gender-matched glossy balloon artwork.
- Birthday and anniversary cards, including the Home birthday reminder, use the same visible cyan edge-glow as Calendar summary boxes on hover and keyboard focus, without movement.

## Boundaries

- Use only PostWorkCulture/daily-briefs. The old Claude/API repo is obsolete.
- No Anthropic/OpenAI API dependency or paid API credits.
- Static responsive GitHub Pages app with JSON data and Python/GitHub Actions refresh.
- Target the full morning refresh for 05:00 `Europe/London` every day so today's edition is published and ready before 05:30. Use GMT/BST-safe UTC triggers (04:00 UTC in BST, 05:00 UTC in GMT), retry at 30-minute intervals through 06:30 UTC while today's edition is still stale, and skip the remaining retries as soon as both profiles carry today's publication date.
- Maintain the independent ChatGPT `Daily Brief Recovery` automation (ID `6a93c7cea924819198568ba6b0ca52cd`) enabled from 05:00 Europe/London. It checks both live publication dates, triggers a missing refresh if stale, inspects failures and verifies deployment. Never pause it after success, no-op or failure.
- GitHub cron and external scheduling are best-effort: do not promise zero failures or exact-time delivery. Recovery must preserve content validation, avoid duplicate active runs, and report unresolved blockers without relabelling stale data.
- Never commit private calendar credentials.
- Mobile first. Chromebook/desktop must have an intentional larger-screen layout.
- Always use real, clickable links. Never invent data, URLs, sources, or test results.

## Profiles

Pete and Sofia each have a personal brief. The Pete/Sofia toggle is removed from the interface: Pete and Sofia access their respective briefs directly via dedicated routes (`/pete/`, `/sofia/`) and cannot access or toggle between both. Keep /pete/ and /sofia/ routes and data/pete.json and data/sofia.json consistent. Never restore the obsolete Us profile.

- A valid `profile=pete` or `profile=sofia` query parameter is authoritative over local storage. Pete routes show Arsenal; Sofia routes do not.

- The Home greeting is `Hey Pete` for Pete and `Hey Sofia` for Sofia, without trailing punctuation. The horizontal dividing line under the greeting is removed.
- Keep the greeting deliberately smaller than the previous headline: 36–52 px below 900 px and 52–68 px from 900 px upwards.
- Do not display the `Daily Briefs` wordmark in page content.
- Place the greeting slightly lower in the hero so it sits comfortably between the date and the Weather panel.

## Current structure

Primary views: Home, Calendar, Fun, News, Arsenal, AI, Dida, Birthday.
Home: Weather, Calendar, Coming up, Around the world, TV Picks.
Do not remove, duplicate, or silently reorder them. Calendar stays above Arsenal in any shared flow.

## Fun: local family activities

- 24 September 2026: Pete replaces Career in both briefs with Fun. This explicitly supersedes all earlier Career UI, job-display and job-discovery requirements. No Career view or job listings are published; jobs must not move to another section.
- Place Fun immediately before News in both profiles, with the existing dark styling, responsive grid and neutral navigation accent. Use '30 Minutes from home' as the section intro. Keep Dida separate.
- Use an approximate 30-minute driving catchment from KT8 2LE, including Surbiton, Twickenham, Teddington, Hanworth, Esher and Weybridge. Traffic varies; provide route checks, never guaranteed drive times. Prioritise dated beer festivals, community festivals, fairs, open days, creative events, seasonal Halloween/Christmas activities, major retail sales/clearance events, and park activities. Cap each venue at two listings. Show only dated events that are ongoing or upcoming this calendar month or within the next two calendar months, based on Europe/London. Exclude undated regular attractions and already-ended events. Beer events must state verified age restrictions.
- Sale cards are rendered as compact cards at the top of the Fun section with simple details (sale headline, date, discount percentage, and direct store link).
- Regular activity cards display cleanly without section icons or tag pills, containing title, description, location, when, age guidance, cost information, route check, and the official details/booking link. Do not infer prices or exact age restrictions. No Fun filter controls.
- Store sourced activities in `data/fun-catalog.json`. The morning refresh checks each source independently, validates activity type and event expiry, and enforces the three-month calendar window (current month plus next two months) for fresh and cached entries. Curated source evidence must still be present; changed pages are omitted for review. New outings are added through verified catalogue maintenance.
- An individual source failure must not block the brief. Retain last-checked entries for at most seven days with the original check date; never retain expired events. If none remain, show an honest empty state. The browser enforces the same date window between refreshes.

## Pete-only Inbox integration (temporarily paused)

- 24 September 2026: Pete requested removal of Inbox from the brief for now. Hide both desktop and mobile entries for every profile and disable direct opening, redirects and embedded email frames. The integration requirements below are retained for a future explicitly approved restoration. The standalone Inbox service is unchanged.

- Add Inbox after the existing primary destinations on desktop and as a Home button on mobile for Pete only. Keep the existing mobile navigation at eight usable destinations. Sofia must never see or enter this view, including after switching profiles or calling the view controller directly.
- The public brief's Inbox destination opens the owner-authenticated private brief at `https://inbox-command-centre.pyro-pete.chatgpt.site/brief/?profile=pete&locked=1&view=inbox` in the same tab.
- This private companion mirrors the current public brief, pins Pete's locked profile, and embeds the existing Inbox app on its own authenticated origin. It preserves Gmail controls, Needs Action defaults, protection/review state and the existing triage schedule. No email data or credentials enter the public repository, JSON, or public brief.
- Sofia's routes and public access stay unchanged. Pete's existing public brief remains available; the private companion does not retroactively make those public pages private.
- Keep an Open full inbox link available within the private Inbox view. Only load the email frame when Inbox is selected. Removing Pete's profile must remove any email frame.

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
- Keep exactly two numbered Home summary filters: `Today / tomorrow` and `This month`. The first combines both days without duplicating multi-day events and is selected by default.
- Keep Calendar immediately below Weather and above Coming up on Home.
- Provide a dedicated Calendar destination with a real Monday-first month grid, previous/Today/next controls, event indicators, and a selected-day agenda. Build it exclusively from the same refreshed calendar feed; never add synthetic events.
- Keep the month view usable at mobile and Chromebook widths: compact event indicators on mobile, readable event titles on larger screens, no horizontal overflow, and visible keyboard focus.
- Both calendar summary filters use a visible cyan edge-glow on hover and keyboard focus, without moving the box.
- On Chromebook/desktop, show the two summary filters in one concise row above a natural-height event list; a short list must never stretch into a dead white slab.

**Around the world**
- Lead with one genuinely astonishing, obscure, source-verified fact each day, then show its precisely matched place image beneath it.
- Show only the `Around the world` title above the fact. Do not display the old `Rare facts · wild places` subtitle.
- Prioritise genuinely rare human stories, obscure facts, Guinness World Records, and remote geographies from different countries: extraordinary people and communities, isolated and indigenous tribes, population oddities and language records, far-away lands, unusual customs, record-breaking feats, and surprising cultural phenomena. Wild places and planet anomalies remain occasional variety, not the default.
- Keep a curated human-first queue large enough to prevent dull fallback. New-day selection must choose an unused human-first fact before any general catalogue item.
- Track every published fact ID in a committed permanent history. Never reuse an ID or duplicate fact text; if the catalogue is exhausted, fail the refresh instead of repeating.
- Every fact must display a useful wider location line in `place/area · country/region` form so an unfamiliar location is understandable without prior knowledge. Retire an item from future selection when Pete rejects it as dull; keep its ID only for permanent history integrity.
- Use curated, place-matched images at least 2,200 pixels wide and 1,000 pixels high. Never display a low-resolution fallback.
- On Chromebook/desktop, short fact copy may be vertically centred beside its image so the 4/8 package uses its whitespace intentionally; fact-first DOM order remains mandatory.

**TV Picks**
- Show five current, named programmes per profile. An eligible pick has released a new episode within the previous seven days or will release one within the next seven days; a new episode qualifies even when the series itself is not new.
- Refresh the selection every morning from current UK broadcast and major-streaming schedules. Relevance is a hard eligibility rule, not a scoring preference: every pick must be a dark or investigative documentary, a dark crime/thriller/mystery, `Silo` or other science fiction, a strong new Apple TV+ series or season premiere, or an allowed major-sport programme. Make the five-card selection documentary-led with at least three dark or investigative documentaries; fail the refresh rather than publish a weaker mix. Use no more than four documentaries when another eligible category is available. Give strong preference to crime and scandals on Netflix, BBC (BBC iPlayer, BBC One, BBC Two, BBC Three, BBC Four), and Channel 4, followed by Apple TV+, when equally strong current programmes are available. Exclude every reality programme, including misclassified Gary Barlow or celebrity-travel shows, plus nature, travel, gardening, medical, food, light crime-comedy and generic documentaries, routine enforcement factual shows, routine sport, news, talk shows, game shows, daily soaps, generic articles, and programmes without a real destination. The only sports exceptions are World Cup, UEFA Euros and Wimbledon programmes.
- Give every card the exact programme artwork supplied by the schedule source. Each card must visibly display the title and programme blurb above its channel or streaming service and availability date (positioned at the bottom of the card content). Ensure the channel or streaming service is always explicitly identified (e.g. Channel 5, Netflix, BBC One). Do not show category repeats or category badges on the cards, as the section scope already specifies the editorial mix. Never use generic streaming art, logos, screenshots, placeholders, or a fixed title allowlist.
- Prefer titles not used during the previous three refresh days without allowing that freshness preference to displace a more relevant programme. Keep source and category variety, and fail before publication if five valid current picks cannot be produced. Keep a committed 30-day selection history so freshness is testable.

**Arsenal**
- Use an official-site-inspired Arsenal visual system: bright red `#E30613`, deep navy `#071D49`, and clean white surfaces. The section opens with a red masthead using Pete's supplied white cannon, and the nav uses that exact same silhouette. Both the latest score and nearest fixture cards share the clean white card theme with a red top border and deep navy typography, paired with the red league-position card. All content below match centre (Latest Club news, Transfer watch, and Reporter watch) shares the exact same white/red colour format: clean white cards, red uppercase kickers, deep navy headings, muted metadata, red hover glow, and a two-column desktop grid matching the News section. Keep it professional, high-contrast, stationary on hover, and responsive.
- Do not show a Premier League table, points total, or matches-played total. Show only Arsenal's current ordinal league position, refreshed from the live table source.
- No betting, odds, gambling promotion, or gambling information.
- Men's first team, all competitions.
- Latest completed and nearest upcoming fixtures.
- Treat Sky Sports and BBC Sport as independent authoritative sources for the nearest upcoming fixture. Check the current day plus forward month coverage so a nearer European or cup match cannot be displaced by a later Premier League-only fallback. Preserve a still-upcoming verified fixture during a partial outage, but fail publication once it expires if neither Sky nor BBC supplies a current replacement.
- The latest completed match must always show score, scorers, competition, a concise factual game summary, actual kickoff time, and stadium. If any required result field cannot be verified, fail the refresh instead of publishing an incomplete result.
- Preserve opponent, stadium, kickoff, competition, TV channel, and previous-meeting details for the upcoming fixture when available. Previous meetings must be checked across competitions and older seasons using reliable history sources, including AiScore H2H and official match reports. A missing result in one feed is not proof of no previous meeting; empty pinned metadata must never suppress the lookup. Use UK dates.
- Put Transfer watch at the bottom of the Arsenal view and always order it newest first. Its trusted list includes only official announcements or reports from Arsenal.com, BBC Sport, Sky Sports, The Athletic/The New York Times, The Guardian, Reuters, or ESPN. Reject rumour roundups, gossip, paper talk, betting, odds, job vacancies, commercial roles, academy, and women's-team items from this trusted list. An Arsenal.com item without explicit first-team context must be corroborated by a separate approved source identifying the same player before it can appear.
- Beneath the trusted list, show a separate Reporter watch for early, speculative public X posts. Mark every item `Unconfirmed · X`; never mix it into trusted reporting. Allow only David Ornstein, Fabrizio Romano, Charles Watts, and James Benge. Order it newest first and reject betting, gambling, women's-team, academy, U21, U18, youth, and girls' items.
- Discover allowlisted public X posts through Google News indexing so the brief does not require a paid X API, credentials, scraping proxy, or new morning-refresh secret.
- Apply the red edge-glow hover/focus treatment to every Arsenal card, including fixtures, league position, news, and transfer updates.
- Render the five Club news items with explicit lead, two-support, and two-stream roles while preserving source order and exact-image eligibility.

**News, AI, Fun, Dida**
- Keep each destination working and independent.
- Jobs and recruitment listings are excluded from every published section now that Career is removed. Do not move rejected vacancies into Fun or News.
- Enforce permanent content-type isolation: News, Sweden, AI and Arsenal Club news use `article`; Fun uses `activity`. No job listings are published.
- Use current content and real source links.
- Keep at least 10 current items in Local News for both profiles. UK News is removed completely from the News section.
- Local News displays the top 10 local stories, single line each (`.tab-story.story-row`), with all top formatting (lead, support, stream grid) removed. Final display order remains strictly newest to oldest.
- Local News is restricted to East Molesey, West Molesey, Molesey, Kingston upon Thames, Hampton, Teddington, Hampton Court, Walton-on-Thames, and genuinely nearby KT8 places: Hampton Wick, Hampton Hill, Bushy Park, Thames Ditton, Long Ditton, Hinchley Wood, Esher, Hersham, Surbiton, and Sunbury-on-Thames. A headline or summary must contain an approved place or unmistakable local-landmark reference; a broad `Surrey`, `Elmbridge`, or `London` mention, the search query, or the publisher name alone is not sufficient evidence. Reject foreign or unrelated place-name matches. Target 16 suitable stories from the freshest 14 days, extending to 30 days before considering any geography change; never silently widen the approved area.
- Local News rejects routine sports scores, results, match reports, fixtures, tables, and round-ups. Sports coverage is allowed only for a venue or facility opening, a major change, or a significant participatory event. All "what's going on", "what's on", and "things to do" weekend listings or event roundups are excluded from Local News and appear exclusively in the Fun section. Prioritise local newspapers and publications, plus reporting on local community developments, parks, and seasonal celebrations.
- Merge Local News candidates across all configured broad, local-publication, and family-activity searches before selection. Prioritisation determines which stories make the expanded list; final display order must always remain strictly newest to oldest.
- Sofia keeps Sweden above Local News.
- Display expanded high-quality, well-framed article images in eligible sections (and up to five in Arsenal news), with no more than one image per article, but only when the exact matching publisher page supplies that image. Keep the article text-only when exact publisher provenance cannot be verified.
- Add an article media block in the browser only after its exact publisher image has loaded, decoded, and met the 1,200 × 675 minimum. A failed or slow image must leave the story text-only instead of reserving an empty dark media slab.
- AI displays the top 10 AI stories, single line each (`.tab-story.story-row`), with all top formatting removed. AI uses exact company marks or the existing code-native fallback. Google, Google DeepMind, and Gemini updates are always placed at the top (tier 0); Western frontier labs (Anthropic/OpenAI) in the middle; and Chinese frontier labs (DeepSeek, Qwen, Moonshot) are placed strictly at the bottom (tier 2). Fun uses decorative activity icons; no unrelated article imagery.
<!-- Historical Career requirement, superseded 24 September 2026: - Career cards use the same cyan edge-glow as Calendar summary boxes on hover and keyboard focus, without movement. -->
<!-- Historical Career requirement, superseded 24 September 2026: - Career uses neutral light grey `#D4D8D5` for its field labels and navigation hover or keyboard focus. Do not use yellow in the Career treatment. -->
- Never use stock, topic-level, personality, search-library, Wikimedia, tab-level, generic, inferred, or guessed article-image fallbacks. This exact-relevance rule supersedes the earlier five-image minimum.
- Article images must be at least 1,200 × 675 pixels. Reject logos, icons, placeholders, low-resolution sources, duplicate sources, and near-duplicate publisher imagery.
- Do not change them as a side effect of other work.
<!-- Historical Career requirement, superseded 24 September 2026: - Both profiles use the same Career rule: show only current UK public-sector jobs with explicit AI relevance. A private-sector AI job and a public-sector role without explicit AI relevance are both ineligible. -->
<!-- Historical Career requirement, superseded 24 September 2026: - Always order Career newest first. Every card must show these seven fields in this exact order: `Job Title`, `Company`, `Description`, `Salary`, `Posted Date`, `Where it was posted`, `Location`. Use `Not stated`, `Date not stated`, or `Description not supplied by publisher` when a publisher omits a field; never infer it. -->
<!-- Historical Career requirement, superseded 24 September 2026: - Career discovery uses focused public LinkedIn searches for UK government, NHS, machine-learning, responsible-AI, AI-governance, and generative-AI vacancies. Reject duplicates, listings older than 30 days, detectable passed closing dates, inactive listings, and links that are not real HTTP(S) job pages. A last-good fallback may retain only jobs already carrying the same verified public-sector, AI-related, and seven-field contract. -->
- Reject job listings whose title names Government Digital Service but whose listed employer is a different organisation; this is treated as a mismatched aggregator duplicate.
- Dida is for a six-year-old. Use age-six development guidance, learning ideas, games, seasonal missions, and birthday activities, with a real age-appropriate source link.
- Dida has one page-level title and three independent graphite zones: Play together, Explore this season, and Parent guide. This approved September 5 update replaces the old This week, Seasonal missions, and Reference library labels. Keep bright green titles/outlines, neutral copy, and 28 px mobile / 36 px desktop zone gaps. Play together has one complete featured activity and two alternatives. Explore this season offers a season selector and real instructions; Parent guide preserves all four existing reference folds, closed by default. Preserve existing learning/game/seasonal ideas and the CDC source.
- Dida uses an original 36-activity rotation with materials, time, setting, adult role, three steps and a playful extension. Include English/Swedish, nature, making, movement and seasonal ideas. Birthday activities are year-neutral and must not infer a birth year.
- Dida includes three original full-colour clay/storybook illustrations. These are decorative artwork, not pictures of Dida. Existing supplied photographs remain protected. Pick another changes the adventure; Save favourite and We tried it persist per profile on this device, with removable stickers and accessible status feedback. Preserve disclosures during background refresh.
- Dida’s three independent zone cards use the strong Calendar cyan edge-glow on hover or when they contain keyboard focus, without movement.
- Dida photographs must be supplied by Pete and kept exactly as supplied. Never source, invent, crop, or substitute a Dida photo.

## September 5 quality and reliability improvements

- Ambiguous Kingston/Hampton headlines require an approved local publication or explicit UK-local context. Exclude foreign namesakes, expired weekend listings, duplicated local editions, standalone weather forecasts and routine results. General reporting about weather impacts may remain News. Bare “park” does not make a story a family activity; adult-only nightlife is not family-first content.
- Positive UK selection requires explicit positive evidence. Generic promising, benefit, win or reopened wording does not rescue disputes, benefit denials, boxing negotiations or closures.
<!-- Historical Career requirement, superseded 24 September 2026: - Career can use exact-vacancy primary metadata verified in `data/career-verified.json` for up to 14 days, never after a confirmed closing date. Record the evidence and preserve the publisher's actual listing-date identity. Show office choices/hybrid requirements, real employer links, and honest missing details. Do not claim a sub-one-hour commute from KT8 without verified journey evidence. -->
- TV still publishes five qualifying primary picks and may retain up to 12 equally in-scope, current, programme-image-verified alternatives. Per-profile device feedback offers Already watched / Not interested and individual Restore. Hidden titles stay excluded on that device. Refill with eligible alternatives; show fewer picks honestly when none remain. Do not weaken interests or invent replacement programmes.
- Fact stock below seven emits a maintenance warning, never blocks an otherwise valid edition. The independent recovery task checks/replenishes the verified reserve toward 21. Actual exhaustion remains a hard no-repeat publication failure.
- Weather and morning writers share a non-cancelling concurrency group. Weather merges only fresh forecast fields into the latest profiles and preserves each profile's own extremes. Morning commits its actual changed files and rebases, failing on conflict rather than restoring stale copies of every JSON file.

## Morning Story target

A swipeable seven-beat story: greeting; Weather; Calendar/free time; family/local idea; viewing; important stories; closing link to full brief. Use current profile data and every protected rule. Pete still needs to choose whether it is default, optional, or inside Home.

## Required workflow

Read this file and CHANGELOG.md; inspect current code/data; bound the scope; identify requirements at risk; implement only that scope; test feature plus mobile and desktop; run QA-CHECKLIST.md; report missing, unexpected, new, conflicting, and passed items; update documentation.

If blocked, state why, what is complete, what remains, and the exact next step. Missing historical detail is never permission to remove current behaviour.
