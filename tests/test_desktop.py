"""Desktop API tests: real local HTTP, IXO authority and DSOE state gates."""
from __future__ import annotations
import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from ixo_foundation.desktop import DesktopServer
from ixo_foundation.system import Foundation


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = Foundation(Path(self.temp.name) / 'state')
        self.server = DesktopServer(('127.0.0.1', 0), self.app, token='test-local-secret')
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        self.app.close()
        self.temp.cleanup()

    def request(self, path, body=None, token=True, origin=None):
        data = None if body is None else json.dumps(body).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['X-IXO-Token'] = 'test-local-secret'
        if origin:
            headers['Origin'] = origin
        req = Request(self.base + path, data=data, headers=headers)
        try:
            with urlopen(req, timeout=4) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def test_liveness_and_static_client(self):
        code, result = self.request('/api/dsoe')
        self.assertEqual(code, 200)
        self.assertEqual(result['native_connected'], 0)
        self.assertEqual(len(result['providers']), 3)
        with urlopen(self.base + '/dsoe.js', timeout=4) as response:
            self.assertIn(b'dsoeAction', response.read())
        with urlopen(self.base + '/', timeout=4) as response:
            self.assertIn(b'panel-dsoe', response.read())

    def test_only_authorized_local_request_creates_task(self):
        body = {'action': 'plan', 'objective': 'Audit package integrity'}
        code, _ = self.request('/api/dsoe/action', body, token=False)
        self.assertEqual(code, 403)
        code, _ = self.request('/api/dsoe/action', body, origin='https://evil.example')
        self.assertEqual(code, 403)
        self.assertEqual(self.app.dsoe.status()['tasks'], [])
        code, result = self.request('/api/dsoe/action', body, origin=self.base)
        self.assertEqual(code, 200)
        task_id = result['task']['id']
        self.assertEqual(result['task']['state'], 'DRAFT')
        code, _ = self.request('/api/dsoe/action', {'action': 'dispatch', 'task_id': task_id})
        self.assertEqual(code, 400)
        code, _ = self.request('/api/dsoe/action', {'action': 'approve', 'task_id': task_id})
        self.assertEqual(code, 200)
        code, response = self.request('/api/dsoe/action', {'action': 'dispatch', 'task_id': task_id})
        self.assertEqual(code, 200)
        self.assertFalse(response['native_upstream_execution'])
        job_id = response['job_id']
        code, _ = self.request('/api/dsoe/handoff?job=' + job_id, token=False)
        self.assertEqual(code, 403)
        code, handoff = self.request('/api/dsoe/handoff?job=' + job_id)
        self.assertEqual(code, 200)
        self.assertEqual(handoff['request']['job_id'], job_id)
        self.assertEqual(self.app.ixo.status(0)['counts']['facts'], 0)

    def test_result_review_and_evidence_cannot_be_skipped(self):
        code, result = self.request('/api/dsoe/action', {'action': 'plan', 'objective': 'Verify gates'})
        task_id = result['task']['id']
        self.request('/api/dsoe/action', {'action': 'approve', 'task_id': task_id})
        code, job = self.request('/api/dsoe/action', {'action': 'dispatch', 'task_id': task_id})
        job_id = job['job_id']
        code, _ = self.request('/api/dsoe/action', {'action': 'evidence', 'job_id': job_id})
        self.assertEqual(code, 400)
        code, _ = self.request('/api/dsoe/action', {'action': 'review', 'job_id': job_id, 'decision': 'accept', 'reason': 'no result'})
        self.assertEqual(code, 400)
        code, _ = self.request('/api/dsoe/action', {'action': 'report', 'job_id': job_id, 'result': {'summary':'fake'}})
        self.assertEqual(code, 400)
        code, _ = self.request('/api/dsoe/action', {'action': 'plan', 'objective': ''})
        self.assertEqual(code, 400)
        self.assertEqual(self.app.aixo.state()['dsoe_evidence_count'], 0)
        self.assertEqual(self.app.ixo.status(0)['counts']['facts'], 0)


if __name__ == '__main__':
    unittest.main()
