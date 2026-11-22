import json
import tempfile
import unittest
from pathlib import Path
from frameshift.core import FrameShift, Ledger

class FrameShiftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "events.jsonl"
        self.app = FrameShift(Ledger(self.path))
    def tearDown(self): self.tmp.cleanup()

    def test_hypothesis_is_not_automatically_canon(self):
        cid = self.app.hypothesis("map is a memory index")
        self.assertEqual(self.app.ledger.latest_claims()[cid]["status"], "hypothesis")

    def test_commit_requires_confirmation(self):
        cid = self.app.hypothesis("candidate fact")
        with self.assertRaises(PermissionError): self.app.commit(cid, "some evidence", False)
        self.assertEqual(self.app.ledger.latest_claims()[cid]["status"], "hypothesis")

    def test_commit_requires_evidence(self):
        cid = self.app.hypothesis("candidate fact")
        with self.assertRaises(ValueError): self.app.commit(cid, "  ", True)

    def test_explicit_commit_records_evidence_and_event(self):
        cid = self.app.hypothesis("candidate fact")
        self.app.commit(cid, "reproduced in three test cases", True)
        claim = self.app.ledger.latest_claims()[cid]
        self.assertEqual(claim["status"], "canon")
        self.assertIn("reproduced in three test cases", claim["evidence"])

    def test_disputed_claim_cannot_be_promoted(self):
        cid = self.app.hypothesis("candidate fact")
        self.app.dispute(cid, "counterexample exists")
        with self.assertRaises(ValueError): self.app.commit(cid, "even more evidence", True)

    def test_bazza_commentary_does_not_create_claim(self):
        before = len(self.app.ledger.latest_claims())
        self.app.say("What if the wizard knows everything?")
        self.assertEqual(len(self.app.ledger.latest_claims()), before)

    def test_identity_separate_from_world_state(self):
        view = self.app.inspect()
        self.assertIn("invariant", view["wizard_identity"])
        self.assertIn("scene", view["world_state"])
        self.assertNotEqual(view["wizard_identity"], view["world_state"])

    def test_ledger_reloads_after_restart(self):
        cid = self.app.hypothesis("persist me")
        restarted = FrameShift(Ledger(self.path))
        self.assertIn(cid, restarted.ledger.latest_claims())

    def test_event_log_lines_are_valid_json(self):
        self.app.hypothesis("json valid")
        rows = [json.loads(line) for line in self.path.read_text(encoding='utf-8').splitlines()]
        self.assertTrue(all("event_id" in row and "kind" in row for row in rows))

if __name__ == "__main__": unittest.main()
