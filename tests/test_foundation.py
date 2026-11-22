"""New integration and provenance gates; all use the real SQLite implementations."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ixo.bridge import capture
from ixo.runtime import IXORuntime
from aixo.engine import AIXOEngine, AIXOError
from ixo_foundation.system import Foundation
from frameshift.judgment import Episode, JudgmentEngine


class FoundationContracts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_operator_case_preserves_write_gate(self):
        with Foundation(self.home) as app:
            out = app.case(workspace='moon2', observation='Two readings of this sentence exist',
                           hypothesis='The phonetic boundary may change interpretation',
                           question='Does interpretation need evidence?')
            self.assertTrue(out['ok'])
            self.assertEqual(out['fact_writes'], 0)
            self.assertEqual(out['captured_new'], 4)
            self.assertEqual(out['event_sequences'], [1,2,3,4])
            snapshot = app.status()
            self.assertEqual(snapshot['ixo']['counts']['facts'], 0)
            self.assertEqual(snapshot['ixo']['counts']['reflections'], 2)
            self.assertEqual(snapshot['aixo']['captured_events'], 4)
            self.assertEqual(app.capture()['captured_new'], 0)
            self.assertTrue(app.aixo.evaluate(out['experiment_id'],'facts_count',0,app.ixo.status(0))['passed'])

    def test_two_ixo_sources_cannot_collide_in_one_aixo(self):
        one = IXORuntime(self.home/'one.db')
        two = IXORuntime(self.home/'two.db')
        aixo = AIXOEngine(self.home/'learn.db')
        try:
            one.activate_set('moon2')
            two.activate_set('hermes')
            self.assertNotEqual(one._get('instance_id'),two._get('instance_id'))
            self.assertEqual(capture(one,aixo),1)
            with self.assertRaisesRegex(AIXOError,'another IXO'):
                capture(two,aixo)
            self.assertEqual(aixo.state()['captured_events'],1)
        finally:
            one.close();two.close();aixo.close()

    def test_provenance_persists_after_restart(self):
        with Foundation(self.home) as app:
            original=app.status()['source_id']
            app.ixo.moon('observe','Source continuity')
            app.capture()
        with Foundation(self.home) as app:
            self.assertEqual(app.status()['source_id'], original)
            self.assertEqual(app.status()['aixo']['source_id'], original)
            self.assertEqual(app.capture()['captured_new'],0)

    def test_replayed_event_tampering_is_rejected_without_changes(self):
        ixo = IXORuntime(self.home/'x.db')
        aixo = AIXOEngine(self.home/'a.db')
        try:
            ixo.moon('observe','One')
            capture(ixo,aixo)
            fake={'seq':1,'at':'2026-01-01','type':'moon2.observe','payload':{'evil':True}}
            with self.assertRaisesRegex(AIXOError,'conflicts'):
                aixo.ingest_events([fake],ixo._get('instance_id'))
            self.assertEqual(aixo.state()['captured_events'],1)
        finally:
            ixo.close();aixo.close()

    def test_legacy_unbound_evidence_requires_manual_migration(self):
        aixo=AIXOEngine(self.home/'old.db')
        ixo=IXORuntime(self.home/'new.db')
        try:
            with aixo.conn:
                aixo.conn.execute("INSERT INTO observed_ixo_events VALUES(1,'old','unknown','{}')")
            ixo.activate_set('main')
            with self.assertRaisesRegex(AIXOError,'Legacy captured'):
                capture(ixo,aixo)
        finally:
            aixo.close();ixo.close()

    def test_invalid_case_does_not_mutate_state(self):
        with Foundation(self.home) as app:
            with self.assertRaises(ValueError):
                app.case(workspace='invalid',observation='hi',hypothesis='new fact',question='why')
            self.assertEqual(app.status()['ixo']['counts']['events'],0)

    def test_case_rejects_overlong_interpretation_before_any_event(self):
        with Foundation(self.home) as app:
            with self.assertRaises(ValueError):
                app.case(workspace='main', observation='valid', hypothesis='x' * 2200, question='why')
            self.assertEqual(app.status()['ixo']['counts']['events'], 0)

    def test_case_refuses_legacy_unbound_capture_before_any_event(self):
        with Foundation(self.home) as app:
            with app.aixo.conn:
                app.aixo.conn.execute("INSERT INTO observed_ixo_events VALUES(1,'old','kind','{}')")
            with self.assertRaisesRegex(AIXOError,'Legacy captured'):
                app.case(workspace='main',observation='valid',hypothesis='hypothesis',question='why')
            self.assertEqual(app.status()['ixo']['counts']['events'], 0)

    def test_read_only_language_probe(self):
        with Foundation(self.home) as app:
            before=app.status()['ixo']['counts'].copy()
            result=Foundation.probe('Find\nEvery\nClue')
            self.assertEqual(before,app.status()['ixo']['counts'])
            self.assertEqual(result['word_count'],3)
            self.assertTrue(any(x['operation']=='line-initials' for x in result['candidates']))

    def test_course_progress_is_durable_and_ordered(self):
        with Foundation(self.home) as app:
            with self.assertRaises(AIXOError):app.aixo.complete_lesson('A2','no artifact')
            app.aixo.complete_lesson('A1','file:///first-artifact.txt')
        with Foundation(self.home) as app:
            self.assertEqual(app.status()['aixo']['course_completed'],1)

    def test_cli_status_and_case_in_subprocess(self):
        root=Path(__file__).resolve().parents[1]
        def call(*arguments):
            result=subprocess.run([sys.executable,'-m','ixo_foundation','--home',str(self.home),*arguments],
                                  cwd=root,text=True,capture_output=True)
            self.assertEqual(result.returncode,0, result.stderr)
            return json.loads(result.stdout)
        self.assertEqual(call('status')['ixo']['active_set'],'main')
        out=call('case','--workspace','research','--observation','I scream or ice cream',
                 '--hypothesis','These boundaries are ambiguous', '--question','What clue selects the meaning?')
        self.assertEqual(out['proposal_status'],'PENDING')
        self.assertEqual(call('status')['aixo']['captured_events'],4)

    def test_judgment_is_not_automatic_fact_promotion(self):
        engine=JudgmentEngine()
        score=engine.judge(Episode('task-one','strategy-A','context',True,0.8,0.8))
        self.assertGreater(score.smartness_score,0.5)
        with Foundation(self.home) as app:
            self.assertEqual(app.status()['ixo']['counts']['facts'],0)

if __name__=='__main__': unittest.main()
