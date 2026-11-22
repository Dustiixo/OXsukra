"""Local IXO desktop server with DSOE operator commands.

One process owns IXO, AIXO and DSOE. UI clients cannot bypass the
Python authorization and state transitions. No upstream agents are run here.
"""
from __future__ import annotations

import argparse
import json
import secrets
import tempfile
import webbrowser
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from aixo.engine import AIXOError
from dsoe.store import DSOEError, MAX_RESULT
from experience.store import ExperienceError
from ixo.common import IXOError
from ixo.server import Handler
from .system import Foundation


class DesktopHandler(Handler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/experience':
            if not secrets.compare_digest(self.headers.get('X-IXO-Token', ''), self.server.token):
                return self.reply(403, {'ok':False,'error':'Invalid local token'})
            return self.reply(200, {'report':self.server.foundation.experience.report(),
                                    'general':self.server.foundation.experience.select(max_items=100)})
        if path == '/experience.js':
            content = (Path(__file__).resolve().parents[1] / 'web' / 'experience.js').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/javascript; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            return self.wfile.write(content)
        if path == '/api/dsoe':
            return self.reply(200, {'status': self.server.foundation.dsoe.status(),
                                    'providers': self.server.foundation.dsoe.providers(),
                                    'native_connected': 0})
        if path == '/api/dsoe/handoff':
            if not secrets.compare_digest(self.headers.get('X-IXO-Token', ''), self.server.token):
                return self.reply(403, {'ok': False, 'error': 'Invalid local token'})
            query = parse_qs(urlsplit(self.path).query)
            job_id = query.get('job', [''])[0]
            if not job_id or len(job_id) > 80:
                return self.reply(400, {'ok': False, 'error': 'Job ID required'})
            try:
                return self.reply(200, self.server.foundation.dsoe.store.make_envelope(job_id))
            except DSOEError as exc:
                return self.reply(400, {'ok': False, 'error': str(exc)})
        if path == '/dsoe.js':
            content = (Path(__file__).resolve().parents[1] / 'web' / 'dsoe.js').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/javascript; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            return self.wfile.write(content)
        if path == '/api/dsoe/task':
            query = parse_qs(urlsplit(self.path).query)
            task_id = query.get('id', [''])[0]
            if not task_id or len(task_id) > 80:
                return self.reply(400, {'ok': False, 'error': 'Task ID required'})
            try:
                return self.reply(200, self.server.foundation.dsoe.detail(task_id))
            except DSOEError as exc:
                return self.reply(400, {'ok': False, 'error': str(exc)})
        return super().do_GET()

    def do_POST(self):
        if urlsplit(self.path).path == '/api/experience/action':
            if not secrets.compare_digest(self.headers.get('X-IXO-Token',''), self.server.token):
                return self.reply(403, {'ok':False,'error':'Invalid local token'})
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',
                                        f'http://localhost:{self.server.server_port}'):
                return self.reply(403, {'ok':False,'error':'Cross-origin write rejected'})
            try:
                size=int(self.headers.get('Content-Length','0'))
                if not 0 < size <= 110000:
                    raise ExperienceError('Invalid experience request size')
                body=json.loads(self.rfile.read(size))
                if not isinstance(body,dict):raise ExperienceError('Expected JSON object')
                xp=self.server.foundation.experience
                if body.get('action')=='sync-ixo':
                    result=xp.capture_ixo(self.server.foundation.ixo)
                elif body.get('action')=='add':
                    result=xp.record(content=body.get('content'), project=body.get('project'),
                                     domain=body.get('domain'), origin=body.get('origin'),
                                     partition=body.get('partition','learning'),kind=body.get('kind','material'),
                                     source_ref=body.get('source_ref'))
                else:
                    raise ExperienceError('Unsupported experience action')
                return self.reply(200,result)
            except (ValueError,TypeError,OSError,ExperienceError,json.JSONDecodeError) as exc:
                return self.reply(400, {'ok':False,'error':str(exc)})
        if urlsplit(self.path).path != '/api/dsoe/action':
            return super().do_POST()
        if not secrets.compare_digest(self.headers.get('X-IXO-Token', ''), self.server.token):
            return self.reply(403, {'ok': False, 'error': 'Invalid local token'})
        origin = self.headers.get('Origin')
        if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',
                                    f'http://localhost:{self.server.server_port}'):
            return self.reply(403, {'ok': False, 'error': 'Cross-origin write rejected'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= MAX_RESULT + 3000:
                raise DSOEError('Invalid request size')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise DSOEError('Request must be a JSON object')
            dsoe = self.server.foundation.dsoe
            command = body.get('action')
            if command == 'plan':
                result = dsoe.plan(body.get('objective'), body.get('workspace'))
            elif command == 'approve':
                result = dsoe.store.approve(body.get('task_id'))
            elif command == 'dispatch':
                result = dsoe.dispatch(body.get('task_id'))
            elif command == 'review':
                if body.get('decision') not in ('accept', 'reject'):
                    raise DSOEError('Explicit accept or reject required')
                row = dsoe.store.review(body.get('job_id'), body['decision'] == 'accept', body.get('reason'))
                result = {'ok': True, 'job_id': row['id'], 'state': row['state']}
            elif command == 'evidence':
                result = dsoe.record_evidence(body.get('job_id'))
            elif command == 'report':
                raw = body.get('result')
                if not isinstance(raw, dict):
                    raise DSOEError('Result must be a JSON object; do not submit fixture as live evidence')
                if len(json.dumps(raw, ensure_ascii=False).encode('utf-8')) > MAX_RESULT:
                    raise DSOEError('Result exceeds maximum size')
                # The core file-based protocol is retained unchanged.
                with tempfile.TemporaryDirectory(prefix='ixo-dsoe-report-') as tmp:
                    path = Path(tmp) / 'result.json'
                    path.write_text(json.dumps(raw, ensure_ascii=False), encoding='utf-8')
                    result = dsoe.report_file(body.get('job_id'), path)
            else:
                raise DSOEError('Unknown DSOE action')
            return self.reply(200, result)
        except (ValueError, KeyError, TypeError, OSError, IXOError, AIXOError, DSOEError,
                json.JSONDecodeError) as exc:
            return self.reply(400, {'ok': False, 'error': str(exc)})


class DesktopServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, foundation, token=None):
        self.foundation = foundation
        self.runtime = foundation.ixo
        self.aixo = foundation.aixo
        self.token = token or secrets.token_urlsafe(32)
        super().__init__(address, DesktopHandler)


def serve(home: Path, port: int = 0, launch: bool = True) -> None:
    with Foundation(home) as foundation:
        server = DesktopServer(('127.0.0.1', port), foundation)
        url = f'http://127.0.0.1:{server.server_port}/?token={server.token}'
        print('IXO DSOE desktop:', url, flush=True)
        if launch:
            webbrowser.open(url)
        try:
            server.serve_forever(poll_interval=.2)
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()


def main(argv=None):
    p = argparse.ArgumentParser(description='Local IXO / AIXO / DSOE desktop')
    p.add_argument('--home', type=Path, default=Path.home() / '.ixo' / 'foundation')
    p.add_argument('--port', type=int, default=0)
    p.add_argument('--no-browser', action='store_true')
    args = p.parse_args(argv)
    serve(args.home, args.port, not args.no_browser)


if __name__ == '__main__':
    main()
