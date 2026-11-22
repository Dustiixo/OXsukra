"""Bounded, deterministic cross-process fuzzing for the G0.3.1 Godot contract.

Launches a fresh external Godot game process for *every* case. The mini-game
is purpose-built; this never modifies or launches a third-party game.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "external_godot_target"
SOURCE = ROOT / "examples" / "door_trigger.brew.json"
SENTINEL = "EXTERNAL_GAME_RESULT "
REJECTED = "EXTERNAL_GAME_REJECTED "


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def case_data(index: int, baseline: dict) -> tuple[str, bytes, bool, str | None]:
    """Return label, bytes, should-accept, expected effect."""
    variant = index % 16
    doc = json.loads(json.dumps(baseline))
    effect = ("closed", "open", "highlight")[(index // 3) % 3]
    doc["behavior"]["effect"] = effect
    doc["behavior"]["duration_ms"] = (index * 479) % 60001
    if variant <= 3:
        return "valid_%s" % effect, json.dumps(doc, sort_keys=True).encode(), True, effect
    if variant == 4:
        doc["behavior"]["effect"] = "execute_script"
        label = "unknown_effect"
    elif variant == 5:
        doc["behavior"]["execute"] = "not_an_allowed_instruction"
        label = "unknown_nested_field"
    elif variant == 6:
        doc["spawn_process"] = "not_an_allowed_instruction"
        label = "unknown_root_field"
    elif variant == 7:
        doc["behavior"]["duration_ms"] = -1
        label = "negative_duration"
    elif variant == 8:
        doc["behavior"]["duration_ms"] = 60001
        label = "excess_duration"
    elif variant == 9:
        doc["behavior"]["trigger"] = "every_frame"
        label = "unknown_trigger"
    elif variant == 10:
        return "broken_json", b'{"schema": "invalid', False, None
    elif variant == 11:
        return "too_large", b"{" + b" " * 262145 + b"}", False, None
    elif variant == 12:
        label = "wrong_approved_digest"
    elif variant == 13:
        doc["behavior"]["duration_ms"] = True
        label = "boolean_duration"
    elif variant == 14:
        del doc["behavior"]
        label = "missing_behavior"
    else:
        doc["behavior"]["duration_ms"] = 0.25
        label = "fractional_duration"
    return label, json.dumps(doc, sort_keys=True).encode(), False, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=int, default=128)
    parser.add_argument("--budget-seconds", type=float, default=90)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not 1 <= args.cases <= 256 or not 5 <= args.budget_seconds <= 120:
        parser.error("cases must be 1..256; budget must be 5..120 seconds")
    godot = os.environ.get("DEEPBREW_GODOT_BIN") or shutil.which("godot")
    if not godot:
        raise RuntimeError("Godot executable required; no simulated passes")
    source_bytes = SOURCE.read_bytes()
    baseline = json.loads(source_bytes)
    source_sha = digest(source_bytes)
    start = time.monotonic()
    passed = 0
    failed: list[dict] = []
    accepted = 0
    rejected = 0
    with tempfile.TemporaryDirectory(prefix="deepbrew_external_bounded_") as tmp:
        root = Path(tmp)
        for index in range(args.cases):
            if time.monotonic() - start >= args.budget_seconds:
                failed.append({"case": index, "reason": "wall-clock budget exceeded"})
                break
            label, data, should_accept, effect = case_data(index, baseline)
            path = root / ("case_%03d.brew.json" % index)
            path.write_bytes(data)
            approved = digest(data)
            if label == "wrong_approved_digest":
                approved = "0" * 64 if approved != "0" * 64 else "f" * 64
            argv = [godot, "--headless", "--path", str(GAME),
                    "--script", "scripts/acceptance.gd", "--", str(path), approved]
            try:
                process = subprocess.run(argv, capture_output=True, text=True,
                                         timeout=min(5.0, max(0.1, args.budget_seconds - (time.monotonic() - start))),
                                         check=False)
            except subprocess.TimeoutExpired:
                failed.append({"case": index, "kind": label, "reason": "process timeout"})
                break
            output = process.stdout + "\n" + process.stderr
            markers = [line[len(SENTINEL):] for line in output.splitlines() if line.startswith(SENTINEL)]
            denials = [line for line in output.splitlines() if line.startswith(REJECTED)]
            observed = None
            if markers:
                try:
                    observed = json.loads(markers[-1])
                except json.JSONDecodeError:
                    pass
            if should_accept:
                ok = (process.returncode == 0 and observed is not None and
                      observed.get("state") == effect and
                      observed.get("door_visible") == (effect != "open") and
                      observed.get("entry_events") == 1 and
                      observed.get("player_entered") is True and
                      observed.get("accepted") is True and
                      observed.get("runtime") == "external_godot_physics_area3d" and
                      observed.get("approved_sha256") == approved)
                if ok:
                    accepted += 1
            else:
                ok = process.returncode != 0 and observed is None and bool(denials)
                if ok:
                    rejected += 1
            if ok:
                passed += 1
            else:
                failed.append({"case": index, "kind": label, "returncode": process.returncode,
                               "output_tail": output[-600:]})
            if index % 16 == 15 and digest(SOURCE.read_bytes()) != source_sha:
                failed.append({"case": index, "reason": "source changed during stress"})
                break
    elapsed = round(time.monotonic() - start, 3)
    final_source_sha = digest(SOURCE.read_bytes())
    if final_source_sha != source_sha:
        failed.append({"reason": "source digest differs at completion"})
    report = {
        "schema": "ixo.deepbrew.studio.bounded_external_stress.g0.3.1",
        "engine": "Godot external_godot_target, launched in a fresh process per case",
        "not_a_third_party_game": True,
        "cases_requested": args.cases,
        "cases_passed": passed,
        "accepted_physics_cases": accepted,
        "rejected_hostile_cases": rejected,
        "failures": failed,
        "wall_seconds": elapsed,
        "wall_budget_seconds": args.budget_seconds,
        "source_sha256_before_and_after": source_sha if final_source_sha == source_sha else None,
        "passed": passed == args.cases and not failed,
    }
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
