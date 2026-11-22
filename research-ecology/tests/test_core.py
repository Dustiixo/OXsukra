import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research_ecology.core import ResearchStore, DocumentText, classify, distill, validate_public_https

class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=ResearchStore(Path(self.temp.name)/'data.db')
    def tearDown(self):
        self.store.close();self.temp.cleanup()
    def test_end_to_end_future_plan_capture_insight_recall(self):
        plan=self.store.plan('thermal management','bracer','2026-11-18T17:00:00-05:00',40)
        self.assertEqual(plan['payload']['slotline_commit'],'NOT_REQUESTED')
        sid=self.store.start('thermal management','bracer')
        source=self.store.source('https://example.org/heat','Thermal conduction creates heat transfer.\nContact resistance limits conductive cooling performance.','conduction cooling',sid)
        self.store.reviewed(source['id'],'skimmed',sid)
        self.store.insight('Contact might share heat between two water-cooled assemblies; verify experimentally.',[source['id']],'bracer',sid)
        recap=self.store.recap(sid)
        self.assertEqual(recap['research_ticks'],1)
        self.assertEqual(recap['competency_signoffs'],0)
        self.assertEqual(len(recap['insights']),1)
        self.assertTrue(self.store.verify())
        self.assertEqual(self.store.export()['owner'],'research-ecology')
    def test_tamper_detection(self):
        self.store.start('topic','project')
        self.store.db.execute("UPDATE events SET body='{}' WHERE seq=1")
        self.store.db.commit();self.assertFalse(self.store.verify())
    def test_no_false_signoff(self):
        self.store.reviewed('src','applied')
        self.assertFalse(self.store.list()[0]['payload']['competency_signoff'])
    def test_classification(self):
        self.assertIn('thermal',classify('thermodynamics heat conduction and cooling'))
    def test_distillation(self):
        x=distill('Graph animation transitions use spring curves.\nMore general discussion and unrelated information.', 'animation transitions',1)
        self.assertEqual(len(x),1);self.assertIn('animation',x[0])
    def test_html_extraction_drops_script(self):
        x=DocumentText();x.feed('<h1>Useful research section</h1><script>bad()</script><p>Thermal conduction is important in the experiment.</p>')
        self.assertNotIn('bad()',str(x.lines));self.assertIn('Useful research section',x.lines)
    def test_public_link_restrictions(self):
        for url in ('http://example.com','https://localhost/','https://127.0.0.1/','https://user:pw@example.org','https://example.org:444/'):
            with self.assertRaises(ValueError):validate_public_https(url)
    def test_dns_blocks_private(self):
        fake=[(None,None,None,None,('192.168.1.1',443))]
        with patch('research_ecology.core.socket.getaddrinfo',return_value=fake):
            with self.assertRaises(ValueError):validate_public_https('https://example.org/a')
    def test_invalid_plan_and_kind(self):
        with self.assertRaises(ValueError):self.store.plan('a','b','date',999)
        with self.assertRaises(ValueError):self.store.add('pass_certified',{})
    def test_extracted_context_not_full_page(self):
        text='\n'.join(f'Block {i} provides a long explanation of animation events.' for i in range(100))
        e=self.store.source('https://example.org',text,'animation')
        self.assertLessEqual(len(e['payload']['extract']),6)
    def test_append_only_observational_log(self):
        first=self.store.start('A','project');self.store.insight('A hypothesis',[], 'project',first)
        assert self.store.verify()
        self.assertEqual(len(self.store.list()),2)
if __name__=='__main__':unittest.main()

from research_ecology.companion import Companion
from datetime import datetime,timezone,timedelta
class CompanionTests(unittest.TestCase):
    def test_character_is_separate_and_quiet(self):
        c=Companion();t=datetime(2026,10,28,tzinfo=timezone.utc)
        c.quiet(10,t)
        self.assertEqual(c.react('insight',t+timedelta(minutes=5)),'')
        self.assertEqual(c.notes,0)
        self.assertEqual(c.react('insight',t+timedelta(minutes=11)),'An idea worth keeping.')
        self.assertEqual(c.notes,1)
        self.assertFalse(hasattr(c,'underbyte_inventory'))
    def test_character_quiet_bounds(self):
        with self.assertRaises(ValueError):Companion().quiet(1)
