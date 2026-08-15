from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import feedparser
import requests
from dateutil import parser as dateparser
from icalendar import Calendar

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
TZ = ZoneInfo("Europe/London")
NOW = datetime.now(TZ)
UA = {"User-Agent": "DailyBriefs/2.0 (+https://github.com/PostWorkCulture/daily-briefs)"}
LAT = 51.400
LON = -0.366


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def weather() -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": "temperature_2m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,weather_code,precipitation_probability_max",
        "timezone": "Europe/London",
        "forecast_days": 7,
    }
    try:
        r = requests.get(url, params=params, headers=UA, timeout=25)
        r.raise_for_status()
        d = r.json()
        labels = {0:"Clear",1:"Mostly clear",2:"Partly cloudy",3:"Cloudy",45:"Foggy",48:"Foggy",51:"Light drizzle",53:"Drizzle",55:"Heavy drizzle",61:"Light rain",63:"Rain",65:"Heavy rain",71:"Light snow",73:"Snow",75:"Heavy snow",80:"Showers",81:"Showers",82:"Heavy showers",95:"Thunderstorms"}
        temp = round(float(d["current"]["temperature_2m"]))
        code = int(d["current"].get("weather_code", 0))
        daily=[]
        pops=d["daily"].get("precipitation_probability_max",[None]*len(d["daily"]["time"]))
        for day,hi,lo,wc,pop in zip(d["daily"]["time"],d["daily"]["temperature_2m_max"],d["daily"]["temperature_2m_min"],d["daily"]["weather_code"],pops):
            daily.append({"date":day,"high":round(hi),"low":round(lo),"summary":labels.get(int(wc),"Forecast"),"rainChance":pop})
        return {"temp":f"{temp}°","summary":labels.get(code,"Latest forecast"),"daily":daily}
    except Exception as exc:
        return {"temp":"—","summary":"Weather unavailable","daily":[],"error":str(exc)}


def google_news(query: str, limit: int = 6, max_age_days: int = 4) -> list[dict]:
    url=f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-GB&gl=GB&ceid=GB:en"
    feed=feedparser.parse(url)
    out=[]; seen=set()
    for entry in feed.entries[:limit*5]:
        raw=clean_html(entry.get("title",""))
        source=""
        title=raw
        if " - " in raw:
            title,source=raw.rsplit(" - ",1)
        key=re.sub(r"\W+","",title.lower())[:120]
        if not key or key in seen: continue
        published=entry.get("published","")
        try:
            dt=dateparser.parse(published).astimezone(TZ)
            if NOW-dt>timedelta(days=max_age_days): continue
            meta=dt.strftime("%a %-d %b")
        except Exception:
            meta="Recent"
        seen.add(key)
        out.append({"title":title.strip(),"summary":"","meta":meta,"source":source.strip(),"url":entry.get("link","")})
        if len(out)>=limit: break
    return out


def rss(url: str, section: str, limit: int = 6, max_age_days: int = 4) -> list[dict]:
    feed=feedparser.parse(url); items=[]; seen=set()
    for entry in feed.entries[:limit*4]:
        title=clean_html(entry.get("title","")); key=re.sub(r"\W+","",title.lower())[:120]
        if not title or key in seen: continue
        summary=clean_html(entry.get("summary",""))[:220]
        try:
            dt=dateparser.parse(entry.get("published","")).astimezone(TZ)
            if NOW-dt>timedelta(days=max_age_days): continue
            meta=dt.strftime("%a %-d %b")
        except Exception: meta=section
        seen.add(key)
        items.append({"title":title,"summary":summary,"meta":meta,"source":section,"url":entry.get("link","")})
        if len(items)>=limit: break
    return items


def calendar_colour_data() -> dict:
    path = DATA / "calendar-colors.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"eventPalette": {}, "events": {}}


def normalize_google_uid(component) -> str:
    uid = clean_html(str(component.get("uid", "")))
    if "@" in uid:
        uid = uid.split("@", 1)[0]
    # Recurring ICS instances typically use the series UID; keep that stable.
    return uid


