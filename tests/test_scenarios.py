"""Generated workflows: matched twins, opposite oracle labels, determinism, observed-field hygiene."""
import copy
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import ALL_FAMILIES, CORE_FAMILIES, case, variants_for  # noqa: E402

from swarm_evidence.audit import EVENT_KEYS, FORBIDDEN_SUBSTRINGS, OBS_KEYS  # noqa: E402
from swarm_evidence.oracle import oracle  # noqa: E402
from swarm_evidence.rules_monitor import rule_monitor  # noqa: E402
from swarm_evidence.scenarios import OUT_OF_LINEAGE_FAMILIES, build_case  # noqa: E402

SEEDS = (0, 1, 2)


def structure(observed):
    return [(e["event_id"], e["tool"], e["worker_id"], e["sequence"], len(e["input_artifact_ids"]),
             len(e["output_artifact_ids"]), e["rationale"], tuple(e["policy_refs"])) for e in observed["events"]]


class TwinTests(unittest.TestCase):
    def test_twins_have_opposite_oracle_labels(self):
        for fam in ALL_FAMILIES:
            for seed in SEEDS:
                with self.subTest(family=fam, seed=seed):
                    labels = {v: oracle(case(fam, seed, v)[1], case(fam, seed, v)[0]["envelope"])["label"]
                              for v in variants_for(fam)}
                    self.assertEqual(labels["viol"], 1)
                    self.assertEqual(labels["flip_a"], 0)
                    if "flip_b" in labels:
                        self.assertEqual(labels["flip_b"], 0)

    def test_released_twins_share_structure_and_envelope(self):
        for fam in ALL_FAMILIES:
            for seed in SEEDS:
                with self.subTest(family=fam, seed=seed):
                    viol, _, mv = case(fam, seed, "viol")
                    twin, _, mt = case(fam, seed, "flip_a")
                    self.assertEqual(structure(viol), structure(twin))
                    self.assertEqual(viol["envelope"], twin["envelope"])
                    self.assertEqual(viol["domain"], twin["domain"])
                    self.assertEqual(mv["core_event_ids"], mt["core_event_ids"])
                    no_run = [[{k: x for k, x in e.items() if k != "run_id"} for e in o["events"]] for o in (viol, twin)]
                    self.assertNotEqual(no_run[0], no_run[1], "twins must differ in some event content")
                    self.assertNotEqual(viol["run_id"], twin["run_id"])

    def test_flip_b_counterfactual_keeps_length_and_ids(self):
        for fam in CORE_FAMILIES:
            with self.subTest(family=fam):
                viol = case(fam, 0, "viol")[0]
                alt = case(fam, 0, "flip_b")[0]
                self.assertEqual([e["event_id"] for e in viol["events"]], [e["event_id"] for e in alt["events"]])

    def test_twin_differences_are_confined_to_core_events(self):
        for fam in ALL_FAMILIES:
            with self.subTest(family=fam):
                viol, _, meta = case(fam, 0, "viol")
                twin = case(fam, 0, "flip_a")[0]
                core = set(meta["core_event_ids"])

                def strip(e):
                    return {k: x for k, x in e.items() if k != "run_id"}  # run_id is per-variant by design

                changed = {a["event_id"] for a, b in zip(viol["events"], twin["events"]) if strip(a) != strip(b)}
                self.assertTrue(changed)
                self.assertLessEqual(changed, core, "distractor events must be variant independent")

    def test_core_families_have_three_workers_with_core_steps(self):
        for fam in CORE_FAMILIES:
            with self.subTest(family=fam):
                obs, _, meta = case(fam, 0, "viol")
                by_id = {e["event_id"]: e for e in obs["events"]}
                workers = {by_id[i]["worker_id"] for i in meta["core_event_ids"]}
                self.assertEqual(workers, {"W1", "W2", "W3"})

    def test_requested_by_is_a_worker_label(self):
        for fam in ALL_FAMILIES:
            env = case(fam, 0, "viol")[0]["envelope"]
            self.assertIn(env["requested_by"], {"W1", "W2", "W3"})


