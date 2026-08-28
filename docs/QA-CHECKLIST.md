# Daily Briefs QA Checklist

After every material change, report: Missing; Unexpectedly changed; Newly added; Conflicts; Passed. A pass requires code/data evidence, an automated test, or visual verification.

## Scope

- [ ] Requested scope only; unrelated sections unchanged.
- [ ] No route, view, control, field, link, colour treatment, or section disappeared.
- [ ] No duplication. Master brief and changelog updated when required.

## Profiles and responsive

- [ ] Pete and Sofia only; no Us.
- [ ] /pete/ and /sofia/ load the correct profile and data.
- [ ] Mobile has no overflow, clipping, or unusable navigation.
- [ ] Chromebook/desktop has an intentional larger-screen layout.
- [ ] Responsive smoke test passes.
- [ ] Primary navigation is solid dark navy with white resting text and icons; mobile stability and destination hover colours remain intact.
- [ ] Fixed mobile navigation sits in an opaque reserved bottom band so live copy is not visible beneath it; all final content can still scroll above the band.
- [ ] The selected Open Horizon mark renders in the Home nav and decodes from new favicon, Apple touch, Android, maskable, manifest, and link-preview paths.
- [ ] Supplied Coming up artwork matches recycling, normal bins, clocks, Halloween, and Christmas; embedded stale dates, countdowns, and fake controls are not visible.
- [ ] Coming up text remains wholly inside the left pastel column and does not overlap the right-side artwork.

## Weather

- [ ] Met Office and KT8 2LE.
- [ ] Daily weather only; no advice or best-time content.
- [ ] Visual matches wording.
- [ ] Rain icon only for rain/showers.
- [ ] Cloud conditions remain distinguishable.
- [ ] No invented fallback data.
- [ ] Hottest and coldest cards each show a locally cached 1,600 × 900 exact-place image with a real source and credit.
- [ ] If no exact-place image can be verified and cached, the morning refresh fails instead of publishing a blank weather card.

## Calendar

- [ ] Real refreshed content and real links.
- [ ] No Soon, For you, or duplicated information.
- [ ] No duplicate Today/Tomorrow pills; numbered controls remain.
- [ ] Calendar stays above Arsenal.

## Editorial hierarchy and content

- [ ] Desktop Home has no dead grid row between Calendar, Around the world, and TV Picks.
- [ ] News groups use lead, supporting, and compact stream tiers without changing source order.
- [ ] A text-only News lead stays compact; it never reserves a large empty media area.
- [ ] On mobile, only an image-verified lead uses full-width media; later verified images use compact thumbnails.
- [ ] Around the world leads with its sourced fact and then its precisely matched linked image.
- [ ] The current fact is human-first, genuinely unusual, source-verified, unused, and drawn from the people, population, traditions, records, or music range.
- [ ] Five unique TV Picks per profile, each tied to a new episode from the previous or next seven days.
- [ ] All five TV Picks remain visible on desktop as well as mobile.
- [ ] Every TV Pick has an exact TVMaze programme image, service/channel, availability date, real destination, and today's generated date.
- [ ] TV Picks history matches the displayed list; recent titles are avoided when enough fresh programmes exist.
- [ ] TV Picks contain no routine sport; only World Cup, UEFA Euros or Wimbledon sport is permitted.
- [ ] Local News is rendered newest to oldest after merging every configured local search.
- [ ] News, AI, Career, and Dida still open and were not altered unexpectedly.
- [ ] All offered sources and destinations are real and clickable.

## Arsenal

- [ ] The supplied cannon asset renders in the red masthead and the nav uses the exact same silhouette at mobile and Chromebook widths.
- [ ] Navy/white match hierarchy, red position card, club-news cards, and navy transfer area render at mobile and Chromebook widths.
- [ ] Premier League card shows only the current ordinal position; no table, points, or played total.
- [ ] No betting, odds, gambling promotion, or gambling information.
- [ ] Men's first team and all competitions.
- [ ] Trusted transfers contain no academy, youth, women's-team, job-vacancy, marketing, or commercial-role items; ambiguous Arsenal.com items have separate approved-source player corroboration.
- [ ] Latest completed and nearest upcoming fixture are correct.
- [ ] Required fixture details and real links remain.
- [ ] No invented scores or fixtures.

## Safety and release

- [ ] Correct repo only.
- [ ] No Anthropic/OpenAI dependency or paid API requirement.
- [ ] No private calendar URL committed.
- [ ] Morning workflow and protected validations pass.
- [ ] Live site resolves after deployment.

## Sign-off

Scope:
Evidence:
Automated checks:
Visual checks:
Missing:
Unexpected:
New:
Conflicts:
Passed:
Recommendation: pass | pass with known issues | fail
