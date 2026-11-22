"""Behavioral tests for safe v0.2 discovery/event layer.
These do not claim any live Discord, streaming, Drive, or VPS integration.
"""
import unittest
from tests import test_funnel as fixture
from funnel.automation import DISCLOSURE_VERSION
from funnel.ui import HTML


class AutomationControlPlane(unittest.TestCase):
    # Use the proven HTTP fixture without inheriting duplicate v0.1 test cases.
    setUp = fixture.FunnelIntegration.setUp
    tearDown = fixture.FunnelIntegration.tearDown
    call = fixture.FunnelIntegration.call

    def test_capabilities_are_descriptive_not_claimed_live(self):
        self.assertEqual(self.call('/api/v1/integrations', token=False)['http_error'], 401)
        registry=self.call('/api/v1/integrations')
        caps={x['id']:x for x in registry['capabilities']}
        self.assertEqual(caps['funnel_hub']['state'],'implemented')
        self.assertEqual(caps['discord_music']['state'],'external_manual')
        self.assertEqual(caps['business_intentions']['state'],'proposed_private')
        self.assertIn('No passive',self.call('/api/v1/disclosure')['collection_default'])
        self.assertEqual(registry['disclosure_version'], DISCLOSURE_VERSION)
        self.assertEqual(self.call('/api/v1/automation/events',token=self.bot)['http_error'],403)
        self.assertIn('event-record',HTML)

    def test_previews_make_no_external_calls_or_jobs(self):
        from unittest.mock import patch
        before=self.call('/api/v1/jobs')['jobs']
        with patch('funnel.hub.discord_event',side_effect=AssertionError('Notification not permitted')):
            result=self.call('/api/v1/automation/preview','POST',{'event_type':'music.requested'})
        self.assertIs(result['executed'],False)
        self.assertEqual(result['mode'],'preview_only')
        self.assertEqual(result['steps'][0]['adapter_state'],'external_manual')
        self.assertTrue(all(step['executed'] is False for step in result['steps']))
        self.assertEqual(self.call('/api/v1/jobs')['jobs'],before)
        self.assertEqual(self.call('/api/v1/automation/events')['events'],[])
        self.assertEqual(self.call('/api/v1/automation/preview','POST',{'event_type':'arbitrary.shell'})['http_error'],400)
        self.assertEqual(self.call('/api/v1/automation/preview','POST',{'event_type':'music.requested'},token=self.bot)['executed'],False)

    def test_explicit_event_consent_and_metadata_only(self):
        data={'event_type':'experiment.proposed','project':'ixo','summary':'Evaluate a safe, traceable proposal',
              'disclosure_version':DISCLOSURE_VERSION,'acknowledged':True}
        without=dict(data,acknowledged=False)
        self.assertEqual(self.call('/api/v1/automation/events','POST',without)['http_error'],412)
        self.assertEqual(self.call('/api/v1/automation/events','POST',{**data,'disclosure_version':'old'})['http_error'],412)
        self.assertEqual(self.call('/api/v1/automation/events','POST',{**data,'arbitrary_script':'rm -rf /'})['http_error'],400)
        self.assertEqual(self.call('/api/v1/automation/events','POST',data,token=self.bot)['http_error'],403)
        from unittest.mock import patch
        with patch('funnel.hub.discord_event',side_effect=AssertionError('No Discord notification')):
            result=self.call('/api/v1/automation/events','POST',data)
        self.assertEqual(result['state'],'recorded_unexecuted')
        self.assertFalse(result['preview']['executed'])
        events=self.call('/api/v1/automation/events')['events']
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]['event_type'],'experiment.proposed')
        self.assertEqual(events[0]['summary'],data['summary'])
        self.assertEqual(events[0]['disclosure_version'],DISCLOSURE_VERSION)
        self.assertEqual(self.call('/api/v1/jobs')['jobs'],[])
