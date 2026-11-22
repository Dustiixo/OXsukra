"""Adaptive budgeted agent scheduler with durable evidence and controlled branching.

Every action is a typed state transition, persisted with an audit receipt. The
research backend does not control scheduling, permissions or external programs.
"""
from __future__ import annotations
import math
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from .ledger import Ledger, now
from .sources import import_source, confirm_excerpt, tokens
from .workers import source_candidates, OllamaBackend

MAX_BRANCHES = 12
MAX_ACTIVE = 5
MAX_EVIDENCE = 75
MAX_MODEL_CALLS_PER_TICK = 2


def _branch(id_, parent, question, tick, kind="probe", importance=1.0):
    return {"id": id_, "parent": parent, "question": question, "kind": kind,
            "status": "active", "importance": float(importance), "spent": 0,
            "seen": [], "failed_reads": 0, "gain": 0.0, "score": 0.0,
            "wake_count": 0, "created_tick": tick, "last_work_tick": -1,
            "parked_reason": None, "analyses": []}


def _save(root, state, rev, events):
    Ledger(root).save(state, rev, events)
    return state


def start(root, goal, mode="offline", model=None, budget=6):
    goal = goal.strip()
    if not 5 <= len(goal) <= 1200:
        raise ValueError("Goal needs 5–1200 characters")
    if mode not in ("offline", "ollama"):
        raise ValueError("Mode must be offline or ollama")
    if mode == "ollama":
        OllamaBackend(model)
    elif model:
        raise ValueError("Offline mode cannot silently configure a model")
    if not 2 <= budget <= 20:
        raise ValueError("Per-tick work budget must be 2–20")
    state = {"schema": "ixo.flowmesh.v1", "session_id": uuid.uuid4().hex, "goal": goal,
             "mode": mode, "model": model, "tick": 0, "budget_per_tick": budget,
             "branches": {"root": _branch("root", None, goal, 0, "main", 2.0)},
             "next_branch": 1, "focus": "root", "findings": [], "links": [], "prompts": [
                 {"tick": 0, "kind": "original", "text": goal, "at": now()}],
             "spawned_questions": [], "last_allocation": {}, "last_run": []}
    Ledger.create(root, state)
    return state


def read(root):
    return Ledger(root).read()[0]


def _mutate(root, func):
    state, rev = Ledger(root).read()
    events = func(state)
    if events:
        _save(root, state, rev, events)
    return state


def _can_spawn(state, question):
    question = question.strip()
    signature = " ".join(sorted(tokens(question)))
    if not signature or len(question) < 12 or len(question) > 360:
        raise ValueError("Probe question must contain a meaningful 12–360 character statement")
    if signature in state["spawned_questions"]:
        raise ValueError("Duplicate research question; reuse its previous branch")
    if len(state["branches"]) >= MAX_BRANCHES:
        raise ValueError("Session branch limit reached")
    if sum(b["status"] == "active" for b in state["branches"].values()) >= MAX_ACTIVE:
        raise ValueError("Active probe limit reached. Park a branch before starting another")
    return signature


def _spawn(state, parent, question, reason, importance=1.0):
    if parent not in state["branches"]:
        raise ValueError("Unknown parent branch")
    signature = _can_spawn(state, question)
    bid = f"p{state['next_branch']:03d}"
    state["next_branch"] += 1
    state["spawned_questions"].append(signature)
    state["branches"][bid] = _branch(bid, parent, question.strip(), state["tick"], importance=importance)
    return {"type": "probe_launched", "branch": bid, "parent": parent, "question": question.strip(), "reason": reason}


def spawn(root, question, parent="root", importance=1.0):
    if not 0.5 <= importance <= 3:
        raise ValueError("Importance must be 0.5–3")
    return _mutate(root, lambda s: [_spawn(s, parent, question, "user_requested", importance)])


