"""Acceptance suite for bounded flow, source integrity, isolation, and Ollama.

All tests are local, deterministic and do not contact models or the internet.
"""
from __future__ import annotations
import json
import sqlite3
import subprocess
import sys
import threading
import time
import tempfile
import unittest
from pathlib import Path
from contextlib import closing
from unittest.mock import patch
from flowmesh import engine
from flowmesh.ledger import Ledger, ConflictError
from flowmesh.sources import import_source, retrieve, confirm_excerpt
from flowmesh.workers import OllamaBackend

HERE = Path(__file__).resolve().parents[1]
GOAL = "Explore MIDI and generation prompt timeline agent orchestration"


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "flow"
        self.state = engine.start(self.root, GOAL)

    def add_sample(self, name="PROBE_NETWORK.md"):
        return engine.add_source(self.root, HERE / "example_sources" / name)


class StartTests(Fixture):
    def test_initial_root_and_budget(self):
        self.assertEqual(self.state["branches"]["root"]["kind"], "main")
        self.assertEqual(self.state["budget_per_tick"], 6)
        self.assertEqual(engine.verify(self.root)["integrity"], "PASS")

    def test_cannot_overwrite_existing_session(self):
        with self.assertRaises(FileExistsError):
            engine.start(self.root, GOAL)
        self.assertEqual(engine.read(self.root)["goal"], GOAL)

    def test_unknown_directory_protected(self):
        p = self.base / "user_data"
        p.mkdir()
        (p / "secret.txt").write_text("do not touch")
        with self.assertRaises(FileExistsError):
            engine.start(p, GOAL)
        self.assertEqual((p / "secret.txt").read_text(), "do not touch")

    def test_goal_and_mode_validation(self):
        with self.assertRaises(ValueError):
            engine.start(self.base / "x", "hi")
        with self.assertRaises(ValueError):
            engine.start(self.base / "x", GOAL, "unknown")
        with self.assertRaises(ValueError):
            engine.start(self.base / "x", GOAL, "offline", "model")
        with self.assertRaises(ValueError):
            engine.start(self.base / "x", GOAL, "ollama", None)
        with self.assertRaises(ValueError):
            engine.start(self.base / "x", GOAL, budget=0)

    def test_source_import_and_provenance(self):
        r = self.add_sample()
        self.assertEqual(len(r["sha256"]), 64)
        x = retrieve(self.root, "agent probe budgets evidence and verification", set())
        self.assertTrue(x)
        self.assertTrue(confirm_excerpt(self.root, x[0]))
        self.assertEqual(engine.verify(self.root)["integrity"], "PASS")

    def test_repeat_source_is_idempotent(self):
        a = self.add_sample()
        b = self.add_sample()
        self.assertEqual(a["name"], b["name"])
        self.assertTrue(b["already_present"])

    def test_sources_reject_unknown_extension(self):
        p = self.base / "bad.py"; p.write_text("print('no')")
        with self.assertRaises(ValueError):
            import_source(self.root, p)

    def test_sources_reject_oversized(self):
        p = self.base / "large.md"; p.write_text("x" * 270000)
        with self.assertRaises(ValueError):
            import_source(self.root, p)

    def test_source_symlink_rejected(self):
        p = self.base / "symlink.md"
        try:
            p.symlink_to(HERE / "example_sources" / "PROBE_NETWORK.md")
        except (OSError, NotImplementedError):
            self.skipTest("platform forbids symlinks")
        with self.assertRaises(ValueError):
            import_source(self.root, p)

    def test_invalid_utf8_import_is_actionable_and_atomic(self):
        bad = self.base / "invalid-utf8.md"
        bad.write_bytes(bytes((0xff, 0xfe, 0x80)))
        ledger_before = list(Ledger(self.root).events())
        state_before = engine.read(self.root)
        with self.assertRaisesRegex(ValueError, "Source is not valid UTF-8") as error:
            engine.add_source(self.root, bad)
        self.assertIn("try importing it again", str(error.exception))
        self.assertNotIn("codec can't decode", str(error.exception))
        self.assertEqual(list((self.root / "sources").iterdir()), [])
        self.assertEqual(Ledger(self.root).events(), ledger_before)
        self.assertEqual(engine.read(self.root), state_before)
        self.assertEqual(engine.verify(self.root)["integrity"], "PASS")

    def test_invalid_utf8_cli_explains_recovery_without_traceback(self):
        bad = self.base / "invalid-cli.md"
        bad.write_bytes(bytes((0xff, 0x80)))
        run = subprocess.run(
            [sys.executable, "-m", "flowmesh", "add-source", "--root", str(self.root), "--file", str(bad)],
            capture_output=True, text=True, cwd=HERE, check=False
        )
        self.assertEqual(run.returncode, 2)
        self.assertIn("FLOWMESH STOP: Source is not valid UTF-8", run.stderr)
        self.assertIn("Save the .md or .txt file as UTF-8", run.stderr)
        self.assertNotIn("Traceback", run.stderr)
        self.assertNotIn("codec can't decode", run.stderr)
        self.assertEqual(engine.verify(self.root)["integrity"], "PASS")

    def test_corrupt_workspace_source_is_explicit_failure(self):
        (self.root / "sources" / "damaged.md").write_bytes(bytes((0xff, 0xfe)))
        with self.assertRaisesRegex(ValueError, "Workspace source damaged.md is not valid UTF-8"):
            retrieve(self.root, "agent probe", set())

    def test_unicode_goal_and_revision(self):
        engine.revise(self.root, "New question: 🎼 what happens next?")
        self.assertIn("🎼", engine.read(self.root)["prompts"][-1]["text"])
        self.assertEqual(engine.verify(self.root)["integrity"], "PASS")


