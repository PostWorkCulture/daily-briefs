"""Report catalogue stock independently of the daily publication gate."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reserve_report(catalog: list[dict], history: dict) -> dict:
    used = {entry.get('id') for entry in history.get('used', [])}
    remaining = len({entry['id'] for entry in catalog if entry.get('id') not in used
                     and entry.get('editorialPriority') == 'human-first'
                     and entry.get('editorialStatus') != 'retired'})
    return {'remaining': remaining, 'needsReplenishment': remaining < 7, 'target': 21}


def main() -> None:
    result = reserve_report(json.loads((ROOT/'data/fact-catalog.json').read_text()),
                            json.loads((ROOT/'data/fact-history.json').read_text()))
    message = f"Verified human-first fact reserve: {result['remaining']} unused. Replenishment target: 21."
    print(('::warning::' if result['needsReplenishment'] else '') + message)
    if os.getenv('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a') as summary:
            summary.write(message + '\n')
    # Low stock is maintenance work. Actual exhaustion still fails world_fact_for_today.


if __name__ == '__main__':
    main()
