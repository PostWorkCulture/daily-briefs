"""Daily source checks for curated local family activities; failures are item-local."""
from datetime import date, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_HOSTS = {'www.hrp.org.uk', 'www.royalparks.org.uk', 'www.kingstonheritage.org.uk', 'www.elmbridge.gov.uk'}

def eligible(item, today):
    from urllib.parse import urlparse
    try:
        checked = date.fromisoformat(item['verifiedAt'])
        return (item.get('contentType') == 'activity' and
                urlparse(item['url']).hostname in ALLOWED_HOSTS and
                item['url'].startswith('https://') and
                0 <= (today - checked).days <= 7 and
                (not item.get('endDate') or date.fromisoformat(item['endDate']) >= today) and
                all(item.get(k) for k in ('id','title','location','summary','when','ages','cost','source','tags')))
    except (KeyError, ValueError, TypeError):
        return False

def activity_sort(item):
    return (0 if item.get('startDate') else 1, item.get('startDate',''), item['title'])

def refresh_activities(today, fetch=requests.get):
    catalog = json.loads((ROOT/'data/fun-catalog.json').read_text())
    cached = {}
    for profile in ('pete', 'sofia'):
        try:
            for item in json.loads((ROOT/f'data/{profile}.json').read_text()).get('sections',{}).get('Fun',[]):
                cached[item['id']] = item
        except (OSError, ValueError, KeyError):
            pass
    def check(item):
        if item.get('endDate') and item['endDate'] < today.isoformat():
            return None
        try:
            response = fetch(item['url'], timeout=12, headers={'User-Agent':'DailyBriefs/3.0'})
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            text = ' '.join(soup.stripped_strings).casefold()
            if not item.get('evidence') or not all(value.casefold() in text for value in item['evidence']):
                logging.warning('Fun source changed: %s; omitted pending review', item['id'])
                return None
            result = {k:v for k,v in item.items() if k != 'evidence'}
            result['verifiedAt'] = today.isoformat()
            return result if eligible(result,today) else None
        except requests.RequestException as error:
            logging.warning('Fun source unavailable: %s (%s)', item['id'],type(error).__name__)
            # Do not resurrect removed entries or silently renew their verification date.
            previous = cached.get(item['id'], item)
            if eligible(previous, today):
                return {k:v for k,v in previous.items() if k != 'evidence'}
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        items = [item for item in pool.map(check,catalog) if item]
    return sorted(items,key=activity_sort)
