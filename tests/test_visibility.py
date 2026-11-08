"""Missing-dependency-metadata masking: removed relations cannot be rebuilt from leftover IDs."""
import copy
import json
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import ALL_FAMILIES, case, mk_event, mk_observed  # noqa: E402

from swarm_evidence.visibility import (CONDITIONS, _bridges, apply_visibility, choose_relations,  # noqa: E402
                                       relations)

MASKING = tuple(c for c in CONDITIONS if c != "full")
PH_RE = re.compile(r"unk-\d{3,}")


def records():
    for fam in ALL_FAMILIES:
        for seed in (0, 1):
            for v in ("viol", "flip_a"):
                yield fam, seed, v, case(fam, seed, v)[0]


class MaskingTests(unittest.TestCase):
    def test_masked_ids_vanish_from_consumers_and_relations_cannot_be_rebuilt(self):
        for fam, seed, v, obs in records():
            for cond in MASKING:
                with self.subTest(family=fam, seed=seed, variant=v, condition=cond):
                    before = copy.deepcopy(obs)
                    masked, audit = apply_visibility(obs, cond)
                    self.assertEqual(obs, before, "input record must not be mutated")
                    chosen = choose_relations(obs, cond)
                    self.assertTrue(audit["audit_ok"])
                    self.assertEqual(audit["n_masked"], len(chosen))
                    self.assertGreater(len(chosen), 0)
                    m_by_id = {e["event_id"]: e for e in masked["events"]}
                    for a, p, c in chosen:
                        self.assertNotIn(a, json.dumps(m_by_id[c]))
                        self.assertIn(a, m_by_id[p]["output_artifact_ids"], "producer keeps its output")
                    remaining = set(relations(masked["events"]))
                    self.assertFalse(remaining & set(chosen))
                    self.assertEqual(len(relations(masked["events"])), audit["n_relations"] - len(chosen))

    def test_whole_events_are_kept_and_untouched_events_are_identical(self):
        for fam, seed, v, obs in records():
            for cond in MASKING:
                with self.subTest(family=fam, seed=seed, variant=v, condition=cond):
                    masked, audit = apply_visibility(obs, cond)
                    consumers = {c for _, _, c in choose_relations(obs, cond)}
                    self.assertEqual(len(consumers), audit["events_affected"])
                    self.assertEqual(len(masked["events"]), len(obs["events"]))
                    self.assertEqual(masked["envelope"], obs["envelope"])
                    for o, m in zip(obs["events"], masked["events"]):
                        for k in ("event_id", "sequence", "worker_id", "tool", "outcome", "rationale"):
                            self.assertEqual(o[k], m[k])
                        if o["event_id"] not in consumers:
                            self.assertEqual(o, m)
                        else:
                            self.assertNotEqual(o, m)

    def test_placeholders_are_unique_per_relation(self):
        for fam, seed, v, obs in records():
            for cond in MASKING:
                with self.subTest(family=fam, seed=seed, variant=v, condition=cond):
                    masked, audit = apply_visibility(obs, cond)
                    where = {}
                    for e in masked["events"]:
                        for ph in set(PH_RE.findall(json.dumps(e))):
                            where.setdefault(ph, []).append(e["event_id"])
                    self.assertEqual(len(where), audit["n_masked"])
                    self.assertTrue(all(len(evs) == 1 for evs in where.values()),
                                    "a placeholder shared by two events would re-link them by equality join")
                    self.assertFalse(PH_RE.search(json.dumps(obs)), "placeholders must not pre-exist")

    def test_random_conditions_mask_the_declared_fraction(self):
        for fam, seed, v, obs in records():
            n = len(relations(obs["events"]))
            for cond, frac in (("random25", 0.25), ("random50", 0.50)):
                with self.subTest(family=fam, seed=seed, variant=v, condition=cond):
                    self.assertEqual(apply_visibility(obs, cond)[1]["n_masked"], int(round(frac * n)))

    def test_bridge_condition_masks_only_cross_worker_relations(self):
        for fam, seed, v, obs in records():
            with self.subTest(family=fam, seed=seed, variant=v):
                worker = {e["event_id"]: e["worker_id"] for e in obs["events"]}
                chosen = choose_relations(obs, "bridges")
                self.assertTrue(chosen)
                self.assertTrue(all(worker[p] != worker[c] for _, p, c in chosen))
                self.assertEqual(apply_visibility(obs, "bridges")[1]["cross_worker_masked"], len(chosen))

    def test_same_view_is_deterministic_and_seeded_by_run(self):
        obs = case("A3", 0, "viol")[0]
        for cond in CONDITIONS:
            with self.subTest(condition=cond):
                self.assertEqual(apply_visibility(obs, cond), apply_visibility(copy.deepcopy(obs), cond))
        other = dict(copy.deepcopy(obs), run_id="run-0000000000")
        self.assertNotEqual(choose_relations(obs, "random50"), choose_relations(other, "random50"))

    def test_full_is_a_noop_copy(self):
        obs = case("C2", 0, "viol")[0]
        masked, audit = apply_visibility(obs, "full")
        self.assertEqual(masked, obs)
        self.assertIsNot(masked, obs)
        self.assertEqual(audit["n_masked"], 0)
        self.assertTrue(audit["audit_ok"])
        masked["events"][0]["tool"] = "tampered"
        self.assertNotEqual(obs["events"][0]["tool"], "tampered")

    def test_unknown_condition_raises(self):
        with self.assertRaises(ValueError):
            choose_relations(case("A1", 0, "viol")[0], "random99")


