"""Produce genuine IXO G0.4 records in a new disposable test directory.

This is an explicit demo creation tool; export_ixo_snapshot.py remains read-only.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from export_ixo_snapshot import export_snapshot, save_snapshot


def seed(ixo_code: Path, new_data_dir: Path, output: Path) -> dict:
    if new_data_dir.exists():
        raise ValueError("Demo IXO data target already exists; refusing overwrite")
    if not (ixo_code / "engine.py").is_file():
        raise ValueError("--ixo-code must point to an existing G0.4 native source folder")
    new_data_dir.parent.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ixo_code.resolve()))
    from engine import IXO  # Imported only for explicitly requested disposable demo creation.

    with IXO(new_data_dir) as ixo:
        world = ixo.project("ECHOFOLD Ocean", "Freeform movement through original IXO project identities")
        core = ixo.project("IXO Control Spine", "Industrial feedback applied to persistent project work")
        entry_a = ixo.capture(world["id"], "Zero-gravity navigation",
                              "Left stick translates; right stick orients; triggers ascend/descend; bumpers roll.",
                              kind="discovery", tags=["echofold", "6dof"],
                              next_step="Test gamepad axes on ASUS")
        entry_b = ixo.capture(world["id"], "Opris breadcrumb return",
                              "Opening a node must preserve a path back to the exact prior camera transform.",
                              kind="idea", tags=["opris", "continuity"],
                              next_step="Prove enter then B returns to prior pose")
        entry_c = ixo.capture(world["id"], "Controller focus boundary",
                              "IXO must not react to a controller while a game or unrelated app is focused.",
                              kind="blocker", tags=["controller", "focus"], next_step="")
        ixo.progress(entry_c["id"], state="blocked", note="Unverified on the ASUS gamepad/Steam environment")
        ixo.link(entry_a["id"], entry_b["id"], "Human-reviewed navigation-to-continuity dependency", approved=True)
        ixo.capture(core["id"], "Native IXO feedback loop",
                    "One-shot blocked-record scan, pending proposal, operator review, native readback and receipt.",
                    kind="discovery", tags=["ixo", "industrial"],
                    next_step="Preserve isolated IC0.1 evidence")
        ixo.capture(core["id"], "Protected broker R11RF6",
                    "Real autonomous external effects remain blocked until dispatch and concurrency fixes pass.",
                    kind="blocker", tags=["safety", "broker"],
                    next_step="Verify protected broker before integration")
        check = ixo.verify()
        if not check["ok"]:
            raise ValueError("Native G0.4 could not verify its seeded source and event history")
    projection = export_snapshot(new_data_dir, include_excerpts=True)
    save_snapshot(projection, output)
    return {"projects": len(projection["projects"]), "entries": len(projection["entries"]),
            "native_verify_ok": check["ok"], "source_integrity": projection["source_integrity"],
            "journal_events_verified": projection["journal_events_verified"],
            "state_id": projection["state_id"]}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ixo-code", type=Path, required=True)
    p.add_argument("--new-data", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    try:
        print(seed(a.ixo_code, a.new_data, a.output))
    except (ValueError, OSError) as e:
        print("DEMO ERROR:", e, file=sys.stderr)
        raise SystemExit(2)
