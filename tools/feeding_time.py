"""Two independent proof meals for DeepBrew Studio G0.3.

Steak 1: the existing native editor exports a .brew.json mod, then a second,
         independently launched Godot game process physically reacts to it.
Steak 2: adversarial fixtures are submitted to that second process, including
         changed bytes, forged opcodes, bounds violations and missing files.

The runtime target is intentionally a purpose-built Godot game fixture, not
Luanti, a third-party title or a proof of arbitrary game modding.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
EXTERNAL = ROOT / "external_godot_target"
BASELINE = ROOT / "examples" / "door_trigger.brew.json"
GODOT = os.environ.get("DEEPBREW_GODOT_BIN") or shutil.which("godot")
SENTINEL = "EXTERNAL_GAME_RESULT "
REJECTED = "EXTERNAL_GAME_REJECTED "


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=25, check=False)


def run_game(mod: Path, expected: str):
    command = [GODOT, "--headless", "--path", str(EXTERNAL),
               "--script", "scripts/acceptance.gd", "--", str(mod), expected]
    process = run(command)
    combined = process.stdout + "\n" + process.stderr
    outputs = [line[len(SENTINEL):] for line in combined.splitlines() if line.startswith(SENTINEL)]
    result = json.loads(outputs[-1]) if outputs else None
    return process.returncode, result, combined


class TwoSteaks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not GODOT:
            raise RuntimeError("Native Godot executable is required; no simulated pass")
        cls.tmp = tempfile.TemporaryDirectory(prefix="deepbrew_two_steaks_")
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        cls.modified = cls.root / "open_door.brew.json"
        cls.baseline = BASELINE.read_bytes()
        cls.baseline_sha = sha(cls.baseline)
        editor_command = [GODOT, "--headless", "--path", str(ROOT),
                          "--script", "tests/export_for_runtime.gd", "--", str(cls.modified)]
        cls.export_process = run(editor_command)
        if cls.export_process.returncode != 0 or not cls.modified.exists():
            raise RuntimeError("Native editor export failed:\n" + cls.export_process.stdout + cls.export_process.stderr)
        cls.modified_bytes = cls.modified.read_bytes()
        cls.modified_sha = sha(cls.modified_bytes)

    def test_01_native_editor_really_exported(self):
        self.assertIn("DEEPBREW_NATIVE_EXPORT " + self.modified_sha, self.export_process.stdout)

    def test_02_editor_rolled_back_its_isolated_copy(self):
        self.assertIn("DEEPBREW_NATIVE_ROLLBACK " + self.baseline_sha, self.export_process.stdout)

    def test_03_original_mod_source_unchanged(self):
        self.assertEqual(BASELINE.read_bytes(), self.baseline)

    def test_04_second_game_process_observes_baseline_closed(self):
        code, observed, log = run_game(BASELINE, self.baseline_sha)
        self.assertEqual(code, 0, log)
        self.assertEqual((observed["state"], observed["door_visible"], observed["entry_events"]),
                         ("closed", True, 1))
        self.assertTrue(observed["player_entered"])
        self.assertEqual(observed["runtime"], "external_godot_physics_area3d")

    def test_05_separate_game_process_accepts_exported_open_mod(self):
        code, observed, log = run_game(self.modified, self.modified_sha)
        self.assertEqual(code, 0, log)
        self.assertEqual((observed["state"], observed["door_visible"], observed["entry_events"]),
                         ("open", False, 1))
        self.assertEqual(observed["duration_ms"], 1500)

    def test_06_original_remains_closed_after_export_and_rollback(self):
        code, observed, log = run_game(BASELINE, self.baseline_sha)
        self.assertEqual(code, 0, log)
        self.assertEqual(observed["state"], "closed")
        self.assertEqual(BASELINE.read_bytes(), self.baseline)

    def test_07_runtime_is_separate_project_without_editor_import(self):
        code = (EXTERNAL / "scripts" / "acceptance.gd").read_text()
        self.assertNotIn("mod_engine.gd", code)
        self.assertNotIn("fracture_probe.gd", code)
        self.assertNotIn("test_simulation", code)
        self.assertNotEqual((EXTERNAL / "project.godot").resolve(), (ROOT / "project.godot").resolve())

    def test_08_mutated_export_rejected_against_approved_digest(self):
        corrupt = self.root / "corrupted_export.brew.json"
        payload = bytearray(self.modified_bytes)
        payload[40] ^= 3
        corrupt.write_bytes(payload)
        code, observed, log = run_game(corrupt, self.modified_sha)
        self.assertNotEqual(code, 0, log)
        self.assertIsNone(observed)
        self.assertIn(REJECTED, log)

    def test_09_forged_digest_rejected(self):
        code, observed, log = run_game(self.modified, "0" * 64)
        self.assertNotEqual(code, 0, log)
        self.assertIsNone(observed)

    def test_10_missing_mod_file_rejected(self):
        code, observed, log = run_game(self.root / "no_such_mod.brew.json", self.modified_sha)
        self.assertNotEqual(code, 0, log)
        self.assertIsNone(observed)

    def _assert_runtime_rejects(self, doc, label):
        path = self.root / (label + ".brew.json")
        data = doc if isinstance(doc, bytes) else json.dumps(doc, sort_keys=True).encode()
        path.write_bytes(data)
        code, observed, log = run_game(path, sha(data))
        self.assertNotEqual(code, 0, f"{label}: accepted despite approved hash: {log}")
        self.assertIsNone(observed)
        self.assertIn(REJECTED, log)

    def _make(self):
        return json.loads(self.modified_bytes)

    def test_11_injected_behavior_opcode_rejected(self):
        doc = self._make()
        doc["behavior"]["effect"] = "execute_external_script"
        self._assert_runtime_rejects(doc, "injected_effect")

    def test_12_unknown_root_payload_rejected(self):
        doc = self._make()
        doc["run_command"] = "echo should_never_run"
        self._assert_runtime_rejects(doc, "unknown_root")

    def test_13_unknown_nested_instruction_rejected(self):
        doc = self._make()
        doc["behavior"]["exec"] = "new feature or malicious instruction"
        self._assert_runtime_rejects(doc, "unknown_nested")

    def test_14_overflow_duration_rejected(self):
        doc = self._make()
        doc["behavior"]["duration_ms"] = 60001
        self._assert_runtime_rejects(doc, "long_duration")

    def test_15_negative_duration_rejected(self):
        doc = self._make()
        doc["behavior"]["duration_ms"] = -1
        self._assert_runtime_rejects(doc, "negative_duration")

    def test_16_fractional_duration_rejected(self):
        doc = self._make()
        doc["behavior"]["duration_ms"] = 0.5
        self._assert_runtime_rejects(doc, "fractional_duration")

    def test_17_boolean_duration_rejected(self):
        doc = self._make()
        doc["behavior"]["duration_ms"] = True
        self._assert_runtime_rejects(doc, "boolean_duration")

    def test_18_wrong_trigger_rejected(self):
        doc = self._make()
        doc["behavior"]["trigger"] = "on_every_frame"
        self._assert_runtime_rejects(doc, "unexpected_trigger")

    def test_19_different_schema_rejected(self):
        doc = self._make()
        doc["schema"] = "deepbrew.behavior.foreign"
        self._assert_runtime_rejects(doc, "foreign_schema")

    def test_20_invalid_json_rejected_even_with_approved_digest(self):
        self._assert_runtime_rejects(b'{"schema":invalid}', "invalid_json")

    def test_21_no_behavior_rejected(self):
        doc = self._make()
        del doc["behavior"]
        self._assert_runtime_rejects(doc, "no_behavior")

    def test_22_large_payload_rejected_even_with_approved_digest(self):
        data = b"{" + b" " * 262145 + b"}"
        self._assert_runtime_rejects(data, "large_payload")

    def test_23_runtime_rejects_unparseable_digest(self):
        code, observed, log = run_game(self.modified, "nope")
        self.assertNotEqual(code, 0, log)
        self.assertIsNone(observed)

    def test_24_no_unexpected_export_write_to_original(self):
        self.assertTrue(self.modified.is_relative_to(self.root))
        self.assertNotEqual(self.modified.resolve(), BASELINE.resolve())
        self.assertEqual(BASELINE.read_bytes(), self.baseline)


if __name__ == "__main__":
    unittest.main(verbosity=2)