class SchedulerTests(Fixture):
    def test_heuristic_research_probes(self):
        self.add_sample()
        engine.step(self.root)
        b = engine.read(self.root)["branches"]
        self.assertGreaterEqual(len(b), 3)
        self.assertIn(b["root"]["status"], ("active", "parked"))
        self.assertTrue(any(v["status"] == "active" for k, v in b.items() if k != "root"))
        events = Ledger(self.root).events()
        self.assertTrue(any(x["type"] == "probe_launched" and x["reason"].startswith("heuristic") for x in events))

    def test_same_session_persists_after_steps(self):
        self.add_sample()
        identity = engine.read(self.root)["session_id"]
        engine.step(self.root, 3)
        self.assertEqual(engine.read(self.root)["session_id"], identity)
        self.assertEqual(engine.read(self.root)["tick"], 3)

    def test_budget_is_conserved_per_tick(self):
        for name in ("PROBE_NETWORK.md", "GENERATION_TIMELINES.md"):
            self.add_sample(name)
        for result in engine.step(self.root, count=5):
            self.assertLessEqual(sum(result["allocated"].values()), 6)
            self.assertLessEqual(len(result["executed"]), 6)

    def test_resource_reallocation_when_parked(self):
        self.add_sample()
        engine.spawn(self.root, "Agent budget allocation and evidence discovery", importance=2.0)
        before = engine.allocate(engine.read(self.root))
        engine.park(self.root, "p001")
        after = engine.allocate(engine.read(self.root))
        self.assertGreater(before["p001"], 0)
        self.assertEqual(after.get("p001", 0), 0)
        self.assertEqual(after["root"], 6)

    def test_evidence_gain_affects_budget(self):
        engine.spawn(self.root, "Agent budget allocation and evidence discovery")
        a = engine.read(self.root)
        before = engine.allocate(a)["p001"]
        a["branches"]["p001"]["gain"] = 4.0
        after = engine.allocate(a)["p001"]
        self.assertGreater(after, before)

    def test_focus_changes_weight(self):
        engine.spawn(self.root, "Agent budget allocation and evidence discovery")
        before = engine.allocate(engine.read(self.root))["p001"]
        engine.set_focus(self.root, "p001")
        after = engine.allocate(engine.read(self.root))["p001"]
        self.assertGreater(after, before)

    def test_park_and_resume(self):
        engine.spawn(self.root, "Agent budget allocation and evidence discovery")
        engine.park(self.root, "p001")
        self.assertEqual(engine.read(self.root)["branches"]["p001"]["status"], "parked")
        engine.wake(self.root, "p001")
        self.assertEqual(engine.read(self.root)["branches"]["p001"]["status"], "active")

    def test_probe_duplicate_blocked(self):
        engine.spawn(self.root, "Agent budget allocation and evidence discovery")
        with self.assertRaises(ValueError):
            engine.spawn(self.root, "Evidence discovery and agent budget allocation")

    def test_child_probe_has_parent(self):
        engine.spawn(self.root, "Agent budget allocation and evidence discovery")
        engine.spawn(self.root, "Validate reliability of recorded research evidence", parent="p001")
        self.assertEqual(engine.read(self.root)["branches"]["p002"]["parent"], "p001")

    def test_user_park_not_auto_woken_on_new_source(self):
        engine.spawn(self.root, "Agent budget allocation and evidence discovery")
        engine.park(self.root, "p001")
        self.add_sample()
        self.assertEqual(engine.read(self.root)["branches"]["p001"]["status"], "parked")

    def test_evidence_import_reawakens_exhausted_probe(self):
        engine.spawn(self.root, "Agent budget allocation evidence and verification")
        engine.step(self.root, 3)
        self.assertEqual(engine.read(self.root)["branches"]["p001"]["status"], "parked")
        self.add_sample()
        self.assertEqual(engine.read(self.root)["branches"]["p001"]["status"], "active")
        self.assertTrue(any(x["type"] == "branch_reactivated" and x["reason"] == "new_relevant_source" for x in Ledger(self.root).events()))

    def test_new_source_stays_readonly_after_import(self):
        p = HERE / "example_sources" / "PROBE_NETWORK.md"
        before = p.read_bytes()
        self.add_sample()
        engine.step(self.root)
        self.assertEqual(p.read_bytes(), before)

    def test_prompt_revision_is_append_only(self):
        engine.revise(self.root, "Look for a more useful path")
        engine.revise(self.root, "Preserve the original experiment")
        prompts = engine.read(self.root)["prompts"]
        self.assertEqual(len(prompts), 3)
        self.assertEqual(prompts[0]["text"], GOAL)

    def test_auto_cap_bounds(self):
        for i in range(4):
            engine.spawn(self.root, f"Probe {i} unique and independent evidence research task")
        with self.assertRaises(ValueError):
            engine.spawn(self.root, "Probe fifth question now that active limit is exceeded")

    def test_no_worker_without_evidence(self):
        engine.step(self.root, 3)
        events = Ledger(self.root).events()
        self.assertFalse(any(x["type"] == "source_excerpt_verified" for x in events))
        self.assertTrue(any(x["type"] == "source_gap" for x in events))

    def test_ledger_tracks_actual_allocation(self):
        self.add_sample()
        engine.step(self.root, 2)
        rows = Ledger(self.root).events()
        allocation = [x for x in rows if x["type"] == "resource_allocation"]
        self.assertEqual(len(allocation), 2)
        self.assertTrue(all(sum(x["credits"].values()) <= 6 for x in allocation))

    def test_peer_discovery_reactivation_contract(self):
        s = engine.read(self.root)
        engine.spawn(self.root, "Agent budget evidence verification")
        s = engine.read(self.root)
        s["branches"]["p001"]["status"] = "parked"
        s["branches"]["p001"]["parked_reason"] = "no_new_evidence"
        excerpt = {"id": "test:new", "text": "Agent budget evidence verification and research", "source_sha256": "ff"}
        from flowmesh.engine import _reactivate_via_discovery
        events = _reactivate_via_discovery(s, excerpt, "root")
        self.assertTrue(events)
        self.assertEqual(s["branches"]["p001"]["status"], "active")