def park(root, branch, reason="user_parked"):
    def change(s):
        b = s["branches"].get(branch)
        if not b or b["status"] != "active":
            raise ValueError("Only active branches can be parked")
        b["status"], b["parked_reason"] = "parked", reason
        if s["focus"] == branch:
            s["focus"] = "root"
        return [{"type": "branch_parked", "branch": branch, "reason": reason}]
    return _mutate(root, change)


def wake(root, branch):
    def change(s):
        b = s["branches"].get(branch)
        if not b or b["status"] != "parked":
            raise ValueError("Only parked branches can be woken")
        if sum(x["status"] == "active" for x in s["branches"].values()) >= MAX_ACTIVE:
            raise ValueError("Active limit reached")
        b["status"], b["parked_reason"] = "active", None
        b["failed_reads"] = 0
        b["wake_count"] += 1
        return [{"type": "branch_reactivated", "branch": branch, "reason": "user_requested"}]
    return _mutate(root, change)


def set_focus(root, branch):
    def change(s):
        if branch not in s["branches"]:
            raise ValueError("Unknown branch")
        s["focus"] = branch
        return [{"type": "focus_shifted", "branch": branch}]
    return _mutate(root, change)


def revise(root, text):
    text = text.strip()
    if not 3 <= len(text) <= 1200:
        raise ValueError("Revision needs 3–1200 characters")
    def change(s):
        s["prompts"].append({"tick": s["tick"], "kind": "revision", "text": text, "at": now()})
        b = s["branches"][s["focus"]]
        # Revisions are preserved as separate objects, never overwrite the original request.
        if b["status"] == "parked" and sum(x["status"] == "active" for x in s["branches"].values()) < MAX_ACTIVE:
            b["status"], b["parked_reason"], b["failed_reads"] = "active", None, 0
            return [{"type": "prompt_revision", "branch": b["id"], "text": text},
                    {"type": "branch_reactivated", "branch": b["id"], "reason": "new_prompt"}]
        return [{"type": "prompt_revision", "branch": b["id"], "text": text}]
    return _mutate(root, change)


def add_source(root, path):
    # Source import is the only optional user-directed file-write operation,
    # scoped exclusively to the workspace's sources folder.
    result = import_source(root, path)
    def change(s):
        events = [{"type": "source_imported", **result}]
        # Dormant branches become eligible for reactivation if the new source
        # is relevant AND hasn't been consumed by that branch yet.
        from .sources import retrieve
        room = MAX_ACTIVE - sum(b["status"] == "active" for b in s["branches"].values())
        for b in s["branches"].values():
            if room <= 0:
                break
            if b["status"] == "parked" and b["parked_reason"] == "no_new_evidence" and b["wake_count"] < 3:
                relevant = retrieve(root, b["question"], set(b["seen"]), limit=1)
                if relevant and relevant[0]["source_sha256"] == result["sha256"]:
                    b["status"], b["parked_reason"], b["failed_reads"] = "active", None, 0
                    b["wake_count"] += 1
                    room -= 1
                    events.append({"type": "branch_reactivated", "branch": b["id"], "reason": "new_relevant_source"})
        return events
    _mutate(root, change)
    return result


def _automatic_leads(goal):
    text = goal.lower()
    candidates = []
    if any(v in text for v in ("midi", "daw", "music")):
        candidates.append(("MIDI event timing scheduling notes and capability mapping", "missing_timing_evidence"))
    if any(v in text for v in ("generat", "prompt", "timeline")):
        candidates.append(("Generation prompt timelines revisions latency and prepared future work", "parallel_independent_question"))
    if any(v in text for v in ("agent", "probe", "ferrofluid", "fungal", "orchestrat", "resource")):
        candidates.append(("Agent probe budgets evidence verification and dormant branch reactivation", "possible_resource_advantage"))
    return candidates


def _weight(branch, focus):
    # Human focus and observed NEW evidence influence allocation. Model enthusiasm
    # or narrative certainty is deliberately excluded from scoring.
    weight = max(0.2, branch["importance"] + min(branch["gain"] * 1.5, 3.0) - 0.45 * branch["failed_reads"])
    if branch["id"] == focus:
        weight += 1.5
    if branch["kind"] == "main":
        weight += 0.6
    return weight


