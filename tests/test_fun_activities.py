import unittest
from datetime import date
from unittest.mock import patch
import requests
from scripts.fun_activities import eligible,refresh_activities

class FunTests(unittest.TestCase):
    def setUp(self):
        import json
        from scripts.fun_activities import ROOT
        self.item=json.loads((ROOT/'data/fun-catalog.json').read_text())[0]
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
        items=refresh_activities(date(2026,9,25),fetch=unavailable)
        self.assertTrue(items)
        self.assertTrue(all(i['verifiedAt']=='2026-09-24' for i in items))
        self.assertEqual(refresh_activities(date(2026,10,10),fetch=unavailable),[])
    def test_source_mismatch_does_not_fall_back(self):
        class Response:
            text='<html>Page removed</html>'
            def raise_for_status(self):pass
        self.assertEqual(refresh_activities(date(2026,9,24),fetch=lambda *a,**kw:Response()),[])
