import json
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from funnel.local_discord import valid_ids,save_ids,load_ids,run_local_discord


class DiscordSetupTests(unittest.TestCase):
    def test_numeric_scope(self):
        self.assertEqual(valid_ids('12345'),'12345')
        self.assertEqual(valid_ids('12345, 67890',multiple=True),'12345,67890')
        for bad in ('', '0', '12x', '-123', '10,10', '12345678901234567890123'):
            with self.assertRaises(ValueError):valid_ids(bad,multiple=True)

    def test_no_credentials_persisted(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'discord_connection.json'
            save_ids(p,'12345','100,200')
            self.assertEqual(load_ids(p),('12345','100,200'))
            body=json.loads(p.read_text(encoding='utf-8'))
            self.assertEqual(set(body),{'schema','guild','allowed'})
            self.assertNotIn('token',body)

    def test_runner_scopes_and_removes_credentials(self):
        calls=[]
        class FakeServer:
            def __init__(self,host,port,vault):
                calls.append(('bind',host,port,str(vault)))
            def serve_forever(self):pass
            def shutdown(self):calls.append(('shutdown',))
            def server_close(self):pass
        def bot():
            self.assertEqual(os.environ['DISCORD_BOT_TOKEN'],'S'*30)
            self.assertEqual(os.environ['DISCORD_GUILD_ID'],'12345')
            self.assertEqual(os.environ['DISCORD_ALLOWED_IDS'],'67890')
            self.assertEqual(os.environ['FUNNEL_HUB_URL'],'http://127.0.0.1:8787')
            self.assertEqual(os.environ['FUNNEL_BOT_API_TOKEN'],'private-member')
            calls.append(('bot',))
        variables=('DISCORD_BOT_TOKEN','DISCORD_GUILD_ID','DISCORD_ALLOWED_IDS',
                   'FUNNEL_HUB_URL','FUNNEL_BOT_API_TOKEN')
        old={k:os.environ.get(k) for k in variables}
        with tempfile.TemporaryDirectory() as t, \
             mock.patch.dict(sys.modules,{'discord':types.SimpleNamespace(__version__='2.4.0')}), \
             mock.patch('funnel.local_discord.load_local',return_value=(Path(t),'private-member','admin-secret')), \
             mock.patch('funnel.local_discord.state_root',return_value=Path(t)), \
             mock.patch('funnel.local_discord.ask_ids',return_value=('12345','67890')), \
             mock.patch('funnel.local_discord.getpass.getpass',return_value='S'*30), \
             mock.patch('funnel.local_discord.FunnelServer',FakeServer), \
             mock.patch('funnel.local_discord.webbrowser.open'), \
             mock.patch('funnel.discord_bridge.run_bot',side_effect=bot):
            run_local_discord()
            self.assertFalse((Path(t)/'discord_connection.json').exists())
        self.assertIn(('bot',),calls)
        self.assertIn(('shutdown',),calls)
        self.assertEqual({k:os.environ.get(k) for k in variables},old)


if __name__=='__main__':unittest.main()