def allocate(state):
    active = [b for b in state["branches"].values() if b["status"] == "active"]
    budget = state["budget_per_tick"]
    if not active:
        return {}
    weights = {b["id"]: _weight(b, state["focus"]) for b in active}
    alloc = {b["id"]: 0 for b in active}
    # One work unit per active branch only if the budget allows it; otherwise
    # give those units to the highest scores. The rest are largest remainders.
    sorted_keys = sorted(weights, key=lambda k: (-weights[k], k))
    for key in sorted_keys[:min(budget, len(active))]:
        alloc[key] += 1
    remaining = budget - sum(alloc.values())
    if remaining:
        total = sum(weights.values())
        quotas = {k: remaining * v / total for k, v in weights.items()}
        for k, q in quotas.items():
            alloc[k] += math.floor(q)
        leftover = budget - sum(alloc.values())
        for k in sorted(weights, key=lambda k: (-(quotas[k] - math.floor(quotas[k])), k))[:leftover]:
            alloc[k] += 1
    return alloc


def _add_verified_evidence(state, branch, excerpt):
    # The claim is an exact source quote. The event is NOT a scientific truth verdict.
    finding = {"id": excerpt["id"], "branch": branch["id"], "file": excerpt["file"],
               "source_sha256": excerpt["source_sha256"], "excerpt_sha256": excerpt["excerpt_sha256"],
               "text": excerpt["text"], "relevance": excerpt["relevance"], "tick": state["tick"]}
    branch["seen"].append(excerpt["id"])
    if len(state["findings"]) >= MAX_EVIDENCE:
        return {"type": "evidence_capacity_reached", "branch": branch["id"], "source_id": excerpt["id"]}
    novel = all(x["id"] != excerpt["id"] for x in state["findings"])
    if novel:
        state["findings"].append(finding)
        branch["gain"] = min(4, branch["gain"] + 1.0 + excerpt["relevance"])
        branch["failed_reads"] = 0
    else:
        branch["gain"] = max(0, branch["gain"] - .2)
        # Cross-branch evidence edges for genuine shared source, not made-up insight.
        other = next((x for x in state["findings"] if x["id"] == excerpt["id"]), None)
        if other and other["branch"] != branch["id"]:
            link = {"a": other["branch"], "b": branch["id"], "source_id": excerpt["id"]}
            if link not in state["links"]:
                state["links"].append(link)
    return {"type": "source_excerpt_verified", "branch": branch["id"],
            "source_id": excerpt["id"], "source_sha256": excerpt["source_sha256"],
            "novel": novel, "relevance": excerpt["relevance"]}


def _reactivate_via_discovery(state, excerpt, discovering_branch):
    """Fungal recirculation: wake exhausted pathways when NEW evidence is relevant.

    Never override a user's deliberate PARK or a model failure. The same source
    cannot reawaken a branch that already examined it. Auto-wake has a cap.
    """
    events = []
    capacity = MAX_ACTIVE - sum(b["status"] == "active" for b in state["branches"].values())
    if capacity <= 0:
        return events
    excerpt_terms = tokens(excerpt["text"])
    for branch in state["branches"].values():
        if capacity == 0:
            break
        if branch["id"] == discovering_branch or branch["status"] != "parked":
            continue
        if branch["parked_reason"] != "no_new_evidence" or branch["wake_count"] >= 3:
            continue
        if excerpt["id"] in branch["seen"]:
            continue
        overlap = tokens(branch["question"]) & excerpt_terms
        if len(overlap) < 2:
            continue
        branch["status"], branch["parked_reason"], branch["failed_reads"] = "active", None, 0
        branch["wake_count"] += 1
        capacity -= 1
        events.append({"type": "branch_reactivated", "branch": branch["id"],
                       "reason": "peer_discovery", "trigger_source_id": excerpt["id"]})
    return events


