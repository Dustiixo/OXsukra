"""Atomic state + event ledger; detects changed records and state snapshots.

This is tamper-evident relative to a retained hash, NOT tamper-proof, and NOT a
cryptographically signed audit trail. Database writes are single-transaction.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import contextmanager, closing
from datetime import datetime, timezone
from pathlib import Path

ZERO = "0" * 64


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj):
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class ConflictError(RuntimeError):
    pass


class Ledger:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.db = self.root / "events.sqlite"

    @contextmanager
    def connect(self):
        if not self.db.exists():
            raise FileNotFoundError(f"No FlowMesh session at {self.root}")
        con = sqlite3.connect(self.db, timeout=8)
        con.execute("PRAGMA busy_timeout=8000")
        try:
            with con:
                yield con
        finally:
            con.close()

    @classmethod
    def create(cls, root: Path, initial: dict):
        root = Path(root)
        if root.exists() and any(root.iterdir()):
            raise FileExistsError(f"Won't initialize over existing files: {root}")
        root.mkdir(parents=True, exist_ok=True)
        (root / "sources").mkdir(exist_ok=False)
        obj = cls(root)
        with closing(sqlite3.connect(obj.db)) as con, con:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute("CREATE TABLE snapshots (singleton INTEGER PRIMARY KEY CHECK(singleton=1), revision INTEGER NOT NULL, state_json TEXT NOT NULL, state_hash TEXT NOT NULL)")
            con.execute("CREATE TABLE events (seq INTEGER PRIMARY KEY AUTOINCREMENT, stamp TEXT NOT NULL, payload TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL)")
            con.execute("CREATE INDEX idx_event_stamp ON events(stamp)")
            con.execute("INSERT INTO snapshots VALUES (1, 0, ?, ?)", (canonical(initial), digest(initial)))
        obj.save(initial, 0, [{"type": "session_created", "goal": initial["goal"], "mode": initial["mode"]}])
        return obj

    def read(self):
        with self.connect() as con:
            row = con.execute("SELECT revision, state_json, state_hash FROM snapshots WHERE singleton=1").fetchone()
            if row is None:
                raise RuntimeError("Missing session state")
            rev, raw, claimed = row
            state = json.loads(raw)
            if digest(state) != claimed:
                raise ValueError("Session snapshot hash mismatch")
            return state, rev

    def save(self, state: dict, expected_revision: int, events: list[dict]):
        if not events:
            raise ValueError("Every state transition must leave an event")
        raw_state = canonical(state)
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT revision FROM snapshots WHERE singleton=1").fetchone()
            if row is None or row[0] != expected_revision:
                raise ConflictError("Session changed in another process; reload before retrying")
            previous = con.execute("SELECT hash FROM events ORDER BY seq DESC LIMIT 1").fetchone()
            prev = previous[0] if previous else ZERO
            for event in events + [{"type": "snapshot_committed", "revision": expected_revision + 1, "state_sha256": digest(state)}]:
                if len(canonical(event)) > 16000:
                    raise ValueError("Event exceeds maximum record size")
                stamp = now()
                payload = canonical(event)
                h = hashlib.sha256((prev + "\n" + stamp + "\n" + payload).encode("utf-8")).hexdigest()
                con.execute("INSERT INTO events(stamp,payload,prev_hash,hash) VALUES (?,?,?,?)", (stamp, payload, prev, h))
                prev = h
            con.execute("UPDATE snapshots SET revision=?,state_json=?,state_hash=? WHERE singleton=1", (expected_revision + 1, raw_state, digest(state)))
        return prev

    def events(self):
        with self.connect() as con:
            return [{"seq": seq, "stamp": stamp, **json.loads(payload), "receipt": h} for seq, stamp, payload, h in con.execute("SELECT seq,stamp,payload,hash FROM events ORDER BY seq")]

    def verify(self):
        with self.connect() as con:
            rows = list(con.execute("SELECT seq,stamp,payload,prev_hash,hash FROM events ORDER BY seq"))
            current = con.execute("SELECT revision,state_json,state_hash FROM snapshots WHERE singleton=1").fetchone()
        prev = ZERO
        next_seq = 1
        final_commit = None
        for seq, stamp, payload, linked_prev, event_hash in rows:
            if seq != next_seq or linked_prev != prev:
                raise ValueError(f"Broken chain or missing event at seq {next_seq}")
            if hashlib.sha256((prev + "\n" + stamp + "\n" + payload).encode("utf-8")).hexdigest() != event_hash:
                raise ValueError(f"Receipt mismatch at seq {seq}")
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid ledger payload") from exc
            if data.get("type") == "snapshot_committed":
                final_commit = data
            prev, next_seq = event_hash, next_seq + 1
        if not current or not final_commit:
            raise ValueError("Missing state commit")
        revision, raw_state, stored_hash = current
        if digest(json.loads(raw_state)) != stored_hash or final_commit.get("state_sha256") != stored_hash or final_commit.get("revision") != revision:
            raise ValueError("Latest snapshot does not match ledger commit")
        return {"events": len(rows), "last_hash": prev, "revision": revision, "state_hash": stored_hash, "integrity": "PASS", "limitations": "locally tamper-evident, unsigned"}
