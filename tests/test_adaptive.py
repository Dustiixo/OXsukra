import copy
import unittest

from governance_router import GovernanceError, recommend_route, suggest_improvements
from governance_router.adaptive import OBSERVATION_SCHEMA
from tests.test_governance_router import packet


def obs(num, workflow="IXO-review", **kwargs):
    item = {
        "schema": OBSERVATION_SCHEMA,
        "workflow_id": workflow,
        "decision_ref": f"review://{num}",
        "receipt_ref": f"receipt://{num}",
        "review_minutes": 24,
        "reopened": False,
        "missing_evidence": False,
        "clarification_needed": False,
    }
    item.update(kwargs)
    return item


class AdaptiveTests(unittest.TestCase):
    def test_no_flags_fails_closed_to_full_review(self):
        p = packet()
        self.assertEqual(recommend_route(p)["recommended_review"], "FULL_FOUR_LENS")

    def test_cross_owner_even_with_low_risk_flags(self):
        p = packet()
        p["impact_flags"] = ["routine", "read_only", "reversible"]
        result = recommend_route(p)
        self.assertEqual(result["recommended_review"], "FULL_FOUR_LENS")
        self.assertIn("DIFFERENT_OWNERS", result["reason_codes"])
        self.assertFalse(result["policy_changed"])

    def test_owner_policy_only_never_authorizes(self):
        p = packet()
        p["target_owner"] = "IXO"
        p["impact_flags"] = ["routine", "reversible"]
        result = recommend_route(p)
        self.assertEqual(result["recommended_review"], "OWNER_POLICY_ONLY")
        self.assertEqual(result["execution_status"], "NOT_AUTHORIZED")
        self.assertTrue(result["must_follow_owner_policy"])

    def test_risky_flags_escalate_even_same_owner(self):
        p = packet()
        p["target_owner"] = "IXO"
        p["impact_flags"] = ["reversible", "financial"]
        self.assertEqual(recommend_route(p)["recommended_review"], "FULL_FOUR_LENS")

    def test_unknown_flags_escalate(self):
        p = packet()
        p["target_owner"] = "IXO"
        p["impact_flags"] = ["some_untested_flag"]
        result = recommend_route(p)
        self.assertEqual(result["recommended_review"], "FULL_FOUR_LENS")
        self.assertIn("UNKNOWN_IMPACT_FLAG", result["reason_codes"])

    def test_duplicate_flags_rejected(self):
        p = packet()
        p["impact_flags"] = ["routine", "routine"]
        with self.assertRaisesRegex(GovernanceError, "duplicate"):
            recommend_route(p)

    def test_sparse_receipts_do_not_produce_advice(self):
        report = suggest_improvements([obs(1), obs(2)], verify_receipt=lambda row: True)
        row = report["workflows"][0]
        self.assertEqual(row["evidence_gate"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(row["suggested_experiments"], [])
        self.assertTrue(report["human_signoff_required"])

    def test_unverified_receipts_are_ignored(self):
        report = suggest_improvements([obs(i) for i in range(8)])
        self.assertEqual(report["verified_observations"], 0)
        self.assertEqual(report["unverified_rejected"], 8)

    def test_measurement_yields_proposals_not_policy_change(self):
        report = suggest_improvements([obs(i, missing_evidence=True, reopened=i % 2 == 0,
                                           clarification_needed=True) for i in range(6)], verify_receipt=lambda row: True)
        row = report["workflows"][0]
        self.assertEqual(row["evidence_gate"], "ENOUGH_FOR_PROPOSAL_ONLY")
        self.assertIn("TRIAL_EVIDENCE_PREFLIGHT", row["suggested_experiments"])
        self.assertIn("TRIAL_INDEPENDENT_SECOND_REVIEW", row["suggested_experiments"])
        self.assertIn("TRIAL_READ_ONLY_CONTEXT_PREFILL", row["suggested_experiments"])
        self.assertFalse(row["automatic_policy_change"])
        self.assertEqual(report["evaluation"], "DESCRIPTIVE_ONLY_NO_CAUSAL_CLAIM")

    def test_workflow_separation_no_person_scoring(self):
        report = suggest_improvements([obs(i, workflow="A", review_minutes=1) for i in range(5)] +
                                      [obs(i, workflow="B", review_minutes=22) for i in range(5)], verify_receipt=lambda row: True)
        self.assertEqual([x["workflow_id"] for x in report["workflows"]], ["A", "B"])
        self.assertFalse(report["rights_and_voting_weights_changed"])

    def test_invalid_observation_is_rejected(self):
        with self.assertRaisesRegex(GovernanceError, "review_minutes"):
            suggest_improvements([obs(0, review_minutes=float("nan"))], verify_receipt=lambda row: True)
        with self.assertRaisesRegex(GovernanceError, "schema"):
            suggest_improvements([{"schema": "wrong"}], verify_receipt=lambda row: True)
        with self.assertRaisesRegex(GovernanceError, "boolean"):
            suggest_improvements([obs(0, reopened=1)], verify_receipt=lambda row: True)

    def test_duplicate_verified_observation_rejected(self):
        with self.assertRaisesRegex(GovernanceError, "duplicate verified"):
            suggest_improvements([obs(0), obs(0)], verify_receipt=lambda row: True)

    def test_change_scope_changes_digest(self):
        p = packet()
        p["impact_flags"] = ["routine", "reversible"]
        a = recommend_route(p)["scope_digest"]
        p["impact_flags"] = ["irreversible"]
        self.assertNotEqual(a, recommend_route(p)["scope_digest"])

    def test_never_approve_on_unknown_evidence(self):
        p = packet()
        p["target_owner"] = "IXO"
        p["impact_flags"] = "not even a list"
        result = recommend_route(p)
        self.assertEqual(result["recommended_review"], "FULL_FOUR_LENS")
        self.assertEqual(result["execution_status"], "NOT_AUTHORIZED")


if __name__ == "__main__":
    unittest.main()