def _work_once(root, state, branch, backend):
    question = branch["question"]
    # The prompt revision is active context, not automatic retroactive replacement.
    revisions = [p["text"] for p in state["prompts"] if p["tick"] <= state["tick"] and p["kind"] == "revision"]
    if revisions and branch["id"] == state["focus"]:
        question += " | Latest revision: " + revisions[-1][:200]
    docs = source_candidates(root, question, branch["seen"])
    events = []
    if docs:
        source = docs[0]
        if not confirm_excerpt(root, source):
            raise ValueError("Source changed before verification")
        events.append(_add_verified_evidence(state, branch, source))
        if events[-1].get("novel"):
            events.extend(_reactivate_via_discovery(state, source, branch["id"]))
        branch["failed_reads"] = 0
    else:
        branch["failed_reads"] += 1
        branch["gain"] = max(0, branch["gain"] - 0.7)
        events.append({"type": "source_gap", "branch": branch["id"], "attempt": branch["failed_reads"]})
    branch["last_work_tick"] = state["tick"]
    branch["spent"] += 1  # charge even when a model times out or returns invalid data
    if backend is not None:
        # One bounded actual LLM request per allocated unit. A failure records
        # the error and parks this branch; no fabricated answer is produced.
        try:
            proposal = backend.interpret(question, docs)
        except Exception as exc:
            events.append({"type": "model_unavailable", "branch": branch["id"], "error": type(exc).__name__, "message": str(exc)[:220]})
            branch["status"], branch["parked_reason"] = "parked", "model_error"
            return events
        branch["analyses"].append({"tick": state["tick"], **proposal})
        events.append({"type": "model_analysis_proposed", "branch": branch["id"],
                       "analysis": proposal["analysis"], "uncertainty": proposal["uncertainty"]})
        for question2 in proposal["suggested_probes"][:1]:
            try:
                events.append(_spawn(state, branch["id"], question2, "llm_suggested_uncertainty"))
            except ValueError:
                pass
    elif branch["kind"] == "main" and branch["spent"] == 1:
        # Not fake AI reasoning. Explicit fixed rules propose first probes;
        # the ledger labels them as heuristic triggers, not model decisions.
        for q, reason in _automatic_leads(state["goal"]):
            try:
                events.append(_spawn(state, "root", q, "heuristic_" + reason))
            except ValueError:
                pass
    if branch["failed_reads"] >= 2:
        branch["status"], branch["parked_reason"] = "parked", "no_new_evidence"
        events.append({"type": "branch_parked", "branch": branch["id"], "reason": "no_new_evidence"})
    return events


def _run_model_jobs(root, state, backend):
    """Run at most 2 independent agent requests concurrently outside DB locks.

    A user may revise or park a branch while these jobs are in flight. Results
    carry the input context version and are revalidated before incorporation.
    """
    allocation = allocate(state)
    jobs = sorted((k for k, v in allocation.items() if v > 0),
                  key=lambda k: (-_weight(state["branches"][k], state["focus"]), k))[:MAX_MODEL_CALLS_PER_TICK]
    if not jobs:
        return {}
    prepared = {}
    for bid in jobs:
        branch = state["branches"][bid]
        question = branch["question"]
        revisions = [p["text"] for p in state["prompts"] if p["kind"] == "revision"]
        if bid == state["focus"] and revisions:
            question += " | Latest revision: " + revisions[-1][:200]
        docs = source_candidates(root, question, branch["seen"])
        prepared[bid] = {"question": question, "docs": docs, "prompt_count": len(state["prompts"]),
                         "original_question": branch["question"]}
    results = {}
    with ThreadPoolExecutor(max_workers=len(prepared), thread_name_prefix="flowmesh-probe") as pool:
        futures = {pool.submit(backend.interpret, data["question"], data["docs"]): bid for bid, data in prepared.items()}
        for future in as_completed(futures):
            bid = futures[future]
            data = prepared[bid]
            try:
                data["outcome"] = future.result()
            except Exception as exc:
                data["error"] = f"{type(exc).__name__}: {str(exc)[:180]}"
            results[bid] = data
    return results


