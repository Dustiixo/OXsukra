"""Read-only re-execution and independent comparison of the saved game proof."""
from __future__ import annotations

import json
from pathlib import Path

from feeding_time import BASELINE, ROOT, run_game, sha


def main() -> None:
    receipt = json.loads((ROOT / "proof" / "EXTERNAL_GAME_ACCEPTANCE.json").read_text())
    mod = ROOT / "proof" / "open_door.brew.json"
    assert sha(BASELINE.read_bytes()) == receipt["original_source_sha256"], "baseline mutated"
    assert sha(mod.read_bytes()) == receipt["native_export_sha256"], "export bytes mutated"
    for phase, path, approved in [
        ("before", BASELINE, receipt["original_source_sha256"]),
        ("after", mod, receipt["native_export_sha256"]),
        ("restore", BASELINE, receipt["original_source_sha256"]),
    ]:
        returncode, live, log = run_game(path, approved)
        assert returncode == 0, f"{phase} failed: {log}"
        assert live == receipt[phase], f"{phase} differs from saved receipt"
    print("EXTERNAL_GAME_RECEIPT VERIFIED: source -> exported mod -> original; 3 independent physics runs")


if __name__ == "__main__":
    main()
