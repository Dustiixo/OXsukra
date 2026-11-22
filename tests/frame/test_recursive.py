import tempfile
import unittest
from pathlib import Path
from frameshift.recursive import RecursiveReview, PROFILES, TransparentDemoBackend
from frameshift.core import Ledger, FrameShift

class RecursiveReviewTests(unittest.TestCase):
    def test_three_passes_over_three_profiles(self):
        result = RecursiveReview().run("How do we test recursive cognition?")
        self.assertEqual(result.synthesis["pass_count"], 3)
        self.assertEqual(result.synthesis["profile_count"], 3)
        self.assertEqual(len(result.assessments), 27)  # 3 questions x 3 profiles x 3 passes
        self.assertEqual({a.pass_number for a in result.assessments}, {1, 2, 3})
        self.assertEqual({a.profile for a in result.assessments}, set(PROFILES))

    def test_provenance_and_lineage_present(self):
        result = RecursiveReview().run("test input")
        self.assertTrue(all(a.source_hash == result.input_hash for a in result.assessments))
        self.assertTrue(all(a.assessment_id for a in result.assessments))
        self.assertTrue(all(a.parent_ids for a in result.assessments if a.pass_number > 1))

    def test_synthesis_does_not_claim_auto_mutation(self):
        result = RecursiveReview().run("test input")
        self.assertFalse(result.synthesis["auto_mutation"])
        self.assertTrue(result.limitations)

    def test_repeat_is_deterministic_for_same_input(self):
        a = RecursiveReview().run("same")
        b = RecursiveReview().run("same")
        self.assertEqual([x.observation for x in a.assessments], [x.observation for x in b.assessments])
        self.assertEqual([x.assessment_id for x in a.assessments], [x.assessment_id for x in b.assessments])

    def test_core_ledger_still_requires_explicit_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            app = FrameShift(Ledger(Path(tmp) / "events.jsonl"))
            cid = app.hypothesis("candidate")
            with self.assertRaises(PermissionError):
                app.commit(cid, "some evidence", False)

if __name__ == "__main__": unittest.main()
