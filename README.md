# Daily Briefs

A responsive personal morning dashboard for Pete, Sofia, and a shared **Us** view.

## Architecture

- Static responsive frontend (mobile, tablet, Chromebook/desktop)
- JSON data files under `data/`
- Python refresh script under `scripts/`
- GitHub Actions morning refresh
- No Anthropic/OpenAI API dependency

## Calendar

The refresh script can read a private Google Calendar ICS feed from the GitHub Actions secret:

`GOOGLE_CALENDAR_ICS_URL`

Never commit the private calendar URL to this public repository.

## Local development

Serve the repository root with any static HTTP server, e.g.:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.
