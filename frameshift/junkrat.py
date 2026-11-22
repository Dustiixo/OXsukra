"""Bounded adversarial self-application for FrameShift.

Junkrat proposes attacks against the architecture, not arbitrary shell/code execution.
Findings are candidates; no source or persistent canon is silently rewritten.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
import hashlib, json
from pathlib import Path
from typing import Any

@dataclass
class Attack:
    attack_id: str
    target: str
    exploit: str
    failure_condition: str
    severity: str
    check: str
    result: str
    evidence: str
    round_found: int

ATTACKS = [
    ("consensus-laundering", "synthesis", "Repeat the same weak claim across all profiles until it looks established.", "A claim's evidence status improves solely because it is repeated.", "critical", "repetition_is_not_evidence"),
    ("lineage-amputation", "provenance", "Drop parent IDs on later passes so a conclusion appears to have no ancestry.", "Any pass 2+ assessment has no parent lineage.", "high", "parent_lineage_required"),
    ("evaluator-mirror", "evaluation", "Use the same assumptions to generate and grade a proposal.", "The system treats self-grading as independent validation.", "high", "evaluator_independence_claimed"),
    ("recursion-runaway", "scheduler", "Keep folding the result back into itself without an information-gain stop rule.", "Run count is unbounded or no stop reason exists.", "high", "bounded_recursion"),
    ("state-poisoning", "memory", "Let a clever hypothesis mutate durable state without evidence or approval.", "Candidate hypothesis changes canon automatically.", "critical", "explicit_write_gate"),
    ("prompt-echo", "independence", "Let later branches see all prior outputs and then count agreement as independent convergence.", "Shared-context agreement is reported as independent evidence.", "medium", "correlated_votes_disclosed"),
    ("metric-gaming", "benchmark", "Optimize verbosity, agreement or number of insights instead of task outcomes.", "No held-out outcome metric distinguishes useful output from longer output.", "high", "heldout_metric_required"),
    ("profile-collapse", "profiles", "Let all profiles drift into the same role and vocabulary.", "Role separation is not represented or checked.", "medium", "profile_roles_preserved"),
    ("false-patch", "evolution", "Adopt a code or policy patch because its author claims it passed.", "A patch is accepted without a reproducible test run and diff.", "critical", "patch_requires_tests_and_review"),
    ("blind-spot-recursion", "meta-evaluation", "Ask the same evaluator to certify that its own blind spots are gone.", "Self-assessment is described as proof of correctness.", "high", "external_validation_required"),
]

class JunkratLab:
    """Recursive red-team loop. Deterministic checks audit architecture contracts."""
    def __init__(self, max_rounds: int = 3):
        if not 1 <= max_rounds <= 5:
            raise ValueError("max_rounds must be between 1 and 5")
        self.max_rounds = max_rounds

    @staticmethod
    def _id(name: str, round_no: int) -> str:
        return hashlib.sha256(f"{name}|{round_no}|frameshift-v0.3".encode()).hexdigest()[:12]

    def run(self, project_dir: str | Path) -> dict[str, Any]:
        root = Path(project_dir)
        recursive_file = root / "frameshift" / "recursive.py"
        core_file = root / "frameshift" / "core.py"
        cli_file = root / "frameshift" / "__main__.py"
        files = {"recursive": recursive_file, "core": core_file, "cli": cli_file}
        source = {k: v.read_text(encoding="utf-8") if v.exists() else "" for k,v in files.items()}
        combined = "\n".join(source.values())
        # The checks are intentionally explicit, reproducible and conservative.
        checks = {
            "repetition_is_not_evidence": "hypothesis repetition is not evidence" in combined.lower() or "does not become fact by repetition" in combined.lower() or "no hypothesis becomes fact by repetition" in combined.lower(),
            "parent_lineage_required": "parent_ids" in source["recursive"] and "parents =" in source["recursive"],
            "evaluator_independence_claimed": "independent" in combined.lower() and ("blind" in combined.lower() or "external" in combined.lower()),
            "bounded_recursion": "pass_count" in source["recursive"] and ("Stopped after three passes" in source["recursive"] or "max_rounds" in combined),
            "explicit_write_gate": "confirm" in source["core"] and "evidence" in source["core"],
            "correlated_votes_disclosed": "not independent evidence" in source["recursive"] or "correlated" in combined.lower(),
            "heldout_metric_required": "held-out" in combined.lower() or "heldout" in combined.lower(),
            "profile_roles_preserved": all(x in source["recursive"] for x in ("Junkrat", "Bazza", "Wizard")),
            "patch_requires_tests_and_review": "unittest" in (root / "README.md").read_text(encoding="utf-8").lower() if (root / "README.md").exists() else False,
            "external_validation_required": "external" in combined.lower() and "self-evaluation" in combined.lower(),
        }
        findings=[]
        for round_no in range(1, self.max_rounds+1):
            # Fold previous round findings back into the next audit, changing focus
            # from direct contract checks to second-order failure analysis.
            for name,target,exploit,failure,severity,check in ATTACKS:
                passed=checks[check]
                if round_no == 1:
                    status = "RESISTED" if passed else "VULNERABILITY"
                    evidence = f"Static contract probe: {'guard indicator found' if passed else 'guard indicator missing'} for {check}."
                elif round_no == 2:
                    status = "PARTIAL" if passed else "VULNERABILITY"
                    evidence = f"Fold-back challenge: a guard phrase in source is not proof the guard works at runtime; test contract {check} directly."
                else:
                    status = "UNPROVEN" if passed else "VULNERABILITY"
                    evidence = f"Meta-attack: static source inspection cannot establish semantic correctness; independent executable tests or held-out outcomes are required for {check}."
                findings.append(Attack(self._id(name, round_no), target, exploit, failure, severity, check, status, evidence, round_no))
        # Collapse repeated findings by attack while preserving round lineage.
        summary=[]
        for name,*rest in ATTACKS:
            rows=[asdict(x) for x in findings if x.exploit == rest[1]]
            summary.append({"attack": name, "rounds": rows, "final_status": rows[-1]["result"]})
        vulnerable=[x["attack"] for x in summary if x["final_status"] == "VULNERABILITY"]
        unproven=[x["attack"] for x in summary if x["final_status"] == "UNPROVEN"]
        return {
            "lab": "Junkrat Recursive Attack Lab", "version": "0.3.0", "project_hash": hashlib.sha256(combined.encode()).hexdigest(),
            "rounds": self.max_rounds, "attacks_per_round": len(ATTACKS), "total_attack_records": len(findings),
            "method": "static contract probes followed by two recursive fold-back challenges; no arbitrary code execution",
            "summary": {"vulnerabilities": vulnerable, "unproven_after_static_audit": unproven, "resisted_in_first_pass": [x["attack"] for x in summary if x["rounds"][0]["result"] == "RESISTED"]},
            "attacks": summary,
            "next_moves": [
                "Convert each guard indicator into a failing test by deliberately removing that guard in a disposable copy.",
                "Run the full test suite after each candidate patch; reject any patch that reduces coverage or breaks invariants.",
                "Add an actual model backend only behind a budgeted adapter; keep generated patches as diffs for human review.",
                "Use held-out tasks and an external scorer before claiming reasoning improved."
            ],
            "safety_boundary": "Junkrat may propose adversarial cases and patches; it does not execute arbitrary generated code, modify source files, or promote hypotheses to durable truth.",
        }

def report_markdown(report: dict[str, Any]) -> str:
    lines=["# Junkrat Recursive Attack Lab — v0.3", "", f"- Rounds: {report['rounds']}", f"- Attack records: {report['total_attack_records']}", f"- Project SHA-256: `{report['project_hash']}`", "", "## Verdict", "", "This is a deterministic static red-team pass, not a proof of semantic safety or intelligence.", "", "## Attack results", ""]
    for item in report["attacks"]:
        lines.append(f"### {item['attack']} — {item['final_status']}")
        lines.append(item["rounds"][0]["exploit"])
        lines.append("")
        for row in item["rounds"]:
            lines.append(f"- Round {row['round_found']}: **{row['result']}** — {row['evidence']}")
        lines.append("")
    lines += ["## Next moves", ""] + [f"{i}. {x}" for i,x in enumerate(report["next_moves"],1)] + ["", "## Boundary", "", report["safety_boundary"], ""]
    return "\n".join(lines)
