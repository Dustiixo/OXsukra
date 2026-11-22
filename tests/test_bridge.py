"""Read-only IXO -> Ocean export and tamper-refusal tests."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from bridge.export_ixo_snapshot import (canonical, export_snapshot, position_for_entry,
                                         position_for_project, save_snapshot, sha256)


def fake_g04_store(root: Path) -> tuple[Path, str]:
    root.mkdir(parents=True, exist_ok=True)
    workbench = root / "workbench"
    (workbench / "blobs").mkdir(parents=True)
    project_id, entry_id, source_id = "a" * 32, "b" * 32, "c" * 32
    original = b"The exact native IXO original source."
    source_sha = hashlib.sha256(original).hexdigest()
    (workbench / "blobs" / source_sha).write_bytes(original)
    wb = sqlite3.connect(workbench / "workbench.sqlite3")
    wb.execute("CREATE TABLE sources (id TEXT, sha256 TEXT, size INTEGER, mime TEXT, name TEXT)")
    wb.execute("INSERT INTO sources VALUES (?,?,?,?,?)", (source_id, source_sha, len(original), "text/plain", "capture.md"))
    wb.commit()
    wb.close()
    db = sqlite3.connect(root / "ixo.sqlite3")
    db.execute("CREATE TABLE projects (id TEXT, name TEXT, description TEXT, created_at TEXT)")
    db.execute("CREATE TABLE entries (id TEXT,project_id TEXT,title TEXT,kind TEXT,state TEXT,next_step TEXT,source_kind TEXT,source_id TEXT,source_sha256 TEXT,tags_json TEXT,created_at TEXT,updated_at TEXT)")
    db.execute("CREATE TABLE journal (seq INTEGER,event_id TEXT,at TEXT,entry_id TEXT,action TEXT,detail_json TEXT,previous_sha256 TEXT,event_sha256 TEXT)")
    db.execute("CREATE TABLE links (id TEXT,left_id TEXT,right_id TEXT,reason TEXT)")
    db.execute("INSERT INTO projects VALUES (?,?,?,?)", (project_id, "Ocean", "Native project", "2026-11-17"))
    db.execute("INSERT INTO entries VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (entry_id, project_id,
               "Signal", "artifact", "blocked", "", "manual", source_id, source_sha,
               '["ixo"]', "2026-11-17", "2026-11-17"))
    detail = {"workbench_source_id": source_id}
    content = {"event_id": "d" * 32, "at": "2026-11-17", "entry_id": entry_id,
               "action": "captured", "detail": detail, "previous_sha256": "0" * 64}
    db.execute("INSERT INTO journal VALUES (?,?,?,?,?,?,?,?)", (1, content["event_id"], content["at"],
               content["entry_id"], content["action"], json.dumps(detail), content["previous_sha256"],
               sha256(canonical(content))))
    db.commit()
    db.close()
    return root, entry_id


class SnapshotTests(unittest.TestCase):
    def test_valid_source_yields_stable_ids_and_private_default(self):
        with tempfile.TemporaryDirectory() as temp:
            root, entry_id = fake_g04_store(Path(temp) / "ixo")
            result = export_snapshot(root)
            self.assertEqual(result["schema"], "echofold.ocean.snapshot.g0.1")
            self.assertEqual(len(result["entries"]), 1)
            self.assertEqual(result["entries"][0]["id"], entry_id)
            self.assertEqual(result["journal_events_verified"], 1)
            self.assertNotIn("original_excerpt", result["entries"][0])
            self.assertEqual(result["state_id"], export_snapshot(root)["state_id"])
            self.assertIn("The exact native IXO", export_snapshot(root, include_excerpts=True)["entries"][0]["original_excerpt"])

    def test_positions_stable_from_identity(self):
        a = "a" * 32
        anchor = position_for_project(a)
        self.assertEqual(anchor, position_for_project(a))
        self.assertEqual(position_for_entry("b" * 32, anchor), position_for_entry("b" * 32, anchor))

    def test_tampered_blob_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _ = fake_g04_store(Path(temp) / "ixo")
            blob = next((root / "workbench" / "blobs").iterdir())
            blob.write_bytes(b"different content")
            with self.assertRaisesRegex(ValueError, "SHA-256|mismatch"):
                export_snapshot(root)

    def test_modified_event_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root, _ = fake_g04_store(Path(temp) / "ixo")
            db = sqlite3.connect(root / "ixo.sqlite3")
            db.execute("UPDATE journal SET action='changed'")
            db.commit()
            db.close()
            with self.assertRaisesRegex(ValueError, "journal verification failed"):
                export_snapshot(root)

    def test_projection_never_overwrites_without_explicit_request(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "projection.json"
            save_snapshot({"schema": "test"}, target)
            with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
                save_snapshot({"schema": "other"}, target)
            self.assertEqual(json.loads(target.read_text())["schema"], "test")
            save_snapshot({"schema": "replaced"}, target, force=True)
            self.assertEqual(json.loads(target.read_text())["schema"], "replaced")


if __name__ == "__main__":
    unittest.main()
