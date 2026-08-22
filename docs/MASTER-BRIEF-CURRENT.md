# MASTER BRIEF - CURRENT

Version 2.0, 22 August 2026. Owner: Pete.
Repo: PostWorkCulture/daily-briefs
Live: https://postworkculture.github.io/daily-briefs/

This is the single source of truth. Preserve every requirement unless Pete explicitly supersedes it. Never change or remove an unrelated section, route, control, field, data source, link, colour treatment, or responsive behaviour. Flag conflicts before editing. Update this file and CHANGELOG.md after approved specification changes. Run QA-CHECKLIST.md after material work.

## Product

Daily Briefs is an exciting, futuristic daily-use morning brief. Combine FABLE OS structure, Morning Story speed and emotion, and Pete/Sofia family personalisation. Use a light sky-blue and soft-lavender base, dark ink text, restrained luminous accents, rounded cards, bold legible type, and meaningful warm photography. Reserve dark treatments for image-led media cards where a strong overlay protects readability. Preserve header styling during unrelated work.

- Use the approved colourful rising-sun and layered-news-card artwork as the dedicated Daily Brief icon across favicon, Apple touch, installable-app, and link-preview metadata. Keep Daily Brief branding separate from Bomberfan and never reuse a Bomberfan image here.
- Primary navigation uses a single code-native balloon for Birthdays and a clean side-on barrel-and-wheel cannon for Arsenal. Keep the aurora edge restrained and do not use stars, sparkles, twinkles, or sparkle glyphs in the navigation.

## Boundaries

- Use only PostWorkCulture/daily-briefs. The old Claude/API repo is obsolete.
- No Anthropic/OpenAI API dependency or paid API credits.
- Static responsive GitHub Pages app with JSON data and Python/GitHub Actions refresh.
- Never commit private calendar credentials.
- Mobile first. Chromebook/desktop must have an intentional larger-screen layout.
- Always use real, clickable links. Never invent data, URLs, sources, or test results.

## Profiles

Pete and Sofia each have a personal brief. Root switch contains Pete and Sofia only. Keep /pete/ and /sofia/ routes and data/pete.json and data/sofia.json consistent. Never restore the obsolete Us profile.

- The Home greeting is `Hey Pete` for Pete and `Hey Sofia` for Sofia, without trailing punctuation.
- Keep the greeting deliberately smaller than the previous headline: 36–52 px below 900 px and 52–68 px from 900 px upwards.
- Place the `Daily Briefs` wordmark directly above the date, not in the sticky top bar.
- Place the greeting slightly lower in the hero so it sits comfortably between the date and the Weather panel.

## Current structure

Primary views: Home, News, Arsenal, AI, Career, Dida.
Home: Weather, Calendar, Around the world, TV Picks.
Do not remove, duplicate, or silently reorder them. Calendar stays above Arsenal in any shared flow.

## Protected requirements

**Weather**
- Met Office only for home area, currently KT8 2LE.
- Daily weather only. No advice or best-time content.
- Visual must match wording. Rain icon only for actual rain/showers, not rain probability.
- Sunny intervals, partly cloudy, and light cloud must be distinguishable.
- Yesterday's warmest and coldest cards must use Met Office observations from England only. Never select Scotland, Wales, Northern Ireland, or another country.
- Both extreme cards must display the verified town and English county in `Town, County` form.

**Calendar**
- Real content refreshed every morning through GOOGLE_CALENDAR_ICS_URL.
- Real links, no duplication, no Soon or For you groups.
- No duplicate Today/Tomorrow pills. Keep numbered controls.
- Today, Tomorrow, This week, and This month summary boxes use a visible cyan edge-glow on hover and keyboard focus, without moving the box.

**Around the world**
- Lead with one genuinely astonishing, obscure, source-verified fact each day, then show its precisely matched place image beneath it.
- Prefer wild places, with occasional extreme-life, human-origins, population-scale, unusual-travel, indigenous-culture, and planet-trend facts.
- Track every published fact ID in a committed permanent history. Never reuse an ID or duplicate fact text; if the catalogue is exhausted, fail the refresh instead of repeating.
- Use curated, place-matched images at least 2,200 pixels wide and 1,000 pixels high. Never display a low-resolution fallback.