class IntegrityTests(Fixture):
    def test_receipt_chain(self):
        self.add_sample()
        engine.step(self.root, 2)
        r = engine.verify(self.root)
        self.assertGreater(r["events"], 10)
        self.assertEqual(len(r["last_hash"]), 64)

    def test_ledger_corruption_detected(self):
        with closing(sqlite3.connect(self.root / "events.sqlite")) as c, c:
            c.execute("UPDATE events SET payload='{}' WHERE seq=1")
        with self.assertRaises(ValueError):
            engine.verify(self.root)

    def test_snapshot_corruption_detected(self):
        with closing(sqlite3.connect(self.root / "events.sqlite")) as c, c:
            c.execute("UPDATE snapshots SET state_json='{}'")
        with self.assertRaises(ValueError):
            engine.read(self.root)

    def test_deleted_source_breaks_receipt_validation(self):
        self.add_sample()
        engine.step(self.root, 1)
        self.assertTrue(engine.read(self.root)["findings"])
        for p in (self.root / "sources").iterdir():
            p.unlink()
        with self.assertRaises(ValueError):
            engine.verify(self.root)

    def test_stale_writer_conflict(self):
        store = Ledger(self.root)
        state, revision = store.read()
        engine.revise(self.root, "Another writer gets here first")
        with self.assertRaises(ConflictError):
            store.save(state, revision, [{"type": "should_not_commit"}])
        self.assertFalse(any(x["type"] == "should_not_commit" for x in store.events()))

    def test_cli_second_process_works(self):
        p = subprocess.run([sys.executable, "-m", "flowmesh", "verify", "--root", str(self.root)], cwd=HERE, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["integrity"], "PASS")


