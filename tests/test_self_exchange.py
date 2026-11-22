"""v0.2.2 exact source handoff and verified review-to-render integration."""
import copy, json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from bytebridge.core import analyze_bytes, digest, verify_vessel
from bytebridge.ledger import initial_world
from bytebridge.self_exchange import source_for_revision, one_slot_literal_edit, validate_source_evidence, METHOD
from bytebridge.self_receipt import SCHEMA2, sign_observation, import_observation

KEY=b'K'*32

class HandoffParserTests(unittest.TestCase):
    def setUp(self):
        self.raw=(b'\x00\xff\x11!HELLO-COLOR-SPATIAL\r\n'*60)
        self.v=analyze_bytes(self.raw,'source.bin')
        self.w=initial_world(self.v['input']['sha256'])
        self.a=source_for_revision(self.v,self.w)
        self.b=self.a.replace(b'  depth <- 1.2.',b'  depth <- 2.7.')

    def test_exact_source_and_1000_splices(self):
        self.assertTrue(verify_vessel(self.raw,self.v))
        self.assertEqual(self.v['input']['sha256'],digest(self.raw))
        self.assertEqual(len(self.v['splices']),1000)
        self.assertEqual(one_slot_literal_edit(self.a,self.b),('depth',1.2,2.7))
        self.assertIn(self.w['head'].encode(),self.a)
    def test_no_edit(self):
        with self.assertRaisesRegex(ValueError,'No Self slot'):
            one_slot_literal_edit(self.a,self.a)
    def test_two_edit_rejected(self):
        changed=self.b.replace(b'  twist <- 2.',b'  twist <- 3.')
        with self.assertRaisesRegex(ValueError,'Exactly one'):
            one_slot_literal_edit(self.a,changed)
    def test_added_method_is_rejected(self):
        changed=self.b.replace(b'  depth <- 2.7.',b'  depth <- 2.7.\n  eval = ( | | shell command: \'oops\' ).')
        with self.assertRaisesRegex(ValueError,'outside one'):
            one_slot_literal_edit(self.a,changed)
    def test_patch_mutation_rejected(self):
        changed=self.b.replace(b'  patch0000 = (|',b'  patch9999 = (|')
        with self.assertRaisesRegex(ValueError,'outside one'):
            one_slot_literal_edit(self.a,changed)
    def test_header_mutation_rejected(self):
        changed=self.b.replace(self.w['head'].encode(),b'f'*64)
        with self.assertRaisesRegex(ValueError,'outside one'):
            one_slot_literal_edit(self.a,changed)
    def test_nan_rejected(self):
        changed=self.a.replace(b'  depth <- 1.2.',b'  depth <- NaN.')
        with self.assertRaisesRegex(ValueError,'numeric slot'):
            one_slot_literal_edit(self.a,changed)
    def test_bounds_rejected(self):
        changed=self.a.replace(b'  depth <- 1.2.',b'  depth <- 12.')
        with self.assertRaisesRegex(ValueError,'out of bounds'):
            one_slot_literal_edit(self.a,changed)
    def test_unicode_rejected(self):
        with self.assertRaisesRegex(ValueError,'ASCII'):
            one_slot_literal_edit(self.a,self.b+b'\xff')
    def test_newline_rejected(self):
        changed=self.b.replace(b'\n',b'\r\n')
        with self.assertRaisesRegex(ValueError,'numeric slot'):
            one_slot_literal_edit(self.a,changed)
    def test_stale_world_revision_bound(self):
        updated=copy.deepcopy(self.w)
        updated['revision']=1  # deliberately corrupt ledger
        with self.assertRaisesRegex(ValueError,'revision'):
            source_for_revision(self.v,updated)
    def test_precision_preserved_after_prior_revision(self):
        from bytebridge.ledger import propose, commit
        value=0.12345678912345678
        updated=commit(self.w,propose(self.w,'threshold',value,'precision survival'),0)
        literal=source_for_revision(self.v,updated)
        self.assertIn(b'  revision <- 1.',literal)
        self.assertIn(updated['head'].encode(),literal)
        # A new edit should preserve the pre-existing fine-grained threshold.
        candidate=literal.replace(b'  depth <- 1.2.',b'  depth <- 2.7.')
        self.assertEqual(one_slot_literal_edit(literal,candidate),('depth',1.2,2.7))
        tiny=commit(self.w,propose(self.w,'threshold',5e-324,'subnormal survival'),0)
        tiny_literal=source_for_revision(self.v,tiny)
        self.assertIn(b'  revision <- 1.',tiny_literal)
        self.assertEqual(one_slot_literal_edit(tiny_literal,
            tiny_literal.replace(b'  depth <- 1.2.',b'  depth <- 2.7.'))[0],'depth')
    def test_schema2_candidate_binding(self):
        data={'schema':SCHEMA2,'sourceSha256':self.w['artifactHash'],'representationPrint':self.v['print'],
              'baseRevision':0,'baseHead':self.w['head'],'slot':'depth','before':1.2,'value':2.7,
              'nonce':'1'*32,'observationMethod':METHOD,'baselineSourceSha256':digest(self.a),
              'objectSourceSha256':digest(self.b),'runtime':{'implementation':'russellallen/self',
              'commit':'unknown-unverified','worldImage':'unknown-unverified','objectOutlinerObserved':False}}
        receipt=sign_observation(data,self.w,self.v,KEY)
        proposal=import_observation(receipt,self.w,self.v,KEY,set(),self.b)
        self.assertEqual(proposal['slot'],'depth')
        self.assertEqual(self.w['mapping']['depth'],1.2)
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            import_observation(receipt,self.w,self.v,KEY,set(),self.b+b'\n')
        with self.assertRaisesRegex(ValueError,'required'):
            import_observation(receipt,self.w,self.v,KEY,set())
        fake=copy.deepcopy(receipt);fake['observationMethod']='NATIVE_PROVEN'
        with self.assertRaisesRegex(ValueError,'Invalid Self source evidence'):
            import_observation(fake,self.w,self.v,KEY,set(),self.b)

