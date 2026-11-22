"""HERMES Windows two-BAT provisioning, without touching real AppData."""
import hashlib
import json
import os
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

from funnel.local_app import install_local, load_local, smoke_local, state_root, run_local_app


class TwoBatLocalInstall(unittest.TestCase):
    def test_install_is_idempotent_and_localhost_authenticated(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            self.assertEqual(state_root(), Path(folder) / 'OX_HERMES')
            first = install_local()
            self.assertEqual(first['status'], 'installed')
            vault, member, admin = load_local()
            self.assertEqual(vault, Path(folder) / 'OX_HERMES' / 'vault')
            self.assertNotEqual(member, admin)
            auth = json.loads((vault / 'auth.json').read_text())
            self.assertEqual(len(auth), 2)
            self.assertIn(hashlib.sha256(member.encode()).hexdigest(), auth)
            self.assertNotIn(member, json.dumps(auth))
            self.assertEqual(smoke_local()['status'], 'pass')
            second = install_local()
            self.assertEqual(second['status'], 'already-installed')
            self.assertEqual(load_local()[1:], (member, admin))

    def test_partial_state_causes_stop_not_vault_reset(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            base = state_root()
            base.mkdir(parents=True)
            (base / 'owner_profile.json').write_text('{"broken": true}')
            with self.assertRaisesRegex(RuntimeError, 'Partial local installation'):
                install_local()
            self.assertFalse((base / 'vault' / 'auth.json').exists())
            self.assertTrue((base / 'owner_profile.json').exists())

    def test_missing_install_does_not_initialize_implicitly(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            with self.assertRaisesRegex(RuntimeError, 'not installed'):
                load_local()
            self.assertFalse(state_root().exists())

    def test_native_launcher_wires_real_hub_without_gui_side_effects(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {'LOCALAPPDATA': folder}):
            install_local()
            observed = []

            def fake_desktop(local_hub_url, member_token, admin_token):
                self.assertEqual(member_token, load_local()[1])
                self.assertEqual(admin_token, load_local()[2])
                req = urllib.request.Request(local_hub_url + '/api/v1/status',
                                             headers={'Authorization': 'Bearer ' + member_token})
                with urllib.request.urlopen(req, timeout=5) as response:
                    observed.append(json.load(response)['actor'])

            with patch('funnel.client.desktop', side_effect=fake_desktop):
                run_local_app()
            self.assertEqual(observed, ['local-owner'])
            self.assertTrue((state_root() / 'vault' / 'auth.json').exists())


if __name__ == '__main__':
    unittest.main()
