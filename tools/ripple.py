"""Stdlib-only, non-networked OX Ripple coordinator. Does NOT modify GitHub."""
import json, sys, hashlib, argparse, datetime, re, unicodedata
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'private' / 'registry.json'
PUB = ROOT / 'public'
RECEIPTS = ROOT / 'receipts' / 'BUILD_EVENTS.jsonl'
REQUIRED_RECEIPT = {'schema','event_id','capsule_id','source_ref','source_sha256','test_status','status','changed_paths','rollback','created_utc'}
VALID_STATUSES = {'candidate','blocked','tested','host-verified','user-accepted','release'}
VALID_TEST_STATUSES = {'PASS','FAIL','BLOCKED','NOT_RUN'}
RECEIPT_SCHEMA = 'ox.ripple.receipt/0.1'

def load():
 data = json.loads(PRIVATE.read_text(encoding='utf-8'))
 assert data['schema'] == 'ox.ripple.private-registry/0.1'
 caps = data['capsules']
 assert len({c['id'] for c in caps}) == len(caps)
 assert all(c['id'].startswith('C') and len(c['id'])==4 for c in caps)
 return caps

def sanitized(c):
 msg = ('physical-device acceptance absent' if c['id']=='C013' else
        'independent source/contract audit pending')
 return {'id': c['id'], 'state': 'UNVERIFIED', 'blocking_gate':msg,
         'review_entry': 'Offer a test/trace/failure reproduction, no claims of integration',
         'last_public_receipt': None}

def public_manifest():
 return {'schema':'ox.ripple.public-capsules/0.1', 'as_of':'2026-11-20',
 'disclaimer':'Alias IDs are not anonymization. These are observation placeholders, not audited runtime status.',
 'capsules':[sanitized(c) for c in load()]}

def make_public():
 PUB.mkdir(parents=True,exist_ok=True)
 (PUB/'capsules.json').write_text(json.dumps(public_manifest(),indent=2)+'\n',encoding='utf-8')
 (PUB/'README.md').write_text("""# OX RIPPLES / Capsule Board\n\nIndependent proof gaps, published under neutral aliases. **No source map, private code, or actual project identities here.**\n\nEvery entry is UNVERIFIED until linked to reproducible source/hash/test evidence by a collaborator.\n\nThis is a candidate collaboration board, not a production status dashboard. **Aliases do not hide GitHub repository ownership.**\n\nContribute: pick a capsule ID, propose one reproducible test, and report PASS/FAIL/BLOCKED with environment, version, input and expected outcome. Actual project mapping and source access must be provided privately by project owner.\n""",encoding='utf-8')
 return len(load())

def audit():
 caps=load();pub=public_manifest()
 raw=json.dumps(pub).lower()
 for c in caps:
  for key in ('source','owner','boundary'):
   s=c.get(key)
   if isinstance(s,str) and len(s)>5 and s.lower() not in ('not-reconciled','none','private','unknown','null'):
    assert s.lower() not in raw, 'private field leaked: '+c['id']+' '+key
 for p in ('CONTINUOUS_RIPPLE_AGENT.md','PROJECT_WORKER.md','INTEGRATOR.md','REVIEWER.md','RELEASE_GATE.md'):
  assert (ROOT/'prompts'/p).is_file()
 assert all(c['release']=='unverified' for c in caps), 'unreviewed release status'
 return len(caps)

def next_task():
 """Never route coordinator work to the separately scheduled VELA build."""
 caps=load()
 target=next((c for c in caps if c['id']=='C015' and c.get('owner')=='IXO'),None)
 if target is None:
  return {'capsule':None,'task':'Reconcile a non-VELA source checkpoint before choosing a code change.', 'release_gate':'BLOCKED', 'reason':'non-VELA source authority missing'}
 return {'capsule':target['id'],
         'task':'Verify FlowMesh M0.6 on physical ASUS with valid and malformed UTF-8 workspace sources; retain host gate until evidence is supplied.',
         'source_ref':'/OXsukra/FlowMesh/Candidates/IXO_FlowMesh_Atlas_M0_6_Candidate.zip',
         'source_sha256':'5ecec1be39a5999afe2563109f08cedade940649710aeb6a13cf7c1e7bc82dee',
         'release_gate':'BLOCKED', 'device_acceptance':'BASELINE_VERIFIED_PATCH_NOT_RUN'}

