import argparse, json, sys
from pathlib import Path
from .core import FrameShift, Ledger
from .recursive import RecursiveReview, to_dict
from .junkrat import JunkratLab, report_markdown
from .construct import analyze_text, solve_linear, solve_construct, caesar_sweep
from .asymmetric import solve as solve_asymmetric


def main() -> int:
    p = argparse.ArgumentParser(prog="frameshift", description="FrameShift Lab: voice, exploration, world-state, evidence ledger")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("say", help="Ask Bazza for commentary (voice only)"); s.add_argument("text")
    h = sub.add_parser("hypothesis", help="Record an exploratory hypothesis"); h.add_argument("text")
    c = sub.add_parser("commit", help="Promote a hypothesis to canon with explicit confirmation")
    c.add_argument("claim_id"); c.add_argument("--evidence", required=True); c.add_argument("--confirm", action="store_true")
    d = sub.add_parser("dispute", help="Mark a claim disputed"); d.add_argument("claim_id"); d.add_argument("--reason", required=True)
    r = sub.add_parser("reject", help="Reject a claim"); r.add_argument("claim_id"); r.add_argument("--reason", required=True)
    rv = sub.add_parser("review", help="Run three passes across all three profiles")
    rv.add_argument("text", help="Task or question to review")
    j = sub.add_parser("junkrat", help="Run bounded recursive adversarial audit against this project")
    j.add_argument("--rounds", type=int, default=3)
    j.add_argument("--out", default="JUNKRAT_AUDIT.md")
    lg = sub.add_parser("lingua", help="Inspect linguistic and symbolic patterns without assuming a hidden code"); lg.add_argument("text", help="Text to analyze")
    sc = sub.add_parser("construct", help="Generate candidate transformations for a clue or text"); sc.add_argument("text", help="Clue text")
    eq = sub.add_parser("equation", help="Solve a linear equation with one variable"); eq.add_argument("expression", help="Equation such as 2*(x+3)=14"); eq.add_argument("--variable", default="x")
    cs = sub.add_parser("caesar", help="Enumerate all Caesar shifts"); cs.add_argument("text", help="Ciphertext")
    ab = sub.add_parser("asymmetric", help="Run asymmetric bilateral abductive reasoning")
    ab.add_argument("--text", required=True, help="Text or multiline construct")
    ab.add_argument("--clue", default="", help="Explicit clue that justifies a transformation")
    ab.add_argument("--expected", default=None, help="Optional evaluator constraint; use for tests, not blind discovery")
    ab.add_argument("--max-results", type=int, default=12)
    sub.add_parser("inspect", help="Show current ledger-derived state")
    sub.add_parser("events", help="Show append-only event history")
    a = p.parse_args(); app = FrameShift(Ledger())
    try:
        if a.cmd == "review": print(json.dumps(to_dict(RecursiveReview().run(a.text)), indent=2, ensure_ascii=False))
        elif a.cmd == "junkrat":
            report = JunkratLab(a.rounds).run(Path(__file__).resolve().parent.parent)
            out = Path(a.out); out.write_text(report_markdown(report), encoding="utf-8")
            print(json.dumps({"report": str(out), "rounds": report["rounds"], "attack_records": report["total_attack_records"], "summary": report["summary"]}, indent=2))
        elif a.cmd == "lingua": print(json.dumps(analyze_text(a.text), indent=2, ensure_ascii=False))
        elif a.cmd == "construct": print(json.dumps(solve_construct(a.text), indent=2, ensure_ascii=False))
        elif a.cmd == "equation": print(json.dumps(solve_linear(a.expression, a.variable), indent=2, ensure_ascii=False))
        elif a.cmd == "caesar": print(json.dumps(caesar_sweep(a.text), indent=2, ensure_ascii=False))
        elif a.cmd == "asymmetric": print(json.dumps(solve_asymmetric(a.text, clue=a.clue, expected=a.expected, max_results=a.max_results), indent=2, ensure_ascii=False))
        elif a.cmd == "say": print(app.say(a.text))
        elif a.cmd == "hypothesis": print(app.hypothesis(a.text))
        elif a.cmd == "commit": app.commit(a.claim_id, a.evidence, a.confirm); print("Promoted to canon.")
        elif a.cmd == "dispute": app.dispute(a.claim_id, a.reason); print("Marked disputed.")
        elif a.cmd == "reject": app.reject(a.claim_id, a.reason); print("Rejected.")
        elif a.cmd == "inspect": print(json.dumps(app.inspect(), indent=2, ensure_ascii=False))
        elif a.cmd == "events": print(json.dumps(app.ledger.events, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, PermissionError, KeyError) as e:
        print(f"ERROR: {e}", file=sys.stderr); return 2

if __name__ == "__main__": raise SystemExit(main())
