"""OX Morph Lab: small, offline, event-sourced prototype-object engine.

Inspired by Self's slot objects and outliners; NOT a Self interpreter or VM.
Python standard library only. This file is the source of truth, not the canvas.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
KEY = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,39}$")
MAX_SLOTS = 40
GENESIS = "0" * 64


class WorldError(ValueError):
    pass


def canon(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def string(value, what, limit=150):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise WorldError(f"{what} must be nonempty text of at most {limit} characters")
    return value.strip()


def check_key(key):
    if not isinstance(key, str) or not KEY.fullmatch(key):
        raise WorldError("Slot names must start with a letter and contain only letters, digits, underscores (max 40)")


def check_slot(slot):
    if not isinstance(slot, dict) or set(slot) != {"kind", "value"}:
        raise WorldError("Slot must contain exactly 'kind' and 'value'")
    kind, value = slot["kind"], slot["value"]
    if kind == "value":
        if value is not None and not isinstance(value, (str, bool, int, float)):
            raise WorldError("Value slots support only text, number, boolean or null")
        if isinstance(value, str) and len(value) > 500:
            raise WorldError("Text value exceeds 500 characters")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if not math.isfinite(value) or abs(value) > 1e9:
                raise WorldError("Numeric slot must be finite and within ±1 billion")
    elif kind == "reference":
        string(value, "Reference ID", 40)
    elif kind == "formula":
        string(value, "Formula", 120)
        check_formula(value)
    else:
        raise WorldError("Supported slot kinds: value, formula, reference")


def check_formula(expr):
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise WorldError("Formula syntax error") from exc
    nodes = list(ast.walk(tree))
    if len(nodes) > 40:
        raise WorldError("Formula is too complex")
    allowed = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Name, ast.Constant,
               ast.Add, ast.Sub, ast.Mult, ast.Div, ast.USub, ast.UAdd, ast.Load)
    if any(not isinstance(n, allowed) for n in nodes):
        raise WorldError("Formulas only allow numbers, slot names, +, -, *, / and parentheses")
    for n in nodes:
        if isinstance(n, ast.Constant) and (type(n.value) not in (int, float) or
            not math.isfinite(n.value) or abs(n.value) > 1e9):
            raise WorldError("Formula constants must be finite numbers within ±1 billion")
        if isinstance(n, ast.Name):
            check_key(n.id)
    return tree


def check_object(obj, state):
    if not isinstance(obj, dict) or set(obj) != {"id", "name", "prototype", "slots"}:
        raise WorldError("Malformed object")
    string(obj["id"], "Object ID", 40)
    string(obj["name"], "Object name", 100)
    parent = obj["prototype"]
    if parent is not None and (parent not in state or parent == obj["id"]):
        raise WorldError("Prototype must reference an existing, different object")
    slots = obj["slots"]
    if not isinstance(slots, dict) or len(slots) > MAX_SLOTS:
        raise WorldError(f"At most {MAX_SLOTS} slots are supported")
    for name, spec in slots.items():
        check_key(name)
        check_slot(spec)
        if spec["kind"] == "reference" and spec["value"] not in state:
            raise WorldError(f"Reference '{name}' points to a missing object")
    seen = {obj["id"]}
    while parent is not None:
        if parent in seen:
            raise WorldError("Prototype cycle detected")
        seen.add(parent)
        parent = state[parent]["prototype"]


def validate_world(state):
    for obj in state.values():
        check_object(obj, state)


def event_hash(seq, ts, actor, action, oid, before, after, reason, prev):
    payload = {"seq": seq, "ts": ts, "actor": actor, "action": action,
               "object_id": oid, "before": before, "after": after, "reason": reason}
    return hashlib.sha256((prev + "|" + canon(payload)).encode("utf-8")).hexdigest()


class World:
    def __init__(self, db_path: str | Path, demo=True):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=3000")
        self.conn.execute("""CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY, ts TEXT NOT NULL, actor TEXT NOT NULL,
            action TEXT NOT NULL, object_id TEXT NOT NULL,
            before_json TEXT NOT NULL, after_json TEXT NOT NULL,
            reason TEXT NOT NULL, prev_hash TEXT NOT NULL, hash TEXT NOT NULL
        )""")
        self.conn.commit()
        self.verify()
        if demo and self.revision == 0:
            self._seed()

    def close(self):
        with self.lock:
            self.conn.close()

    @property
    def revision(self):
        return self.conn.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]

    def verify(self):
        with self.lock:
            rows = self.conn.execute("SELECT * FROM events ORDER BY seq").fetchall()
            prev, state = GENESIS, {}
            for expected, row in enumerate(rows, 1):
                seq, ts, actor, action, oid, b, a, reason, old_hash, new_hash = row
                if seq != expected:
                    raise WorldError(f"Event sequence gap at {expected}")
                try:
                    before, after = json.loads(b), json.loads(a)
                    # strict canonical serialization is part of the hash contract
                    if b != canon(before) or a != canon(after):
                        raise ValueError("Non-canonical JSON")
                except (ValueError, TypeError) as exc:
                    raise WorldError(f"Event {seq} contains invalid JSON") from exc
                if old_hash != prev or event_hash(seq, ts, actor, action, oid, before, after, reason, prev) != new_hash:
                    raise WorldError(f"Event {seq}: integrity chain mismatch")
                if state.get(oid) != before:
                    raise WorldError(f"Event {seq}: inconsistent before state")
                if after is None:
                    state.pop(oid, None)
                else:
                    if after.get("id") != oid:
                        raise WorldError(f"Event {seq}: object identity changed")
                    state[oid] = after
                try:
                    validate_world(state)
                except WorldError as exc:
                    raise WorldError(f"Event {seq}: {exc}") from exc
                prev = new_hash
            return state, len(rows), prev

    def _write(self, action, oid, before, after, reason, expected_revision, actor="local-human"):
        reason = string(reason, "Change reason", 250)
        if len(reason) < 3:
            raise WorldError("Explain why the object is changing (at least 3 characters)")
        with self.lock:
            state, rev, prev_hash = self.verify()
            if expected_revision is not None and expected_revision != rev:
                raise WorldError(f"Outdated revision: client {expected_revision}, world {rev}. Refresh and retry")
            if state.get(oid) != before:
                raise WorldError("Object changed since it was inspected")
            new_state = dict(state)
            if after is None:
                new_state.pop(oid, None)
            else:
                new_state[oid] = after
            validate_world(new_state)
            seq = rev + 1
            ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
            digest = event_hash(seq, ts, actor, action, oid, before, after, reason, prev_hash)
            self.conn.execute("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?)",
                              (seq, ts, actor, action, oid, canon(before), canon(after), reason, prev_hash, digest))
            self.conn.commit()
            return {"seq": seq, "hash": digest, "object_id": oid}

    def create(self, name, prototype=None, slots=None, reason="Created prototype object", expected_revision=None):
        with self.lock:
            state, _, _ = self.verify()
            oid = uuid.uuid4().hex[:12]
            while oid in state:
                oid = uuid.uuid4().hex[:12]
            obj = {"id": oid, "name": name, "prototype": prototype, "slots": slots or {}}
            return self._write("create", oid, None, obj, reason, expected_revision)

    def mutate(self, operation, oid, reason, expected_revision=None, **params):
        with self.lock:
            state, _, _ = self.verify()
            if oid not in state:
                raise WorldError("No such object")
            before = state[oid]
            after = json.loads(canon(before))
            if operation == "set_slot":
                name, slot = params.get("slot_name"), params.get("slot")
                check_key(name)
                check_slot(slot)
                after["slots"][name] = slot
            elif operation == "drop_slot":
                name = params.get("slot_name")
                if name not in after["slots"]:
                    raise WorldError("This object does not own that slot")
                del after["slots"][name]
            elif operation == "rename":
                after["name"] = params.get("name")
            elif operation == "set_prototype":
                after["prototype"] = params.get("prototype")
            else:
                raise WorldError("Unsupported mutation")
            if after == before:
                raise WorldError("No change to record")
            return self._write(operation, oid, before, after, reason, expected_revision)

    def undo_object(self, oid, reason="Reverted most recent object change", expected_revision=None):
        with self.lock:
            state, rev, _ = self.verify()
            if expected_revision is not None and expected_revision != rev:
                raise WorldError("Outdated world revision; refresh before undo")
            row = self.conn.execute("SELECT before_json FROM events WHERE object_id=? ORDER BY seq DESC LIMIT 1", (oid,)).fetchone()
            if row is None:
                raise WorldError("Object has no history")
            previous = json.loads(row[0])
            current = state.get(oid)
            if previous == current:
                raise WorldError("Nothing to revert")
            return self._write("revert", oid, current, previous, reason, expected_revision)

    def clone(self, oid, name, reason="Cloned with prototype delegation", expected_revision=None):
        with self.lock:
            state, _, _ = self.verify()
            if oid not in state:
                raise WorldError("No such object to clone")
            return self.create(name, prototype=oid, slots={}, reason=reason, expected_revision=expected_revision)

    def history(self, limit=80):
        with self.lock:
            rows = self.conn.execute("SELECT seq,ts,actor,action,object_id,reason,hash FROM events ORDER BY seq DESC LIMIT ?", (limit,)).fetchall()
            return [{"seq": r[0], "ts": r[1], "actor": r[2], "action": r[3],
                     "object_id": r[4], "reason": r[5], "hash": r[6]} for r in rows]

    def state(self):
        with self.lock:
            objects, revision, head = self.verify()
            result = {}
            for oid, obj in objects.items():
                result[oid] = {**obj, "resolved": self.resolve(oid, objects)}
            return {"version": VERSION, "revision": revision, "head": head,
                    "objects": result, "events": self.history(), "verified": True,
                    "persistence": "SQLite append-only hash-linked event history"}

    def resolve(self, oid, state=None):
        if state is None:
            state = self.verify()[0]
        if oid not in state:
            raise WorldError("Missing object")
        def find_slot(target, key):
            seen = set()
            while target is not None:
                if target in seen:
                    raise WorldError("Prototype cycle detected")
                seen.add(target)
                if key in state[target]["slots"]:
                    return state[target]["slots"][key], target
                target = state[target]["prototype"]
            return None, None
        keys = set()
        parent = oid
        while parent is not None:
            keys.update(state[parent]["slots"])
            parent = state[parent]["prototype"]
        def evaluate(key, stack=()):
            if key in stack:
                raise WorldError("Cyclic formula: " + " → ".join((*stack, key)))
            if len(stack) > 30:
                raise WorldError("Formula resolution depth exceeded")
            spec, owner = find_slot(oid, key)
            if spec is None:
                raise WorldError(f"Unknown slot '{key}'")
            if spec["kind"] != "formula":
                return spec["value"]
            def compute(node):
                if isinstance(node, ast.Expression):
                    return compute(node.body)
                if isinstance(node, ast.Constant):
                    return node.value
                if isinstance(node, ast.Name):
                    value = evaluate(node.id, (*stack, key))
                    if type(value) not in (int, float):
                        raise WorldError(f"'{node.id}' must resolve to a number")
                    return value
                if isinstance(node, ast.UnaryOp):
                    value = compute(node.operand)
                    return -value if isinstance(node.op, ast.USub) else +value
                if isinstance(node, ast.BinOp):
                    a, b = compute(node.left), compute(node.right)
                    if isinstance(node.op, ast.Add): result = a + b
                    elif isinstance(node.op, ast.Sub): result = a - b
                    elif isinstance(node.op, ast.Mult): result = a * b
                    else:
                        if b == 0: raise WorldError("Division by zero")
                        result = a / b
                    if not math.isfinite(result) or abs(result) > 1e12:
                        raise WorldError("Formula result exceeds safe numeric range")
                    return result
                raise WorldError("Unsupported formula expression")
            return compute(check_formula(spec["value"]))
        resolved = {}
        for key in sorted(keys):
            spec, owner = find_slot(oid, key)
            row = {"kind": spec["kind"], "source": owner, "inherited": owner != oid,
                   "spec": spec}
            try:
                row["value"] = evaluate(key)
            except (WorldError, OverflowError, ZeroDivisionError, TypeError) as exc:
                row["error"] = str(exc)
            resolved[key] = row
        return resolved

    def _seed(self):
        base = self.create("SIGNAL / base trait", None,
            {"bpm": {"kind": "value", "value": 120},
             "half_time": {"kind": "formula", "value": "bpm / 2"},
             "beat_ms": {"kind": "formula", "value": "60000 / bpm"},
             "intensity": {"kind": "value", "value": 1.0},
             "origin": {"kind": "value", "value": "DEMO / not an integration"}},
            reason="Seed a demonstrative parent object")["object_id"]
        pulse = self.create("VELA / pulse study", base,
            {"bpm": {"kind": "value", "value": 155},
             "motif": {"kind": "value", "value": "A moving signal in one persistent object"}},
            reason="Seed a child demonstrating inherited formulas")["object_id"]
        self.create("VELA / pulse clone", pulse,
            {"intensity": {"kind": "value", "value": 1.4}},
            reason="Seed second-level prototype delegation")
        self.create("ECHOFOLD / observer", None,
            {"target": {"kind": "reference", "value": pulse},
             "mode": {"kind": "value", "value": "Spatial perspective / illustrative"},
             "authority": {"kind": "value", "value": "read-only"}},
            reason="Seed a reference, not an inherited object")
        self.create("OPRIS / continuity note", None,
            {"target": {"kind": "reference", "value": pulse},
             "purpose": {"kind": "value", "value": "Demonstrate durable identity + change history"}},
            reason="Seed illustrative continuity reference")