class FullCLIHandoff(unittest.TestCase):
    def run_cli(self,*args,expect=0):
        proc=subprocess.run([sys.executable,'-m','bytebridge.cli',*map(str,args)],capture_output=True,text=True,timeout=30)
        self.assertEqual(proc.returncode,expect, proc.stdout+'\n'+proc.stderr)
        result=proc.stdout if proc.returncode==0 else proc.stderr
        try:return json.loads(result)
        except json.JSONDecodeError:return {'error':result}
    def test_review_roundtrip_render_and_adversaries(self):
        with tempfile.TemporaryDirectory() as t:
            temp=Path(t);src=temp/'input.bin';original=b'\x00\xfffoo-one-time-byte-vessel'*38
            src.write_bytes(original)
            world=temp/'world';key=temp/'key';key.write_bytes(KEY)
            self.run_cli('ingest',src,'--out',world)
            before=self.run_cli('verify',world)
            self.assertEqual(before['spliceCount'],1000)
            self.run_cli('render',world)
            info=self.run_cli('self-export',world)
            baseline=Path(info['path']).read_bytes()
            self.assertEqual(info['status'],'EXPORTED_LITERAL_NOT_EXECUTED')
            self.run_cli('self-export',world,expect=2)
            candidate=temp/'edited.self';candidate.write_bytes(baseline.replace(b'  depth <- 1.2.',b'  depth <- 2.5.'))
            receipt=temp/'signed.json'
            staged=self.run_cli('self-stage',world,'--candidate',candidate,'--key-file',key,'--receipt-out',receipt)
            self.assertEqual(staged['slot'],'depth')
            signed=json.loads(receipt.read_text());self.assertEqual(signed['schema'],SCHEMA2)
            # Tampered candidate rejects without consuming nonce or changing the world.
            candidate.write_bytes(candidate.read_bytes()+b'"foreign object"')
            self.run_cli('self-import',world,'--receipt',receipt,'--key-file',key,'--candidate',candidate,expect=2)
            candidate.write_bytes(candidate.read_bytes().replace(b'"foreign object"',b''))
            self.run_cli('self-import',world,'--receipt',receipt,'--key-file',key,expect=2)
            imported=self.run_cli('self-import',world,'--receipt',receipt,'--key-file',key,'--candidate',candidate)
            self.assertEqual(imported['status'],'REVIEW_REQUIRED')
            self.assertEqual(self.run_cli('verify',world)['revision'],0)
            self.run_cli('self-import',world,'--receipt',receipt,'--key-file',key,'--candidate',candidate,expect=2)
            proposal=Path(imported['proposalPath'])
            self.run_cli('commit',world,'--proposal',proposal,'--expected-revision','0',expect=2)
            committed=self.run_cli('commit',world,'--proposal',proposal,'--expected-revision','0','--approve')
            self.assertEqual(committed['revision'],1)
            self.run_cli('self-import',world,'--receipt',receipt,'--key-file',key,'--candidate',candidate,expect=2)
            self.run_cli('commit',world,'--proposal',proposal,'--expected-revision','0','--approve',expect=2)
            new_render=self.run_cli('render',world)
            self.assertEqual(new_render['status'],'RENDERED')
            self.assertEqual(src.read_bytes(),original)
            self.assertEqual((world/'original.bin').read_bytes(),original)
            self.assertEqual(self.run_cli('verify',world)['spliceCount'],1000)
            first=world/'renders'/'rev00000'
            second=world/'renders'/'rev00001'
            self.assertNotEqual(digest((first/'byte_world.obj').read_bytes()),digest((second/'byte_world.obj').read_bytes()))
            self.assertEqual(digest((first/'byte_view.wav').read_bytes()),digest((second/'byte_view.wav').read_bytes()))
            # Following accepted revision yields a separate immutable literal.
            next_=self.run_cli('self-export',world)
            self.assertIn(b'  depth <- 2.5.',Path(next_['path']).read_bytes())
            self.assertEqual(self.run_cli('verify',world)['revision'],1)
    def test_modified_export_refused_at_stage(self):
        with tempfile.TemporaryDirectory() as t:
            temp=Path(t);src=temp/'input.bin';src.write_bytes(b'abc'*100)
            world=temp/'world';self.run_cli('ingest',src,'--out',world)
            path=Path(self.run_cli('self-export',world)['path']);original=path.read_bytes()
            candidate=temp/'edited.self';candidate.write_bytes(original.replace(b'  twist <- 2.',b'  twist <- 3.'))
            key=temp/'key';key.write_bytes(KEY)
            path.write_bytes(original+b'"forged"')
            result=self.run_cli('self-stage',world,'--candidate',candidate,'--key-file',key,'--receipt-out',temp/'r.json',expect=2)
            self.assertIn('baseline does not match',result['error'])
    def test_key_inside_source_and_candidate_inside_world_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            temp=Path(t);src=temp/'input.bin';src.write_bytes(b'abc'*50)
            world=temp/'world';self.run_cli('ingest',src,'--out',world)
            path=Path(self.run_cli('self-export',world)['path']);original=path.read_bytes()
            inside=world/'editable.self';inside.write_bytes(original.replace(b'  depth <- 1.2.',b'  depth <- 2.'))
            key=temp/'key';key.write_bytes(KEY)
            res=self.run_cli('self-stage',world,'--candidate',inside,'--key-file',key,'--receipt-out',temp/'r.json',expect=2)
            self.assertIn('cannot reside',res['error'])
            outside=temp/'edit.self';outside.write_bytes(inside.read_bytes())
            key2=world/'key';key2.write_bytes(KEY)
            res=self.run_cli('self-stage',world,'--candidate',outside,'--key-file',key2,'--receipt-out',temp/'r2.json',expect=2)
            self.assertIn('Signing key cannot reside',res['error'])

if __name__=='__main__':unittest.main()
