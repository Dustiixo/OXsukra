"""Additional offline packaging and onboarding validation."""
import json
import unittest
from pathlib import Path
import importlib.util
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
MODULE_PATH=ROOT/'tools/hermes_operator.py'
spec=importlib.util.spec_from_file_location('hermes_operator',MODULE_PATH)
operator=importlib.util.module_from_spec(spec)
spec.loader.exec_module(operator)

class OnboardingAssets(unittest.TestCase):
    def test_blueprint_is_reference_only(self):
        design=json.loads((ROOT/'server_blueprint.json').read_text(encoding='utf-8'))
        self.assertFalse(design['auto_create'])
        self.assertEqual(design['team_size'],4)
        self.assertIn('04 // ALCHEMY',[c['name'] for c in design['categories']])
        channels=[name for c in design['categories'] for name in c['text']]
        self.assertEqual(len(channels),len(set(channels)))
        self.assertIn('disclosure-and-rules', channels)

    def test_no_live_credentials_or_invasive_default(self):
        self.assertFalse((ROOT/'vault').exists())
        # A real Windows installation deliberately creates .venv BEFORE tests
        # are run. It must not make the source-only release check fail.
        self.assertTrue((ROOT/'requirements-bot.txt').is_file())
        self.assertFalse((ROOT/'bot.json').exists())
        for name in ['INSTALL_HERMES.bat','OPEN_HERMES.bat']:
            self.assertTrue((ROOT/name).exists(),name)
        core=(ROOT/'INSTALL_HERMES.bat').read_text(encoding='utf-8').lower()
        self.assertIn('unittest discover',core)
        self.assertNotIn('funnel hub',core)
        self.assertNotIn('funnel watch',core)
        self.assertNotIn('pip install discord',core)
        self.assertIn('local-install',core)

    def test_bot_url_validator_rejects_public_http(self):
        for url in ['http://example.com:8787','https://user@host.tld', 'http://8.8.8.8:8787']:
            self.assertFalse(operator.valid_local_or_secure_url(url))
        for url in ['https://hub.example.net','http://127.0.0.1:8787','http://100.64.2.5:8787']:
            self.assertTrue(operator.valid_local_or_secure_url(url))

    def test_member_materials_exist(self):
        for name in ['README_FIRST.md','MEETING_OVERVIEW.html','PROPOSAL_FOR_THE_FOUR_OF_US.md','DISCORD_PROPOSAL_POST.txt', 'TEAM_DECISIONS_TO_FILL.md','GROUP_DISCLOSURE_TEMPLATE.md','MILESTONES_AND_FUTURE_PROSPECTS.md']:
            self.assertTrue((ROOT/name).is_file(),name)

    def test_operator_launcher_does_not_shadow_python_stdlib(self):
        result=subprocess.run([sys.executable,str(ROOT/'tools/hermes_operator.py'),'doctor'],
                              cwd=ROOT,text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('Hub/client: READY',result.stdout)

if __name__=='__main__':unittest.main()