class ModelTests(Fixture):
    def test_localhost_only(self):
        backend = OllamaBackend("fake-model:latest")
        self.assertEqual(backend.url, "http://127.0.0.1:11434/api/chat")
        with self.assertRaises(ValueError):
            OllamaBackend("bad model name")

    def test_fake_model_is_proposal_not_verified_evidence(self):
        class Fake:
            def interpret(self, question, sources):
                return {"analysis": "Hypothesis: agent shifts might help", "uncertainty": "No source evidence", "suggested_probes": ["Investigate specific independent code evidence for scheduling"]}
        engine.step(self.root, backend_override=Fake())
        s = engine.read(self.root)
        self.assertEqual(s["findings"], [])
        events = Ledger(self.root).events()
        self.assertTrue(any(e["type"] == "model_analysis_proposed" for e in events))
        self.assertTrue(any(e["type"] == "probe_launched" for e in events))

    def test_bad_model_failure_parks_without_fabrication(self):
        class Broken:
            def interpret(self, question, sources):
                raise TimeoutError("no model available")
        engine.step(self.root, backend_override=Broken())
        s=engine.read(self.root)
        self.assertEqual(s["branches"]["root"]["status"], "parked")
        self.assertEqual(s["branches"]["root"]["spent"], 1)
        self.assertEqual(s["findings"], [])
        self.assertTrue(any(e["type"] == "model_unavailable" for e in Ledger(self.root).events()))

    def test_offline_never_calls_model_network(self):
        with patch("flowmesh.workers.urllib.request.build_opener", side_effect=AssertionError("network called")):
            engine.step(self.root, 1)

    def test_no_arbitrary_execution_capability(self):
        class Malicious:
            def interpret(self, question, sources):
                return {"analysis": "run rm -rf from the model!", "uncertainty": "none", "suggested_probes": ["Run shell commands and delete files immediately"]}
        sentry = self.base / "sentry.md"; sentry.write_text("safe")
        engine.step(self.root, backend_override=Malicious())
        self.assertEqual(sentry.read_text(), "safe")
        self.assertEqual(engine.read(self.root)["findings"], [])

    def test_model_work_is_capped_per_tick(self):
        class Fake:
            calls = 0
            def interpret(self, question, sources):
                self.calls += 1
                return {"analysis": "bounded proposal", "uncertainty": "unknown", "suggested_probes": []}
        fake = Fake()
        engine.spawn(self.root, "Check separate research evidence for concurrent probes")
        result = engine.step(self.root, backend_override=fake)[0]
        self.assertEqual(fake.calls, 2)
        self.assertEqual(result["model_calls"], 2)
        self.assertLessEqual(sum(result["allocated"].values()), 6)

    def test_ollama_json_response_is_bounded_and_structured(self):
        from unittest.mock import MagicMock
        response = MagicMock()
        response.status = 200
        response.read.return_value = json.dumps({"message": {"content": json.dumps({
            "analysis": "A grounded possibility", "uncertainty": "Needs actual evidence",
            "suggested_probes": ["Investigate a specific testable research gap"]})}}).encode()
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with patch("flowmesh.workers.urllib.request.build_opener", return_value=opener) as builder:
            proposal = OllamaBackend("local-model").interpret("How should probes allocate resources?", [])
        self.assertEqual(proposal["analysis"], "A grounded possibility")
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:11434/api/chat")
        self.assertEqual(json.loads(request.data)["stream"], False)
        self.assertTrue(builder.called)

    def test_two_model_agents_really_run_concurrently(self):
        engine.spawn(self.root, "Check independent probe synchronization under load")
        barrier = threading.Barrier(2, timeout=2)
        class Fake:
            def interpret(self, question, sources):
                barrier.wait()
                return {"analysis": "parallel accepted", "uncertainty": "still proposed", "suggested_probes": []}
        result = engine.step(self.root, backend_override=Fake())[0]
        self.assertEqual(result["model_calls"], 2)
        self.assertEqual(sum(x["type"] == "model_analysis_proposed" for x in Ledger(self.root).events()), 2)

    def test_user_revision_during_model_work_invalidates_stale_result(self):
        started = threading.Event()
        release = threading.Event()
        class Slow:
            def interpret(self, question, sources):
                started.set()
                if not release.wait(timeout=5):
                    raise TimeoutError("test never released model")
                return {"analysis": "old prompt result", "uncertainty": "stale", "suggested_probes": []}
        errors=[]
        def running():
            try:
                engine.step(self.root, backend_override=Slow())
            except Exception as exc:
                errors.append(str(exc))
        worker=threading.Thread(target=running, daemon=True)
        worker.start()
        self.assertTrue(started.wait(timeout=3))
        engine.revise(self.root, "Change the objective while a local LLM is still thinking")
        release.set(); worker.join(timeout=5)
        self.assertFalse(worker.is_alive())
        self.assertFalse(errors, errors)
        events=Ledger(self.root).events()
        self.assertTrue(any(x["type"] == "model_result_stale" for x in events))
        self.assertFalse(any(x["type"] == "model_analysis_proposed" for x in events))
        self.assertEqual(engine.read(self.root)["prompts"][-1]["text"], "Change the objective while a local LLM is still thinking")

    def test_user_park_during_model_call_discards_that_branch_result(self):
        started=threading.Event(); release=threading.Event()
        engine.spawn(self.root, "Independent probe scheduling and evidence collection")
        class Slow:
            def interpret(self, question, sources):
                started.set()
                if not release.wait(timeout=5):
                    raise TimeoutError("held")
                return {"analysis": "may be stale", "uncertainty": "unknown", "suggested_probes": []}
        failures=[]
        thread=threading.Thread(target=lambda: (engine.step(self.root, backend_override=Slow())),daemon=True)
        thread.start()
        self.assertTrue(started.wait(timeout=3))
        engine.park(self.root, "p001")
        release.set(); thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual(engine.read(self.root)["branches"]["p001"]["status"], "parked")
        self.assertTrue(any(x["type"] == "model_result_discarded" and x["branch"] == "p001" for x in Ledger(self.root).events()))

    def test_malformed_ollama_result_is_rejected(self):
        from unittest.mock import MagicMock
        response = MagicMock()
        response.status = 200
        response.read.return_value = b'{"message":{"content":"not json"}}'
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with patch("flowmesh.workers.urllib.request.build_opener", return_value=opener):
            with self.assertRaises(json.JSONDecodeError):
                OllamaBackend("local-model").interpret("Test", [])


if __name__ == "__main__":
    unittest.main()
