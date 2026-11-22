import importlib.util, json, unittest, tempfile, subprocess, sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ripple',P/'tools'/'ripple.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
class TestRipple(unittest.TestCase):
 def test_unhashable_receipt_enums_fail_closed(self):
  with tempfile.TemporaryDirectory() as t:
   original=r.RECEIPTS;r.RECEIPTS=Path(t)/'events.jsonl'
   base={'schema':r.RECEIPT_SCHEMA,'event_id':'unhashable-test','capsule_id':'C015','source_ref':'immutable','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    for field in ('status','test_status','capsule_id'):
     for value in ([],{},None):
      d=dict(base);d[field]=value
      with self.assertRaisesRegex(ValueError,'invalid status|invalid test_status|unknown capsule'):r.receipt(d)
      self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=original
 def test_unhashable_historical_enums_audit_readonly(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'bad.jsonl'
   d={'schema':r.RECEIPT_SCHEMA,'event_id':'bad-enums','capsule_id':[],'source_ref':'immutable','source_sha256':'0'*64,'test_status':{},'status':[],'changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   reasons=[x['reason'] for x in r.journal_audit(path)['issues']]
   self.assertTrue(any('unknown capsule_id' in x for x in reasons))
   self.assertTrue(any('invalid status' in x for x in reasons))
   self.assertTrue(any('invalid test_status' in x for x in reasons))
   self.assertEqual(before,path.read_bytes())

 def test_reject_invalid_source_hash_without_write(self):
  with tempfile.TemporaryDirectory() as t:
   old=r.RECEIPTS;r.RECEIPTS=Path(t)/'j.jsonl'
   d={'schema':r.RECEIPT_SCHEMA,'event_id':'bad-source','capsule_id':'C015','source_ref':'immutable','source_sha256':'not-a-hash','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'invalid source_sha256'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=old
 def test_audit_invalid_source_hash_without_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'j.jsonl'
   d={'schema':r.RECEIPT_SCHEMA,'event_id':'bad-source','capsule_id':'C015','source_ref':'immutable','source_sha256':'not-a-hash','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   result=r.journal_audit(path)
   self.assertIn('invalid source_sha256',[i['reason'] for i in result['issues']])
   self.assertEqual(before,path.read_bytes())
 def test_registry_aliases_unique(self):
  cs=r.load();self.assertEqual(len(cs),len({x['id'] for x in cs}));self.assertGreaterEqual(len(cs),20)
 def test_public_no_private_names(self):self.assertGreaterEqual(r.audit(),20)
 def test_public_export_is_deterministic(self):
  a=r.public_manifest();b=r.public_manifest();self.assertEqual(a,b)
 def test_public_contains_only_alias_fields(self):
  for c in r.public_manifest()['capsules']:
   self.assertEqual(set(c),{'id','state','blocking_gate','review_entry','last_public_receipt'})
 def test_published_local_export_excludes_private_sources(self):
  public=(P/'public'/'capsules.json').read_text().lower()+' '+(P/'public'/'README.md').read_text().lower()
  for c in r.load():
   for v in (c.get('source'),c.get('owner')):
    if isinstance(v,str) and len(v)>7 and v not in ('not-reconciled',):self.assertNotIn(v.lower(),public)
 def test_task_is_blocked_until_device(self):self.assertEqual(r.next_task()['release_gate'],'BLOCKED')
 def test_next_task_does_not_overlap_vela(self):
  task=r.next_task()
  self.assertEqual(task['capsule'],'C015')
  self.assertIn('FlowMesh M0.6',task['task'])
  self.assertTrue(task['source_ref'].endswith('IXO_FlowMesh_Atlas_M0_6_Candidate.zip'))
  self.assertEqual(task['source_sha256'],'5ecec1be39a5999afe2563109f08cedade940649710aeb6a13cf7c1e7bc82dee')
  self.assertNotIn('VELA',task['task'])
  self.assertEqual(task['device_acceptance'],'BASELINE_VERIFIED_PATCH_NOT_RUN')
 def test_next_task_fails_closed_if_ixo_source_mapping_missing(self):
  orig=r.load
  try:
   r.load=lambda:[c for c in orig() if c['id']!='C015']
   task=r.next_task()
   self.assertIsNone(task['capsule'])
   self.assertEqual(task['release_gate'],'BLOCKED')
  finally:r.load=orig
 def test_cannot_falsely_pass_test(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'r.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'one','capsule_id':'C013','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'PASS','status':'tested','changed_paths':[],'rollback':'none','created_utc':'2026-11-20T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'test_log_sha256'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=orig
 def test_no_release_self_approval(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'r.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'one','capsule_id':'C013','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'release','changed_paths':[],'rollback':'none','created_utc':'2026-11-20T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'promotion blocked'):r.receipt(d)
   finally:r.RECEIPTS=orig
 def test_reject_duplicate_event_id_without_mutating_journal(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'r.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'same','capsule_id':'C013','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-20T00:00:00Z'}
   try:
    r.receipt(d);before=r.RECEIPTS.read_bytes()
    with self.assertRaisesRegex(ValueError,'duplicate event_id'):r.receipt(d)
    self.assertEqual(before,r.RECEIPTS.read_bytes())
   finally:r.RECEIPTS=orig
 def test_reject_corrupted_prior_journal(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'r.jsonl';r.RECEIPTS.write_text('{bad\n')
   d={'schema':'ox.ripple.receipt/0.1','event_id':'new','capsule_id':'C013','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-20T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'malformed prior receipt'):r.receipt(d)
    self.assertEqual(r.RECEIPTS.read_text(),'{bad\n')
   finally:r.RECEIPTS=orig
 def test_historical_journal_audit_flags_invalid_pass_and_status_without_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'journal.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'historical','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'PASS','status':'tested-patch-candidate','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n',encoding='utf-8');before=path.read_bytes()
   result=r.journal_audit(path)
   self.assertEqual(result['records'],1)
   self.assertEqual({x['reason'] for x in result['issues']},{'invalid status: tested-patch-candidate','PASS missing test_log_sha256'})
   self.assertEqual(before,path.read_bytes())
 def test_historical_journal_audit_detects_duplicate_and_invalid_json(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'journal.jsonl';d={'schema':'ox.ripple.receipt/0.1','event_id':'repeat','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n'+json.dumps(d)+'\n{bad\n')
   reasons=[x['reason'] for x in r.journal_audit(path)['issues']]
   self.assertIn('duplicate event_id',reasons);self.assertIn('invalid JSON',reasons)
 def test_strict_audit_exits_nonzero_for_historical_defects(self):
  proc=subprocess.run([sys.executable,str(P/'tools'/'ripple.py'),'audit-journal','--strict'],capture_output=True,text=True)
  self.assertEqual(proc.returncode,2)
  self.assertGreaterEqual(len(json.loads(proc.stdout)['issues']),2)
 def test_nonstrict_audit_retains_readonly_compatibility(self):
  journal=P/'receipts'/'BUILD_EVENTS.jsonl'; before=journal.read_bytes()
  proc=subprocess.run([sys.executable,str(P/'tools'/'ripple.py'),'audit-journal'],capture_output=True,text=True)
  self.assertEqual(proc.returncode,0)
  self.assertEqual(journal.read_bytes(),before)
 def test_cli_audit_journal_file_selects_independent_fixture(self):
  with tempfile.TemporaryDirectory() as t:
   fixture=Path(t)/'separate.jsonl'
   fixture.write_text('{bad\n',encoding='utf-8')
   cmd=[sys.executable,str(P/'tools'/'ripple.py'),'audit-journal','--file',str(fixture),'--strict']
   proc=subprocess.run(cmd,capture_output=True,text=True)
   self.assertEqual(proc.returncode,2,proc.stderr)
   report=json.loads(proc.stdout)
   self.assertEqual(report['records'],1)
   self.assertEqual(report['issues'],[{'line':1,'reason':'invalid JSON'}])
   self.assertEqual(fixture.read_text(encoding='utf-8'),'{bad\n')
 def test_cli_audit_journal_file_clean_fixture_does_not_inherit_historical_errors(self):
  with tempfile.TemporaryDirectory() as t:
   fixture=Path(t)/'clean.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'clean','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   fixture.write_text(json.dumps(d)+'\n',encoding='utf-8')
   proc=subprocess.run([sys.executable,str(P/'tools'/'ripple.py'),'audit-journal','--file',str(fixture),'--strict'],capture_output=True,text=True)
   self.assertEqual(proc.returncode,0,proc.stderr)
   self.assertEqual(json.loads(proc.stdout),{'records':1,'issues':[]})
 def test_reject_unknown_test_status_without_writing(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'bad-status','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'PASSED_UNCHECKED','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'invalid test_status'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=orig
 def test_strict_audit_flags_unknown_test_status_in_separate_journal(self):
  with tempfile.TemporaryDirectory() as t:
   fixture=Path(t)/'unknown.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'unknown','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'SUCCESSISH','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   fixture.write_text(json.dumps(d)+'\n',encoding='utf-8');before=fixture.read_bytes()
   proc=subprocess.run([sys.executable,str(P/'tools'/'ripple.py'),'audit-journal','--file',str(fixture),'--strict'],capture_output=True,text=True)
   self.assertEqual(proc.returncode,2,proc.stderr)
   self.assertIn({'line':1,'reason':'invalid test_status: SUCCESSISH'},json.loads(proc.stdout)['issues'])
   self.assertEqual(fixture.read_bytes(),before)
 def test_reject_fake_pass_digest_without_writing(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'bad-digest','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'PASS','test_log_sha256':'not-a-sha','status':'tested','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'valid SHA256'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=orig
 def test_audit_flags_fake_pass_digest_without_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'journal.jsonl';d={'schema':'ox.ripple.receipt/0.1','event_id':'fake','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'PASS','test_log_sha256':'x','status':'tested','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   p.write_text(json.dumps(d)+'\n');before=p.read_bytes()
   self.assertIn({'line':1,'reason':'PASS invalid test_log_sha256'},r.journal_audit(p)['issues'])
   self.assertEqual(before,p.read_bytes())
 def test_reject_preexisting_duplicate_ids_without_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'prior','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   r.RECEIPTS.write_text(json.dumps(d)+'\n'+json.dumps(d)+'\n',encoding='utf-8');before=r.RECEIPTS.read_bytes()
   try:
    d['event_id']='new'
    with self.assertRaisesRegex(ValueError,'duplicate prior event_id'):r.receipt(d)
    self.assertEqual(before,r.RECEIPTS.read_bytes())
   finally:r.RECEIPTS=orig
 def test_reject_blank_historical_event_id_without_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'  ','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   r.RECEIPTS.write_text(json.dumps(d)+'\n',encoding='utf-8');before=r.RECEIPTS.read_bytes()
   try:
    d['event_id']='new'
    with self.assertRaisesRegex(ValueError,'malformed prior receipt'):r.receipt(d)
    self.assertEqual(before,r.RECEIPTS.read_bytes())
   finally:r.RECEIPTS=orig
 def test_audit_flags_unknown_capsule_without_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'unknown.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'unknown-capsule','capsule_id':'C999','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn({'line':1,'reason':'unknown capsule_id'},r.journal_audit(path)['issues'])
   self.assertEqual(before,path.read_bytes())
 def test_audit_flags_bad_changed_paths_without_mutation(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'badpaths.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'bad-paths','capsule_id':'C015','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':'pretend.py','rollback':'none','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn({'line':1,'reason':'changed_paths must be list'},r.journal_audit(path)['issues'])
   self.assertEqual(before,path.read_bytes())
 def test_append_only(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'r.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'one','capsule_id':'C013','source_ref':'x','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'none','created_utc':'2026-11-20T00:00:00Z'}
   try:
    r.receipt(d);d['event_id']='two';r.receipt(d)
    self.assertEqual(len(r.RECEIPTS.read_text().splitlines()),2)
   finally:r.RECEIPTS=orig
 def test_receipt_rejects_traversal_paths_without_writing(self):
  with tempfile.TemporaryDirectory() as t:
   orig=r.RECEIPTS;r.RECEIPTS=Path(t)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'unsafe','capsule_id':'C015','source_ref':'immutable','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':['../private/registry.json'],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'safe relative paths'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=orig
 def test_journal_audit_detects_unsafe_paths_readonly(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'unsafe','capsule_id':'C015','source_ref':'immutable','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':['safe/file.py','../../secret'], 'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn('changed_paths must be safe relative paths',[x['reason'] for x in r.journal_audit(path)['issues']])
   self.assertEqual(path.read_bytes(),before)

 def test_reject_wrong_receipt_schema_without_writing(self):
  with tempfile.TemporaryDirectory() as t:
   old=r.RECEIPTS;r.RECEIPTS=Path(t)/'events.jsonl'
   d={'schema':'foreign.receipt/0.1','event_id':'wrong-schema','capsule_id':'C015','source_ref':'immutable','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'invalid receipt schema'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=old
 def test_audit_wrong_schema_read_only(self):
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'events.jsonl'
   d={'schema':'foreign.receipt/0.1','event_id':'wrong-schema','capsule_id':'C015','source_ref':'immutable','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn({'line':1,'reason':'invalid receipt schema'},r.journal_audit(path)['issues'])
   self.assertEqual(path.read_bytes(),before)

 def test_duplicate_changed_paths_rejected_without_append(self):
  with tempfile.TemporaryDirectory() as temp:
   old=r.RECEIPTS;r.RECEIPTS=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'duplicate-path','capsule_id':'C015','source_ref':'immutable','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':['src/a.py','src/a.py'],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'safe relative paths'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=old
 def test_duplicate_changed_paths_audit_readonly(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'duplicate-path','capsule_id':'C015','source_ref':'immutable','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'blocked','changed_paths':['src/a.py','src/a.py'],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn('changed_paths must be safe relative paths',[x['reason'] for x in r.journal_audit(path)['issues']])
   self.assertEqual(path.read_bytes(),before)

 def test_audit_rejects_unverified_promotion_readonly(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'forged-host','capsule_id':'C015','source_ref':'immutable','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'host-verified','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn('unsupported promotion without independent acceptance',[x['reason'] for x in r.journal_audit(path)['issues']])
   self.assertEqual(before,path.read_bytes())
 def test_audit_does_not_flag_candidate_as_promotion(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'candidate-only','capsule_id':'C015','source_ref':'immutable','source_sha256':'0000000000000000000000000000000000000000000000000000000000000000','test_status':'NOT_RUN','status':'candidate','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n')
   self.assertEqual([],r.journal_audit(path)['issues'])

 def test_reject_bidi_path_without_append(self):
  with tempfile.TemporaryDirectory() as temp:
   old=r.RECEIPTS;r.RECEIPTS=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'bidi-path','capsule_id':'C015','source_ref':'immutable','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':['src/\u202eevil.py'],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'safe relative paths'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=old
 def test_audit_flags_bidi_path_readonly(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'bidi-path','capsule_id':'C015','source_ref':'immutable','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':['src/\u202eevil.py'],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn('changed_paths must be safe relative paths',[x['reason'] for x in r.journal_audit(path)['issues']])
   self.assertEqual(before,path.read_bytes())

 def test_reject_invisible_event_id_without_append(self):
  with tempfile.TemporaryDirectory() as temp:
   old=r.RECEIPTS;r.RECEIPTS=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'safe\u202eforged','capsule_id':'C015','source_ref':'immutable','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'invalid event_id'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=old
 def test_audit_invisible_event_id_readonly(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'safe\u202eforged','capsule_id':'C015','source_ref':'immutable','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn('invalid event_id',[x['reason'] for x in r.journal_audit(path)['issues']])
   self.assertEqual(before,path.read_bytes())


 def test_unsafe_event_id_rejected_without_append(self):
  with tempfile.TemporaryDirectory() as temp:
   old=r.RECEIPTS;r.RECEIPTS=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'unsafe/id','capsule_id':'C015','source_ref':'immutable','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'invalid event_id'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=old
 def test_unsafe_event_id_audit_readonly(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'unsafe/id','capsule_id':'C015','source_ref':'immutable','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n'); before=path.read_bytes()
   self.assertIn('invalid event_id',[x['reason'] for x in r.journal_audit(path)['issues']])
   self.assertEqual(before,path.read_bytes())

 def test_reject_empty_source_ref_without_append(self):
  with tempfile.TemporaryDirectory() as temp:
   old=r.RECEIPTS;r.RECEIPTS=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'missing-source','capsule_id':'C015','source_ref':'  ','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore','created_utc':'2026-11-21T00:00:00Z'}
   try:
    with self.assertRaisesRegex(ValueError,'invalid source_ref'):r.receipt(d)
    self.assertFalse(r.RECEIPTS.exists())
   finally:r.RECEIPTS=old
 def test_audit_flags_invisible_rollback_readonly(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'events.jsonl'
   d={'schema':'ox.ripple.receipt/0.1','event_id':'bad-rollback','capsule_id':'C015','source_ref':'immutable','source_sha256':'0'*64,'test_status':'NOT_RUN','status':'blocked','changed_paths':[],'rollback':'restore\u202e','created_utc':'2026-11-21T00:00:00Z'}
   path.write_text(json.dumps(d)+'\n');before=path.read_bytes()
   self.assertIn('invalid rollback',[x['reason'] for x in r.journal_audit(path)['issues']])
   self.assertEqual(before,path.read_bytes())

 def test_next_reflects_confirmed_asus_reproduction(self):
  task=r.next_task()
  self.assertIn('Verify FlowMesh M0.6 on physical ASUS',task['task'])
  self.assertEqual('BASELINE_VERIFIED_PATCH_NOT_RUN',task['device_acceptance'])
  self.assertEqual('BLOCKED',task['release_gate'])

if __name__=='__main__':unittest.main()
