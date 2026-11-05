# Daily Briefs

A responsive personal morning dashboard with separate personalised briefs for Pete and Sofia, published by GitHub Pages.

- Pete: https://postworkculture.github.io/daily-briefs/pete/
- Sofia: https://postworkculture.github.io/daily-briefs/sofia/

## Specification and process

- Master brief (single source of truth): [docs/MASTER-BRIEF-CURRENT.md](docs/MASTER-BRIEF-CURRENT.md)
- Repository rules for AI assistants: [AGENTS.md](AGENTS.md) (ChatGPT copy: [docs/PROJECT-INSTRUCTIONS.md](docs/PROJECT-INSTRUCTIONS.md))
- QA checklist: [docs/QA-CHECKLIST.md](docs/QA-CHECKLIST.md)
- Change history: [docs/CHANGELOG.md](docs/CHANGELOG.md)

## Repository layout

| Path | Purpose |
| --- | --- |
| `index.html`, `pete/`, `sofia/` | Static front end; the profile folders are locked routes onto the same app |
| `js/`, `css/` | Browser code and styles, loaded by `index.html` (no build step) |
| `data/` | Published JSON: `pete.json`, `sofia.json`, fact catalogue and history, TV Picks history, story-image rules, `refresh-status.json` |
| `assets/` | Images: brand icons (`icons/`, with editable sources in `icons/masters/`), cached news images, weather-extreme and world-fact pictures, Dida illustrations, AI company logos |
| `scripts/` | Refresh pipeline (see below); `scripts/tools/` holds one-off generators and `scripts/integrations/` the Google Apps Script calendar sync |
| `tests/` | Python unit tests (`python -m unittest discover -s tests -p 'test_*.py'`) and a Node test (`node --test tests/inbox-view.test.cjs`) |
| `.github/workflows/` | Morning refresh, weather refresh and responsive UI check |

## Morning refresh pipeline

`scripts/run_refresh.py` runs the pipeline and never lets one failing component stop publication: a component whose sources fail is carried forward from the last published edition and recorded in `data/refresh-status.json`.

1. `refresh.py` – news, AI, Sweden, Fun, calendar, Around-the-world fact, base weather and Arsenal block
2. `enrich_weather_v2.py` – Met Office forecast and England temperature extremes with exact-place photos
3. `enrich_arsenal.py`, `finalize_arsenal.py`, `enrich_next_fixture.py` – latest result, trusted transfers, next fixture
4. `enrich_tv_picks.py` – five documentary-led TV Picks from TVMaze
5. `refresh_story_images.py` – exact publisher images for stories (orphaned cached images are pruned)
6. `validate_brief.py` – protected-rule validator; the final gate before commit

It runs twice a day-cycle: the Windows scheduled task `DailyBriefMorningRefresh` (`scripts/daily_refresh_runner.ps1`, installed by `scripts/install_daily_task.ps1`) at 04:55 local time, and the GitHub Actions `Morning refresh` workflow as a backup. Both wait for 05:00 Europe/London and skip when today's edition is already published. `scripts/refresh_weather_only.py` refreshes the forecast four times a day.

## Calendar

The refresh reads a private Google Calendar ICS feed from the GitHub Actions secret `GOOGLE_CALENDAR_ICS_URL` (and event colours from `GOOGLE_CALENDAR_COLORS_URL`, produced by `scripts/integrations/google_apps_script_calendar_sync.js`). Never commit the private calendar URL to this public repository.

## Local development

    pip install -r requirements.txt
    python -m http.server 4173        # then open http://localhost:4173/pete/
    python -m unittest discover -s tests -p 'test_*.py'
    python scripts/responsive_ui_check.py   # needs playwright and the server above
