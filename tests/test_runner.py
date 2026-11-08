"""Checkpoint store, run planning, budget guard, retries and resume, with a fake monitor and a virtual clock.

No network and no real sleeping: ``swarm_evidence.runner.time`` is replaced by ``FakeClock`` wherever a retry or
rate-limit pause could sleep.
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import time as real_time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import APITimeoutError, FakeClock, FakeMonitor, RateLimitError, case  # noqa: E402

from swarm_evidence import runner  # noqa: E402
from swarm_evidence.adaption_monitor import max_cost  # noqa: E402
from swarm_evidence.runner import (EST_INPUT_MARGIN, OUTPUT_CAP_ISOLATED, OUTPUT_CAP_SINGLE, RateGate,  # noqa: E402
                                   Store, execute, plan_calls)

MODEL = "gemma-4-31b-it"
FIXED_EST = 1000


def observed_by_id(keys=(("A1", 0, "viol"), ("A1", 0, "flip_a"), ("B1", 0, "viol"))):
    out = {}
    for fam, seed, v in keys:
        obs = case(fam, seed, v)[0]
        out[obs["run_id"]] = obs
    return out


def make_specs(n_cases=3, stage="unit"):
    obs = observed_by_id()
    rids = sorted(obs)[:n_cases]
    specs = plan_calls(stage, ("dependency", "lexical"), (2000,), ("full",), rids, obs, MODEL)
    for s in specs:
        s["est_input_tokens"] = FIXED_EST  # identical worst-case reservation per call
    return specs


WORST = max_cost(MODEL, int(FIXED_EST * EST_INPUT_MARGIN), OUTPUT_CAP_SINGLE)


class RunnerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.store = Store(Path(self._tmp.name) / "nested" / "runs.sqlite")
        self.addCleanup(self.store.conn.close)
        self.clock = FakeClock()
        patcher = mock.patch.object(runner, "time", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_exec(self, specs, monitor, ceiling=10.0, stage_budget=10.0, **kw):
        kw.setdefault("concurrency", 1)
        kw.setdefault("rpm", 0)
        kw.setdefault("progress_every", 0)
        return execute(specs, monitor, self.store, ceiling=ceiling, stage_budget=stage_budget, **kw)

    def attempts(self):
        cur = self.store.conn.execute("SELECT run_key, attempt, error_type, error, reserved_cost FROM attempts "
                                      "ORDER BY rowid")
        return cur.fetchall()


class StoreTests(RunnerTestCase):
    def test_insert_is_idempotent_and_keeps_the_first_row(self):
        self.store.insert_call({"run_key": "k1", "status": "completed", "response_text": "first", "cost": 0.5})
        self.store.insert_call({"run_key": "k1", "status": "transport_error", "response_text": "second", "cost": 9.0})
        rows = self.store.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["status"], rows[0]["response_text"], rows[0]["cost"]), ("completed", "first", 0.5))
        self.assertTrue(self.store.has("k1"))
        self.assertFalse(self.store.has("k2"))

    def test_spent_includes_calls_reservations_and_adjustments(self):
        self.assertEqual(self.store.spent(), 0.0)
        self.store.insert_call({"run_key": "k1", "cost": 0.25})
        self.store.insert_attempt("k2", 1, "APITimeoutError", "timeout", 0.5)
        self.store.adjust("pilot", 1.0, "earlier stage")
        self.assertAlmostEqual(self.store.spent(), 1.75)

    def test_store_survives_reopen(self):
        path = Path(self._tmp.name) / "nested" / "runs.sqlite"
        self.store.insert_call({"run_key": "k1", "cost": 0.1})
        again = Store(path)
        self.addCleanup(again.conn.close)
        self.assertTrue(again.has("k1"))


class PlanCallsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obs = observed_by_id()
        cls.rids = sorted(cls.obs)

    def plan(self, arms=("dependency", "lexical", "isolated", "full"), caps=(2000, 6000), vis=("full",), model=MODEL,
             replicate=0, stage="s"):
        return plan_calls(stage, arms, caps, vis, self.rids, self.obs, model, replicate=replicate)

    def test_run_keys_are_stable_and_unique(self):
        a, b = self.plan(), self.plan()
        self.assertEqual(a, b)
        keys = [s["run_key"] for s in a]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(len(k) == 24 for k in keys))

    def test_key_components(self):
        base = {s["run_key"] for s in self.plan()}
        self.assertEqual(base, {s["run_key"] for s in self.plan(stage="other-stage-label")})
        self.assertFalse(base & {s["run_key"] for s in self.plan(replicate=1)})
        self.assertFalse(base & {s["run_key"] for s in self.plan(model="qwen3.5-397b")})
        self.assertFalse(base & {s["run_key"] for s in self.plan(vis=("random50",))})

    def test_call_layout(self):
        specs = self.plan()
        n = len(self.rids)
        by_arm = {}
        for s in specs:
            by_arm.setdefault(s["arm"], []).append(s)
        self.assertEqual(len(by_arm["full"]), n, "the full arm is cap independent and de-duplicated")
        self.assertTrue(all(s["cap"] is None for s in by_arm["full"]))
        self.assertEqual(len(by_arm["dependency"]), 2 * n)
        self.assertEqual(len(by_arm["isolated"]), 3 * 2 * n)
        self.assertEqual(sorted({s["call_index"] for s in by_arm["isolated"]}), [0, 1, 2])
        for s in specs:
            self.assertEqual(s["max_output_tokens"],
                             OUTPUT_CAP_ISOLATED if s["arm"] == "isolated" else OUTPUT_CAP_SINGLE)

    def test_spec_contents_match_selection(self):
        for s in self.plan(vis=("full", "random25", "bridges")):
            with self.subTest(arm=s["arm"], cap=s["cap"], vis=s["visibility"]):
                self.assertTrue(s["mask_audit_ok"])
                self.assertEqual(s["input_sha"], hashlib.sha256(s["input_text"].encode()).hexdigest()[:16])
                obs_ids = {e["event_id"] for e in self.obs[s["run_id"]]["events"]}
                self.assertLessEqual(set(s["shown_ids"]), obs_ids)
                # event IDs appear in the prompt only as event records: exactly the shown set, nothing else
                self.assertEqual(set(re.findall(r'"(e-[0-9a-f]{6})"', s["input_text"])), set(s["shown_ids"]))

    def test_estimated_input_never_exceeds_cap_for_single_call_arms(self):
        specs = plan_calls("s", ("dependency", "lexical", "chronological", "bm25", "lexical_prf", "shuffled"),
                           (2000, 6000), ("full", "random50", "bridges"), self.rids, self.obs, MODEL)
        for s in specs:
            with self.subTest(arm=s["arm"], cap=s["cap"], vis=s["visibility"]):
                self.assertLessEqual(s["est_input_tokens"], s["cap"])

    def test_view_hash_tracks_visibility(self):
        specs = self.plan(arms=("dependency",), caps=(2000,), vis=("full", "random25", "random50", "bridges"))
        hashes = {}
        for s in specs:
            hashes.setdefault(s["run_id"], set()).add(s["view_hash"])
        self.assertTrue(all(len(h) == 4 for h in hashes.values()))


class ExecuteTests(RunnerTestCase):
    def test_all_pending_calls_complete_and_are_recorded(self):
        specs = make_specs()
        mon = FakeMonitor(cost=WORST)
        summary = self.run_exec(specs, mon)
        self.assertEqual(summary["statuses"], {"completed": len(specs)})
        self.assertIsNone(summary["stop_reason"])
        self.assertEqual(len(mon.calls), len(specs))
        rows = {r["run_key"]: r for r in self.store.rows()}
        self.assertEqual(set(rows), {s["run_key"] for s in specs})
        for s in specs:
            r = rows[s["run_key"]]
            self.assertEqual(json.loads(r["shown_ids"]), s["shown_ids"])
            self.assertEqual(r["n_shown"], len(s["shown_ids"]))
            self.assertEqual(r["transport_attempts"], 1)
            self.assertIsNone(r["parse_error"])
            self.assertTrue(json.loads(r["parsed"])["valid"])
        self.assertAlmostEqual(summary["spent_after"], WORST * len(specs))
        self.assertEqual(self.attempts(), [])
        # the input text sent to the model is exactly the planned one
        self.assertEqual([c[0] for c in mon.calls], [s["input_text"] for s in specs])

    def test_resume_skips_completed_keys_and_keeps_first_rows(self):
        specs = make_specs()
        self.run_exec(specs[:2], FakeMonitor(cost=WORST))
        first = {r["run_key"]: r for r in self.store.rows()}
        mon2 = FakeMonitor(cost=WORST, response_text='{"score": 1, "verdict": "violation", '
                                                     '"evidence_event_ids": [], "reason": "second run"}')
        summary = self.run_exec(specs, mon2)
        self.assertEqual(summary["n_pending_at_start"], len(specs) - 2)
        self.assertEqual(len(mon2.calls), len(specs) - 2)
        rows = {r["run_key"]: r for r in self.store.rows()}
        self.assertEqual(len(rows), len(specs))
        for k, r in first.items():
            self.assertEqual(rows[k], r, "completed first attempts are immutable")
        # a third run has nothing to do
        mon3 = FakeMonitor()
        summary3 = self.run_exec(specs, mon3)
        self.assertEqual((summary3["n_pending_at_start"], len(mon3.calls), summary3["statuses"]), (0, 0, {}))

    def test_global_ceiling_stops_new_calls(self):
        specs = make_specs()
        mon = FakeMonitor(cost=WORST)
        summary = self.run_exec(specs, mon, ceiling=2.5 * WORST, stage_budget=100.0)
        self.assertEqual(summary["stop_reason"], "global_ceiling")
        self.assertEqual(len(mon.calls), 2)
        self.assertEqual(summary["statuses"], {"completed": 2, "skipped": len(specs) - 2})
        self.assertLessEqual(self.store.spent(), 2.5 * WORST)

    def test_ceiling_counts_prior_spend_but_stage_budget_does_not(self):
        self.store.adjust("earlier", 1.0, "previous stage")
        specs = make_specs()
        s1 = self.run_exec(specs, FakeMonitor(cost=WORST), ceiling=1.0 + 2.5 * WORST, stage_budget=100.0)
        self.assertEqual((s1["stop_reason"], s1["statuses"].get("completed")), ("global_ceiling", 2))
        self.assertAlmostEqual(s1["spent_before"], 1.0)

    def test_stage_budget_stops_new_calls(self):
        self.store.adjust("earlier", 1.0, "previous stage")
        specs = make_specs()
        mon = FakeMonitor(cost=WORST)
        summary = self.run_exec(specs, mon, ceiling=100.0, stage_budget=2.5 * WORST)
        self.assertEqual(summary["stop_reason"], "stage_budget")
        self.assertEqual(len(mon.calls), 2)
        self.assertEqual(summary["statuses"], {"completed": 2, "skipped": len(specs) - 2})

    def test_ceiling_below_one_reservation_makes_no_call(self):
        mon = FakeMonitor(cost=WORST)
        summary = self.run_exec(make_specs(), mon, ceiling=0.5 * WORST)
        self.assertEqual(summary["stop_reason"], "global_ceiling")
        self.assertEqual(mon.calls, [])
        self.assertEqual(self.store.rows(), [])

    def test_interrupted_stage_resumes_without_duplicates(self):
        specs = make_specs()
        mon1 = FakeMonitor(cost=WORST)
        self.run_exec(specs, mon1, ceiling=2.5 * WORST)
        mon2 = FakeMonitor(cost=WORST)
        summary = self.run_exec(specs, mon2, ceiling=100.0)
        self.assertIsNone(summary["stop_reason"])
        self.assertEqual(len(mon1.calls) + len(mon2.calls), len(specs))
        keys = [r["run_key"] for r in self.store.rows()]
        self.assertEqual(sorted(keys), sorted(s["run_key"] for s in specs))

    def test_time_stop(self):
        mon = FakeMonitor()
        summary = self.run_exec(make_specs(), mon, stop_at_utc="2000-01-01T00:00:00+00:00")
        self.assertEqual(summary["stop_reason"], "time_stop")
        self.assertEqual(mon.calls, [])

    def test_non_transient_error_is_logged_and_not_retried(self):
        specs = make_specs()
        mon = FakeMonitor(cost=WORST, script={1: ValueError("boom")})
        summary = self.run_exec(specs, mon)
        self.assertEqual(len(mon.calls), len(specs), "no retry for a non-transient error")
        self.assertEqual(summary["statuses"], {"transport_error": 1, "completed": len(specs) - 1})
        row = self.store.rows("run_key=?", (specs[0]["run_key"],))[0]
        self.assertEqual(row["status"], "transport_error")
        self.assertEqual(row["parse_error"], "ValueError: boom")
        self.assertEqual(row["cost"], 0.0)
        self.assertIsNone(row["response_text"])
        self.assertEqual(row["transport_attempts"], 1)
        self.assertEqual(self.attempts(), [(specs[0]["run_key"], 1, "ValueError", "boom", 0.0)])

    def test_rate_limit_error_pauses_and_retries(self):
        specs = make_specs()
        mon = FakeMonitor(cost=WORST, script={1: RateLimitError("429 too many requests")})
        t0 = real_time.monotonic()
        summary = self.run_exec(specs, mon)
        self.assertLess(real_time.monotonic() - t0, 10.0, "virtual clock: the 60 s pause must not really sleep")
        self.assertEqual(summary["statuses"], {"completed": len(specs)})
        self.assertEqual(summary["rate_limit_events"], 1)
        self.assertEqual(len(mon.calls), len(specs) + 1)
        row = self.store.rows("run_key=?", (specs[0]["run_key"],))[0]
        self.assertEqual((row["status"], row["transport_attempts"]), ("completed", 2))
        self.assertEqual(self.attempts(), [(specs[0]["run_key"], 1, "RateLimitError", "429 too many requests", 0.0)])
        self.assertGreaterEqual(self.clock.slept, 60.0, "the global 60 s pause after a 429 is honored")

    def test_persistent_rate_limits_end_in_transport_error(self):
        specs = make_specs()[:1]
        mon = FakeMonitor(script={i: RateLimitError("429") for i in range(1, 10)})
        summary = self.run_exec(specs, mon, max_attempts=3)
        self.assertEqual(summary["statuses"], {"transport_error": 1})
        self.assertEqual(summary["rate_limit_events"], 3)
        self.assertEqual(len(self.attempts()), 3)
        self.assertEqual(self.store.rows()[0]["transport_attempts"], 3)

    def test_uncertain_billing_keeps_a_reservation(self):
        specs = make_specs()[:1]
        mon = FakeMonitor(cost=WORST, script={1: APITimeoutError("read timeout")})
        summary = self.run_exec(specs, mon)
        self.assertEqual(summary["statuses"], {"completed": 1})
        (att,) = self.attempts()
        self.assertEqual(att[2], "APITimeoutError")
        self.assertAlmostEqual(att[4], WORST)
        self.assertAlmostEqual(self.store.spent(), 2 * WORST, msg="reservation + billed cost both counted")
        self.assertEqual(self.clock.slept, 2.0, "exponential backoff 2**attempt on the virtual clock")

    def test_missing_provider_cost_falls_back_to_price_table(self):
        specs = make_specs()[:1]
        self.run_exec(specs, FakeMonitor(cost=None))
        row = self.store.rows()[0]
        self.assertAlmostEqual(row["cost"], max_cost(MODEL, 1000, 40))

    def test_parsed_output_and_unsupported_ids_are_stored(self):
        specs = make_specs()[:1]
        shown = specs[0]["shown_ids"][0]
        text = json.dumps({"score": 0.9, "verdict": "violation", "evidence_event_ids": [shown, "e-notshown"],
                           "reason": "x"})
        self.run_exec(specs, FakeMonitor(response_text=text))
        parsed = json.loads(self.store.rows()[0]["parsed"])
        self.assertTrue(parsed["valid"])
        self.assertEqual(parsed["unsupported_ids"], ["e-notshown"])

    def test_invalid_output_is_stored_with_its_error(self):
        specs = make_specs()[:1]
        self.run_exec(specs, FakeMonitor(response_text="not json at all"))
        row = self.store.rows()[0]
        self.assertEqual(row["status"], "completed")
        self.assertEqual(row["parse_error"], "json_decode")
        self.assertEqual(row["response_text"], "not json at all")

    def test_stage_log_records_start_and_end(self):
        self.run_exec(make_specs(stage="logged"), FakeMonitor())
        events = self.store.conn.execute("SELECT stage, event FROM stage_log ORDER BY rowid").fetchall()
        self.assertEqual(events, [("logged", "start"), ("logged", "end")])

    def test_concurrent_execution_records_every_call_once(self):
        specs = make_specs()
        mon = FakeMonitor(cost=WORST)
        summary = self.run_exec(specs, mon, concurrency=4)
        self.assertEqual(summary["statuses"], {"completed": len(specs)})
        self.assertEqual(len(mon.calls), len(specs))
        self.assertEqual(len(self.store.rows()), len(specs))

    # SOURCE BUG (latent): runner.py:181 filters pending specs once, before any call, and never de-duplicates.
    # A spec list containing the same run_key twice calls the model twice; INSERT OR IGNORE (runner.py:75) then silently drops
    # the second (billed) response, so its cost is missing from the ledger the ceiling guard reads. plan_calls already
    # de-duplicates, so the CLI path is not affected today.
    # Fixed after the freeze (see protocol/POST_FREEZE_CHANGES.md); kept as a regression test.
    def test_duplicate_specs_call_the_model_once(self):
        specs = make_specs()
        mon = FakeMonitor(cost=WORST)
        self.run_exec(specs + [dict(specs[0])], mon)
        self.assertEqual(len(mon.calls), len(specs))

    # SOURCE BUG: same root cause as test_adaption_monitor.ParseInvalidTests.test_huge_integer_score_is_rejected_not_raised.
    # parse_output raises OverflowError inside execute() after the response was received and billed; execute() then
    # propagates the exception and the call row (with its cost) is never written, so a resume re-bills the call.
    # Fixed after the freeze (see protocol/POST_FREEZE_CHANGES.md); kept as a regression test.
    def test_huge_integer_score_does_not_crash_the_stage(self):
        specs = make_specs()[:1]
        text = '{"score": ' + "9" * 400 + ', "verdict": "benign", "evidence_event_ids": [], "reason": "x"}'
        self.run_exec(specs, FakeMonitor(cost=WORST, response_text=text))
        row = self.store.rows()[0]
        self.assertEqual(row["parse_error"], "bad_score")
        self.assertAlmostEqual(row["cost"], WORST)


class RateGateTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        patcher = mock.patch.object(runner, "time", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_zero_rpm_never_waits(self):
        g = RateGate(0)
        for _ in range(5):
            g.wait()
        self.assertEqual(self.clock.slept, 0.0)

    def test_spacing_pause_and_backoff(self):
        g = RateGate(60)
        self.assertEqual(g.interval, 1.0)
        g.wait()
        self.assertEqual(self.clock.slept, 0.0)
        g.wait()
        self.assertAlmostEqual(self.clock.slept, 1.0)
        g.on_rate_limit(60.0)
        self.assertEqual(g.n_429, 1)
        self.assertAlmostEqual(g.interval, 1.15)
        before = self.clock.slept
        g.wait()
        self.assertGreaterEqual(self.clock.slept - before, 60.0 - 1e-9)


if __name__ == "__main__":
    unittest.main()
