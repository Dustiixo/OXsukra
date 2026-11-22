import copy
import unittest

from governance_router import GovernanceError, prepare_handoff, review, scope_digest


def packet():
    return {
        "schema": "ox.governance.decision.v0",
        "decision_id": "D-001",
        "origin_owner": "IXO",
        "target_owner": "BuildFactory",
        "action_ref": "proposal://change-17",
        "impact": "cross-owner code modification",
        "question": "Should the change be promoted?",
        "affected_owner_refs": ["owner://IXO", "owner://BuildFactory"],
        "lenses": {
            n: {"state": "reported", "method": "recorded session", "summary": n,
                "evidence_refs": ["evidence://%s" % n], "dissent_refs": []}
            for n in ("direct", "deliberative", "liquid", "participatory")
        },
    }


class GovernanceTests(unittest.TestCase):
    def test_all_lenses_considered_no_auto_winner(self):
        result = review(packet())
        self.assertEqual(result["status"], "AWAITING_HUMAN_AUTHORITY")
        self.assertIsNone(result["automatic_winner"])
        self.assertFalse(result["authorized"])

    def test_pending_blocks_handoff(self):
        item = packet()
        item["lenses"]["liquid"] = {"state": "pending"}
        self.assertEqual(review(item)["status"], "NEEDS_REVIEW")
        with self.assertRaisesRegex(GovernanceError, "all four lenses"):
            prepare_handoff(item, {"receipt_ref": "signed://R", "scope_digest": scope_digest(item)},
                            registered_owners={"BuildFactory"}, verify_human_approval=lambda a, d: True)

    def test_waiver_requires_reason(self):
        item = packet()
        item["lenses"]["liquid"] = {"state": "not_applicable"}
        with self.assertRaisesRegex(GovernanceError, "waiver reason"):
            review(item)
        item["lenses"]["liquid"]["reason"] = "No delegates registered for this matter"
        self.assertEqual(review(item)["waived_lenses"], ["liquid"])

    def test_dissent_survives_handoff(self):
        item = packet()
        item["lenses"]["participatory"]["dissent_refs"] = ["objection://O-4"]
        digest = scope_digest(item)
        handoff = prepare_handoff(item, {"receipt_ref": "signed://R-3", "scope_digest": digest},
                                  registered_owners={"BuildFactory"},
                                  verify_human_approval=lambda a, d: a["scope_digest"] == d)
        self.assertEqual(handoff["execution_status"], "NOT_EXECUTED")
        self.assertEqual(handoff["dissent_by_lens"], {"participatory": ["objection://O-4"]})
        self.assertEqual(handoff["review_status"], "CONTESTED_HUMAN_REVIEW")

    def test_scope_tamper_invalidates_approval(self):
        item = packet()
        old = scope_digest(item)
        item["action_ref"] = "proposal://different"
        with self.assertRaisesRegex(GovernanceError, "exact decision scope"):
            prepare_handoff(item, {"receipt_ref": "signed://R", "scope_digest": old},
                            registered_owners={"BuildFactory"}, verify_human_approval=lambda a, d: True)

    def test_changed_review_invalidates_approval(self):
        item = packet()
        old = scope_digest(item)
        item["lenses"]["direct"]["summary"] = "Changed after approval"
        with self.assertRaisesRegex(GovernanceError, "exact decision scope"):
            prepare_handoff(item, {"receipt_ref": "signed://R", "scope_digest": old},
                            registered_owners={"BuildFactory"}, verify_human_approval=lambda a, d: True)

    def test_unverified_or_unknown_owner_denied(self):
        item = packet()
        approval = {"receipt_ref": "signed://R", "scope_digest": scope_digest(item)}
        with self.assertRaisesRegex(GovernanceError, "unregistered owner"):
            prepare_handoff(item, approval, registered_owners={"Other"},
                            verify_human_approval=lambda a, d: True)
        with self.assertRaisesRegex(GovernanceError, "independently verified"):
            prepare_handoff(item, approval, registered_owners={"BuildFactory"},
                            verify_human_approval=lambda a, d: False)

    def test_bad_evidence_or_extra_lens_rejected(self):
        item = packet()
        item["lenses"]["direct"]["evidence_refs"] = []
        with self.assertRaisesRegex(GovernanceError, "evidence reference"):
            review(item)
        item = packet()
        item["lenses"]["expert_override"] = {"state": "reported"}
        with self.assertRaisesRegex(GovernanceError, "exactly four"):
            review(item)


if __name__ == "__main__":
    unittest.main()
