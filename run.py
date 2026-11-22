"""Run the offline-only OX Morph Lab local browser interface."""
from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from engine import World, WorldError

ROOT = Path(__file__).resolve().parent
ASSETS = {"/": (ROOT / "static" / "index.html", "text/html; charset=utf-8"),
          "/app.js": (ROOT / "static" / "app.js", "application/javascript; charset=utf-8"),
          "/style.css": (ROOT / "static" / "style.css", "text/css; charset=utf-8"),
          "/splice": (ROOT / "static" / "splice.html", "text/html; charset=utf-8"),
          "/splice.js": (ROOT / "static" / "splice.js", "application/javascript; charset=utf-8"),
          "/splice-core.mjs": (ROOT / "static" / "splice-core.mjs", "application/javascript; charset=utf-8"),
          "/splice.css": (ROOT / "static" / "splice.css", "text/css; charset=utf-8"),
          "/byte": (ROOT / "static" / "byte.html", "text/html; charset=utf-8"),
          "/byte.js": (ROOT / "static" / "byte.js", "application/javascript; charset=utf-8"),
          "/byte-core.mjs": (ROOT / "static" / "byte-core.mjs", "application/javascript; charset=utf-8"),
          "/byte.css": (ROOT / "static" / "byte.css", "text/css; charset=utf-8")}


def make_handler(world, token, port):
    class Handler(BaseHTTPRequestHandler):
        server_version = "OXSpliceWorld/0.2"
        def log_message(self, fmt, *args):
            sys.stderr.write("[local] " + fmt % args + "\n")

        def respond(self, code, data):
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            # Reject DNS-rebinding origins before exposing state and CSRF token.
            actual_port = self.server.server_address[1]
            if self.headers.get("Host", "") not in {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}:
                self.respond(403, {"error": "Invalid loopback Host"})
                return
            path = urlsplit(self.path).path
            if path == "/api/state":
                try:
                    self.respond(200, {**world.state(), "csrf_token": token})
                except WorldError as exc:
                    self.respond(500, {"error": str(exc)})
                return
            if path not in ASSETS:
                self.respond(404, {"error": "Not found"})
                return
            asset, content_type = ASSETS[path]
            data = asset.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; media-src 'self' blob:; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            if urlsplit(self.path).path != "/api/mutate":
                self.respond(404, {"error": "Not found"})
                return
            # No CORS; anti-CSRF token + JSON-only POST. Bound exclusively to loopback.
            host = self.headers.get("Host", "")
            origin = self.headers.get("Origin")
            actual_port = self.server.server_address[1]
            acceptable_hosts = {f"127.0.0.1:{actual_port}", f"localhost:{actual_port}"}
            if host not in acceptable_hosts or (origin and origin not in {"http://" + h for h in acceptable_hosts}):
                self.respond(403, {"error": "Host / origin rejected"})
                return
            if self.headers.get("X-OX-Token") != token or self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self.respond(403, {"error": "CSRF token or Content-Type rejected"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 2 or length > 20000:
                    raise WorldError("Request must be 2 to 20,000 bytes")
                data = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(data, dict):
                    raise WorldError("Expected a JSON object")
                op = data.get("op")
                rev = data.get("expected_revision")
                if type(rev) is not int:
                    raise WorldError("Expected integer world revision")
                reason = data.get("reason", "")
                if op == "create":
                    result = world.create(data.get("name"), data.get("prototype"), {}, reason, rev)
                elif op == "clone":
                    result = world.clone(data.get("object_id"), data.get("name"), reason, rev)
                elif op == "revert":
                    result = world.undo_object(data.get("object_id"), reason, rev)
                elif op in {"set_slot", "drop_slot", "rename", "set_prototype"}:
                    result = world.mutate(op, data.get("object_id"), reason, rev,
                        slot_name=data.get("slot_name"), slot=data.get("slot"),
                        name=data.get("name"), prototype=data.get("prototype"))
                else:
                    raise WorldError("Unsupported command")
                self.respond(200, {"result": result, "world": world.state()})
            except (WorldError, ValueError, TypeError, KeyError) as exc:
                self.respond(400, {"error": str(exc)})
            except Exception as exc:
                sys.stderr.write(f"Mutation failure: {exc}\n")
                self.respond(500, {"error": "Internal error"})

    return Handler


def main(argv=None):
    p = argparse.ArgumentParser(description="OX Morph Lab local-first object world")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--db", default=str(Path.home() / ".ox-morph-lab" / "world.sqlite3"))
    p.add_argument("--no-demo", action="store_true", help="Start an empty world on a new database")
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args(argv)
    if not (1024 <= args.port <= 65535):
        p.error("Port must be between 1024 and 65535")
    world = World(args.db, demo=not args.no_demo)
    url = f"http://127.0.0.1:{args.port}"
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(world, secrets.token_urlsafe(32), args.port))
    print(f"OX SPLICE WORLD v0.2  |  {url}\nLocal-only; database: {world.db_path}\nCtrl+C to stop", flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        world.close()

if __name__ == "__main__":
    main()
