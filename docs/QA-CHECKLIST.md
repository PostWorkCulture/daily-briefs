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
- [ ] Supplied Coming up artwork matches recycling, normal bins, clocks, Halloween, and Christmas; embedded stale dates, countdowns, and fake controls are not visible.
- [ ] Coming up text remains wholly inside the left pastel column and does not overlap the right-side artwork.

## Weather

- [ ] Met Office and KT8 2LE.
- [ ] Daily weather only; no advice or best-time content.
- [ ] Visual matches wording.
- [ ] Rain icon only for rain/showers.
- [ ] Cloud conditions remain distinguishable.
- [ ] No invented fallback data.

## Calendar

- [ ] Real refreshed content and real links.
- [ ] No Soon, For you, or duplicated information.
- [ ] No duplicate Today/Tomorrow pills; numbered controls remain.
- [ ] Calendar stays above Arsenal.

## Content

- [ ] Around the world has one linked image and a fact directly below.
- [ ] At least four named TV Picks per profile with matching artwork.
- [ ] News, AI, Career, and Dida still open and were not altered unexpectedly.
- [ ] All offered sources and destinations are real and clickable.

## Arsenal

- [ ] No betting, odds, gambling promotion, or gambling information.
- [ ] Men's first team and all competitions.
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