class SyntheticMaskTests(unittest.TestCase):
    def ledger(self, note="Joined the inputs."):
        events = [mk_event("e1", 1, "register_source", outs=["a-000001"], worker="W1"),
                  mk_event("e2", 2, "register_source", outs=["a-000002"], worker="W1"),
                  mk_event("e3", 3, "lookup_join", ins=["a-000001", "a-000002"], outs=["a-000003"],
                           args={"primary": "a-000001", "reference": "a-000002"}, worker="W2", note=note)]
        return mk_observed(events, target="a-000003")

    def test_arguments_and_inputs_are_masked_together(self):
        obs = self.ledger()
        masked, audit = apply_visibility(obs, "bridges")
        self.assertEqual(audit["n_masked"], 2)
        e3 = masked["events"][2]
        self.assertEqual(e3["input_artifact_ids"], ["unk-001", "unk-002"])
        self.assertEqual(e3["arguments"], {"primary": "unk-001", "reference": "unk-002"})

    def test_unmasked_id_left_in_a_note_fails_the_audit(self):
        obs = self.ledger(note="Joined a-000001 against a-000002.")
        _, audit = apply_visibility(obs, "bridges")
        self.assertFalse(audit["audit_ok"], "a surviving ID must be reported, never silently passed")

    # SOURCE BUG (latent): visibility.py's docstring promises that every occurrence of a masked artifact inside the
    # consumer (inputs, arguments, version map, *note*) is replaced, but apply_visibility (visibility.py:140-143) only rewrites
    # whole JSON string values ('"a-000001"'), so an ID mentioned inside free-text rationale survives. The audit flags it
    # (audit_ok=False) and `run` refuses such plans; generated notes never contain IDs, so released data is unaffected.
    @unittest.expectedFailure
    def test_ids_inside_notes_are_masked(self):
        obs = self.ledger(note="Joined a-000001 against a-000002.")
        masked, _ = apply_visibility(obs, "bridges")
        self.assertNotIn("a-000001", masked["events"][2]["rationale"])


class BridgeAlgorithmTests(unittest.TestCase):
    def E(self, *pairs):
        return {frozenset(p) for p in pairs}

    def test_path_triangle_pendant_and_components(self):
        self.assertEqual(_bridges({"a", "b", "c"}, self.E(("a", "b"), ("b", "c"))), self.E(("a", "b"), ("b", "c")))
        self.assertEqual(_bridges({"a", "b", "c"}, self.E(("a", "b"), ("b", "c"), ("a", "c"))), set())
        self.assertEqual(_bridges({"a", "b", "c", "d"}, self.E(("a", "b"), ("b", "c"), ("a", "c"), ("c", "d"))),
                         self.E(("c", "d")))
        self.assertEqual(_bridges({"a", "b", "x", "y", "lone"}, self.E(("a", "b"), ("x", "y"))),
                         self.E(("a", "b"), ("x", "y")))

    def test_two_cycles_joined_by_one_edge(self):
        edges = self.E(("a", "b"), ("b", "c"), ("c", "a"), ("c", "d"), ("d", "e"), ("e", "f"), ("f", "d"))
        self.assertEqual(_bridges(set("abcdef"), edges), self.E(("c", "d")))


if __name__ == "__main__":
    unittest.main()
