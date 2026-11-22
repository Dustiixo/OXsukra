"""Opt-in, token-protected, loopback-only, read-only FlowMesh spatial viewer.

No workspace writes. Every /api/trace invocation verifies the FlowMesh ledger.
This serves only hardcoded UI assets; arbitrary file paths are never served.
"""
from __future__ import annotations

import argparse
import http.server
import json
from pathlib import Path
import secrets
import sys
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from spatial_lab.export_trace import export

ASSETS = {
    '/': ('index.html', 'text/html; charset=utf-8'),
    '/index.html': ('index.html', 'text/html; charset=utf-8'),
    '/chamber.css': ('chamber.css', 'text/css; charset=utf-8'),
    '/chamber.js': ('chamber.js', 'text/javascript; charset=utf-8'),
    '/trace_data.js': ('trace_data.js', 'text/javascript; charset=utf-8'),
}


def make_handler(root: Path, token: str):
    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = 'IXOChamber/0.3'
        sys_version = ''

        def log_message(self, fmt: str, *args):
            # Avoid printing URLs with authentication query parameters.
            pass

        def reply(self, code, data: bytes, mime='text/plain; charset=utf-8'):
            self.send_response(code)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            self.reply(405, b'Read-only service. No write endpoints.\n')

        def do_GET(self):
            u = urlparse(self.path)
            if u.path == '/api/trace':
                supplied = parse_qs(u.query).get('key', [''])[0]
                if not secrets.compare_digest(supplied, token):
                    return self.reply(403, b'Unauthorized local trace access.\n')
                try:
                    # Explicit ledger verification occurs inside export() before inspection.
                    payload = json.dumps(export(root), ensure_ascii=False).encode('utf-8')
                    if len(payload) > 8_000_000:
                        return self.reply(413, b'Trace too large for local viewer.\n')
                    return self.reply(200, payload, 'application/json; charset=utf-8')
                except Exception:
                    # Do not reveal paths, raw source text, or exceptions via failed endpoint.
                    return self.reply(409, b'FlowMesh workspace verification failed; no trace served.\n')
            if u.path not in ASSETS:
                return self.reply(404, b'Not found.\n')
            if u.path in ['/', '/index.html']:
                supplied = parse_qs(u.query).get('key', [''])[0]
                if not secrets.compare_digest(supplied, token):
                    return self.reply(403, b'Enter via the authorized local URL.\n')
            name, mime = ASSETS[u.path]
            return self.reply(200, (HERE / name).read_bytes(), mime)
    return Handler


def start(root: Path, port: int = 0):
    root = root.resolve(strict=True)
    # Fail closed before announcing a viewer URL.
    export(root)
    token = secrets.token_urlsafe(24)
    server = http.server.ThreadingHTTPServer(('127.0.0.1', port), make_handler(root, token))
    return server, token


def main():
    ap = argparse.ArgumentParser(description='Read-only private FlowMesh spatial viewer on 127.0.0.1')
    ap.add_argument('--root', required=True, type=Path, help='Existing verified FlowMesh workspace')
    ap.add_argument('--port', type=int, default=0, help='Loopback port, 0 assigns a free port')
    args = ap.parse_args()
    try:
        server, token = start(args.root, args.port)
    except Exception as e:
        raise SystemExit('BLOCKED: source integrity check failed: ' + type(e).__name__)
    host, port = server.server_address
    print('IXO Spatial Chamber M0.3 / LIVE LOCAL READ-ONLY', flush=True)
    print(f'Open in a browser: http://127.0.0.1:{port}/?key={token}', flush=True)
    print('Press Ctrl+C to stop; never share the URL or a private trace.', flush=True)
    try:
        server.serve_forever(poll_interval=.3)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
