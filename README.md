# Daily Briefs

A responsive personal morning dashboard with separate personalised briefs for Pete and Sofia.

## Product specification

- Current master brief: [docs/MASTER-BRIEF-CURRENT.md](docs/MASTER-BRIEF-CURRENT.md)
- Project operating rules: [docs/PROJECT-INSTRUCTIONS.md](docs/PROJECT-INSTRUCTIONS.md)
- QA checklist: [docs/QA-CHECKLIST.md](docs/QA-CHECKLIST.md)
- Change history: [docs/CHANGELOG.md](docs/CHANGELOG.md)

## Architecture

- Static responsive frontend (mobile, tablet, Chromebook/desktop)
- JSON data files under data/
- Python refresh script under scripts/
- GitHub Actions morning refresh
- No Anthropic/OpenAI API dependency

## Calendar

The refresh script can read a private Google Calendar ICS feed from the GitHub Actions secret:

GOOGLE_CALENDAR_ICS_URL

Never commit the private calendar URL to this public repository.

## Local development

Serve the repository root with any static HTTP server, for example:

    python3 -m http.server 8000

Then open http://localhost:8000.
