"""Real HTTP privacy and review boundaries for the four-member pilot."""
import hashlib
import io
import json
import os
import sqlite3
from contextlib import closing
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from unittest.mock import patch

from funnel.common import init_data
from funnel.hub import FunnelServer, db_open, setup_db


class PrivateByDefaultPilot(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        creds = init_data(self.root)
        self.alice, self.bob, self.bot, self.admin = (
            creds[0][2], creds[1][2], creds[4][2], creds[5][2]
        )
        self.server = FunnelServer('127.0.0.1', 0, self.root)
        self.url = f'http://127.0.0.1:{self.server.server_port}'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def call(self, path, method='GET', body=None, token=None, binary=False):
        token = self.alice if token is None else token
        headers = {'Authorization': 'Bearer ' + token}
        if body is not None and not binary:
            body = json.dumps(body).encode()
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(self.url + path, data=body,
                                     method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=7) as response:
                if path.endswith('/download') or path.endswith('/obsidian-export'):
                    return response.read()
                return json.load(response)
        except urllib.error.HTTPError as exc:
            with exc:
                return {'http_error': exc.code, **json.load(exc)}

    def upload(self, name, payload=b'PRIVATE ALPHA TEST', token=None):
        digest = hashlib.sha256(payload).hexdigest()
        created = self.call('/api/v1/uploads', 'POST',
                            {'name': name, 'project': 'ixo',
                             'size': len(payload), 'sha256': digest}, token=token)
        self.assertIn('upload_id', created, created)
        ident = created['upload_id']
        written = self.call(f'/api/v1/uploads/{ident}/chunk?offset=0', 'PATCH',
                            payload, token=token, binary=True)
        self.assertEqual(written['offset'], len(payload))
        result = self.call(f'/api/v1/uploads/{ident}/complete', 'POST', {}, token=token)
        self.assertIn('item_id', result, result)
        return result

    def test_private_item_isolation_across_all_read_endpoints(self):
        item = self.upload('private_design.txt')
        ident = item['item_id']
        self.assertEqual(item['visibility'], 'private')
        self.assertEqual(len(self.call('/api/v1/items', token=self.bob)['items']), 0)
        self.assertEqual(len(self.call('/api/v1/jobs', token=self.bob)['jobs']), 0)
        self.assertEqual(self.call('/api/v1/status', token=self.bob)['items'], 0)
        self.assertEqual(self.call('/api/v1/items/' + ident, token=self.bob)['http_error'], 404)
        self.assertEqual(self.call('/api/v1/items/' + ident + '/download', token=self.bob)['http_error'], 404)
        self.assertEqual(self.call('/api/v1/items/' + ident, token=self.bot)['http_error'], 404)
        self.assertEqual(self.call('/api/v1/search?q=private_design', token=self.bob)['items'], [])
        self.assertEqual(len(self.call('/api/v1/items', token=self.admin)['items']), 1)

    def test_explicit_team_share_and_revoke_are_audited(self):
        item = self.upload('team_demo.txt', b'SHARED TEST FILE')
        path = '/api/v1/items/' + item['item_id']
        self.assertEqual(self.call(path + '/share', 'POST',
                                   {'visibility': 'team'})['http_error'], 412)
        self.assertEqual(self.call(path + '/share', 'POST',
                                   {'visibility': 'team', 'acknowledged': True}, token=self.admin)['http_error'], 412)
        self.assertEqual(self.call(path + '/share', 'POST',
                                   {'visibility': 'team', 'acknowledged': True})['visibility'], 'team')
        self.assertEqual(self.call(path + '/download', token=self.bob), b'SHARED TEST FILE')
        self.assertEqual(len(self.call('/api/v1/items', token=self.bob)['items']), 1)
        self.assertEqual(self.call(path + '/share', 'POST',
                                   {'visibility': 'private'})['visibility'], 'private')
        self.assertEqual(self.call(path + '/download', token=self.bob)['http_error'], 404)
        self.assertEqual(self.call('/api/v1/audit', token=self.bob)['http_error'], 403)
        actions = [e['action'] for e in self.call('/api/v1/audit', token=self.admin)['events']]
        self.assertIn('item.received', actions)
        self.assertEqual(actions.count('item.visibility'), 2)

    def test_notes_need_author_submission_and_admin_review(self):
        result = self.call('/api/v1/notes', 'POST', {'title': 'Private discovery',
                           'body': 'Not an approved finding', 'project': 'ixo'})
        ident = result['note_id']
        path = '/api/v1/notes/' + ident
        self.assertEqual(self.call('/api/v1/notes', token=self.bob)['notes'], [])
        self.assertEqual(self.call(path + '/markdown', token=self.bob)['http_error'], 404)
        self.assertEqual(self.call(path + '/review', 'POST',
                                   {'decision': 'approve'}, token=self.admin)['http_error'], 409)
        self.assertEqual(self.call(path + '/submit', 'POST', {})['http_error'], 412)
        self.assertEqual(self.call(path + '/submit', 'POST',
                                   {'acknowledged': True})['state'], 'submitted')
        self.assertEqual(self.call('/api/v1/notes', token=self.bob)['notes'], [])
        approved = self.call(path + '/review', 'POST', {'decision': 'approve'}, token=self.admin)
        self.assertEqual(approved['state'], 'approved')
        self.assertEqual(len(self.call('/api/v1/notes', token=self.bob)['notes']), 1)
        with zipfile.ZipFile(io.BytesIO(self.call('/api/v1/obsidian-export', token=self.bob))) as archive:
            self.assertEqual(len(archive.namelist()), 1)
        self.assertEqual(self.call(path + '/withdraw', 'POST', {})['visibility'], 'private')
        self.assertEqual(self.call('/api/v1/notes', token=self.bob)['notes'], [])
        with zipfile.ZipFile(io.BytesIO(self.call('/api/v1/obsidian-export', token=self.bob))) as archive:
            self.assertEqual(archive.namelist(), [])

    def test_remote_mirror_needs_separate_owner_permission(self):
        item = self.upload('remote_test.txt')
        path = '/api/v1/items/' + item['item_id']
        self.assertEqual(self.call(path + '/authorize-mirror', 'POST',
                                   {'acknowledged': True})['http_error'], 409)
        self.call(path + '/share', 'POST', {'visibility': 'team', 'acknowledged': True})
        self.assertEqual(self.call(path + '/authorize-mirror', 'POST',
                                   {'acknowledged': False})['http_error'], 412)
        self.assertEqual(self.call(path + '/authorize-mirror', 'POST',
                                   {'acknowledged': True}, token=self.bob)['http_error'], 404)
        self.assertTrue(self.call(path + '/authorize-mirror', 'POST',
                                  {'acknowledged': True})['mirror_authorized'])
        self.assertEqual(self.call(path + '/share', 'POST',
                                   {'visibility': 'private'})['http_error'], 409)

    def test_remote_config_does_not_copy_private_uploads(self):
        with patch.dict(os.environ, {'FUNNEL_RCLONE_REMOTE': 'teamdrive:OX_Funnel'}), \
             patch('funnel.hub.subprocess.run') as external, \
             patch('funnel.hub.discord_event') as outbound:
            item = self.upload('private_image.txt')
            limit = time.time() + 5
            while time.time() < limit:
                jobs = self.call('/api/v1/jobs')['jobs']
                match = [j for j in jobs if j['id'] == item['job_id']]
                if match and match[0]['status'] in ('done', 'failed'):
                    break
                time.sleep(.05)
            else:
                self.fail('Private job did not complete')
            self.assertEqual(match[0]['status'], 'done')
            self.assertEqual(match[0]['mirror'], 'not-authorized')
            external.assert_not_called()
            outbound.assert_not_called()


class LegacyVaultMigration(unittest.TestCase):
    def test_v04_data_becomes_private_without_deletion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            # sqlite3.Connection's context manager commits, but DOES NOT close.
            # On Windows an open handle blocks TemporaryDirectory cleanup.
            with closing(sqlite3.connect(root / 'funnel.sqlite3')) as c, c:
                c.execute('CREATE TABLE items(id TEXT PRIMARY KEY, actor TEXT, name TEXT, project TEXT, size INTEGER, sha256 TEXT, annotation TEXT DEFAULT "", created REAL, preview TEXT DEFAULT "", purpose_slug TEXT DEFAULT "dump_inbox", route_state TEXT DEFAULT "needs_review")')
                c.execute('CREATE TABLE notes(id TEXT PRIMARY KEY, author TEXT, title TEXT, body TEXT, project TEXT, item_id TEXT DEFAULT "", state TEXT DEFAULT "proposed", created REAL)')
                c.execute('INSERT INTO items(id,actor,name,project,size,sha256,created) VALUES (?,?,?,?,?,?,?)',
                          ('legacy-a','dev-1','older.txt','ixo',3,'f'*64,1.0))
                c.execute('INSERT INTO notes(id,author,title,body,project,created) VALUES (?,?,?,?,?,?)',
                          ('legacy-n','dev-1','Old note','Private draft','ixo',1.0))
            setup_db(root)
            with db_open(root) as c:
                self.assertEqual(c.execute("SELECT visibility FROM items WHERE id='legacy-a'").fetchone()[0], 'private')
                self.assertEqual(c.execute("SELECT visibility FROM notes WHERE id='legacy-n'").fetchone()[0], 'private')
                self.assertEqual(c.execute("SELECT mirror_approved FROM items WHERE id='legacy-a'").fetchone()[0], 0)
            setup_db(root)  # second startup must preserve the same rows
            with db_open(root) as c:
                self.assertEqual(c.execute('SELECT count(*) FROM items').fetchone()[0], 1)
                self.assertEqual(c.execute('SELECT count(*) FROM notes').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