class _CompletedBackend:
    def __init__(self, outcome):
        self.outcome = outcome
    def interpret(self, question, docs):
        if "error" in self.outcome:
            raise RuntimeError(self.outcome["error"])
        return self.outcome["outcome"]


def step(root, count=1, backend_override=None):
    """One bounded work cycle per tick; model reasoning is parallel and read-only.

    The scheduler commits *after* model requests, allowing prompt revisions or
    branch parking to happen while Ollama works. A stale model result is never
    silently applied after user changes the context.
    """
    if not 1 <= count <= 100:
        raise ValueError("Step count must be 1–100")
    outputs = []
    for _ in range(count):
        snapshot = read(root)
        backend = backend_override if backend_override is not None else (OllamaBackend(snapshot["model"]) if snapshot["mode"] == "ollama" else None)
        prepared = _run_model_jobs(root, snapshot, backend) if backend is not None else {}
        # Re-read after long-running requests, so human revisions survive.
        s, rev = Ledger(root).read()
        s["tick"] += 1
        allocation = allocate(s)
        events = [{"type": "resource_allocation", "tick": s["tick"], "credits": allocation,
                   "total_credits": sum(allocation.values()), "maximum": s["budget_per_tick"]}]
        executed = []
        delivered = set()
        for bid, granted in allocation.items():
            branch = s["branches"][bid]
            for _q in range(granted):
                if branch["status"] != "active":
                    break
                invoke = None
                if bid in prepared and bid not in delivered:
                    delivered.add(bid)
                    job = prepared[bid]
                    if (job["prompt_count"] != len(s["prompts"]) or
                            job["original_question"] != branch["question"]):
                        events.append({"type": "model_result_stale", "branch": bid,
                                       "reason": "input_changed_while_processing"})
                    else:
                        invoke = _CompletedBackend(job)
                events.extend(_work_once(root, s, branch, invoke))
                executed.append(bid)
        for bid in prepared:
            if bid not in delivered:
                events.append({"type": "model_result_discarded", "branch": bid,
                               "reason": "branch_not_scheduled_after_changes"})
        s["last_allocation"] = allocation
        s["last_run"] = executed
        for b in s["branches"].values():
            b["gain"] = round(max(0, b["gain"] * 0.85), 4)
            b["score"] = round(_weight(b, s["focus"]), 3) if b["status"] == "active" else 0
        events.append({"type": "tick_finished", "tick": s["tick"], "units_executed": len(executed),
                       "model_calls": len(prepared),
                       "active": [b["id"] for b in s["branches"].values() if b["status"] == "active"]})
        _save(root, s, rev, events)
        outputs.append({"tick": s["tick"], "allocated": allocation, "executed": executed,
                        "model_calls": len(prepared), "new_events": [x["type"] for x in events]})
    return outputs


def verify(root):
    obj = Ledger(root).verify()
    state = read(root)
    if state["schema"] != "ixo.flowmesh.v1":
        raise ValueError("Invalid state schema")
    if len(state["branches"]) > MAX_BRANCHES:
        raise ValueError("Exceeded branch cap")
    for f in state["findings"]:
        if not confirm_excerpt(root, f):
            raise ValueError("Evidence source missing or altered: " + f["id"])
    obj.update({"branches": len(state["branches"]), "verified_source_excerpts": len(state["findings"]),
                "tick": state["tick"], "source_references_checked": True})
    return obj


def view(root):
    state = read(root)
    return {"session": state["session_id"], "tick": state["tick"], "mode": state["mode"],
            "goal": state["goal"], "focus": state["focus"], "budget": state["budget_per_tick"],
            "active": sum(b["status"] == "active" for b in state["branches"].values()),
            "branches": [{"id": b["id"], "parent": b["parent"], "status": b["status"],
                          "spent": b["spent"], "score": b["score"], "question": b["question"],
                          "last_gain": round(b["gain"], 3), "parked_reason": b["parked_reason"]}
                         for b in state["branches"].values()],
            "allocations": state["last_allocation"], "findings": len(state["findings"]),
            "prompts": len(state["prompts"]), "links": len(state["links"])}
