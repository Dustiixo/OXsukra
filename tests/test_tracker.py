import tempfile
import unittest
from pathlib import Path
from tracker import Tracker, fixture

class TrackerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'tracker.db'; self.now=1000
        self.t=Tracker(self.path,lambda:self.now)
    def test_opt_in_and_restart(self):
        self.assertEqual(self.t.tick(fixture),'paused')
        self.t.enable(True); self.assertEqual(self.t.tick(fixture),'ok')
        other=Tracker(self.path,lambda:self.now)
        self.assertEqual(other.tick(fixture),'waiting')
        self.now+=900; self.assertEqual(other.tick(fixture),'ok')
        other.enable(False); self.assertEqual(self.t.tick(fixture),'paused')
    def test_error_backoff_and_stale(self):
        self.t.enable(True); self.t.tick(fixture); self.now+=900
        def fail(): raise RuntimeError('secret')
        self.assertEqual(self.t.tick(fail),'error')
        self.assertEqual(self.t.status()['next_due'],self.now+1800)
        self.now+=900; self.assertTrue(self.t.status()['stale'])
        self.assertEqual(self.t.tick(fixture),'waiting')
        self.now+=900; self.assertEqual(self.t.tick(fixture),'ok')
        self.assertEqual(self.t.status()['failures'],0)
    def test_lock(self):
        self.t.enable(True); db=self.t.connect(); db.execute('BEGIN IMMEDIATE')
        try: self.assertEqual(self.t.tick(fixture),'busy')
        finally: db.close()
        self.assertEqual(self.t.tick(fixture),'ok')

class LeaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'tracker.db'; self.now=1000
        self.t=Tracker(self.path,lambda:self.now); self.t.enable(True)
    def test_fetch_does_not_hold_write_lock(self):
        def fetch():
            with self.t.connect() as db:
                db.execute('INSERT INTO history(at,outcome,detail) VALUES(?,?,?)',(self.now,'probe','outside lock'))
            self.assertTrue(self.t.status()['in_flight'])
            return fixture()
        self.assertEqual(self.t.tick(fetch),'ok')
        self.assertFalse(self.t.status()['in_flight'])
    def test_concurrent_tick_busy(self):
        other=Tracker(self.path,lambda:self.now)
        self.assertEqual(self.t.tick(lambda: {'other':other.tick(fixture)}),'ok')
        self.assertEqual(self.t.status()['observation']['other'],'busy')
    def test_expired_lease_recovery_and_late_worker(self):
        other=Tracker(self.path,lambda:self.now)
        def slow():
            self.now+=181
            self.assertEqual(other.tick(fixture),'ok')
            return {'late':True}
        self.assertEqual(self.t.tick(slow),'superseded')
        self.assertNotIn('late',self.t.status()['observation'])
    def test_pause_cancels_in_flight(self):
        self.assertEqual(self.t.tick(lambda:(self.t.enable(False),fixture())[1]),'superseded')
        self.assertFalse(self.t.status()['enabled'])
