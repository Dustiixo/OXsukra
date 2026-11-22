import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from visual_lab.export_trace import export
from flowmesh import engine

class TraceProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.package=Path(__file__).resolve().parents[2]
        cls.sample=json.loads((cls.package/'visual_lab/sample_trace.json').read_text(encoding='utf-8'))

    def test_sample_uses_correct_schema_and_actual_events(self):
        t=self.sample
        self.assertEqual(t['schema'],'ixo.flowmesh.visual-trace.v1')
        self.assertEqual(t['source_integrity'],'PASS')
        self.assertEqual(len(t['events']),72)
        self.assertEqual(len(t['findings']),15)
        self.assertEqual(t['source_mode'],'offline')
        self.assertEqual([x['seq'] for x in t['events']],list(range(1,73)))

    def test_projection_has_no_absolute_file_paths_or_receipt_chain_keys(self):
        t=self.sample
        self.assertNotIn('session_id',t)
        for e in t['events']:
            self.assertNotIn('receipt',e)
            self.assertNotIn('state_sha256',e)
            self.assertNotIn('C:\\',str(e))
        for f in t['findings']:
            self.assertEqual(f['file'],Path(f['file']).name)

    def test_live_export_rejects_failed_integrity(self):
        with patch('visual_lab.export_trace.engine.verify',return_value={'integrity':'FAIL'}):
            with self.assertRaisesRegex(ValueError,'refusing export'):
                export(Path('/tmp/nonexistent'))

    def test_export_from_demo_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'session'
            engine.start(root,'Timeline and research evidence',budget=3)
            input_file=Path(tmp)/'case.md'
            input_file.write_text('Research evidence needs a clear receipt.\n',encoding='utf8')
            engine.add_source(root,input_file)
            before=engine.verify(root)['last_hash']
            t=export(root)
            after=engine.verify(root)['last_hash']
            self.assertEqual(before,after)
            self.assertEqual(t['source_integrity'],'PASS')
            self.assertEqual(t['source_mode'],'offline')
            self.assertNotIn('receipt',t['events'][0])

if __name__=='__main__': unittest.main()
