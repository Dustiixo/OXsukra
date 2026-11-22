"""Regression and anti-self-contamination checks, independent of any live AI model."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from experience.store import ExperienceStore, ExperienceError
from ixo_foundation.system import Foundation
from ixo.runtime import IXORuntime

ROOT=Path(__file__).resolve().parents[1]

class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.dir=tempfile.TemporaryDirectory()
        self.home=Path(self.dir.name)
        self.store=ExperienceStore(self.home/'xp.sqlite3')

    def tearDown(self):
        self.store.close()
        self.dir.cleanup()

    def add(self, name, *, origin='ixo_development',domain='ixo_engineering',partition='learning',kind='material',project='IXO'):
        return self.store.record(content=f'Case content: {name}',project=project,domain=domain,
                                 origin=origin,partition=partition,kind=kind,source_ref=f'source://{name}')

    def test_only_ixo_material_flags_imbalance_and_selects_no_general_material(self):
        for i in range(8):self.add(f'ixo-{i}')
        stats=self.store.report()
        self.assertEqual(stats['ixo_exposure_share'],1.0)
        self.assertTrue(any('dominates' in w for w in stats['warnings']))
        self.assertEqual(self.store.select(scope='general')['selected'],0)
        self.assertEqual(self.store.select(scope='ixo')['selected'],8)

    def test_external_source_labels_not_guessed_from_ixo_text(self):
        self.store.record(content='IXO appears in a real independent workflow example',project='Haven',
                          domain='home_tools',origin='independent_project',source_ref='haven/a.md')
        self.assertEqual(self.store.report()['independent_learning_records'],1)

    def test_global_dedup_prevents_cross_domain_and_holdout_leakage(self):
        original=self.add('same')
        dupe=self.store.record(content='Case content: same',project='Haven',domain='home_tools',
                               origin='independent_project',partition='holdout',kind='task_case',source_ref='copy.md')
        self.assertEqual(original['id'],dupe['id'])
        self.assertTrue(dupe['duplicate'])
        self.assertEqual(dupe['original_partition'],'learning')
        self.assertEqual(self.store.report()['total_records'],1)
        self.assertEqual(self.store.report()['observed_exposures'],2)

    def test_balance_when_there_are_many_ixo_events(self):
        for i in range(120):self.add(f'ixo-{i}')
        for i in range(10):self.add(f'haven-{i}',project='Haven',domain='personal_habits',origin='independent_project')
        for i in range(10):self.add(f'kova-{i}',project='Kova',domain='retail_systems',origin='independent_project')
        out=self.store.select(max_items=25,self_cap=0.35)
        self.assertGreater(out['by_origin'].get('ixo_development',0),0)
        self.assertLessEqual(out['by_origin']['ixo_development']/out['selected'],0.35)
        self.assertEqual(out['selected'],25)
        self.assertEqual(len({x['id'] for x in out['records']}),25)
        self.assertEqual(out,self.store.select(max_items=25,self_cap=0.35))

    def test_export_has_no_holdouts_and_never_overwrites(self):
        self.add('self')
        self.add('haven',origin='independent_project',domain='home',project='Haven')
        hold=self.add('hold',origin='independent_project',domain='home',project='Haven',partition='holdout',kind='task_case')
        target=self.home/'export.jsonl'
        x=self.store.export(target)
        self.assertEqual(x['exported'],1)
        self.assertNotIn(hold['id'],target.read_text())
        with self.assertRaises(FileExistsError):self.store.export(target)

    def test_general_method_gate_needs_three_external_holdouts_two_domains(self):
        method=self.store.propose_method('candidate','Try a method on unrelated projects')
        id_=method['id']
        with self.assertRaisesRegex(ExperienceError,'blocked'):
            self.store.promote(id_)
        for i,domain in enumerate(('home_tools','retail','retail')):
            record=self.add(f'case-{i}',project='outside',origin='independent_project',
                            domain=domain,partition='holdout',kind='task_case')
            self.store.assess(id_,record['id'],passed=True,assessor='operator',evidence_ref=f'review/{i}.md')
        self.assertTrue(self.store.method_status(id_)['eligible_for_operator_promotion'])
        promoted=self.store.promote(id_)
        self.assertEqual(promoted['status'],'OPERATOR_PROMOTED')
        self.assertTrue(promoted['assessment'].startswith('Operator-attested'))
        with self.assertRaises(ExperienceError):self.store.promote(id_)

    def test_one_failed_external_case_blocks_promotion(self):
        method=self.store.propose_method('bad','This method sometimes fails')['id']
        for i,domain in enumerate(('home','home','retail','music')):
            r=self.add(f'failure-{i}',origin='independent_project',domain=domain,
                       partition='holdout',kind='task_case',project='different')
            self.store.assess(method,r['id'],passed=i!=3,assessor='deterministic_test',evidence_ref=f'test/{i}')
        self.assertFalse(self.store.method_status(method)['eligible_for_operator_promotion'])
        with self.assertRaises(ExperienceError):self.store.promote(method)

    def test_ixo_only_cases_cannot_validate_general_methods(self):
        candidate=self.store.propose_method('generic','Supposedly general')['id']
        record=self.add('internal-case',partition='holdout',kind='task_case')
        with self.assertRaisesRegex(ExperienceError,'IXO development'):
            self.store.assess(candidate,record['id'],passed=True,assessor='operator',evidence_ref='log.txt')

    def test_fixtures_cannot_be_promoted_or_used_for_training(self):
        fixture=self.add('fixture',origin='fixture',partition='holdout',kind='task_case')
        candidate=self.store.propose_method('fake','Should never pass')['id']
        with self.assertRaisesRegex(ExperienceError,'non-fixture'):
            self.store.assess(candidate,fixture['id'],passed=True,assessor='operator',evidence_ref='anything')
        self.assertEqual(self.store.report()['fixture_records'],1)
        self.assertEqual(self.store.select()['selected'],0)

    def test_readonly_sync_preserves_ixo_and_deduplicates_exposures(self):
        with Foundation(self.home/'app') as app:
            app.ixo.activate_set('moon2')
            app.ixo.moon('observe','Same thing')
            app.ixo.moon('observe','Same thing')
            first=app.experience.capture_ixo(app.ixo)
            second=app.experience.capture_ixo(app.ixo)
            self.assertEqual(first['new_exposures'],3)
            self.assertEqual(second['new_exposures'],0)
            self.assertEqual(app.experience.report()['observed_exposures'],3)
            self.assertEqual(app.experience.report()['ixo_development_records'],3)
            self.assertEqual(app.ixo.status()['counts']['facts'],0)
        with Foundation(self.home/'app') as app:
            self.assertEqual(app.experience.report()['observed_exposures'],3)

    def test_second_ixo_source_refused(self):
        one=IXORuntime(self.home/'one.sqlite3')
        two=IXORuntime(self.home/'two.sqlite3')
        try:
            self.store.capture_ixo(one)
            with self.assertRaisesRegex(ExperienceError,'bound to another'):
                self.store.capture_ixo(two)
        finally:
            one.close();two.close()

    def test_file_optin_limits_symlinks_and_excludes_nontext(self):
        root=self.home/'project';root.mkdir()
        (root/'a.md').write_text('Haven specs',encoding='utf-8')
        (root/'bad.jpg').write_bytes(b'not image')
        (root/'.git').mkdir()
        (root/'.git'/'hidden.md').write_text('should not ingest')
        result=self.store.ingest_tree(root,project='Haven',domain='home_tools',origin='independent_project')
        self.assertEqual(result['accepted'],1)
        self.assertEqual(self.store.report()['independent_learning_records'],1)
        with self.assertRaises(ExperienceError):self.store.record_file(root/'bad.jpg',project='x',domain='y',origin='independent_project')

    def test_cli_real_subprocess_end_to_end(self):
        def run(*args):
            p=subprocess.run([sys.executable,'-m','ixo_foundation','--home',str(self.home/'cli'),
                              'experience',*args],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            return json.loads(p.stdout)
        self.assertEqual(run('report')['total_records'],0)
        out=run('add','A separate old project note','--project','Haven','--domain','home',
                '--origin','independent_project','--source','archive/Haven/notes.md')
        self.assertTrue(out['ok'])
        self.assertEqual(run('report')['independent_learning_records'],1)
        self.assertEqual(run('select')['selected'],1)

if __name__=='__main__':unittest.main()
