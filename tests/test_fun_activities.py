import unittest
from datetime import date
from unittest.mock import patch
import requests
from scripts.fun_activities import eligible,refresh_activities

class FunTests(unittest.TestCase):
    def setUp(self):
        import json, tempfile
        from pathlib import Path
        self.item=dict(id='fixture-event', title='Fixture event', location='Teddington',
                       summary='Test-only event', when='October 2026', ages='Families',
                       cost='Free', tags=['Events'], source='Test fixture',
                       url='https://www.hrp.org.uk/test-event/', evidence=['Fixture event'],
                       startDate='2026-10-01', endDate='2026-10-31',
                       verifiedAt='2026-09-24', contentType='activity')
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.fixture_root=Path(temporary.name)
        (self.fixture_root/'data').mkdir()
        (self.fixture_root/'data/fun-catalog.json').write_text(json.dumps([self.item]))
        # Cached dates deliberately differ from the catalogue to prove preservation.
        cached=dict(self.item, verifiedAt='2026-09-25')
        for profile in ('pete','sofia'):
            (self.fixture_root/f'data/{profile}.json').write_text(json.dumps({'sections':{'Fun':[cached]}}))
    def test_expired_events_and_stale_sources_rejected(self):
        item=dict(self.item,verifiedAt='2026-11-02')
        self.assertFalse(eligible(item,date(2026,11,2)))
        self.assertFalse(eligible(self.item,date(2026,10,10)))
        self.assertTrue(eligible(self.item,date(2026,9,24)))
    def test_non_activity_and_untrusted_links_rejected(self):
        self.assertFalse(eligible(dict(self.item,contentType='job'),date(2026,9,24)))
        self.assertFalse(eligible(dict(self.item,url='https://untrusted.example/activity'),date(2026,9,24)))
    def test_outage_keeps_recent_items_without_renewing_dates(self):
        def unavailable(*args,**kwargs):raise requests.Timeout()
        with patch('scripts.fun_activities.ROOT', self.fixture_root):
            items=refresh_activities(date(2026,9,26),fetch=unavailable)
            self.assertEqual(len(items),1)
            self.assertEqual(items[0]['verifiedAt'],'2026-09-25')
            self.assertEqual(len(refresh_activities(date(2026,10,2),fetch=unavailable)),1)
            self.assertEqual(refresh_activities(date(2026,10,3),fetch=unavailable),[])
    def test_source_mismatch_does_not_fall_back(self):
        class Response:
            text='<html>Page removed</html>'
            def raise_for_status(self):pass
        with patch('scripts.fun_activities.ROOT', self.fixture_root):
            self.assertEqual(refresh_activities(date(2026,9,26),fetch=lambda *a,**kw:Response()),[])
    def test_selection_limits_repeated_venues_and_regular_outings(self):
        from scripts.fun_activities import select_activities
        events=[dict(self.item,id=str(n),venue='same') for n in range(4)]
        regular=[{k:v for k,v in dict(self.item,id='park'+str(n),venue='park'+str(n)).items() if k not in ('startDate','endDate')} for n in range(3)]
        result=select_activities(regular+events)
        self.assertEqual(len(result),3)
        self.assertTrue(all(i.get('startDate') for i in result[:2]))
        self.assertFalse(result[-1].get('startDate'))
    def test_calendar_window_matches_browser_at_boundaries(self):
        import subprocess,json
        from scripts.fun_activities import in_event_window, ROOT
        cases=[
            ('2026-09-24','2026-08-01','2026-09-25',True),
            ('2026-09-24','2026-09-01','2026-09-23',False),
            ('2026-09-24','2026-10-31','2026-11-03',True),
            ('2026-09-24','2026-11-01','2026-11-01',False),
            ('2026-12-31','2027-01-31','2027-01-31',True),
            ('2026-12-31','2027-02-01','2027-02-01',False),
            ('2027-01-01','2027-02-28','2027-02-28',True),
            ('2027-01-01','2027-02-30','2027-02-30',False),
            ('2026-09-24',None,None,False),
            ('2026-09-24','2026-10-12','2026-10-11',False),
        ]
        for today,start,end,want in cases:
            item={'startDate':start,'endDate':end}
            self.assertEqual(in_event_window(item,date.fromisoformat(today)),want)
        js="const f=require('./js/fun-events.js'); const cases=JSON.parse(process.argv[1]); console.log(JSON.stringify(cases.map(([d,s,e])=>f({startDate:s,endDate:e},d))));"
        actual=json.loads(subprocess.check_output(['node','-e',js,json.dumps(cases)],cwd=ROOT))
        self.assertEqual(actual,[c[3] for c in cases])