def calendar_events() -> list[dict]:
    url=os.getenv("GOOGLE_CALENDAR_ICS_URL","").strip()
    if not url: return []
    try:
        r=requests.get(url,headers=UA,timeout=30); r.raise_for_status(); cal=Calendar.from_ical(r.content)
    except Exception: return []

    colours = calendar_colour_data()
    palette = colours.get("eventPalette", {})
    event_colours = colours.get("events", {})

    start_window=NOW.replace(hour=0,minute=0,second=0,microsecond=0)
    next_month=(start_window.replace(day=28)+timedelta(days=4)).replace(day=1)
    following=(next_month.replace(day=28)+timedelta(days=4)).replace(day=1)
    end_window=following-timedelta(seconds=1)
    events=[]
    for component in cal.walk("VEVENT"):
        start=component.decoded("dtstart")
        end=component.decoded("dtend") if component.get("dtend") else start
        all_day=not isinstance(start,datetime)
        if all_day: start=datetime.combine(start,datetime.min.time(),TZ)
        elif start.tzinfo is None: start=start.replace(tzinfo=TZ)
        else: start=start.astimezone(TZ)
        if not isinstance(end,datetime): end=datetime.combine(end,datetime.min.time(),TZ)
        elif end.tzinfo is None: end=end.replace(tzinfo=TZ)
        else: end=end.astimezone(TZ)
        if end<start_window or start>end_window: continue

        title=clean_html(str(component.get("summary","Calendar event"))) or "Calendar event"
        event_id = normalize_google_uid(component)
        color_id = event_colours.get(event_id)
        colour = palette.get(str(color_id)) if color_id else None
        time_label="All day" if all_day else start.strftime("%-I:%M%p").lower().replace(":00","")
        events.append({
            "title":title,"summary":"","url":"","start":start.isoformat(),"end":end.isoformat(),
            "date":start.date().isoformat(),"time":time_label,"allDay":all_day,
            "color":colour,"colorId":color_id,"googleEventId":event_id,
            "calendarColorSource":"google" if color_id else "calendar-default"
        })
    events.sort(key=lambda x:x["start"])
    return events


def build_profiles() -> dict[str,dict]:
    wx=weather(); cal=calendar_events()

    ai=google_news('(OpenAI OR Anthropic OR "Google DeepMind" OR "AI model") when:3d',8,3)
    arsenal=google_news('Arsenal FC when:3d',8,3)
    local=google_news('(Kingston upon Thames OR Molesey OR Esher OR Walton-on-Thames OR Elmbridge) when:4d',8,4)
    uk=rss('https://feeds.bbci.co.uk/news/rss.xml','BBC News',6,2) or google_news('UK news when:2d',6,2)
    tv=google_news('(Netflix OR "BBC iPlayer" OR ITVX OR "Disney+") (new series OR new film OR streaming) UK when:4d',7,4)
    career=google_news('("UK Civil Service" jobs OR "AI jobs" UK OR public sector careers) when:7d',6,7)
    sweden=google_news('(Sweden OR Swedish) news when:4d',7,4)
    family=google_news('(Surrey family events OR Kingston family events OR Elmbridge family events OR Hampton Court events) when:14d',8,14)

    stamp=NOW.strftime("%A, %-d %B %Y · refreshed %-I:%M%p").replace("AM","am").replace("PM","pm")
    pete_sections={"AI":ai,"Arsenal":arsenal,"Local news":local,"UK news":uk,"Career":career}
    sofia_sections={"Sweden":sweden,"Local news":local,"UK news":uk,"AI":ai,"Career":career}
    us_sections={"Local ideas":family,"Local news":local,"UK news":uk}
    def first(items,fallback): return items[0] if items else {"title":fallback,"summary":"","meta":"","source":"","url":""}
    return {
      "pete":{"updatedLabel":stamp,"weather":wx,"calendar":cal,"lead":first(ai or arsenal or local,"Your morning brief is ready."),"interests":[dict(first(ai,"AI updates"),section="AI"),dict(first(arsenal,"Arsenal"),section="Arsenal"),dict(first(local,"Local"),section="Local")],"watch":tv,"sections":pete_sections},
      "sofia":{"updatedLabel":stamp,"weather":wx,"calendar":cal,"lead":first(sweden or local or tv,"Your morning brief is ready."),"interests":[dict(first(sweden,"Sweden"),section="Sweden"),dict(first(local,"Local"),section="Local"),dict(first(tv,"Tonight"),section="Watch")],"watch":tv,"sections":sofia_sections},
      "us":{"updatedLabel":stamp,"weather":wx,"calendar":cal,"lead":first(family or local,"Your shared day is ready."),"interests":[dict(first(family,"Family ideas"),section="Family"),dict(first(local,"Local"),section="Local"),dict(first(tv,"Tonight"),section="Watch")],"watch":tv,"sections":us_sections},
    }


def main()->None:
    profiles=build_profiles()
    for name,payload in profiles.items():
        (DATA/f"{name}.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("Updated:",", ".join(str(DATA/f"{x}.json") for x in profiles))

if __name__=="__main__": main()
