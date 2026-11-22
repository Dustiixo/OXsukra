import json
import tempfile
import unittest
from pathlib import Path
from aixo.engine import AIXOEngine,AIXOError
from ixo.runtime import IXORuntime
from ixo.bridge import capture

class JointEngineTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name)
  self.ixo=IXORuntime(root/'ixo.sqlite3');self.aixo=AIXOEngine(root/'aixo.sqlite3')
 def tearDown(self):self.ixo.close();self.aixo.close();self.temp.cleanup()
 def test_course_requires_artifact(self):
  with self.assertRaises(AIXOError):self.aixo.complete_lesson('A1',' ')
 def test_course_order(self):
  with self.assertRaises(AIXOError):self.aixo.complete_lesson('A2','read')
  self.aixo.complete_lesson('A1','Saved file')
  self.assertEqual(self.aixo.state()['lessons'][0]['artifact'],'Saved file')
 def test_experiment_eval_pass_and_fail(self):
  i=self.aixo.create_experiment('Workspace','Is it main?')['experiment_id']
  good=self.aixo.evaluate(i,'active_set','main',self.ixo.status(0));self.assertTrue(good['passed'])
  bad=self.aixo.evaluate(i,'active_set','moon2',self.ixo.status(0));self.assertFalse(bad['passed'])
  self.assertEqual(len(self.aixo.state()['evaluations']),2)
 def test_reject_unsafe_assertion(self):
  i=self.aixo.create_experiment('Check','Run no code')['experiment_id']
  with self.assertRaises(AIXOError):self.aixo.evaluate(i,'__class__','anything',self.ixo.status(0))
 def test_capture_idempotent(self):
  self.ixo.activate_set('aixo');self.ixo.moon('observe','Event recorded')
  self.assertEqual(capture(self.ixo,self.aixo),2)
  self.assertEqual(capture(self.ixo,self.aixo),0)
  self.assertEqual(self.aixo.state()['captured_events'],2)
 def test_capture_after_new_event(self):
  self.ixo.activate_set('hermes');capture(self.ixo,self.aixo)
  self.ixo.propose('New fact for isolated capture');self.assertEqual(capture(self.ixo,self.aixo),1)
 def test_capture_no_mutation_of_ixo(self):
  self.ixo.activate_set('moon2');count=self.ixo.status(0)['counts']['events'];capture(self.ixo,self.aixo)
  i=self.aixo.create_experiment('Read-only','Verify workspace')['experiment_id']
  self.aixo.evaluate(i,'active_set','moon2',self.ixo.status(0))
  self.assertEqual(count,self.ixo.status(0)['counts']['events'])
 def test_persistence_on_both_sides(self):
  self.ixo.activate_set('aixo');self.aixo.complete_lesson('A1','Artifact exists')
  capture(self.ixo,self.aixo);dbi=self.ixo.path;dba=self.aixo.path;self.ixo.close();self.aixo.close()
  self.ixo=IXORuntime(dbi);self.aixo=AIXOEngine(dba)
  self.assertEqual(self.ixo.status(0)['active_set'],'aixo')
  self.assertTrue(self.aixo.state()['lessons'][0]['completed_at'])
  self.assertEqual(self.aixo.state()['captured_events'],1)
 def test_missing_experiment(self):
  with self.assertRaises(AIXOError):self.aixo.evaluate(999,'active_set','main',self.ixo.status(0))
 def test_no_arbitrary_aixo_write_into_ixo(self):
  self.aixo.create_experiment('Isolation','Evidence separate')
  self.assertEqual(self.ixo.status(0)['counts']['events'],0)
  self.assertEqual(self.ixo.status(0)['counts']['facts'],0)
