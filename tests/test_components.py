"""Dedicated acceptance contracts for separately implemented IXO components."""
import tempfile
import unittest
from pathlib import Path
from ixo.runtime import IXORuntime, IXOError
from aixo.engine import AIXOEngine
from ixo.bridge import capture


class ComponentContracts(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)
        self.ixo=IXORuntime(self.path/'ixo.db')
        self.aixo=AIXOEngine(self.path/'aixo.db')

    def tearDown(self):
        self.ixo.close(); self.aixo.close(); self.temp.cleanup()

    def test_habitat_exposes_independent_component(self):
        self.assertIsNotNone(self.ixo.habitat)
        self.assertEqual(self.ixo.habitat.activate_set('moon2')['active_set'],'moon2')
        self.assertEqual(self.ixo.status(0)['active_set'],'moon2')

    def test_habitat_rejects_unknown_without_an_event(self):
        before=self.ixo.status(0)['counts']['events']
        with self.assertRaises(IXOError): self.ixo.habitat.activate_set('imaginary')
        self.assertEqual(self.ixo.status(0)['counts']['events'],before)

    def test_hermes_explicit_proposal_and_approval(self):
        p=self.ixo.hermes.propose('The orbital core is a navigation landmark')
        self.assertEqual(p['status'],'PENDING')
        self.assertEqual(self.ixo.status(0)['counts']['facts'],0)
        self.ixo.hermes.resolve(p['id'],'approve')
        self.assertEqual(self.ixo.status(0)['counts']['facts'],1)

    def test_hermes_memory_origin_blocked(self):
        p=self.ixo.hermes.propose('Memory is untrusted',source='memory')
        self.assertEqual(p['status'],'BLOCKED')
        with self.assertRaises(IXOError):self.ixo.hermes.resolve(p['id'],'approve')

    def test_hermes_refuses_silent_truncation(self):
        with self.assertRaises(IXOError):self.ixo.hermes.propose('z'*2201)
        self.assertEqual(self.ixo.status(0)['counts']['proposals'],0)

    def test_hermes_protected_requires_reason(self):
        with self.assertRaises(IXOError):self.ixo.hermes.propose('Protected',protected=True)

    def test_moon2_ledger_does_not_create_a_fact(self):
        self.ixo.moon2.moon('reflect','This might be important')
        state=self.ixo.status(0)
        self.assertEqual(state['counts']['reflections'],1)
        self.assertEqual(state['counts']['facts'],0)

    def test_moon2_bad_stage_does_not_emit(self):
        with self.assertRaises(IXOError):self.ixo.moon2.moon('hallucinate','wrong')
        self.assertEqual(self.ixo.status(0)['counts']['events'],0)

    def test_aixo_captures_but_cannot_change_ixo(self):
        self.ixo.habitat.activate_set('hermes')
        before=self.ixo.status(0)
        self.assertEqual(capture(self.ixo,self.aixo),1)
        self.assertEqual(capture(self.ixo,self.aixo),0)
        self.assertEqual(self.ixo.status(0)['counts'],before['counts'])
        self.assertEqual(self.aixo.state()['captured_events'],1)

    def test_aixo_evaluates_true_and_false(self):
        ex=self.aixo.create_experiment('Habitat contract','Workspace restored')['experiment_id']
        snapshot=self.ixo.status(0)
        yes=self.aixo.evaluate(ex,'active_set','main',snapshot)
        no=self.aixo.evaluate(ex,'active_set','moon2',snapshot)
        self.assertTrue(yes['passed'])
        self.assertFalse(no['passed'])

    def test_black_hole_client_is_a_client_not_runtime(self):
        js=(Path(__file__).parents[1]/'web'/'app.js').read_text(encoding='utf-8')
        self.assertIn('BLACK HOLE PORTAL',js)
        self.assertIn("command('/go main')",js)
        self.assertNotIn('localStorage.setItem',js)

    def test_restart_persists_each_domain(self):
        self.ixo.activate_set('aixo')
        self.ixo.moon('observe','first event')
        self.aixo.create_experiment('Recover','Check persistence')
        capture(self.ixo,self.aixo)
        self.ixo.close();self.aixo.close()
        self.ixo=IXORuntime(self.path/'ixo.db')
        self.aixo=AIXOEngine(self.path/'aixo.db')
        self.assertEqual(self.ixo.status(0)['active_set'],'aixo')
        self.assertEqual(self.ixo.status(0)['counts']['reflections'],1)
        self.assertEqual(len(self.aixo.state()['experiments']),1)
        self.assertEqual(self.aixo.state()['captured_events'],2)

if __name__=='__main__':unittest.main()
