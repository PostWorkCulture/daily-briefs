# MASTER BRIEF - CURRENT

Version 1.4, 18 August 2026. Owner: Pete.
Repo: PostWorkCulture/daily-briefs
Live: https://postworkculture.github.io/daily-briefs/

This is the single source of truth. Preserve every requirement unless Pete explicitly supersedes it. Never change or remove an unrelated section, route, control, field, data source, link, colour treatment, or responsive behaviour. Flag conflicts before editing. Update this file and CHANGELOG.md after approved specification changes. Run QA-CHECKLIST.md after material work.

## Product

Daily Briefs is an exciting, futuristic daily-use morning brief. Combine FABLE OS structure, Morning Story speed and emotion, and Pete/Sofia family personalisation. Use a dark navy/purple or cinematic base, luminous accents, rounded cards, bold legible type, and meaningful warm photography. Preserve header styling during unrelated work.

## Boundaries

- Use only PostWorkCulture/daily-briefs. The old Claude/API repo is obsolete.
- No Anthropic/OpenAI API dependency or paid API credits.
- Static responsive GitHub Pages app with JSON data and Python/GitHub Actions refresh.
- Never commit private calendar credentials.
- Mobile first. Chromebook/desktop must have an intentional larger-screen layout.
- Always use real, clickable links. Never invent data, URLs, sources, or test results.

## Profiles

Pete and Sofia each have a personal brief. Root switch contains Pete and Sofia only. Keep /pete/ and /sofia/ routes and data/pete.json and data/sofia.json consistent. Never restore the obsolete Us profile.

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

**Around the world**
- One pictured place daily, linked to a real destination.
- Put an amazing or rare fact directly beneath it.
- Use curated, place-matched images at least 2,200 pixels wide and 1,000 pixels high. Never display a low-resolution fallback.

**TV Picks**
- Keep at least four named picks per profile.
- Programme artwork must match. Permanent editorial rules still need Pete's decision.

**Arsenal**
- No betting, odds, gambling promotion, or gambling information.
- Men's first team, all competitions.
- Latest completed and nearest upcoming fixtures.
- Preserve opponent, stadium, kickoff, competition, TV channel, and previous-meeting details when available.

**News, AI, Career, Dida**
- Keep each destination working and independent.
- Use current content and real source links.
- Show up to five relevant, unique, high-resolution article images in every populated News, Arsenal, AI, and Career tab, with no more than one image per article. Apply the same coverage standard to Pete and Sofia.
- Article images must be at least 1,200 × 675 pixels, and the refresh must reject logos, icons, placeholders, low-resolution sources, duplicate sources, and near-duplicate publisher imagery.
- Do not change them as a side effect of other work.
- Sofia's Career section shows current senior non-software product roles suited to her 17 years in product development at Strategic Insight, a B2B financial-data company.
- Sofia's roles must be fully remote or explicitly offer at least three work-from-home days per week. Generic hybrid roles do not qualify without evidence of that working pattern.
- Favour UK- and Sweden-based roles for Sofia; Europe-wide remote roles are a lower-priority fallback.
- Pete's Career section shows current UK roles in Civil Service, public sector, AI, digital, data, and automation, using the same multi-site search pool as Sofia.
- Career searches include LinkedIn, Arbeitnow, Remote OK, Remotive, Jobicy, and Sweden's official JobTech feed. Reject duplicates, listings older than 30 days, inactive listings when detectable, and links that are not real HTTP(S) job pages.

## Morning Story target

A swipeable seven-beat story: greeting; Weather; Calendar/free time; family/local idea; viewing; important stories; closing link to full brief. Use current profile data and every protected rule. Pete still needs to choose whether it is default, optional, or inside Home.

## Required workflow

Read this file and CHANGELOG.md; inspect current code/data; bound the scope; identify requirements at risk; implement only that scope; test feature plus mobile and desktop; run QA-CHECKLIST.md; report missing, unexpected, new, conflicting, and passed items; update documentation.

If blocked, state why, what is complete, what remains, and the exact next step. Missing historical detail is never permission to remove current behaviour.
