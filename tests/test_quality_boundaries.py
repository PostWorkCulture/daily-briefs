import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import refresh
import refresh_weather_only as weather


class QualityBoundaryTests(unittest.TestCase):
    def test_foreign_namesake_requires_uk_evidence(self):
        self.assertFalse(refresh.local_news_item_is_in_scope({'title':'Fire at Superior Parts on Hagley Park Road in Kingston', 'source':'IRIE FM'}))
        self.assertFalse(refresh.local_news_item_is_in_scope({'title':'Kingston opens a new library', 'source':'Unknown'}))
        self.assertTrue(refresh.local_news_item_is_in_scope({'title':'Kingston opens a new library', 'source':'Kingston Nub News'}))
        self.assertFalse(refresh.local_family_activity_item({'title':'Hagley Park Road fire'}))
        self.assertFalse(refresh.local_family_activity_item({'title':'Adults-only Lego event in Kingston'}))

    def test_adversarial_positive_words_do_not_pass(self):
        for title in ('Trump promising Argentina support for Falklands demands', 'PIP benefit denials overturned after tribunal win', 'Fury and Joshua boxing talks reopened', 'Clock starts ticking on race to buy Scotland church'):
            self.assertFalse(refresh.positive_uk_news_item_is_in_scope({'title':title}), title)
        for title in ('NHS promising trial improves cancer treatment', 'Restored railway station reopens to passengers', 'Community charity football fundraiser raises £5000'):
            self.assertTrue(refresh.positive_uk_news_item_is_in_scope({'title':title}), title)

    def test_old_weekend_listings_expire_but_future_seasons_remain(self):
        with patch.object(refresh, 'NOW', datetime(2026,9,5,tzinfo=refresh.TZ)):
            self.assertTrue(refresh.local_event_has_expired({'title':"What's on in Teddington this weekend",'publishedAt':'2026-08-27T09:00:00+01:00'}))
            self.assertFalse(refresh.local_event_has_expired({'title':"What's on in Teddington this weekend",'publishedAt':'2026-09-03T09:00:00+01:00'}))
            self.assertFalse(refresh.local_event_has_expired({'title':"What's on in Teddington for Christmas",'publishedAt':'2026-08-27T09:00:00+01:00'}))

    def test_local_editions_of_same_report_are_deduplicated(self):
        titles=['Man jailed for assisting former Teddington School pupil following prison escape','Man jailed for assisting former Kingston resident following prison escape']
        items=[{'title':title,'source':'Kingston Nub News','url':f'https://example.com/{i}'} for i,title in enumerate(titles)]
        self.assertEqual(len(refresh.select_local_news(items)),1)

    def test_weather_merge_preserves_latest_editorial_and_profile_extremes(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(weather,'DATA',Path(directory)):
            for name in ('pete','sofia'):
                value={'edition':'latest','sections':{'Career':[{'title':'New role'}]},'weather':{}}
                if name=='pete': value['weather']['yesterdayExtremes']={'town':'Pete verified place'}
                (Path(directory)/f'{name}.json').write_text(json.dumps(value))
            fresh={'temp':'20°','source':'Met Office','daily':[{'high':20}]}
            weather.merge_weather(fresh)
            pete=json.loads((Path(directory)/'pete.json').read_text())
            sofia=json.loads((Path(directory)/'sofia.json').read_text())
            self.assertEqual(pete['edition'],'latest')
            self.assertEqual(pete['sections']['Career'][0]['title'],'New role')
            self.assertEqual(pete['weather']['yesterdayExtremes']['town'],'Pete verified place')
            self.assertNotIn('yesterdayExtremes',sofia['weather'])
            self.assertNotIn('yesterdayExtremes',fresh)


if __name__=='__main__':
    unittest.main()
