"""Read-only, independently checked G0.4 IXO -> ECHOFOLD Ocean projection.

No IXO engine import, database writes, model calls, file launches or network IO.
The output is a disposable *projection*, never a second source of authority.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import sqlite3
import tempfile


SCHEMA = "echofold.ocean.snapshot.g0.1"
MAX_SOURCE_BYTES = 12 * 1024 * 1024


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def readonly_database(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise ValueError(f"Missing IXO database: {path.name}")
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def stable_vector(identifier: str, radius: float) -> list[float]:
    raw = hashlib.sha256(identifier.encode("utf-8")).digest()
    coordinates = [int.from_bytes(raw[x:x + 4], "big") / 0xFFFFFFFF * 2 - 1 for x in (0, 4, 8)]
    length = math.sqrt(sum(x * x for x in coordinates)) or 1.0
    return [round(x / length * radius, 3) for x in coordinates]


def position_for_project(project_id: str) -> list[float]:
    return stable_vector("project:" + project_id, 14.0)


def position_for_entry(entry_id: str, anchor: list[float]) -> list[float]:
    delta = stable_vector("entry:" + entry_id, 3.0 + int(entry_id[:2], 16) / 85.0)
    return [round(base + offset, 3) for base, offset in zip(anchor, delta)]


def verified_journal(connection: sqlite3.Connection) -> tuple[str, dict[str, str], int]:
    previous = "0" * 64
    captured_sources: dict[str, str] = {}
    count = 0
    for event in connection.execute("SELECT event_id,at,entry_id,action,detail_json,previous_sha256,event_sha256 FROM journal ORDER BY seq"):
        try:
            detail = json.loads(event["detail_json"])
        except json.JSONDecodeError as error:
            raise ValueError("Malformed IXO journal JSON") from error
        fields = {"event_id": event["event_id"], "at": event["at"], "entry_id": event["entry_id"],
                  "action": event["action"], "detail": detail, "previous_sha256": previous}
        if event["previous_sha256"] != previous or sha256(canonical(fields)) != event["event_sha256"]:
            raise ValueError("IXO journal verification failed at event " + str(count + 1))
        if event["action"] == "captured":
            if not isinstance(detail, dict) or not isinstance(detail.get("workbench_source_id"), str):
                raise ValueError("Captured event lacks its original Workbench source ID")
            if event["entry_id"] in captured_sources:
                raise ValueError("Duplicate captured event for one IXO entry")
            captured_sources[event["entry_id"]] = detail["workbench_source_id"]
        previous = event["event_sha256"]
        count += 1
    return previous, captured_sources, count


def export_snapshot(data_dir: Path, *, max_entries: int = 80, include_excerpts: bool = False) -> dict:
    data_dir = Path(data_dir).resolve()
    if not 1 <= max_entries <= 500:
        raise ValueError("max_entries must be between 1 and 500")
    with readonly_database(data_dir / "ixo.sqlite3") as core, \
            readonly_database(data_dir / "workbench" / "workbench.sqlite3") as workbench:
        head, captured_sources, journal_count = verified_journal(core)
        projects = []
        anchors = {}
        for row in core.execute("SELECT id,name,description,created_at FROM projects ORDER BY id"):
            anchor = position_for_project(row["id"])
            anchors[row["id"]] = anchor
            projects.append({"id": row["id"], "kind": "project", "name": row["name"],
                             "description": row["description"][:280], "created_at": row["created_at"],
                             "position": anchor})
        entries = []
        selected = core.execute(
            "SELECT id,project_id,title,kind,state,next_step,source_kind,source_id,source_sha256,tags_json,created_at,updated_at "
            "FROM entries ORDER BY updated_at DESC,id LIMIT ?", (max_entries,)).fetchall()
        for row in selected:
            if row["project_id"] not in anchors:
                raise ValueError("IXO entry references a missing project")
            source_id = captured_sources.get(row["id"])
            if source_id is None:
                raise ValueError("IXO entry lacks a captured Workbench receipt")
            source = workbench.execute("SELECT id,sha256,size,mime,name FROM sources WHERE id=?", (source_id,)).fetchone()
            if source is None or source["sha256"] != row["source_sha256"] or source["size"] > MAX_SOURCE_BYTES:
                raise ValueError("IXO source metadata mismatch or unexpected source size")
            blob = data_dir / "workbench" / "blobs" / source["sha256"]
            if not blob.is_file() or blob.is_symlink():
                raise ValueError("Missing or unsafe immutable source blob")
            content = blob.read_bytes()
            if len(content) != source["size"] or sha256(content) != row["source_sha256"]:
                raise ValueError("IXO immutable source failed SHA-256 verification")
            try:
                tags = json.loads(row["tags_json"])
            except json.JSONDecodeError as error:
                raise ValueError("Invalid original IXO tag JSON") from error
            entry = {"id": row["id"], "project_id": row["project_id"], "kind": "entry",
                     "title": row["title"], "entry_kind": row["kind"], "state": row["state"],
                     "next_step": row["next_step"], "source_id": source_id,
                     "source_sha256": row["source_sha256"], "tags": tags,
                     "created_at": row["created_at"], "updated_at": row["updated_at"],
                     "position": position_for_entry(row["id"], anchors[row["project_id"]])}
            if include_excerpts and source["mime"].startswith("text/") and b"\x00" not in content[:512]:
                try:
                    entry["original_excerpt"] = content.decode("utf-8")[:360]
                except UnicodeDecodeError:
                    pass
            entries.append(entry)
        entry_ids = {entry["id"] for entry in entries}
        edges = []
        for row in core.execute("SELECT left_id,right_id,reason FROM links ORDER BY id"):
            if row["left_id"] in entry_ids and row["right_id"] in entry_ids:
                edges.append({"from": row["left_id"], "to": row["right_id"],
                              "reason": row["reason"][:200]})
    payload = {"schema": SCHEMA, "source": "IXO Convergence G0.4 read-only projection",
               "generated_at_utc": datetime.now(timezone.utc).isoformat(),
               "source_label": data_dir.name, "journal_head_sha256": head,
               "journal_events_verified": journal_count, "source_integrity": "VERIFIED_SELECTED_ENTRIES",
               "includes_source_excerpts": include_excerpts,
               "projects": projects, "entries": entries, "approved_links": edges,
               "authority": {"data_mutation": False, "agent_execution": False, "source_db_is_authoritative": True}}
    # Stable identity for resume even when exported at different times.
    payload["state_id"] = sha256(canonical({"journal_head": head, "entries": [e["id"] for e in entries]}))
    return payload


def save_snapshot(payload: dict, path: Path, *, force: bool = False) -> None:
    path = Path(path).resolve()
    if path.exists() and not force:
        raise ValueError("Refusing to overwrite an existing projection (use --replace-projection)")
    if not path.parent.is_dir():
        raise ValueError("Projection destination directory must already exist")
    raw = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".ocean-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a read-only ECHOFOLD Ocean projection from real IXO G0.4 storage")
    parser.add_argument("--ixo-data", required=True, type=Path, help="Existing G0.4 data directory (never modified)")
    parser.add_argument("--output", required=True, type=Path, help="A separate JSON projection file")
    parser.add_argument("--max-entries", type=int, default=80)
    parser.add_argument("--include-excerpts", action="store_true", help="Opt in to exporting original text snippets")
    parser.add_argument("--replace-projection", action="store_true", help="Allow replacement of a previous projection only")
    args = parser.parse_args()
    try:
        data_dir, output = args.ixo_data.resolve(), args.output.resolve()
        if output.is_relative_to(data_dir):
            raise ValueError("Projection must be outside the authoritative IXO data directory")
        payload = export_snapshot(data_dir, max_entries=args.max_entries,
                                  include_excerpts=args.include_excerpts)
        save_snapshot(payload, output, force=args.replace_projection)
        print(json.dumps({"ok": True, "projects": len(payload["projects"]),
                          "entries": len(payload["entries"]),
                          "journal_events_verified": payload["journal_events_verified"],
                          "state_id": payload["state_id"], "output": str(output)}, indent=2))
        return 0
    except (ValueError, sqlite3.Error, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
