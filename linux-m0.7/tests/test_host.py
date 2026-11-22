import importlib.util
import io
import json
import os
from pathlib import Path
import secrets
import struct
import subprocess
import sys
import time
import uuid

import pytest

HOST=Path(__file__).resolve().parents[1]/"host"/"parallax_host.py"
spec=importlib.util.spec_from_file_location("parallax_host",HOST)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

@pytest.fixture
def instance(tmp_path):return m.Host(tmp_path/"vault")

def begin(host,site="https://demo.example.org/"):
    session=str(uuid.uuid4());password="correct horse battery staple"
    out=host.handle({"command":"create","sessionId":session,"passphrase":password,"site":site})
    assert out["encrypted"] is True
    return session,password

def event(t="request",to="https://cdn.example.net/script.js?apikey=SECRET"):
    return {"type":t,"from":"https://demo.example.org/home?access_token=SECRET","to":to,"at":1780000000000,"kind":"script","status":200}

def test_archive_encrypt_redact_and_reopen(instance):
    sid,pw=begin(instance)
    saved=instance.handle({"command":"append","events":[event(),event("response","https://images.example.net/picture.png#secret")]})
    assert saved=={"saved":2,"rejected":0}
    raw=instance.path(sid).read_bytes()
    for clear in (b"script.js",b"demo.example",b"SECRET",b"correct horse",b"request"):
        assert clear not in raw
    out=instance.handle({"command":"read","sessionId":sid,"passphrase":pw})
    assert out["total"]==2
    assert out["events"][0]["to"]=="https://cdn.example.net/script.js"
    assert out["events"][0]["from"]=="https://demo.example.org/home"
    assert instance.path(sid).stat().st_mode & 0o777 == 0o600

def test_cookie_values_never_saved(instance):
    sid,pw=begin(instance)
    raw={"type":"cookie_meta","from":"https://demo.example.org/","name":"pref", "cookieDomain":".demo.example.org","httpOnly":True,"secure":True,"session":False,"value":"COOKIE_SECRET", "at":1780000000000}
    instance.handle({"command":"append","events":[raw]})
    out=instance.handle({"command":"read","sessionId":sid,"passphrase":pw})
    assert "value" not in out["events"][0]
    assert "COOKIE_SECRET" not in str(out)

def test_bad_passphrase_denied(instance):
    sid,pw=begin(instance)
    with pytest.raises(m.BadRequest):instance.handle({"command":"read","sessionId":sid,"passphrase":"incorrect-passphrase-123"})

def test_reject_cross_origin_and_private_paths(instance):
    sid,pw=begin(instance)
    bad=[event(to="file:///etc/passwd"),event(to="https://demo.example.org/checkout"),{"type":"request","from":"https://different.example/","to":"https://cdn.example.net/"},event(to="http://127.0.0.1/private")]
    response=instance.handle({"command":"append","events":bad})
    assert response["saved"]==0 and response["rejected"]==4

def test_truncated_frame_tail_read_and_recover(instance):
    sid,pw=begin(instance)
    instance.handle({"command":"append","events":[event()]})
    p=instance.path(sid)
    with p.open("ab") as f:f.write(struct.pack("<I",120));f.write(b"partial")
    with p.open("rb") as f:header=f.read(m.HEADER_SIZE)
    key=m.derive(pw,header[len(m.MAGIC):])
    with pytest.raises(m.BadRequest):m.frames(p,key)
    assert len(m.frames(p,key,repair=True))==2
    assert len(m.frames(p,key))==2

def test_approved_ai_only_explicit_endpoint_and_rejects_bad_node(instance,monkeypatch):
    with pytest.raises(m.BadRequest):instance.handle({"command":"local-summary","model":"qwen:3b","node":{"id":"file:///etc/passwd","type":"page","hits":1}})
    called=[]
    class FakeResp:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,n):return json.dumps({"response":"Observed a request count."}).encode()
    class FakeOpener:
        def open(self,request,timeout=0):
            called.append((request.full_url,timeout,request.data))
            return FakeResp()
    monkeypatch.setattr(m.urllib.request,"build_opener",lambda *args:FakeOpener())
    out=instance.handle({"command":"local-summary","model":"qwen2.5:3b","node":{"id":"https://demo.example.org/","type":"site","hits":5}})
    assert out["summary"] and called[0][0]=="http://127.0.0.1:11434/api/generate"
    assert b"prompt" in called[0][2]

def test_lock_delete_and_uuid_path_security(instance):
    sid,pw=begin(instance)
    assert instance.handle({"command":"list"})["captures"][0]["sessionId"]==sid
    with pytest.raises(m.BadRequest):instance.handle({"command":"delete","sessionId":sid,"confirm":"DELETE"})
    instance.handle({"command":"lock"})
    assert instance.handle({"command":"delete","sessionId":sid,"confirm":"DELETE"})["deleted"]
    with pytest.raises(m.BadRequest):instance.handle({"command":"read","sessionId":"../../../etc/passwd","passphrase":pw})

def test_influx_stress_no_plaintext(instance):
    sid,pw=begin(instance)
    start=time.monotonic()
    for n in range(55):
        batch=[event(to=f"https://static.example.net/r/{n*48+i}.js?secret=discard") for i in range(48)]
        response=instance.handle({"command":"append","events":batch})
        assert response["saved"]==48
    elapsed=time.monotonic()-start
    out=instance.handle({"command":"read","sessionId":sid,"passphrase":pw,"limit":3})
    assert out["total"]==2640 and len(out["events"])==3
    assert elapsed<20, f"Influx encryption unexpectedly slow: {elapsed}s"
    assert b"secret=discard" not in instance.path(sid).read_bytes()

def test_protocol_round_trip(tmp_path):
    env=dict(os.environ);env["HOME"]=str(tmp_path)
    child=subprocess.Popen([sys.executable,str(HOST)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env)
    sid=str(uuid.uuid4());msg={"id":"t1","command":"create","sessionId":sid,"site":"https://demo.example.org/","passphrase":"some very long passphrase"}
    data=json.dumps(msg).encode()
    child.stdin.write(struct.pack("<I",len(data))+data);child.stdin.flush()
    head=child.stdout.read(4);assert len(head)==4
    output=json.loads(child.stdout.read(struct.unpack("<I",head)[0]))
    assert output["ok"] is True and output["id"]=="t1"
    child.stdin.close();assert child.wait(timeout=5)==0