class FullViewAgreementTests(unittest.TestCase):
    def test_full_view_rule_monitor_agrees_with_oracle(self):
        for fam in ALL_FAMILIES:
            for seed in range(5):
                for v in variants_for(fam):
                    with self.subTest(family=fam, seed=seed, variant=v):
                        obs, world, _ = case(fam, seed, v)
                        label = oracle(world, obs["envelope"])["label"]
                        res = rule_monitor(obs["events"], obs["envelope"])
                        self.assertEqual(res["verdict"], "violation" if label else "benign")
                        self.assertEqual(res["score"], float(label))

    def test_violation_evidence_is_shown_and_nonempty(self):
        for fam in ALL_FAMILIES:
            with self.subTest(family=fam):
                obs = case(fam, 0, "viol")[0]
                res = rule_monitor(obs["events"], obs["envelope"])
                ids = {e["event_id"] for e in obs["events"]}
                self.assertTrue(res["evidence_event_ids"])
                self.assertLessEqual(set(res["evidence_event_ids"]), ids)
                self.assertEqual(res["evidence_event_ids"], sorted(set(res["evidence_event_ids"])))


class DeterminismTests(unittest.TestCase):
    def test_build_case_is_deterministic(self):
        for fam in ("A2", "B4", "C3", "CX"):
            for v in variants_for(fam):
                a = build_case(fam, 3, v)
                b = build_case(fam, 3, v)
                self.assertEqual(json.dumps(a[0], sort_keys=True), json.dumps(b[0], sort_keys=True))
                self.assertEqual(a[2], b[2])

    def test_seeds_produce_different_cases(self):
        a = case("A1", 0, "viol")[0]
        b = case("A1", 1, "viol")[0]
        self.assertNotEqual([e["event_id"] for e in a["events"]], [e["event_id"] for e in b["events"]])

    def test_ids_are_unique_and_sequences_contiguous(self):
        for fam in ALL_FAMILIES:
            with self.subTest(family=fam):
                obs = case(fam, 1, "viol")[0]
                ids = [e["event_id"] for e in obs["events"]]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual([e["sequence"] for e in obs["events"]], list(range(1, len(ids) + 1)))
                outs = [a for e in obs["events"] for a in e["output_artifact_ids"]]
                self.assertEqual(len(outs), len(set(outs)), "each artifact has exactly one producer")
                self.assertTrue(all(e["run_id"] == obs["run_id"] for e in obs["events"]))


class ObservedHygieneTests(unittest.TestCase):
    def test_observed_record_has_exactly_the_audited_keys(self):
        for fam in ALL_FAMILIES:
            for v in variants_for(fam):
                with self.subTest(family=fam, variant=v):
                    obs = case(fam, 0, v)[0]
                    self.assertEqual(set(obs), OBS_KEYS)
                    for e in obs["events"]:
                        self.assertEqual(set(e), EVENT_KEYS)

    def test_no_label_revealing_strings_in_monitor_visible_values(self):
        for fam in ALL_FAMILIES:
            for v in ("viol", "flip_a"):
                with self.subTest(family=fam, variant=v):
                    obs = case(fam, 0, v)[0]
                    text = json.dumps([obs["envelope"], [{k: x for k, x in e.items() if k != "run_id"}
                                                         for e in obs["events"]]]).lower()
                    for bad in FORBIDDEN_SUBSTRINGS:
                        self.assertNotIn(bad, text)

    def test_target_is_produced_by_the_last_core_event(self):
        for fam in ALL_FAMILIES:
            with self.subTest(family=fam):
                obs, _, meta = case(fam, 0, "viol")
                target = obs["envelope"]["target_artifact_id"]
                producers = [e for e in obs["events"] if target in e["output_artifact_ids"]]
                self.assertEqual(len(producers), 1)
                self.assertEqual(producers[0]["event_id"], meta["core_event_ids"][-1])

    def test_out_of_lineage_families_are_declared_core_families(self):
        self.assertLessEqual(OUT_OF_LINEAGE_FAMILIES, set(CORE_FAMILIES))

    def test_build_case_does_not_mutate_cached_templates(self):
        a = copy.deepcopy(case("B2", 0, "viol")[0])
        build_case("B2", 0, "flip_a")
        build_case("B2", 0, "flip_b")
        self.assertEqual(a, build_case("B2", 0, "viol")[0])


if __name__ == "__main__":
    unittest.main()
