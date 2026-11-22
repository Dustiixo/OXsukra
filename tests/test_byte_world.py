import copy
import io
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from bytebridge.core import analyze_bytes, reconstruct_patches, verify_vessel, render_self_literal, MAX_INPUT
from bytebridge.ledger import initial_world, propose, commit, verify
from bytebridge.projections import obj_projection, sonify
from bytebridge.cli import initialize, verify_directory

ROOT=Path(__file__).resolve().parents[1]
SAMPLE=bytes((i*29+(i>>4)*17)%256 for i in range(5112))


class ByteWorldTests(unittest.TestCase):
    def test_basic(self):
        v=analyze_bytes(SAMPLE,'test.bin')
        self.assertEqual(len(v['splices']),1000)
        self.assertEqual(v['splices'][999]['end'],len(SAMPLE))
        self.assertTrue(verify_vessel(SAMPLE,v))

    def test_empty_input(self):
        v=analyze_bytes(b'')
        self.assertEqual(v['patches'],[])
        self.assertTrue(all(x['length']==0 for x in v['splices']))
        self.assertTrue(verify_vessel(b'',v))

    def test_tiny_input_has_empty_splices(self):
        v=analyze_bytes(b'\x00\xff')
        self.assertEqual(sum(x['length'] for x in v['splices']),2)
        self.assertTrue(verify_vessel(b'\x00\xff',v))

    def test_byte_boundaries(self):
        v=analyze_bytes(bytes(range(256)))
        self.assertEqual(reconstruct_patches(bytes(range(256)),v['patches']),bytes(range(256)))

    def test_high_entropy_is_more_patches(self):
        low=analyze_bytes(b'\x00'*8192)
        mixed=analyze_bytes(bytes(range(256))*32)
        self.assertGreater(len(mixed['patches']),len(low['patches']))

    def test_identity_independent_of_name(self):
        a=analyze_bytes(SAMPLE,'x.txt');b=analyze_bytes(SAMPLE,'x.mp3')
        self.assertEqual(a['print'],b['print']);self.assertEqual(a['input']['sha256'],b['input']['sha256'])

    def test_repeated_is_deterministic(self):
        self.assertEqual(analyze_bytes(SAMPLE,'x'),analyze_bytes(SAMPLE,'x'))

    def test_oversized_rejected(self):
        with self.assertRaises(ValueError):analyze_bytes(b'\x00'*(MAX_INPUT+1))

    def test_only_bytes(self):
        with self.assertRaises(TypeError):analyze_bytes('hello')

    def test_patch_mutation_rejected(self):
        v=analyze_bytes(SAMPLE);v['patches'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):verify_vessel(SAMPLE,v)

    def test_patch_gap_rejected(self):
        v=analyze_bytes(SAMPLE);v['patches'][1]['start']+=1
        with self.assertRaises(ValueError):verify_vessel(SAMPLE,v)

    def test_source_mutation_rejected(self):
        v=analyze_bytes(SAMPLE)
        with self.assertRaises(ValueError):verify_vessel(SAMPLE+b'x',v)

    def test_splice_mutation_rejected(self):
        v=analyze_bytes(SAMPLE);v['splices'][23]['entropyMilli']+=1
        with self.assertRaises(ValueError):verify_vessel(SAMPLE,v)

    def test_all_addresses_unique(self):
        v=analyze_bytes(SAMPLE)
        keys={(s['gateRow'],s['gateColumn'],s['subsplice']) for s in v['splices']}
        self.assertEqual(len(keys),1000)

    def test_native_source_no_raw_user_text(self):
        v=analyze_bytes(SAMPLE,"unsafe. _RunScript: '/tmp/evil.self'")
        source=render_self_literal(v)
        self.assertIn('parent* = traits clonable.',source)
        self.assertIn('originDigest',source)
        self.assertNotIn('evil',source)
        self.assertEqual(source.count('startByte ='),min(len(v['patches']),40))

    def test_self_export_limit(self):
        v=analyze_bytes(SAMPLE)
        with self.assertRaises(ValueError):render_self_literal(v,300)

    def test_ledger_happy_path(self):
        h=analyze_bytes(SAMPLE)['input']['sha256'];w=initial_world(h)
        p=propose(w,'twist',3.5,'change mapping to inspect spiral curvature')
        w2=commit(w,p,0)
        self.assertTrue(verify(w2,h));self.assertEqual(w2['revision'],1)
        self.assertEqual(w2['mapping']['twist'],3.5)
        self.assertEqual(w['revision'],0)

    def test_ledger_stale_revision_rejected(self):
        h=analyze_bytes(SAMPLE)['input']['sha256'];w=initial_world(h)
        p=propose(w,'hue',45,'inspect hue projection')
        w=commit(w,p,0)
        with self.assertRaises(ValueError):commit(w,p,1)

    def test_ledger_no_unknown_slots_or_nan(self):
        w=initial_world(analyze_bytes(SAMPLE)['input']['sha256'])
        for key,value in [('evil',1),('depth',float('nan')),('depth',4),('depth',float('inf'))]:
            with self.assertRaises(ValueError):propose(w,key,value,'test attempted mutation')

    def test_ledger_event_tamper_rejected(self):
        h=analyze_bytes(SAMPLE)['input']['sha256'];w=initial_world(h)
        w=commit(w,propose(w,'hue',20,'color-only view change'),0)
        w['events'][0]['event']['value']=-160
        with self.assertRaises(ValueError):verify(w,h)

    def test_obj_and_audio(self):
        v=analyze_bytes(SAMPLE);w=initial_world(v['input']['sha256'])
        o=obj_projection(v,w['mapping']);wav=sonify(v)
        self.assertEqual(o.count(b'\nv '),1000)
        self.assertEqual(o.count(b'\nl '),999)
        with wave.open(io.BytesIO(wav),'rb') as f:
            self.assertEqual((f.getnchannels(),f.getsampwidth(),f.getframerate(),f.getnframes()),(1,2,16000,160000))

    def test_projection_changes_not_original(self):
        v=analyze_bytes(SAMPLE);w=initial_world(v['input']['sha256'])
        a=obj_projection(v,w['mapping']);new=commit(w,propose(w,'twist',5.5,'make twist more exaggerated'),0)
        b=obj_projection(v,new['mapping']);self.assertNotEqual(a,b)
        self.assertTrue(verify_vessel(SAMPLE,v))

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'input.mp3';raw.write_bytes(SAMPLE)
            target=root/'world';initialize(raw,target)
            v=verify_directory(target)
            self.assertEqual(v['status'],'VERIFIED_LOCAL_ONLY')
            self.assertEqual((target/'original.bin').read_bytes(),SAMPLE)
            self.assertTrue((target/'native_self_object.self').exists())

    def test_cli_rejects_corrupt_native_candidate(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'input';raw.write_bytes(SAMPLE)
            target=root/'world';initialize(raw,target)
            (target/'native_self_object.self').write_text('corrupt')
            with self.assertRaises(ValueError):verify_directory(target)

    def test_cli_proposal_requires_explicit_approval(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'input';raw.write_bytes(SAMPLE)
            target=root/'world';initialize(raw,target)
            cmd=[sys.executable,'-m','bytebridge.cli','propose',str(target),'--slot','hue','--value','33','--reason','test inspected hue']
            r=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(r.returncode,0,r.stderr)
            p=Path(json.loads(r.stdout)['proposalPath'])
            args=[sys.executable,'-m','bytebridge.cli','commit',str(target),'--proposal',str(p),'--expected-revision','0']
            self.assertNotEqual(subprocess.run(args,cwd=ROOT,capture_output=True).returncode,0)
            self.assertEqual(subprocess.run(args+['--approve'],cwd=ROOT,capture_output=True).returncode,0)
            self.assertEqual(verify_directory(target)['revision'],1)

    def test_revision_render(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);raw=root/'input';raw.write_bytes(SAMPLE)
            target=root/'world';initialize(raw,target)
            r=subprocess.run([sys.executable,'-m','bytebridge.cli','render',str(target)],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertTrue((target/'renders'/'rev00000'/'receipt.json').exists())
            self.assertNotEqual(subprocess.run([sys.executable,'-m','bytebridge.cli','render',str(target)],cwd=ROOT,capture_output=True).returncode,0)

if __name__=='__main__':unittest.main()
