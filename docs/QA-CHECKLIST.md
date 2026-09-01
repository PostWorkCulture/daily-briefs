# Daily Briefs QA Checklist

After every material change, report: Missing; Unexpectedly changed; Newly added; Conflicts; Passed. A pass requires code/data evidence, an automated test, or visual verification.

## Scope

- [ ] Requested scope only; unrelated sections unchanged.
- [ ] No route, view, control, field, link, colour treatment, or section disappeared.
- [ ] No duplication. Master brief and changelog updated when required.

## Profiles and responsive

- [ ] Pete and Sofia only; no Us.
- [ ] /pete/ and /sofia/ load the correct profile and data.
- [ ] Direct `profile=pete` and `profile=sofia` queries override stale local storage; locked routes hide the switch with zero occupied geometry and retain the correct Arsenal visibility.
- [ ] No utility top bar, duplicate date, compact weather text, or profile badge appears above the main date; on locked routes the main date is the first visible line.
- [ ] Mobile has no overflow, clipping, or unusable navigation.
- [ ] Chromebook/desktop has an intentional larger-screen layout.
- [ ] Responsive smoke test passes.
- [ ] Primary navigation is solid dark navy with white resting text and icons; mobile stability and destination hover colours remain intact.
- [ ] Fixed mobile navigation sits in an opaque reserved bottom band so live copy is not visible beneath it; all final content can still scroll above the band.
- [ ] The selected Open Horizon mark renders in the Home nav and decodes from new favicon, Apple touch, Android, maskable, manifest, and link-preview paths.
- [ ] Supplied Coming up artwork matches recycling, general and garden waste, clocks, Halloween, and Christmas; embedded stale dates, countdowns, and fake controls are not visible.
- [ ] General-bin weeks read `General & garden waste` and `Put out both bins`, without repetitive collection wording.
- [ ] Coming up text remains wholly inside the left pastel column and does not overlap the right-side artwork.
- [ ] `prefers-reduced-motion` disables scripted smooth scrolling, navigation animation, and visible transition duration; keyboard focus retains a real outline.
- [ ] The greeting and every title directly on the blue canvas use dark `#142A3D` ink and meet at least 4.5:1 contrast; white remains reserved for dark surfaces and strongly overlaid media.

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
- [ ] Desktop Calendar uses four summary boxes in one row above a natural-height event list; short event lists do not stretch.
- [ ] News groups use lead, supporting, and compact stream tiers without changing source order.
- [ ] A text-only News lead uses the 7/5 desktop lead-and-support rail; it never reserves an empty media area.
- [ ] Desktop stream stories share one flat divided paper rail with no individual tile rounding or shadow; mobile secondary stories remain one divided feed.
- [ ] An image-verified desktop lead places media left and copy right; mobile keeps lead media above its copy.
- [ ] News and Arsenal media blocks appear only after the exact publisher image loads and decodes at 1,200 × 675 or larger; failed or slow images leave a text-only story with no empty dark slab.
- [ ] AI and Career have no orphan stream card at 900–1,099 px or at the current Chromebook width.
- [ ] On mobile, only an image-verified lead uses full-width media; later verified images use compact thumbnails.
- [ ] Around the world leads with its sourced fact and then its precisely matched linked image.
- [ ] The current fact is human-first, genuinely unusual, source-verified, unused, not retired, and drawn from the people, population, traditions, records, or music range.
- [ ] Every current and catalogue fact shows a useful `place/area · country/region` location line.
- [ ] Five unique TV Picks per profile, each tied to a new episode from the previous or next seven days.
- [ ] All five TV Picks remain visible on desktop as well as mobile.
- [ ] Every TV Pick has an exact TVMaze programme image, service/channel, availability date, real destination, and today's generated date.
- [ ] TV Picks history matches the displayed list; recent titles are avoided when enough fresh programmes exist.
- [ ] TV Picks contain no routine sport; only World Cup, UEFA Euros or Wimbledon sport is permitted.
- [ ] TV Picks contain no reality programme or Gary Barlow; dark documentaries, `Silo`/science fiction and new Apple TV+ releases outrank weak lifestyle or celebrity-travel content.
- [ ] BBC iPlayer, Channel 4 and Netflix receive first platform preference when equally strong current picks are available.
- [ ] Local News is rendered newest to oldest after merging every configured local search.
- [ ] Every Local News story has headline or summary evidence for the approved KT8 cluster; broad Surrey, Elmbridge, or London references and foreign/unrelated namesakes are rejected. The refresh may extend from 14 to 30 days for depth but does not widen the geography.
- [ ] News, AI, Career, and Dida still open and were not altered unexpectedly.
- [ ] Dida has one page-level title followed by exactly three white age-six zones.
- [ ] Birthday months use a full-width single card, two balanced half-width cards, or three equal cards on one Chromebook row.
- [ ] All offered sources and destinations are real and clickable.

## Arsenal

- [ ] The supplied cannon asset renders in the red masthead and the nav uses the exact same silhouette at mobile and Chromebook widths.
- [ ] Navy/white match hierarchy, red position card, club-news cards, and navy transfer area render at mobile and Chromebook widths.
- [ ] Five Club news cards retain source order and receive one lead, two support, and two stream roles.
- [ ] Premier League card shows only the current ordinal position; no table, points, or played total.
- [ ] No betting, odds, gambling promotion, or gambling information.
- [ ] Men's first team and all competitions.
- [ ] Trusted transfers contain no academy, youth, women's-team, job-vacancy, marketing, or commercial-role items; ambiguous Arsenal.com items have separate approved-source player corroboration.
- [ ] Latest completed and nearest upcoming fixture are correct.
- [ ] Latest completed match visibly includes score, scorers, competition, quick factual summary, kickoff time and stadium; publication fails if any field is unavailable.
- [ ] Required upcoming fixture details and real links remain.
- [ ] No invented scores or fixtures.

## Safety and release

- [ ] Correct repo only.
- [ ] No Anthropic/OpenAI dependency or paid API requirement.
- [ ] No private calendar URL committed.
- [ ] Morning workflow and protected validations pass.
- [ ] Full refresh targets 06:00 Europe/London across GMT and BST, retries only while the edition is stale, and skips once both profiles are current.
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
