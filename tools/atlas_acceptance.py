"""Disposable M0.6 UTF-8 acceptance probe; no existing workspace is touched."""
import argparse, hashlib, json, os, pathlib, platform, subprocess, sys, tempfile, zipfile
EXPECTED='5ecec1be39a5999afe2563109f08cedade940649710aeb6a13cf7c1e7bc82dee'
def main():
    p=argparse.ArgumentParser(); p.add_argument('archive',type=pathlib.Path); a=p.parse_args()
    digest=hashlib.sha256(a.archive.read_bytes()).hexdigest()
    if digest!=EXPECTED: raise SystemExit('Archive SHA256 mismatch; stopped before extraction')
    env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
    print(json.dumps({'archive_sha256':digest,'platform':platform.platform(),'python':sys.version,'physical_device_acceptance':'NOT_ESTABLISHED_BY_SCRIPT'}))
    with tempfile.TemporaryDirectory(prefix='atlas-accept-') as tmp:
        base=pathlib.Path(tmp); zipfile.ZipFile(a.archive).extractall(base)
        src=base/'IXO_FlowMesh_Atlas_M0_6_Candidate'; root=base/'session'
        def run(args, code=0, needle=None):
            r=subprocess.run([sys.executable,*map(str,args)],cwd=src,env=env,capture_output=True,encoding='utf-8',errors='strict')
            print(json.dumps({'args':list(map(str,args)),'exit':r.returncode,'stdout':r.stdout,'stderr':r.stderr},ensure_ascii=True))
            if r.returncode!=code or (needle and needle not in r.stderr) or 'Traceback' in r.stderr: raise RuntimeError('Unexpected command outcome')
            return r.stdout
        def cli(cmd,*args,**kw): return run(['-m','flowmesh',cmd,'--root',root,*args],**kw)
        def snapshot(): return {str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob('*') if f.is_file()}
        run(['VERIFY_PACKAGE.py']); cli('init','--goal','agent probe research')
        good=base/'good.md'; good.write_bytes('agent probe research: café 音楽 🎼'.encode('utf-8'))
        cli('add-source','--file',good); assert any(f.read_bytes()==good.read_bytes() for f in (root/'sources').iterdir())
        bad=base/'bad.md'; bad.write_bytes(b'\xff\xfe\x80'); before=snapshot()
        cli('add-source','--file',bad,code=2,needle='Source is not valid UTF-8'); assert snapshot()==before
        damaged=root/'sources'/'damaged.md'; damaged.write_bytes(b'\xff\xfe')
        cli('step',code=2,needle='Workspace source damaged.md is not valid UTF-8')
        damaged.unlink(); cli('step'); assert json.loads(cli('verify'))['integrity']=='PASS'
        print('PASS: disposable UTF-8 acceptance procedure; physical identity and user acceptance require independent evidence')
if __name__=='__main__': main()
