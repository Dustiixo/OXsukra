import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from engine import World, WorldError, check_formula


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'world.sqlite3'
        self.world = World(self.path, demo=False)

    def tearDown(self):
        self.world.close()
        self.tmp.cleanup()

    def create(self, name, prototype=None, slots=None):
        return self.world.create(name, prototype, slots, reason='Test created object')['object_id']

    def test_seed_replay_after_restart(self):
        db = Path(self.tmp.name) / 'demo.sqlite3'
        w = World(db, demo=True)
        s = w.state()
        self.assertEqual(s['revision'], 5)
        self.assertTrue(s['verified'])
        self.assertEqual(len(s['objects']), 5)
        w.close()
        w2 = World(db, demo=True)
        self.assertEqual(w2.state()['head'], s['head'])
        self.assertEqual(w2.state()['revision'], 5)
        w2.close()

    def test_inherited_formula_in_receiver_context(self):
        parent = self.create('Parent', slots={
            'bpm': {'kind':'value','value':120},
            'half': {'kind':'formula','value':'bpm / 2'}})
        child = self.create('Child', parent, {'bpm':{'kind':'value','value':155}})
        row = self.world.resolve(child)['half']
        self.assertEqual(row['value'], 77.5)
        self.assertTrue(row['inherited'])
        self.assertEqual(row['source'], parent)

    def test_parent_edit_live_propagation_but_child_override_wins(self):
        parent = self.create('Parent', slots={'bpm': {'kind':'value','value':120}})
        child = self.create('Child', parent)
        self.world.mutate('set_slot',parent,'Tune a signal',slot_name='bpm',slot={'kind':'value','value':144})
        self.assertEqual(self.world.resolve(child)['bpm']['value'],144)
        self.world.mutate('set_slot',child,'Override signal',slot_name='bpm',slot={'kind':'value','value':160})
        self.assertEqual(self.world.resolve(child)['bpm']['value'],160)

    def test_reference_is_not_prototype(self):
        a = self.create('A', slots={'x':{'kind':'value','value':2}})
        b = self.create('B',slots={'target':{'kind':'reference','value':a}})
        self.assertIn('target',self.world.resolve(b))
        self.assertNotIn('x',self.world.resolve(b))

    def test_reject_missing_reference(self):
        a = self.create('A')
        with self.assertRaisesRegex(WorldError, 'missing object'):
            self.world.mutate('set_slot',a,'Broken pointer',slot_name='target',slot={'kind':'reference','value':'unknown'})

    def test_reject_prototype_cycle(self):
        a = self.create('A')
        b = self.create('B', a)
        with self.assertRaisesRegex(WorldError, 'cycle'):
            self.world.mutate('set_prototype',a,'Dangerous cycle',prototype=b)

    def test_formula_cycle_is_reported_not_executed(self):
        a = self.create('A', slots={'a':{'kind':'formula','value':'b + 1'},'b':{'kind':'formula','value':'a + 1'}})
        row = self.world.resolve(a)['a']
        self.assertIn('Cyclic',row['error'])

    def test_formula_rejects_code_execution(self):
        for expr in ('__import__("os").system("id")','a.__class__','[1,2,3]','2 ** 20', 'b[0]'):
            with self.subTest(expr=expr), self.assertRaises(WorldError):
                check_formula(expr)

    def test_formula_math_and_bad_input(self):
        a = self.create('A',slots={'a':{'kind':'value','value':12},'b':{'kind':'formula','value':'(a + 8) / 2'}})
        self.assertEqual(self.world.resolve(a)['b']['value'],10)
        self.world.mutate('set_slot',a,'Divide by zero probe',slot_name='a',slot={'kind':'value','value':0})
        self.world.mutate('set_slot',a,'Division changed',slot_name='b',slot={'kind':'formula','value':'12 / a'})
        self.assertIn('Division by zero',self.world.resolve(a)['b']['error'])

    def test_event_revert_is_compensating_not_deletion(self):
        a = self.create('A',slots={'x':{'kind':'value','value':10}})
        self.world.mutate('set_slot',a,'Change x to eleven',slot_name='x',slot={'kind':'value','value':11})
        revision_before = self.world.revision
        self.world.undo_object(a)
        self.assertEqual(self.world.revision,revision_before+1)
        self.assertEqual(self.world.resolve(a)['x']['value'],10)
        self.assertEqual(self.world.history(1)[0]['action'],'revert')
        self.assertEqual(len(self.world.history()),3)

    def test_revert_creation_rejects_live_dependents(self):
        a = self.create('A')
        b = self.create('B',prototype=a)
        with self.assertRaisesRegex(WorldError,'Prototype must reference'):
            self.world.undo_object(a)
        self.assertIn(a,self.world.state()['objects'])

    def test_revert_creation_without_references_removes_only_live_object(self):
        a = self.create('A')
        self.world.undo_object(a)
        self.assertNotIn(a,self.world.state()['objects'])
        self.assertEqual(len(self.world.history()),2)

    def test_revision_conflict(self):
        revision=self.world.revision
        self.create('A')
        with self.assertRaisesRegex(WorldError,'Outdated revision'):
            self.world.create('B',reason='Try stale write',expected_revision=revision)

    def test_hash_integrity_corruption_detected(self):
        self.create('A')
        self.world.conn.execute('UPDATE events SET reason=? WHERE seq=1',('tampered',))
        self.world.conn.commit()
        with self.assertRaisesRegex(WorldError,'integrity chain mismatch'):
            self.world.verify()

    def test_undo_parent_change_restores_link(self):
        a=self.create('Root')
        b=self.create('Child')
        self.world.mutate('set_prototype',b,'Adopt root',prototype=a)
        self.assertEqual(self.world.state()['objects'][b]['prototype'],a)
        self.world.undo_object(b)
        self.assertIsNone(self.world.state()['objects'][b]['prototype'])

    def test_no_recursive_code_and_injection_rejected(self):
        a=self.create('A')
        with self.assertRaises(WorldError):
            self.world.mutate('set_slot',a,'Attempt unsafe',slot_name='<script>',slot={'kind':'value','value':'x'})
        with self.assertRaises(WorldError):
            self.world.mutate('set_slot',a,'Attempt huge',slot_name='x',slot={'kind':'value','value':float('nan')})

if __name__=='__main__':
    unittest.main()
