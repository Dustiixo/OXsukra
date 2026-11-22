import copy, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from bytebridge.core import analyze_bytes
from bytebridge.ledger import initial_world, commit
from bytebridge.self_receipt import SCHEMA,sign_observation,import_observation
from bytebridge.cli import initialize

KEY=b'k'*32
class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.v=analyze_bytes(b'\x00\xff\x01abc'*100,'example.bin')
        self.w=initial_world(self.v['input']['sha256'])
        self.raw={'schema':SCHEMA,'sourceSha256':self.w['artifactHash'],'representationPrint':self.v['print'],
            'baseRevision':0,'baseHead':self.w['head'],'slot':'depth','before':1.2,'value':2.1,
            'nonce':'a'*32,'runtime':{'implementation':'russellallen/self','commit':'unverified-fixture',
              'worldImage':'unverified-fixture','objectOutlinerObserved':False}}
        self.receipt=sign_observation(self.raw,self.w,self.v,KEY)
    def test_review_only_and_manual_commit(self):
        p=import_observation(self.receipt,self.w,self.v,KEY,set())
        self.assertEqual(self.w['revision'],0)
        w2=commit(self.w,p,0)
        self.assertEqual(w2['mapping']['depth'],2.1)
        self.assertEqual(self.w['mapping']['depth'],1.2)
    def test_replay(self):
        with self.assertRaisesRegex(ValueError,'Replayed'):
            import_observation(self.receipt,self.w,self.v,KEY,{'a'*32})
    def test_tampered_mac(self):
        r=copy.deepcopy(self.receipt);r['value']=2.9
        with self.assertRaisesRegex(ValueError,'authentication'):
            import_observation(r,self.w,self.v,KEY,set())
    def test_wrong_key(self):
        with self.assertRaisesRegex(ValueError,'authentication'):
            import_observation(self.receipt,self.w,self.v,b'x'*32,set())
    def test_wrong_identity(self):
        r=copy.deepcopy(self.receipt);r['sourceSha256']='f'*64
        with self.assertRaisesRegex(ValueError,'different world'):
            import_observation(r,self.w,self.v,KEY,set())
    def test_stale(self):
        p=import_observation(self.receipt,self.w,self.v,KEY,set())
        w2=commit(self.w,p,0)
        with self.assertRaisesRegex(ValueError,'Stale'):
            import_observation(self.receipt,w2,self.v,KEY,set())
    def test_code_injection_slot(self):
        r=copy.deepcopy(self.receipt);r['slot']='__import__("os")'
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            import_observation(r,self.w,self.v,KEY,set())
    def test_nan(self):
        r=copy.deepcopy(self.receipt);r['value']=float('nan')
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            import_observation(r,self.w,self.v,KEY,set())
    def test_unknown_fields(self):
        r=copy.deepcopy(self.receipt);r['command']='rm -rf /'
        with self.assertRaisesRegex(ValueError,'fields'):
            import_observation(r,self.w,self.v,KEY,set())
    def test_weak_key(self):
        with self.assertRaisesRegex(ValueError,'32 bytes'):
            import_observation(self.receipt,self.w,self.v,b'weak',set())
    def test_cli_replay_and_key_isolation(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'src.bin';src.write_bytes(b'\x00\xffabc'*100)
            out=root/'world';initialize(src,out)
            v=json.loads((out/'vessel.json').read_text());w=json.loads((out/'world.json').read_text())
            raw=copy.deepcopy(self.raw)
            raw.update(sourceSha256=w['artifactHash'],representationPrint=v['print'])
            receipt=sign_observation(raw,w,v,KEY)
            rp=root/'receipt.json';rp.write_text(json.dumps(receipt));key=root/'key';key.write_bytes(KEY)
            cmd=[sys.executable,'-m','bytebridge.cli','self-import',str(out),'--receipt',str(rp),'--key-file',str(key)]
            first=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            self.assertEqual(json.loads(first.stdout)['status'],'REVIEW_REQUIRED')
            self.assertEqual(json.loads((out/'world.json').read_text())['revision'],0)
            again=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(again.returncode,2)
            self.assertIn('Replayed',again.stderr)
            bad=subprocess.run(cmd[:-1]+[str(out/'original.bin')],capture_output=True,text=True)
            self.assertEqual(bad.returncode,2)
            self.assertIn('cannot reside',bad.stderr)
if __name__=='__main__':unittest.main()
