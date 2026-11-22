#!/usr/bin/env python3
"""OX PARALLAX native messaging host: encrypted, bounded local-first evidence frames.
Wire format follows Firefox native messaging: u32 little-endian length + JSON.
No page code is ever executed; local model use is opt-in per user request.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import uuid
import urllib.request
from urllib.parse import urlsplit
from typing import BinaryIO

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

MAGIC=b"OXCAP07\x00"
HEADER_SIZE=len(MAGIC)+16
FRAME_MAX=250_000
INPUT_MAX=950_000
EVENT_TYPES={"navigation","request","response","redirect","popup","link","asset","mutation","resource_hint","cookie_meta","error","dom_removed","overflow"}
MODEL_PATTERN=re.compile(r"^[a-zA-Z0-9._:/-]{1,80}$")
ACCOUNT=re.compile(r"(?:^|/)(?:login|logout|signin|sign-in|signup|sign-up|account|accounts|auth|oauth|callback|payment|checkout|billing|settings|reset|password|private|admin|session)(?:/|$)", re.I)
SECRET=re.compile(r"(?:bearer|token|secret|api[_-]?key|access[_-]?key|jwt|sessionid|authorization)",re.I)

class BadRequest(Exception): pass

def safe_uuid(value):
    try:
        x=uuid.UUID(str(value))
        if str(x)!=value: raise ValueError()
        return str(x)
    except (ValueError, TypeError): raise BadRequest("Invalid capture identifier")

def scrub_url(value):
    if not isinstance(value,str) or len(value)>4096:return None
    try:
        u=urlsplit(value)
        if u.scheme not in ("https","http") or not u.hostname or u.username or u.password:return None
        host=u.hostname.lower()
        if host in ("localhost",) or host.endswith((".local",".internal",".localhost")):return None
        if ":" in host or re.match(r"^\d+\.\d+\.\d+\.\d+$",host):return None
        if u.port not in (None,80,443):return None
        if ACCOUNT.search(u.path) or SECRET.search(u.path):return None
        p=u.path or "/"
        if any(len(s)>28 or re.search(r"[A-Za-z0-9_-]{20,}",s) for s in p.split("/")):p="/[redacted-path]"
        return f"{u.scheme}://{host}{p[:180]}"
    except ValueError:return None

def origin(url):
    safe=scrub_url(url)
    if not safe:return None
    x=urlsplit(safe)
    return f"{x.scheme}://{x.hostname}"

def scrub_event(obj,site):
    if not isinstance(obj,dict) or obj.get("type") not in EVENT_TYPES:return None
    src=scrub_url(obj.get("from"))
    dest=scrub_url(obj.get("to")) if obj.get("to") else None
    if not src or origin(src)!=origin(site) or (obj.get("to") and not dest):return None
    e={"type":obj["type"],"from":src,"to":dest,"at":max(0,min(4102444800000,int(obj.get("at") or 0)))}
    if isinstance(obj.get("kind"),str):e["kind"]=re.sub(r"[^a-zA-Z0-9_./-]","",obj["kind"])[:32]
    if isinstance(obj.get("status"),int):e["status"]=max(0,min(599,obj["status"]))
    if isinstance(obj.get("count"),int):e["count"]=max(0,min(1000000,obj["count"]))
    if obj["type"]=="cookie_meta":
        e["name"]=re.sub(r"[^a-zA-Z0-9._-]","",str(obj.get("name", "")))[:65]
        e["domain"]=re.sub(r"[^a-zA-Z0-9.-]","",str(obj.get("cookieDomain","")))[:128]
        for k in ("httpOnly","secure","session"):e[k]=obj.get(k) is True
        e["sameSite"]=obj.get("sameSite") if obj.get("sameSite") in ("no_restriction","lax","strict","unspecified") else "unspecified"
        e["to"]=None
    return e

def derive(passphrase,salt):
    if not isinstance(passphrase,str) or len(passphrase)<12 or len(passphrase)>512:
        raise BadRequest("Passphrase requires 12–512 characters")
    return hashlib.scrypt(passphrase.encode("utf-8"),salt=salt,n=2**14,r=8,p=1,dklen=32)

def encrypt_frame(key,header,obj):
    body=json.dumps(obj,ensure_ascii=False,separators=(",", ":")).encode("utf-8")
    if len(body)>FRAME_MAX-32:raise BadRequest("Event frame too large")
    nonce=os.urandom(12)
    ciphertext=AESGCM(key).encrypt(nonce,body,header)
    packet=nonce+ciphertext
    return struct.pack("<I",len(packet))+packet

def frames(path,key,repair=False):
    """Return authenticated records, ignore/recover only a truncated trailing frame."""
    records=[]
    with path.open("r+b" if repair else "rb") as f:
        header=f.read(HEADER_SIZE)
        if len(header)!=HEADER_SIZE or not header.startswith(MAGIC):raise BadRequest("Invalid archive")
        pos=f.tell()
        while True:
            lengthbuf=f.read(4)
            if not lengthbuf:break
            if len(lengthbuf)<4:
                if repair:f.truncate(pos);break
                raise BadRequest("Truncated archive frame header")
            n=struct.unpack("<I",lengthbuf)[0]
            if n<28 or n>FRAME_MAX:raise BadRequest("Corrupt archive frame length")
            packet=f.read(n)
            if len(packet)!=n:
                if repair:f.truncate(pos);break
                raise BadRequest("Truncated archive frame")
            try: data=AESGCM(key).decrypt(packet[:12],packet[12:],header)
            except InvalidTag:raise BadRequest("Incorrect passphrase or corrupted archive")
            try: record=json.loads(data)
            except (ValueError,UnicodeError):raise BadRequest("Invalid archive record")
            records.append(record);pos=f.tell()
    return records

class Host:
    def __init__(self,root:Path|None=None):
        self.root=(root or (Path.home()/".local/share/oxsukra/parallax/vault")).expanduser()
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        os.chmod(self.root,0o700)
        self.session=None; self.key=None; self.site=None
    def path(self,session):return self.root/(safe_uuid(session)+".oxcap")
    def handle(self,msg):
        if not isinstance(msg,dict):raise BadRequest("Expected JSON object")
        command=msg.get("command")
        if command=="create":
            session=safe_uuid(msg.get("sessionId"));site=origin(msg.get("site"))
            if not site or not site.startswith("https://"):raise BadRequest("HTTPS public site required")
            salt=os.urandom(16); key=derive(msg.get("passphrase"),salt)
            path=self.path(session)
            old=os.umask(0o077)
            try:
                with path.open("xb") as f:
                    os.chmod(path,0o600)
                    header=MAGIC+salt;f.write(header)
                    f.write(encrypt_frame(key,header,{"kind":"verification","version":7,"site":site}))
                    f.flush();os.fsync(f.fileno())
            finally:os.umask(old)
            self.session=session;self.key=key;self.site=site
            return {"sessionId":session,"encrypted":True}
        if command=="append":
            if not self.key or not self.session or not self.site:raise BadRequest("Vault is locked")
            incoming=msg.get("events")
            if not isinstance(incoming,list) or len(incoming)>64:raise BadRequest("Batch must be 0–64 events")
            accepted=[e for raw in incoming if (e:=scrub_event(raw,self.site))]
            if not accepted:return {"saved":0,"rejected":len(incoming)}
            path=self.path(self.session)
            if path.stat().st_size>256*1024*1024:raise BadRequest("Archive at 256 MiB limit")
            # This session was freshly created and authenticated in this process.
            # Do not reread/decrypt the growing archive on every influx batch (O(N^2)).
            with path.open("ab") as f:
                with path.open("rb") as h:header=h.read(HEADER_SIZE)
                f.write(encrypt_frame(self.key,header,{"kind":"events","data":accepted}))
                f.flush();os.fsync(f.fileno())
            return {"saved":len(accepted),"rejected":len(incoming)-len(accepted)}
        if command=="lock":
            self.session=None;self.key=None;self.site=None
            return {"locked":True}
        if command=="list":
            return {"captures":[{"sessionId":p.stem} for p in sorted(self.root.glob("*.oxcap")) if re.fullmatch(r"[a-f0-9-]{36}",p.stem)][:100]}
        if command=="read":
            path=self.path(msg.get("sessionId"));
            if not path.is_file():raise BadRequest("Archive not found")
            with path.open("rb") as f:header=f.read(HEADER_SIZE)
            if not header.startswith(MAGIC):raise BadRequest("Not a PARALLAX archive")
            key=derive(msg.get("passphrase"),header[len(MAGIC):])
            records=frames(path,key)
            events=[e for frame in records if frame.get("kind")=="events" for e in frame.get("data",[])];
            limit=min(120,max(1,int(msg.get("limit") or 60)))
            return {"events":events[-limit:],"total":len(events),"encryptedAtRest":True}
        if command=="delete":
            session=safe_uuid(msg.get("sessionId"))
            if msg.get("confirm")!="DELETE":raise BadRequest("Explicit deletion confirmation required")
            if self.session==session:raise BadRequest("Lock current session before deletion")
            self.path(session).unlink(missing_ok=False)
            return {"deleted":True,"note":"Filesystem deletion cannot guarantee SSD secure erasure"}
        if command=="local-summary":
            model=msg.get("model");node=msg.get("node")
            if not isinstance(model,str) or not MODEL_PATTERN.fullmatch(model):raise BadRequest("Invalid local model")
            if not isinstance(node,dict) or set(node.keys())!={"id","type","hits"}:raise BadRequest("Invalid node metadata")
            url=scrub_url(node["id"])
            if not url or not isinstance(node["hits"],int):raise BadRequest("Unsafe metadata")
            prompt=("Describe ONLY what is supported by these observed browser graph node fields. "
              "Do not infer hidden code, identities, intent or unseen requests. "
              "An observed destination does not prove any data was sent beyond the browser event. "
              "Keep under 110 words.\n"+json.dumps({"url":url,"type":str(node["type"])[:40],"hits":max(0,min(100000,node["hits"]))}))
            body=json.dumps({"model":model,"prompt":prompt,"stream":False,"options":{"num_predict":180}}).encode()
            # Never respect HTTP(S)_PROXY environment variables for this endpoint.
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            request=urllib.request.Request("http://127.0.0.1:11434/api/generate",body,{"Content-Type":"application/json"},method="POST")
            try:
                with opener.open(request,timeout=15) as response:data=response.read(40_000)
                result=json.loads(data)
                return {"summary":str(result.get("response", ""))[:3000],"endpoint":"loopback-only"}
            except Exception as e:raise BadRequest("Local Ollama unavailable or response invalid") from e
        raise BadRequest("Unrecognized command")

def read_message(stdin:BinaryIO):
    length=stdin.read(4)
    if not length:return None
    if len(length)!=4:raise BadRequest("Truncated native message length")
    size=struct.unpack("<I",length)[0]
    if size>INPUT_MAX:raise BadRequest("Native message exceeds maximum")
    data=stdin.read(size)
    if len(data)!=size:raise BadRequest("Truncated native message body")
    try:return json.loads(data)
    except (ValueError,UnicodeError):raise BadRequest("Invalid JSON")

def reply(stdout:BinaryIO,msg):
    data=json.dumps(msg,ensure_ascii=False,separators=(",", ":")).encode("utf-8")
    stdout.write(struct.pack("<I",len(data))+data);stdout.flush()

def main():
    h=Host()
    while True:
        try:
            msg=read_message(sys.stdin.buffer)
            if msg is None:break
            ref=msg.get("id") if isinstance(msg,dict) else None
            try: result=h.handle(msg);reply(sys.stdout.buffer,{"id":ref,"ok":True,**result})
            except (BadRequest,OSError,ValueError,TypeError) as e:
                reply(sys.stdout.buffer,{"id":ref,"ok":False,"error":str(e)[:160]})
        except BadRequest:
            break
    return 0

if __name__=="__main__":raise SystemExit(main())