def valid_changed_paths(value):
 """Only relative, printable, non-traversing archive paths are admissible."""
 if not isinstance(value,list): return False
 if len(value) != len(set(x for x in value if isinstance(x,str))): return False
 for item in value:
  if not isinstance(item,str) or not item or item.startswith(('/', '\\')) or '\\' in item:
   return False
  if any(part in ('', '.', '..') for part in item.split('/')):
   return False
  if ':' in item or any(unicodedata.category(ch) in ('Cc','Cf','Cs','Co','Cn','Zl','Zp') for ch in item):
   return False
 return True

def valid_receipt_text(value):
 return isinstance(value,str) and bool(value.strip()) and all(unicodedata.category(ch) not in ("Cc","Cf","Cs","Co","Cn","Zl","Zp") for ch in value)

def valid_event_id(value):
 return (isinstance(value,str) and bool(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',value)))

def receipt(data):
 missing=REQUIRED_RECEIPT-set(data)
 if missing: raise ValueError('missing receipt fields: '+','.join(sorted(missing)))
 if data['schema'] != RECEIPT_SCHEMA:raise ValueError('invalid receipt schema')
 for field in ('source_ref','rollback'):
  if not valid_receipt_text(data[field]):raise ValueError('invalid '+field)
 if not isinstance(data['source_sha256'],str) or not re.fullmatch(r'[0-9a-fA-F]{64}',data['source_sha256']):raise ValueError('invalid source_sha256')
 if not isinstance(data['status'],str) or data['status'] not in VALID_STATUSES:raise ValueError('invalid status')
 if not isinstance(data['test_status'],str) or data['test_status'] not in VALID_TEST_STATUSES:raise ValueError('invalid test_status')
 if data['test_status']=='PASS':
  if not data.get('test_log_sha256'):raise ValueError('PASS requires test_log_sha256')
  if not isinstance(data['test_log_sha256'],str) or not re.fullmatch(r'[0-9a-fA-F]{64}',data['test_log_sha256']):raise ValueError('PASS requires valid SHA256 test_log_sha256')
 if data['status'] in {'host-verified','user-accepted','release'}:raise ValueError('promotion blocked: independent acceptance not implemented by this tool')
 if not isinstance(data['capsule_id'],str) or data['capsule_id'] not in {c['id'] for c in load()}: raise ValueError('unknown capsule')
 if not valid_changed_paths(data['changed_paths']):raise ValueError('changed_paths must be safe relative paths')
 if not valid_event_id(data['event_id']):raise ValueError('invalid event_id')
 # Fail closed on a damaged journal and prevent replaying an event under the same ID.
 if RECEIPTS.exists():
  seen_prior=set()
  for lineno,line in enumerate(RECEIPTS.read_text(encoding='utf-8').splitlines(),1):
   try: old=json.loads(line)
   except json.JSONDecodeError as e:raise ValueError(f'malformed prior receipt line {lineno}') from e
   if not isinstance(old,dict) or not valid_event_id(old.get('event_id')):raise ValueError(f'malformed prior receipt line {lineno}')
   if old['event_id'] in seen_prior:raise ValueError(f'duplicate prior event_id line {lineno}')
   seen_prior.add(old['event_id'])
   if old['event_id']==data['event_id']:raise ValueError('duplicate event_id')
 RECEIPTS.parent.mkdir(parents=True,exist_ok=True)
 with RECEIPTS.open('a',encoding='utf-8') as f:f.write(json.dumps(data,sort_keys=True)+'\n')

def journal_audit(path=None):
 """Read-only historical receipt audit; never rewrites append-only evidence."""
 path = Path(path) if path is not None else RECEIPTS
 issues=[]; seen=set(); count=0
 if not path.exists(): return {'records':0,'issues':[{'line':0,'reason':'journal missing'}]}
 for lineno,line in enumerate(path.read_text(encoding='utf-8').splitlines(),1):
  count+=1
  try: d=json.loads(line)
  except json.JSONDecodeError:
   issues.append({'line':lineno,'reason':'invalid JSON'});continue
  if not isinstance(d,dict):
   issues.append({'line':lineno,'reason':'not an object'});continue
  missing=REQUIRED_RECEIPT-set(d)
  if missing: issues.append({'line':lineno,'reason':'missing required fields: '+','.join(sorted(missing))})
  if d.get('schema') != RECEIPT_SCHEMA:issues.append({'line':lineno,'reason':'invalid receipt schema'})
  for field in ('source_ref','rollback'):
   if not valid_receipt_text(d.get(field)):issues.append({'line':lineno,'reason':'invalid '+field})
  if not isinstance(d.get('source_sha256'),str) or not re.fullmatch(r'[0-9a-fA-F]{64}',d['source_sha256']):issues.append({'line':lineno,'reason':'invalid source_sha256'})
  eid=d.get('event_id')
  if not valid_event_id(eid):issues.append({'line':lineno,'reason':'invalid event_id'})
  elif eid in seen:issues.append({'line':lineno,'reason':'duplicate event_id'})
  else:seen.add(eid)
  if not isinstance(d.get('capsule_id'),str) or d['capsule_id'] not in {c['id'] for c in load()}:issues.append({'line':lineno,'reason':'unknown capsule_id'})
  if not isinstance(d.get('changed_paths'),list):issues.append({'line':lineno,'reason':'changed_paths must be list'})
  elif not valid_changed_paths(d['changed_paths']):issues.append({'line':lineno,'reason':'changed_paths must be safe relative paths'})
  if not isinstance(d.get('status'),str) or d['status'] not in VALID_STATUSES:issues.append({'line':lineno,'reason':'invalid status: '+str(d.get('status'))})
  if isinstance(d.get('status'),str) and d['status'] in {'host-verified','user-accepted','release'}:issues.append({'line':lineno,'reason':'unsupported promotion without independent acceptance'})
  if not isinstance(d.get('test_status'),str) or d['test_status'] not in VALID_TEST_STATUSES:issues.append({'line':lineno,'reason':'invalid test_status: '+str(d.get('test_status'))})
  if d.get('test_status')=='PASS':
   digest=d.get('test_log_sha256')
   if not digest:issues.append({'line':lineno,'reason':'PASS missing test_log_sha256'})
   elif not isinstance(digest,str) or not re.fullmatch(r'[0-9a-fA-F]{64}',digest):issues.append({'line':lineno,'reason':'PASS invalid test_log_sha256'})
 return {'records':count,'issues':issues}

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['audit','next','make-public','append-receipt','audit-journal']);p.add_argument('--file');p.add_argument('--strict',action='store_true',help='Exit nonzero if journal audit detects any issue')
 a=p.parse_args();
 if a.command=='audit':print(json.dumps({'ok':True,'capsules':audit()}))
 elif a.command=='next':print(json.dumps(next_task(),indent=2))
 elif a.command=='audit-journal':
  report=journal_audit(a.file);print(json.dumps(report,indent=2))
  if a.strict and report['issues']:sys.exit(2)
 elif a.command=='make-public':print(json.dumps({'public_capsules':make_public()}))
 else:
  if not a.file:p.error('--file receipt.json required')
  receipt(json.loads(Path(a.file).read_text(encoding='utf-8')))
  print('receipt appended')
if __name__=='__main__':main()
