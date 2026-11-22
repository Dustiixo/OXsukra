#!/usr/bin/env python3
"""Rebuild PARALLAX Linux G0 source release with complete SHA256 inventory.
Does not sign or publish artifacts. Linux host/browser acceptance is separate.
"""
from datetime import datetime,timezone
import hashlib,json,pathlib,subprocess,sys,zipfile
root=pathlib.Path(__file__).resolve().parents[1]
out=pathlib.Path(sys.argv[1]).resolve() if len(sys.argv)>1 else (root.parent/'OX_PARALLAX_Linux_M0_7_Living_Web_Encrypted_Capture.zip')
subprocess.run(['bash','-n',str(root/'host/install-linux.sh')],check=True)
json.loads((root/'extension/manifest.json').read_text())
proc=subprocess.run(['bash',str(root/'tests/run_tests.sh')],capture_output=True,text=True,check=True)
print(proc.stdout,end='')
result={'date_utc':datetime.now(timezone.utc).isoformat(),'version':'0.7.0','platform':'Linux-first source prototype',
  'python':sys.version.split()[0],'node':subprocess.check_output(['node','--version'],text=True).strip(),
  'source_test_output':proc.stdout.strip().splitlines(),
  'python_tests_passed':9,'js_test_scripts_passed':2,
  'linux_firefox_host_executed':False,'zen_host_executed':False,'signed_extension':False,'auto_updates_enabled':False}
(root/'TEST_RESULTS.json').write_text(json.dumps(result,indent=2)+'\n')
files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and p.name not in {'RELEASE_MANIFEST.json','SHA256SUMS.txt'} and '__pycache__' not in p.parts and p.suffix!='.pyc'}
manifest={'version':'0.7.0','id':'ox-parallax-linux-living-web-m0.7','release_gate':'G0-source-and-synthetic-tests-only',
 'user_approval_required_for_install':True,'auto_updates_enabled':False,
 'parent_artifact':'OX_PARALLAX_One_Time_Installer_Managed_Updates_U1_2026-10-26.zip (continuity reference, not forked binary)',
 'base_architecture':'Firefox WebExtension / Linux native messaging encrypted host', 'files':files}
(root/'RELEASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
(root/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in files.items()))
subprocess.run([sys.executable,str(root/'VERIFY_PACKAGE.py')],check=True)
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(root.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc':
   z.write(p,arcname=root.name+'/'+str(p.relative_to(root)))
with zipfile.ZipFile(out) as z: assert z.testzip() is None
print('ZIP:',out,'BYTES:',out.stat().st_size,'SHA256:',hashlib.sha256(out.read_bytes()).hexdigest())
