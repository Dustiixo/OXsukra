"""Real HTTP end-to-end tests for adaptive taxonomy and Java interoperability."""
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import unittest
import urllib.request
from tests import test_funnel as fixture
from funnel.hub import db_open, setup_db


class PurposeIntegration(unittest.TestCase):
    setUp = fixture.FunnelIntegration.setUp
    tearDown = fixture.FunnelIntegration.tearDown
    call = fixture.FunnelIntegration.call
    create = fixture.FunnelIntegration.create
    finish = fixture.FunnelIntegration.finish

    def test_previews_are_evidence_backed_and_nonexecuting(self):
        known=self.call('/api/v1/route/preview','POST',
                        {'name':'engine_main.java','description':'compile source','project':'shared'})
        self.assertEqual(known['contract'],'hermes.purpose.v1')
        self.assertEqual(known['decision'],'suggested')
        self.assertEqual(known['purpose'],'development')
        self.assertIn('java',known['candidate_scores'][0]['matched_terms'])
        self.assertFalse(known['executed'])
        unknown=self.call('/api/v1/route/preview','POST',{'name':'mystery.bin'})
        self.assertEqual(unknown['decision'],'needs_review')
        self.assertEqual(unknown['purpose'],'dump_inbox')
        self.assertEqual(self.call('/api/v1/purpose-requests')['requests'],[])
        self.assertEqual(self.call('/api/v1/route/preview','POST',{'name':''})['http_error'],400)

    def test_upload_routes_to_purpose_or_triage_with_record(self):
        data=b'public test text'
        first=self.finish(self.create('VELA_music.mid',data),data)
        second=self.finish(self.create('opaque_material.bin',data),data)
        self.assertEqual(first['purpose'],'creative')
        self.assertEqual(first['route_state'],'provisional')
        self.assertEqual(second['purpose'],'dump_inbox')
        self.assertEqual(second['route_state'],'needs_review')
        self.assertEqual(len(self.call('/api/v1/items?purpose=creative')['items']),1)
        tickets=self.call('/api/v1/purpose-requests')['requests']
        self.assertEqual(len(tickets),1)
        self.assertEqual(tickets[0]['kind'],'triage')
        self.assertEqual(tickets[0]['item_id'],second['item_id'])
        with db_open(self.root) as c:
            history=c.execute('SELECT * FROM purpose_events ORDER BY created').fetchall()
        self.assertEqual(len(history),2)

    def test_new_category_approval_changes_later_predictions(self):
        ticket=self.call('/api/v1/purpose-requests','POST',
             {'kind':'new_purpose','title':'Simulation','reason':'Game and scene assets',
              'proposed_slug':'simulation','keywords':['mesh','scene']})
        self.assertEqual(ticket['status'],'open')
        self.assertEqual(self.call('/api/v1/route/preview','POST',{'name':'scene.mesh'})['decision'],'needs_review')
        denied=self.call(f"/api/v1/purpose-requests/{ticket['request_id']}/resolve",'POST',
                         {'decision':'approve'},token=self.member)
        self.assertEqual(denied['http_error'],403)
        accepted=self.call(f"/api/v1/purpose-requests/{ticket['request_id']}/resolve",'POST',
                           {'decision':'approve'},token=self.admin)
        self.assertEqual(accepted['status'],'approved')
        self.assertEqual(accepted['discord_action'],'none')
        plan=self.call('/api/v1/route/preview','POST',{'name':'scene.mesh'})
        self.assertEqual(plan['decision'],'suggested')
        self.assertEqual(plan['purpose'],'simulation')
        self.assertEqual(plan['channel_hint'],'#file-drop')
        self.assertEqual(self.call(f"/api/v1/purpose-requests/{ticket['request_id']}/resolve",'POST',
            {'decision':'approve'},token=self.admin)['http_error'],409)

    def test_missing_file_ticket_and_admin_learning(self):
        req=self.call('/api/v1/purpose-requests','POST',
             {'kind':'missing_file','title':'Syntra contract test','reason':'Need the latest typed interface'})
        self.assertEqual(req['status'],'open')
        data=b'dummy test only'
        file=self.finish(self.create('thermal_sensor.bin',data),data)
        update=self.call(f"/api/v1/items/{file['item_id']}/purpose",'POST',
                         {'purpose':'development','learn_term':'thermal'},token=self.admin)
        self.assertEqual(update['status'],'approved_by_admin')
        self.assertEqual(update['trained_term'],'thermal')
        newer=self.call('/api/v1/route/preview','POST',{'name':'thermal_report.dat'})
        self.assertEqual(newer['purpose'],'development')
        self.assertEqual(newer['decision'],'suggested')
        item=self.call(f"/api/v1/items/{file['item_id']}")['item']
        self.assertEqual(item['route_state'],'approved_by_admin')
        self.assertEqual(len([r for r in self.call('/api/v1/purpose-requests')['requests'] if r['status']=='resolved']),1)

    def test_business_sensitive_preflight_and_restricted_corrections(self):
        data=b'not actually confidential'
        import hashlib
        hash=hashlib.sha256(data).hexdigest()
        result=self.call('/api/v1/uploads','POST',
             {'name':'company_budget.md','project':'business','size':len(data),'sha256':hash})
        self.assertEqual(result['http_error'],403)
        plan=self.call('/api/v1/route/preview','POST',{'name':'company_budget.md','project':'shared'})
        self.assertEqual(plan['decision'],'restricted')
        self.assertEqual(plan['purpose'],'business_intentions')
        self.assertEqual(self.call('/api/v1/items')['items'],[])
        t=self.call('/api/v1/purpose-requests','POST',{'kind':'new_purpose','title':'Invoices',
            'reason':'financial records need restricted access','proposed_slug':'invoices',
            'keywords':['invoice']})
        self.call(f"/api/v1/purpose-requests/{t['request_id']}/resolve",'POST',{'decision':'approve'},token=self.admin)
        protected={x['slug']:x for x in self.call('/api/v1/purposes')['purposes']}
        self.assertEqual(protected['invoices']['restricted'],1)

    def test_schema_restart_does_not_duplicate_taxonomy(self):
        with db_open(self.root) as c:
            before=c.execute('SELECT count(*) FROM purpose_rules').fetchone()[0]
        setup_db(self.root)
        with db_open(self.root) as c:
            after=c.execute('SELECT count(*) FROM purpose_rules').fetchone()[0]
        self.assertEqual(before,after)

    def test_java_interop_over_real_http(self):
        # Java integration is OPTIONAL. A working JRE is not necessarily a
        # full JDK; Windows' "java File.java" source launcher needs compiler
        # support and must never block installing the Python HERMES core.
        if os.environ.get('HERMES_RUN_OPTIONAL_JAVA_TEST')!='1':
            self.skipTest('Optional Java interop is an opt-in developer check, not an installer gate')
        if not shutil.which('java') or not shutil.which('javac'):
            self.skipTest('Optional Java adapter needs a JDK 17+ (not required by local HERMES)')
        compiler=subprocess.run(['javac','-version'],capture_output=True,text=True,timeout=5)
        version=re.search(r'javac\s+(\d+)',compiler.stdout+' '+compiler.stderr)
        if compiler.returncode or not version or int(version.group(1))<17:
            self.skipTest('Optional Java adapter requires JDK 17+; local HERMES remains supported')
        path=Path(__file__).resolve().parents[1]/'adapters/java/HermesBridge.java'
        env={**os.environ,'HERMES_HUB_TOKEN':self.member,'HERMES_HUB_URL':self.base}
        result=subprocess.run(['java',str(path),'preview','SyntraBridge.java','build source API'],
                              env=env,check=False,capture_output=True,text=True,timeout=30)
        if result.returncode!=0 and ('JDK compiler' in result.stderr or 'not supported' in result.stderr
                                     or 'Could not find or load main class' in result.stderr):
            self.skipTest('Java JRE lacks JDK source launcher')
        self.assertEqual(result.returncode,0,result.stderr)
        response=json.loads(result.stdout)
        self.assertEqual(response['contract'],'hermes.purpose.v1')
        self.assertEqual(response['purpose'],'development')
        self.assertFalse(response['executed'])

    def test_dashboard_includes_clickable_purpose_preview(self):
        with urllib.request.urlopen(self.base+'/',timeout=5) as response:
            html=response.read().decode('utf-8')
        self.assertIn('HERMES · ADAPTIVE PURPOSE FUNNEL',html)
        self.assertIn('purpose-preview',html)
        self.assertIn('/api/v1/purpose-requests',html)


if __name__=='__main__': unittest.main()
