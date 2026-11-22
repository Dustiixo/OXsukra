"""Operations must call real component methods, change underlying state and preserve authority boundaries."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from ixo_foundation.system import Foundation


class FeatureOperations(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.home=Path(self.tmp.name)/'home'
        self.app=Foundation(self.home)
        self.hub=self.app.operations

    def tearDown(self):
        self.app.close()
        self.tmp.cleanup()

    def test_component_catalog_has_real_entrypoints(self):
        ids={x['id'] for x in self.hub.list()}
        self.assertIn('hermes.propose',ids)
        self.assertIn('quality.tests',ids)
        self.assertIn('workflow.investigate',ids)
        self.assertGreaterEqual(len(ids),20)

    def test_workspace_affects_underlying_runtime(self):
        sets=self.app.ixo.status(0)['sets']
        self.assertTrue(sets)
        result=self.hub.run('habitat.activate',{'workspace':sets[-1]})
        self.assertTrue(result['passed'])
        self.assertEqual(self.app.ixo.status(0)['active_set'],sets[-1])
        self.assertEqual(self.hub.run('habitat.inspect')['result']['active_set'],sets[-1])

    def test_hermes_approval_is_explicit(self):
        p=self.hub.run('hermes.propose',{'text':'A new tested operator fact'})
        self.assertTrue(p['passed'])
        self.assertEqual(self.app.ixo.status(0)['counts']['facts'],0)
        identifier=p['result']['id']
        approve=self.hub.run('hermes.resolve',{'id':identifier,'decision':'approve'})
        self.assertTrue(approve['passed'])
        self.assertEqual(self.app.ixo.status(0)['counts']['facts'],1)
        self.assertFalse(self.hub.run('hermes.resolve',{'id':identifier,'decision':'approve'})['passed'])

    def test_moon2_stages_are_real(self):
        r=self.hub.run('moon2.record',{'stage':'observe','text':'Observed filesystem event'})
        self.assertTrue(r['passed'])
        self.assertTrue(self.hub.run('moon2.inspect')['result']['reflections'])

    def test_aixo_evaluates_observed_state_not_user_claim(self):
        e=self.hub.run('aixo.experiment',{'title':'Live state','question':'Is there one fact?'})
        id_=e['result']['experiment_id']
        report=self.hub.run('aixo.evaluate',{'experiment_id':id_,'assertion':'facts_count','expected':42})
        self.assertFalse(report['passed'])
        self.assertEqual(report['result']['observed'],0)
        self.assertEqual(len(self.app.aixo.state()['evaluations']),1)

    def test_dsoe_plan_is_persisted_but_not_executed(self):
        r=self.hub.run('dsoe.plan',{'objective':'Test actual handoff workflow'})
        self.assertTrue(r['passed'],r)
        self.assertTrue(self.app.dsoe.status()['tasks'])
        self.assertEqual(self.hub.run('dsoe.inspect')['result']['native_connected'],0)

    def test_ingest_real_independent_material_and_select(self):
        root=Path(self.tmp.name)/'external-project';root.mkdir()
        (root/'app.py').write_text('def independent_function():\n    return 17\n')
        r=self.hub.run('workflow.ingest_project',{'path':str(root),'project':'Project R','domain':'retail'})
        self.assertTrue(r['passed'],r)
        self.assertGreater(r['result']['ingested']['accepted'],0)
        self.assertIn('retail',r['result']['report']['non_ixo_learning_domains'])
        self.assertTrue(r['result']['selection']['selected'])

    def test_frameshift_does_actual_analysis(self):
        result=self.hub.run('frameshift.analyze',{'text':'what if silent springs are springs?'})
        self.assertTrue(result['passed'],result)
        self.assertTrue(result['result'])

    def test_workflow_chains_real_components(self):
        before=self.app.ixo.status(0)['counts'].copy()
        r=self.hub.run('workflow.investigate',{'workspace':'main','observation':'An unclear note about running code',
          'hypothesis':'The user might refer to a program runtime', 'question':'How would we verify?'})
        self.assertTrue(r['passed'],r)
        after=self.app.ixo.status(0)['counts']
        self.assertGreater(after['proposals'],before['proposals'])
        self.assertGreater(after['reflections'],before['reflections'])
        self.assertEqual(after['facts'],before['facts'])
        self.assertEqual(len(self.app.aixo.state()['experiments']),1)
        self.assertGreater(self.app.aixo.state()['captured_events'],0)

    def test_invalid_or_failed_actions_get_receipt(self):
        r=self.hub.run('habitat.activate',{'workspace':'bad-set'})
        self.assertFalse(r['passed'])
        self.assertTrue(self.hub.receipts())
        with self.assertRaises(ValueError):
            self.hub.run('unknown.command',{})
        with self.assertRaises(ValueError):
            self.hub.run('habitat.activate',{'workspace':'main','evil':'value'})

    def test_main_cli_exposes_actual_operations(self):
        cmd=[sys.executable,'-m','ixo_foundation','--home',str(self.home),'run-feature',
             'moon2.record','--data',json.dumps({'stage':'observe','text':'Main CLI operation connected'})]
        cp=subprocess.run(cmd,capture_output=True,text=True,cwd=Path(__file__).resolve().parents[1],timeout=20)
        self.assertEqual(cp.returncode,0,cp.stderr)
        self.assertTrue(json.loads(cp.stdout)['passed'])
        self.assertTrue(any(x['text']=='Main CLI operation connected' for x in self.app.ixo.status(0)['reflections']))

    def test_cli_run_invokes_working_module_and_uses_own_home(self):
        cmd=[sys.executable,'-m','ixo_foundation.ops_cli','--home',str(self.home),'run',
             'moon2.record','--data',json.dumps({'stage':'reflect','text':'CLI verified operation'})]
        cp=subprocess.run(cmd,capture_output=True,text=True,cwd=Path(__file__).resolve().parents[1],timeout=20)
        self.assertEqual(cp.returncode,0,cp.stderr)
        self.assertTrue(json.loads(cp.stdout)['passed'])
        self.assertTrue(any(x['text']=='CLI verified operation' for x in self.app.ixo.status(0)['reflections']))


if __name__=='__main__':unittest.main()
