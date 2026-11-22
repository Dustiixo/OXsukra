"""DSOE integration regression tests using real SQLite and all three adapters."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from aixo.engine import AIXOError
from dsoe.registry import PROVIDERS
from dsoe.store import DSOEError
from dsoe.protocol import fixture
from ixo_foundation.system import Foundation

class DSOEContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name)
        self.app=Foundation(self.home)

    def tearDown(self):
        self.app.close()
        self.temp.cleanup()

    def make_task(self):
        return self.app.dsoe.plan('Analyze an ambiguous instruction and define evidence')

    def make_report(self,job,envelope=None,**updates):
        envelope=envelope or self.app.dsoe.store.make_envelope(job['id'])
        report={'protocol':'dsoe-json-file-v1','job_id':job['id'],'provider':job['provider'],
                'request_sha256':envelope['request_sha256'],
                'summary':'Stage was examined; this is an unverified fixture result'}
        report.update({'evidence_origin':'fixture'})
        report.update(fixture(envelope))
        report.update(updates)
        return report

    def test_three_pinned_separate_upstreams(self):
        self.assertEqual([x.key for x in PROVIDERS],
                         ['pantheonos','odysseus_pantheon','duskript_pantheon'])
        self.assertTrue(all(not x.upstream_connected for x in PROVIDERS))
        self.assertEqual(len({x.repository for x in PROVIDERS}),3)

    def test_new_task_has_three_persistent_ordered_jobs(self):
        data=self.make_task()
        self.assertEqual(data['task']['state'],'DRAFT')
        self.assertEqual([j['stage'] for j in data['jobs']],['plan','operate','review'])
        self.assertEqual(self.app.status()['ixo']['counts']['facts'],0)
        self.assertEqual(self.app.status()['ixo']['counts']['events'],0)
        self.assertEqual(self.app.status()['dsoe']['task_count'],1)

    def test_requires_operator_task_approval(self):
        task=self.make_task()['task']['id']
        with self.assertRaisesRegex(DSOEError,'approval'):
            self.app.dsoe.dispatch(task)
        self.assertFalse((self.home/'dsoe'/'outbox').exists())
        self.app.dsoe.store.approve(task)
        r=self.app.dsoe.dispatch(task)
        self.assertTrue(Path(r['handoff_file']).exists())
        self.assertFalse(r['native_upstream_execution'])

    def test_habitat_identity_is_not_silently_changed(self):
        with self.assertRaisesRegex(DSOEError,'activate workspace'):
            self.app.dsoe.plan('Test',workspace='research')
        self.assertEqual(self.app.ixo.status()['active_set'],'main')
        self.app.ixo.activate_set('research')
        self.assertEqual(self.app.dsoe.plan('Test',workspace='research')['task']['workspace'],'research')

    def test_cannot_skip_stages_or_review_before_report(self):
        task=self.make_task()
        tid=task['task']['id']
        self.app.dsoe.store.approve(tid)
        self.app.dsoe.dispatch(tid)
        with self.assertRaisesRegex(DSOEError,'Previous stage'):
            self.app.dsoe.dispatch(tid)
        with self.assertRaisesRegex(DSOEError,'unreported'):
            self.app.dsoe.store.review(task['jobs'][0]['id'],True,'Unreviewed')

    def test_reject_inconsistent_provider_and_checksum(self):
        task=self.make_task()
        tid=task['task']['id']
        self.app.dsoe.store.approve(tid)
        self.app.dsoe.dispatch(tid)
        job=task['jobs'][0]
        for change in ({'provider':'odysseus_pantheon'}, {'request_sha256':'x'*64}, {'job_id':'other'}):
            with self.subTest(change=change):
                with self.assertRaisesRegex(DSOEError,'mismatch'):
                    self.app.dsoe.store.report(job['id'],self.make_report(job,**change))
        self.assertEqual(self.app.dsoe.detail(tid)['jobs'][0]['state'],'DISPATCHED')

    def test_report_requires_dispatched_job_and_is_bounded(self):
        task=self.make_task()
        job=task['jobs'][0]
        with self.assertRaisesRegex(DSOEError,'dispatched'):
            self.app.dsoe.store.report(job['id'],self.make_report(job))
        self.app.dsoe.store.approve(task['task']['id'])
        self.app.dsoe.dispatch(task['task']['id'])
        with self.assertRaisesRegex(DSOEError,'exceeds'):
            self.app.dsoe.store.report(job['id'],self.make_report(job,extra='x'*17000))

    def test_result_hash_conflicts_are_rejected(self):
        task=self.make_task()
        tid=task['task']['id']; job=task['jobs'][0]
        self.app.dsoe.store.approve(tid);self.app.dsoe.dispatch(tid)
        payload=self.make_report(job)
        self.app.dsoe.store.report(job['id'],payload)
        self.app.dsoe.store.report(job['id'],payload)
        with self.assertRaisesRegex(DSOEError,'dispatched'):
            self.app.dsoe.store.report(job['id'],{**payload,'summary':'Different replay'})

    def test_sequential_three_stage_evidence_and_no_fact_promotion(self):
        task=self.make_task();tid=task['task']['id']
        self.app.dsoe.store.approve(tid)
        for i,job in enumerate(task['jobs']):
            handoff=self.app.dsoe.dispatch(tid)
            self.assertEqual(handoff['provider'],PROVIDERS[i].key)
            envelope=json.loads(Path(handoff['handoff_file']).read_text(encoding='utf-8'))
            self.assertEqual(len(envelope['accepted_predecessors']),i)
            response=self.make_report(job,envelope)
            report_path=self.home/f'result-{i}.json'
            report_path.write_text(json.dumps(response), encoding='utf-8')
            self.app.dsoe.report_file(job['id'],report_path)
            with self.assertRaisesRegex(DSOEError,'acceptance'):
                self.app.dsoe.record_evidence(job['id'])
            self.app.dsoe.store.review(job['id'],True,f'Validated stage {i} manually')
            self.assertTrue(self.app.dsoe.record_evidence(job['id'])['aixo_evidence_new'])
            self.assertFalse(self.app.dsoe.record_evidence(job['id'])['aixo_evidence_new'])
        self.assertEqual(self.app.dsoe.detail(tid)['task']['state'],'COMPLETE')
        self.assertEqual(self.app.aixo.state()['dsoe_evidence_count'],3)
        self.assertTrue(all(row['evidence_origin']=='fixture' for row in self.app.aixo.state()['dsoe_evidence']))
        self.assertEqual(self.app.ixo.status()['counts']['facts'],0)
        self.assertEqual(self.app.ixo.status()['counts']['proposals'],0)
        with self.assertRaisesRegex(DSOEError,'approval|already accepted'):
            self.app.dsoe.dispatch(tid)

    def test_rejected_stage_blocks_follow_on_stages(self):
        task=self.make_task();tid=task['task']['id'];job=task['jobs'][0]
        self.app.dsoe.store.approve(tid);self.app.dsoe.dispatch(tid)
        self.app.dsoe.store.report(job['id'],self.make_report(job))
        self.app.dsoe.store.review(job['id'],False,'Unreliable model output')
        with self.assertRaisesRegex(DSOEError,'approval'):
            self.app.dsoe.dispatch(tid)
        self.assertEqual(self.app.dsoe.detail(tid)['task']['state'],'BLOCKED')

    def test_aixo_provenance_and_conflict_guard(self):
        task=self.make_task();tid=task['task']['id'];job=task['jobs'][0]
        self.app.dsoe.store.approve(tid);self.app.dsoe.dispatch(tid)
        self.app.dsoe.store.report(job['id'],self.make_report(job))
        self.app.dsoe.store.review(job['id'],True,'Reviewed')
        record=self.app.dsoe.store.verified_result(job['id'])
        with self.assertRaisesRegex(AIXOError,'another IXO'):
            self.app.aixo.ingest_dsoe_evidence({**record,'ixo_source_id':'another-instance'},self.app.ixo._get('instance_id'))
        self.assertTrue(self.app.aixo.ingest_dsoe_evidence(record,self.app.ixo._get('instance_id')))
        with self.assertRaisesRegex(AIXOError,'conflict'):
            self.app.aixo.ingest_dsoe_evidence({**record,'sha256':'a'*64},self.app.ixo._get('instance_id'))
        self.assertEqual(self.app.aixo.state()['dsoe_evidence_count'],1)

    def test_reopening_same_home_persists_tasks(self):
        tid=self.make_task()['task']['id']
        self.app.close()
        self.app=Foundation(self.home)
        self.assertEqual(self.app.dsoe.detail(tid)['task']['state'],'DRAFT')
        self.assertEqual(len(self.app.dsoe.detail(tid)['jobs']),3)

    def test_no_cross_instance_dsoe_database(self):
        tid=self.make_task()['task']['id']
        self.app.close()
        self.app=None
        from dsoe.store import DSOEStore
        with self.assertRaisesRegex(DSOEError,'another IXO'):
            DSOEStore(self.home/'dsoe'/'dsoe.sqlite3','unrelated-source')
        self.app=Foundation(self.home)
        self.assertEqual(self.app.dsoe.detail(tid)['task']['id'],tid)

    def test_cli_provider_registry_and_durable_plan(self):
        # Execute actual CLI in child Python process rather than calling parser directly.
        root=Path(__file__).resolve().parents[1]
        def command(*args):
            run=subprocess.run([sys.executable,'-m','ixo_foundation','--home',str(self.home),'dsoe',*args],cwd=root,text=True,capture_output=True)
            self.assertEqual(run.returncode,0,run.stderr)
            return json.loads(run.stdout)
        self.assertEqual(len(command('providers')),3)
        task=command('plan','Write a verified plan')
        self.assertEqual(command('detail',task['task']['id'])['task']['state'],'DRAFT')

    def test_stage_result_type_contracts(self):
        task=self.make_task();job=task['jobs'][0];tid=task['task']['id']
        self.app.dsoe.store.approve(tid);self.app.dsoe.dispatch(tid)
        report=self.make_report(job)
        report.pop('team_plan')
        with self.assertRaisesRegex(DSOEError,'team_plan'):
            self.app.dsoe.store.report(job['id'],report)

if __name__=='__main__': unittest.main()
