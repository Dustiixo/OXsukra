import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from ixo.runtime import IXORuntime, IXOError, SETS, STAGES

class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.db=Path(self.tmp.name)/'ixo.db'
        self.r=IXORuntime(self.db)
    def tearDown(self):
        self.r.close();self.tmp.cleanup()
    def test_starts_main(self):self.assertEqual(self.r.status()['active_set'],'main')
    def test_workspace_set(self):
        self.r.activate_set('moon2');self.assertEqual(self.r.status()['active_set'],'moon2')
    def test_unknown_set_does_not_mutate(self):
        with self.assertRaises(IXOError):self.r.activate_set('invented')
        self.assertEqual(self.r.status()['counts']['events'],0)
    def test_persists_restart(self):
        self.r.activate_set('kova');self.r.close();self.r=IXORuntime(self.db)
        self.assertEqual(self.r.status()['active_set'],'kova')
    def test_proposal_not_fact(self):
        self.r.propose('A real proposition')
        self.assertEqual(self.r.status()['counts']['facts'],0)
        self.assertEqual(self.r.status()['counts']['proposals'],1)
    def test_approve_proposal(self):
        p=self.r.propose('Unique atomic statement')
        self.r.resolve(p['id'],'approve')
        self.assertEqual(self.r.status()['counts']['facts'],1)
    def test_rejected_proposal(self):
        p=self.r.propose('Unique atomic statement')
        self.r.resolve(p['id'],'reject');self.assertEqual(self.r.status()['counts']['facts'],0)
    def test_duplicate_classification(self):
        self.r.resolve(self.r.propose('The moon is green')['id'],'approve')
        p=self.r.propose(' THE  moon IS green ')
        self.assertEqual(p['classification'],'AGREE')
        self.r.resolve(p['id'],'approve')
        self.assertEqual(self.r.status()['counts']['facts'],1)
    def test_overlap_blocks_approval(self):
        self.r.resolve(self.r.propose('Contextual models are tracked')['id'],'approve')
        p=self.r.propose('Contextual models are not tracked')
        self.assertEqual(p['classification'],'REVIEW')
        with self.assertRaises(IXOError): self.r.resolve(p['id'],'approve')
        self.assertEqual(self.r.status()['counts']['facts'],1)
    def test_memory_origin_blocked(self):
        p=self.r.propose('Source object','memory')
        self.assertEqual(p['status'],'BLOCKED')
        with self.assertRaises(IXOError): self.r.resolve(p['id'],'approve')
    def test_protected_requires_reason(self):
        with self.assertRaises(IXOError):self.r.propose('A protected proposition',protected=True)
    def test_protected_reason_stored(self):
        p=self.r.propose('An invariant',protected=True,protection_reason='constitution')
        self.r.resolve(p['id'],'approve')
        self.assertEqual(self.r.status()['facts'][0]['protection_reason'],'constitution')
    def test_overflow_rejected_no_truncation(self):
        with self.assertRaises(IXOError):self.r.propose('x'*2201)
        self.assertEqual(self.r.status()['counts']['proposals'],0)
    def test_invalid_stage(self):
        with self.assertRaises(IXOError):self.r.moon('propose','no')
    def test_moon_never_writes_facts(self):
        for stage in STAGES:self.r.moon(stage,'observation')
        s=self.r.status();self.assertEqual(s['counts']['facts'],0)
        self.assertEqual(s['counts']['reflections'],5)
    def test_separate_workspace_reflection(self):
        self.r.activate_set('aixo');self.r.moon('reflect','One thing learned')
        self.assertEqual(self.r.status()['reflections'][0]['workspace'],'aixo')
    def test_unrecognized_command(self):
        with self.assertRaises(IXOError):self.r.command('/destroy everything')
    def test_event_sequence_monotonic(self):
        self.r.activate_set('hermes');self.r.moon('observe','hello')
        seqs=[x['seq'] for x in self.r.status()['events']]
        self.assertEqual(seqs,sorted(seqs,reverse=True))
    def test_db_integrity(self):
        self.r.activate_set('moon2')
        self.assertEqual(self.r.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
    def test_concurrent_writes(self):
        threads=[threading.Thread(target=lambda n=n:self.r.moon('observe',f'Observation {n}')) for n in range(15)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertEqual(self.r.status()['counts']['reflections'],15)
        self.assertEqual(self.r.status()['counts']['events'],15)
    def test_failed_approval_no_extra_event(self):
        self.r.resolve(self.r.propose('Signal active')['id'],'approve')
        p=self.r.propose('Signal inactive')
        previous=self.r.status()['counts']['events']
        with self.assertRaises(IXOError):self.r.resolve(p['id'],'approve')
        self.assertEqual(self.r.status()['counts']['events'],previous)
    def test_many_events_without_loss(self):
        for n in range(110):self.r.moon('observe',str(n))
        self.assertEqual(self.r.status()['counts']['events'],110)
        self.assertEqual(len(self.r.status()['events']),35)
    def test_no_automatic_fact_after_stage_act(self):
        self.r.command('/act Review potential connection')
        self.assertEqual(self.r.status()['counts']['facts'],0)

if __name__=='__main__':unittest.main()
