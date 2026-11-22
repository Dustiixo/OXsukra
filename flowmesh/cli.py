"""FlowMesh command surface: no shell commands or execution tools."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from . import engine
from .ledger import Ledger


def _pretty(value):
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def demo(root: Path):
    """Deterministic offline acceptance scenario with no hidden network/model calls."""
    here = Path(__file__).resolve().parent.parent
    engine.start(root, "Explore MIDI DAW generation prompt timelines, agent probe allocation, and resource orchestration", budget=6)
    for item in sorted((here / "example_sources").glob("*.md")):
        engine.add_source(root, item)
    before = engine.read(root)["session_id"]
    a = engine.step(root, count=2)
    branch_ids = [x for x in engine.read(root)["branches"] if x != "root"]
    if not branch_ids:
        raise AssertionError("Auto probe did not launch")
    # User can interrupt the middle of research, hold a branch, reallocate, restore.
    child = branch_ids[0]
    if engine.read(root)["branches"][child]["status"] == "active":
        engine.park(root, child)
        parked_explicitly = True
    else:
        parked_explicitly = False
    engine.revise(root, "Probe the cost of keeping a generation pathway open while a later prompt arrives")
    b = engine.step(root, count=2)
    if engine.read(root)["branches"][child]["status"] == "parked":
        engine.wake(root, child)
        restored = True
    else:
        restored = False
    c = engine.step(root, count=2)
    report = {"schema": "ixo.flowmesh.demo.v1", "session_unchanged": before == engine.read(root)["session_id"],
              "first_probe": child, "user_parked_branch": parked_explicitly,
              "resumed_branch": restored, "ticks": len(a + b + c),
              "integrity": engine.verify(root), "final_state": engine.view(root),
              "important_limit": "Offline rule-driven probes, not proof of model comprehension or live OS orchestration"}
    result = root / "DEMO_PROOF.json"
    result.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description="IXO FlowMesh M0.1 | adaptive research probes, safe by default")
    sp = p.add_subparsers(dest="command", required=True)
    for cmd in ("demo", "init", "step", "status", "verify", "events", "probe", "park", "wake", "focus", "revise", "add-source", "gui"):
        sub = sp.add_parser(cmd)
        sub.add_argument("--root", required=True, type=Path)
        if cmd == "init":
            sub.add_argument("--goal", required=True)
            sub.add_argument("--mode", choices=("offline", "ollama"), default="offline")
            sub.add_argument("--model", default=None, help="Explicit local Ollama model; localhost:11434 only")
            sub.add_argument("--budget", type=int, default=6)
        elif cmd == "step":
            sub.add_argument("--count", type=int, default=1)
        elif cmd == "events":
            sub.add_argument("--limit", type=int, default=60)
        elif cmd == "probe":
            sub.add_argument("--question", required=True)
            sub.add_argument("--parent", default="root")
            sub.add_argument("--importance", type=float, default=1)
        elif cmd in ("park", "wake", "focus"):
            sub.add_argument("--branch", required=True)
        elif cmd == "revise":
            sub.add_argument("--text", required=True)
        elif cmd == "add-source":
            sub.add_argument("--file", required=True, type=Path)
    args = p.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command == "init":
            output = engine.start(root, args.goal, args.mode, args.model, args.budget)
        elif args.command == "demo":
            output = demo(root)
        elif args.command == "step":
            output = engine.step(root, args.count)
        elif args.command == "status":
            output = engine.view(root)
        elif args.command == "verify":
            output = engine.verify(root)
        elif args.command == "events":
            output = Ledger(root).events()[-max(1, min(200, args.limit)):]
        elif args.command == "probe":
            output = engine.spawn(root, args.question, args.parent, args.importance)
        elif args.command == "park":
            output = engine.park(root, args.branch)
        elif args.command == "wake":
            output = engine.wake(root, args.branch)
        elif args.command == "focus":
            output = engine.set_focus(root, args.branch)
        elif args.command == "revise":
            output = engine.revise(root, args.text)
        elif args.command == "add-source":
            output = engine.add_source(root, args.file)
        elif args.command == "gui":
            from .desktop import open_desktop
            open_desktop(root)
            return
        _pretty(output)
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"FLOWMESH STOP: {exc}", file=sys.stderr)
        sys.exit(2)
