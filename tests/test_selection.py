"""Budgeted evidence selectors: cap enforcement, determinism, graph edge cases, no hidden inputs."""
import copy
import hashlib
import json
import os
import subprocess
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import ALL_FAMILIES, ROOT, case, mk_event, mk_observed  # noqa: E402

from swarm_evidence.audit import EVENT_KEYS, OBS_KEYS  # noqa: E402
from swarm_evidence.prompts import event_cost, overhead_tokens  # noqa: E402
from swarm_evidence.selection import (ISOLATED_VIEW_NOTE, METHODS, dependency_order, select,  # noqa: E402
                                      shuffle_permutation)

CAPS = (2000, 6000)
ALL_METHODS = METHODS + ("full",)
SINGLE_CALL_BUDGETED = tuple(m for m in METHODS if m != "isolated")


def producer_of(events, artifact):
    for e in events:
        if artifact in e["output_artifact_ids"]:
            return e["event_id"]
    return None


def sample_records():
    for fam in ALL_FAMILIES:
        for seed in (0, 1):
            for v in ("viol", "flip_a"):
                yield fam, seed, v, case(fam, seed, v)[0]


class BudgetTests(unittest.TestCase):
    def test_single_call_selectors_respect_cap(self):
        for fam, seed, v, obs in sample_records():
            by_id = {e["event_id"]: e for e in obs["events"]}
            for cap in CAPS:
                for m in SINGLE_CALL_BUDGETED:
                    with self.subTest(family=fam, seed=seed, variant=v, cap=cap, method=m):
                        (c,) = select(m, obs, cap)
                        ids = c["event_ids"]
                        self.assertEqual(len(ids), len(set(ids)))
                        self.assertLessEqual(set(ids), set(by_id))
                        cost = sum(event_cost(by_id[i]) for i in ids)
                        self.assertEqual(c["used"], cost)
                        self.assertEqual(c["overhead"], overhead_tokens(obs["domain"], obs["envelope"]))
                        self.assertEqual(c["budget"], cap - c["overhead"])
                        self.assertLessEqual(cost, c["budget"])
                        self.assertLessEqual(cost + c["overhead"], cap)
                        self.assertEqual(len(ids) + c["skipped"], c["candidates"])

    def test_isolated_calls_split_by_worker_and_never_overfill(self):
        for fam, seed, v, obs in sample_records():
            by_id = {e["event_id"]: e for e in obs["events"]}
            for cap in CAPS:
                with self.subTest(family=fam, seed=seed, variant=v, cap=cap):
                    calls = select("isolated", obs, cap)
                    self.assertEqual([c["worker"] for c in calls], ["W1", "W2", "W3"])
                    for c in calls:
                        self.assertEqual(c["view_note"], ISOLATED_VIEW_NOTE.format(w=c["worker"]))
                        self.assertTrue(all(by_id[i]["worker_id"] == c["worker"] for i in c["event_ids"]))
                        self.assertEqual(c["used"], sum(event_cost(by_id[i]) for i in c["event_ids"]))
                        self.assertEqual(c["budget"], cap // 3 - c["overhead"])
                        self.assertLessEqual(c["used"], max(c["budget"], 0))

    def test_isolated_large_cap_respects_per_call_cap(self):
        for fam, seed, v, obs in sample_records():
            with self.subTest(family=fam, seed=seed, variant=v):
                calls = select("isolated", obs, 6000)
                for c in calls:
                    self.assertGreater(len(c["event_ids"]), 0)
                    self.assertLessEqual(c["used"] + c["overhead"], 6000 // 3)
                self.assertLessEqual(sum(c["used"] + c["overhead"] for c in calls), 6000)

    # SOURCE BUG: selection.py:174 computes the isolated per-call budget as 2000 // 3 - overhead, but the fixed
    # per-call overhead (instructions + policy + envelope + view note) is larger than 666 estimated tokens
    # (699-755 with PROMPT_VERSION v3; 691-745 with v2), so every per-call budget is negative, every isolated call
    # at the small cap shows ZERO events (all families, seeds 0-4), and the three calls together exceed the
    # 2000-token cap (2097-2265). Example: A1:0 viol -> overhead 753, budget -87, total 2259 (v3).
    # The pilot_v2 rows in results/runs.sqlite show n_shown=0 for all 36 isolated calls.
    @unittest.expectedFailure
    def test_isolated_small_cap_respects_per_call_cap(self):
        for fam, seed, v, obs in sample_records():
            with self.subTest(family=fam, seed=seed, variant=v):
                calls = select("isolated", obs, 2000)
                for c in calls:
                    self.assertGreaterEqual(c["budget"], 0)
                    self.assertLessEqual(c["used"] + c["overhead"], 2000 // 3)
                self.assertLessEqual(sum(c["used"] + c["overhead"] for c in calls), 2000)

    def test_full_view_shows_everything_without_budget(self):
        obs = case("B2", 0, "viol")[0]
        (c,) = select("full", obs, 2000)
        self.assertIsNone(c["budget"])
        self.assertEqual(c["event_ids"], [e["event_id"] for e in obs["events"]])
        self.assertEqual(c["skipped"], 0)
        self.assertEqual(c["used"], sum(event_cost(e) for e in obs["events"]))

    def test_small_cap_is_binding_for_most_records(self):
        # the budget comparison is only informative if full prompts exceed the small cap
        over = [select("full", obs, 2000)[0]["used"] + overhead_tokens(obs["domain"], obs["envelope"]) > 2000
                for *_, obs in sample_records()]
        self.assertGreater(sum(over) / len(over), 0.9)

    def test_unknown_method_raises(self):
        with self.assertRaises(ValueError):
            select("oracle_peek", case("A1", 0, "viol")[0], 2000)


class OversizedEventTests(unittest.TestCase):
    def build(self):
        big_note = "x" * 30000  # ~12000 estimated tokens: larger than any per-call budget
        events = [mk_event("e01", 1, "register_source", outs=["s"],
                           args={"license": {"permitted_uses": ["external_share"]}}, worker="W1"),
                  mk_event("e02", 2, "transform", ins=["s"], outs=["x"], args={"op": "normalize"}, worker="W2"),
                  mk_event("e03", 3, "profile_dataset", ins=["s"], worker="W1"),
                  mk_event("e04", 4, "transform", ins=["x"], outs=["y"], worker="W1"),
                  mk_event("e05", 5, "stage_export", ins=["y"], outs=["t"], worker="W1", note=big_note)]
        return mk_observed(events, target="t")

    def test_oversized_event_is_skipped_counted_and_smaller_events_still_fill(self):
        obs = self.build()
        big = obs["events"][-1]
        self.assertGreater(event_cost(big), 6000)
        for cap in CAPS:
            for m in SINGLE_CALL_BUDGETED:
                with self.subTest(cap=cap, method=m):
                    (c,) = select(m, obs, cap)
                    self.assertNotIn("e05", c["event_ids"])
                    self.assertGreaterEqual(c["skipped"], 1)
                    self.assertEqual(len(c["event_ids"]), 4, "greedy fill must continue past the oversized event")
        calls = select("isolated", obs, 6000)
        w1 = calls[0]
        self.assertEqual(w1["worker"], "W1")
        self.assertNotIn("e05", w1["event_ids"])
        self.assertEqual(w1["skipped"], 1)
        self.assertEqual(sorted(w1["event_ids"]), ["e01", "e03", "e04"])


class DependencyGraphTests(unittest.TestCase):
    def test_target_producer_is_first_for_dependency_and_shuffled(self):
        for fam in ALL_FAMILIES:
            obs = case(fam, 0, "viol")[0]
            prod = producer_of(obs["events"], obs["envelope"]["target_artifact_id"])
            for m in ("dependency", "shuffled"):
                with self.subTest(family=fam, method=m):
                    self.assertEqual(select(m, obs, 2000)[0]["event_ids"][0], prod)

    def test_bfs_order_distance_then_newest_then_id(self):
        events = [mk_event("e1", 1, "register_source", outs=["a1"]),
                  mk_event("e2", 2, "register_source", outs=["b1"]),
                  mk_event("e3", 3, "transform", ins=["a1"], outs=["a2"]),
                  mk_event("e4", 4, "revoke_use", ins=["a1"]),  # annotation on a1 (distance 2) -> rank 2.5
                  mk_event("e5", 5, "merge", ins=["a2", "b1"], outs=["t"]),
                  mk_event("e6", 6, "register_source", outs=["zz"]),  # disconnected
                  mk_event("e7", 7, "profile_dataset", ins=["zz"])]  # annotation on a disconnected artifact
        # distances: e5=0; e3 (a2) and e2 (b1) = 1 -> newer first; e1 (a1) = 2; e4 = 2.5
        self.assertEqual(dependency_order(events, "t"), ["e5", "e3", "e2", "e1", "e4"])

    def test_equal_rank_ties_break_on_event_id(self):
        events = [mk_event("e_b", 1, "register_source", outs=["p"]),
                  mk_event("e_a", 1, "register_source", outs=["q"]),
                  mk_event("e_t", 2, "merge", ins=["p", "q"], outs=["t"])]
        self.assertEqual(dependency_order(events, "t"), ["e_t", "e_a", "e_b"])

    def test_cycles_terminate(self):
        events = [mk_event("e1", 1, "transform", ins=["x"], outs=["y"]),
                  mk_event("e2", 2, "transform", ins=["y"], outs=["x"]),
                  mk_event("e3", 3, "transform", ins=["z"], outs=["z"])]  # self-loop
        self.assertEqual(dependency_order(events, "x"), ["e2", "e1"])
        self.assertEqual(dependency_order(events, "z"), ["e3"])
        obs = mk_observed(events, target="x")
        for m in METHODS:
            with self.subTest(method=m):
                select(m, obs, 2000)

    def test_missing_producers_and_unproduced_target(self):
        events = [mk_event("e1", 1, "transform", ins=["ghost"], outs=["t"]),
                  mk_event("e2", 2, "profile_dataset", ins=["orphan"])]
        self.assertEqual(dependency_order(events, "t"), ["e1"])
        self.assertEqual(dependency_order(events, "nothing"), [])
        self.assertEqual(dependency_order(events, "orphan"), ["e2"])  # annotation only, rank 0.5
        obs = mk_observed(events, target="nothing")
        for m in METHODS:
            with self.subTest(method=m):
                calls = select(m, obs, 2000)
                if m == "dependency":
                    self.assertEqual(calls[0]["event_ids"], [])

    def test_disconnected_events_are_never_selected_by_dependency(self):
        obs = case("A3", 0, "viol")[0]
        reachable = set(dependency_order(obs["events"], obs["envelope"]["target_artifact_id"]))
        big = select("dependency", obs, 10 ** 7)[0]
        self.assertEqual(set(big["event_ids"]), reachable)
        self.assertLess(len(reachable), len(obs["events"]))

    def test_empty_ledger(self):
        obs = mk_observed([], target="t")
        for m in ALL_METHODS:
            with self.subTest(method=m):
                calls = select(m, obs, 2000)
                self.assertTrue(all(c["event_ids"] == [] for c in calls))

    def test_shuffle_is_a_fixed_point_bijection(self):
        obs = case("B4", 0, "viol")[0]
        events, target = obs["events"], obs["envelope"]["target_artifact_id"]
        mapping = shuffle_permutation(events, target, obs["run_id"])
        ids = sorted(e["event_id"] for e in events)
        self.assertEqual(sorted(mapping), ids)
        self.assertEqual(sorted(mapping.values()), ids)
        prod = producer_of(events, target)
        self.assertEqual(mapping[prod], prod)
        self.assertEqual(mapping, shuffle_permutation(events, target, obs["run_id"]))
        self.assertNotEqual(mapping, shuffle_permutation(events, target, "run-other"))
        self.assertGreater(sum(1 for k, v in mapping.items() if k != v), len(ids) // 2)

    def test_shuffle_without_target_producer(self):
        events = [mk_event("e1", 1, "register_source", outs=["a"]), mk_event("e2", 2, "transform", ins=["a"], outs=["b"])]
        mapping = shuffle_permutation(events, "nothing", "run-x")
        self.assertEqual(sorted(mapping.values()), ["e1", "e2"])


class DeterminismTests(unittest.TestCase):
    def test_repeated_and_copied_inputs_give_identical_selections(self):
        for fam in ("A4", "B2", "C2", "BX"):
            obs = case(fam, 1, "viol")[0]
            for m in ALL_METHODS:
                for cap in CAPS:
                    with self.subTest(family=fam, method=m, cap=cap):
                        self.assertEqual(select(m, obs, cap), select(m, copy.deepcopy(obs), cap))

    def test_selection_is_invariant_to_ledger_list_order(self):
        for fam in ("A1", "B3", "C4"):
            obs = case(fam, 0, "flip_a")[0]
            rev = dict(obs, events=list(reversed(obs["events"])))
            for m in ALL_METHODS:
                with self.subTest(family=fam, method=m):
                    a = [sorted(c["event_ids"]) for c in select(m, obs, 2000)]
                    b = [sorted(c["event_ids"]) for c in select(m, rev, 2000)]
                    self.assertEqual(a, b)

    def test_selection_is_identical_across_hash_seeds(self):
        script = (
            "import hashlib, json, sys\n"
            "sys.path.insert(0, %r)\n"
            "from swarm_evidence.scenarios import build_case\n"
            "from swarm_evidence.selection import select\n"
            "out = []\n"
            "for fam in ('A3', 'B2', 'C3'):\n"
            "    obs = build_case(fam, 0, 'viol')[0]\n"
            "    for m in ('chronological','lexical','bm25','lexical_prf','dependency','shuffled','isolated','full'):\n"
            "        for cap in (2000, 6000):\n"
            "            out.append([c['event_ids'] for c in select(m, obs, cap)])\n"
            "print(hashlib.sha256(json.dumps(out).encode()).hexdigest())\n" % str(ROOT))
        digests = set()
        for seed in ("0", "1", "4242"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=str(ROOT),
                               timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr)
            digests.add(r.stdout.strip())
        self.assertEqual(len(digests), 1, "selection depends on string-hash randomization")


class NoHiddenInputTests(unittest.TestCase):
    def strip(self, obs):
        out = {k: copy.deepcopy(v) for k, v in obs.items() if k in OBS_KEYS}
        out["events"] = [{k: v for k, v in e.items() if k in EVENT_KEYS} for e in obs["events"]]
        return out

    def test_selection_runs_on_audited_keys_only_and_ignores_extra_fields(self):
        for fam in ("A2", "B1", "C1"):
            obs, _, meta = case(fam, 0, "viol")
            stripped = self.strip(obs)
            polluted = copy.deepcopy(stripped)
            polluted.update(label=1, gold_event_ids=meta["core_event_ids"], family=fam, variant="viol")
            core = set(meta["core_event_ids"])
            for e in polluted["events"]:
                e["core"] = e["event_id"] in core
                e["gold"] = e["event_id"] in core
            for m in ALL_METHODS:
                for cap in CAPS:
                    with self.subTest(family=fam, method=m, cap=cap):
                        self.assertEqual(select(m, stripped, cap), select(m, polluted, cap))


if __name__ == "__main__":
    unittest.main()