**TV Picks**
- Keep at least four named picks per profile.
- Programme artwork must match. Permanent editorial rules still need Pete's decision.

**Arsenal**
- No betting, odds, gambling promotion, or gambling information.
- Men's first team, all competitions.
- Latest completed and nearest upcoming fixtures.
- Preserve opponent, stadium, kickoff, competition, TV channel, and previous-meeting details when available.
- Put Transfer watch at the bottom of the Arsenal view and always order it newest first. Its trusted list includes only official announcements or reports from Arsenal.com, BBC Sport, Sky Sports, The Athletic/The New York Times, The Guardian, Reuters, or ESPN. Reject rumour roundups, gossip, paper talk, betting, odds, academy, and women's-team items from this trusted list.
- Beneath the trusted list, show a separate Reporter watch for early, speculative public X posts. Mark every item `Unconfirmed · X`; never mix it into trusted reporting. Allow only David Ornstein, Fabrizio Romano, Charles Watts, and James Benge. Order it newest first and reject betting, gambling, women's-team, academy, U21, U18, youth, and girls' items.
- Discover allowlisted public X posts through Google News indexing so the brief does not require a paid X API, credentials, scraping proxy, or new morning-refresh secret.
- Apply the red edge-glow hover/focus treatment to every Arsenal card, including fixtures, league position, news, and transfer updates.

**News, AI, Career, Dida**
- Keep each destination working and independent.
- Use current content and real source links.
- Keep at least 10 current items in Local News and at least 10 current items in UK News for both profiles.
- Show up to five unique, high-resolution article images in each News and Arsenal view, with no more than one image per article, but only when the exact matching publisher page supplies that image. Keep the article text-only when exact publisher provenance cannot be verified.
- AI and Career never show article photography. Use stylish, decorative code-native section icons while preserving the current article and job content, metadata, and real links.
- Never use stock, topic-level, personality, search-library, Wikimedia, tab-level, generic, inferred, or guessed article-image fallbacks. This exact-relevance rule supersedes the earlier five-image minimum.
- Article images must be at least 1,200 × 675 pixels. Reject logos, icons, placeholders, low-resolution sources, duplicate sources, and near-duplicate publisher imagery.
- Do not change them as a side effect of other work.
- Sofia's Career section shows current senior non-software product roles suited to her 17 years in product development at Strategic Insight, a B2B financial-data company.
- Sofia's roles must be fully remote or explicitly offer at least three work-from-home days per week. Generic hybrid roles do not qualify without evidence of that working pattern.
- Favour UK- and Sweden-based roles for Sofia; Europe-wide remote roles are a lower-priority fallback.
- Pete's Career section shows current UK roles in Civil Service, public sector, AI, digital, data, and automation, using the same multi-site search pool as Sofia.
- Career searches include LinkedIn, Arbeitnow, Remote OK, Remotive, Jobicy, and Sweden's official JobTech feed. Reject duplicates, listings older than 30 days, inactive listings when detectable, and links that are not real HTTP(S) job pages.
- Dida uses lime green, not orange, with playful code-native icons and colour. Split it into three clear zones: This week, Seasonal missions, and Reference library. Keep weekly quick wins first, preserve every existing idea and guide, and keep all four reference groups collapsed by default on mobile and desktop.
- Dida photographs must be supplied by Pete and kept exactly as supplied. Never source, invent, crop, or substitute a Dida photo.

## Morning Story target

A swipeable seven-beat story: greeting; Weather; Calendar/free time; family/local idea; viewing; important stories; closing link to full brief. Use current profile data and every protected rule. Pete still needs to choose whether it is default, optional, or inside Home.

## Required workflow

Read this file and CHANGELOG.md; inspect current code/data; bound the scope; identify requirements at risk; implement only that scope; test feature plus mobile and desktop; run QA-CHECKLIST.md; report missing, unexpected, new, conflicting, and passed items; update documentation.

If blocked, state why, what is complete, what remains, and the exact next step. Missing historical detail is never permission to remove current behaviour.
