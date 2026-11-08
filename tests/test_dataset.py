"""Dataset generation, composition-validity gate, leakage audit, split hygiene and committed-file consistency.

Generation runs into a temporary directory (~0.3 s); the committed ``data/`` files are only read.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import ROOT, case  # noqa: E402

from swarm_evidence.audit import DATA_FILES, OBS_KEYS, leakage_audit, validate_all  # noqa: E402
from swarm_evidence.dataset import N_SEEDS_CONTROL, N_SEEDS_CORE, generate, load_jsonl, minimal_evidence  # noqa: E402
from swarm_evidence.oracle import oracle  # noqa: E402
from swarm_evidence.protocol import PILOT_CASES, STAGES, stage_run_ids  # noqa: E402
from swarm_evidence.rules_monitor import rule_monitor  # noqa: E402
from swarm_evidence.scenarios import CONTROLS, FAMILIES  # noqa: E402

N_BASE = len(FAMILIES) * N_SEEDS_CORE + len(CONTROLS) * N_SEEDS_CONTROL


class GeneratedDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        cls.summary = generate(cls.root)
        cls.obs = load_jsonl(cls.root / "data/observed/trajectories.jsonl")
        cls.cases = load_jsonl(cls.root / "data/manifest/cases.jsonl")
        cls.labels = load_jsonl(cls.root / "data/eval/labels.jsonl")
        cls.validity = load_jsonl(cls.root / "data/eval/validity.jsonl")

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_gate_passes_for_every_base_case(self):
        self.assertEqual(self.summary["n_base_cases"], N_BASE)
        self.assertEqual(self.summary["n_trajectories"], 2 * N_BASE)
        self.assertEqual(self.summary["gate_failed"], [])
        self.assertEqual(self.summary["gate_passed"], N_BASE)
        for g in self.validity:
            with self.subTest(base=g["base_case_id"]):
                self.assertTrue(g["labels_ok"] and g["twin_structure_match"] and g["full_view_rule_agrees"])
                self.assertTrue(g["gold_nonempty"])
                if not g["control"]:
                    self.assertTrue(g["counterfactual_ok"])
                    self.assertTrue(g["gold_multi_worker"])
                    self.assertTrue(g["flip_b_same_length"])

    def test_generation_is_byte_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            again = generate(Path(d))
        self.assertEqual(again["hashes"], self.summary["hashes"])

    def test_leakage_and_mask_audits_pass(self):
        rep = validate_all(self.root)
        self.assertTrue(rep["ok"], rep)
        self.assertTrue(leakage_audit(self.root)["ok"])

    def test_released_files_separate_labels_from_observations(self):
        for o in self.obs:
            self.assertEqual(set(o), OBS_KEYS)
        allowed_case_keys = {"run_id", "base_case_id", "family", "domain", "split", "subset", "control", "n_events"}
        for c in self.cases:
            self.assertEqual(set(c), allowed_case_keys)
        self.assertEqual({o["run_id"] for o in self.obs}, {c["run_id"] for c in self.cases})
        self.assertEqual({o["run_id"] for o in self.obs}, {r["run_id"] for r in self.labels})

    def test_labels_match_oracle_and_gold_is_shown_evidence(self):
        obs_by_id = {o["run_id"]: o for o in self.obs}
        balance = defaultdict(list)
        for r in self.labels:
            fam, seed = r["base_case_id"].split(":")
            o, world, _ = case(fam, int(seed), r["variant"])
            with self.subTest(run=r["run_id"]):
                self.assertEqual(o["run_id"], r["run_id"])
                self.assertEqual(oracle(world, o["envelope"])["label"], r["label"])
                ids = {e["event_id"] for e in obs_by_id[r["run_id"]]["events"]}
                self.assertTrue(r["gold_event_ids"])
                self.assertLessEqual(set(r["gold_event_ids"]), ids)
            balance[r["base_case_id"]].append(r["label"])
        self.assertTrue(all(sorted(v) == [0, 1] for v in balance.values()), "each base case is one balanced pair")

    def test_split_hygiene(self):
        fam_split = defaultdict(set)
        base_split = defaultdict(set)
        for c in self.cases:
            fam_split[c["family"]].add((c["split"], c["subset"]))
            base_split[c["base_case_id"]].add(c["subset"])
        self.assertTrue(all(len(v) == 1 for v in fam_split.values()), "a family never straddles splits")
        self.assertTrue(all(len(v) == 1 for v in base_split.values()), "twins stay together")
        subsets = {next(iter(v))[1] for v in fam_split.values()}
        self.assertEqual(subsets, {"prompt_design", "calibration", "test", "control"})
        per_domain_test = defaultdict(set)
        for f, v in fam_split.items():
            if next(iter(v))[1] == "test":
                per_domain_test[f[0]].add(f)
        self.assertTrue(all(len(v) >= 2 for v in per_domain_test.values()), "multiple held-out families per domain")

    def test_observed_file_is_shuffled_not_grouped_by_label(self):
        lab = {r["run_id"]: r["label"] for r in self.labels}
        seq = [lab[o["run_id"]] for o in self.obs]
        self.assertNotEqual(seq, sorted(seq))
        self.assertNotEqual(seq, sorted(seq, reverse=True))

    def test_stage_run_ids(self):
        pilot = stage_run_ids("pilot", self.cases)
        self.assertEqual(len(pilot), 2 * len(PILOT_CASES))
        self.assertEqual(len(stage_run_ids("stage1", self.cases)),
                         2 * N_SEEDS_CORE * sum(1 for f in FAMILIES.values() if f[3] == "test"))
        self.assertEqual(len(stage_run_ids("controls", self.cases)), 2 * N_SEEDS_CONTROL * len(CONTROLS))
        test_ids = set(stage_run_ids("stage1", self.cases))
        for name in ("pilot", "calibration", "controls"):
            self.assertFalse(test_ids & set(stage_run_ids(name, self.cases)), name)
        for name in STAGES:
            self.assertEqual(stage_run_ids(name, self.cases), sorted(stage_run_ids(name, self.cases)))


class LeakageAuditDetectsProblems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.clean = Path(cls._tmp.name) / "clean"
        generate(cls.clean)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def tampered(self, mutate):
        d = Path(tempfile.mkdtemp(dir=self._tmp.name)) / "root"
        shutil.copytree(self.clean, d)
        p = d / "data/observed/trajectories.jsonl"
        rows = load_jsonl(p)
        mutate(rows)
        p.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
        return leakage_audit(d)

    def test_extra_label_field_is_flagged(self):
        def m(rows):
            rows[0]["label"] = 1
        rep = self.tampered(m)
        self.assertFalse(rep["ok"])
        self.assertTrue(any("observed keys" in p for p in rep["problems"]))

    def test_extra_event_field_is_flagged(self):
        def m(rows):
            rows[1]["events"][0]["core"] = True
        self.assertTrue(any("event keys" in p for p in self.tampered(m)["problems"]))

    def test_revealing_string_is_flagged(self):
        def m(rows):
            rows[2]["events"][3]["rationale"] = "This is the gold violating step."
        self.assertTrue(any("contains" in p for p in self.tampered(m)["problems"]))

    def test_twin_structure_mismatch_is_flagged(self):
        def m(rows):
            rows[0]["events"][0]["tool"] = "something_else"
        self.assertTrue(any("twin structure differs" in p for p in self.tampered(m)["problems"]))


class MinimalEvidenceTests(unittest.TestCase):
    def test_gold_is_one_minimal(self):
        for fam, v in (("A4", "viol"), ("A4", "flip_a"), ("B3", "viol"), ("C2", "flip_a"), ("C3", "viol")):
            obs, world, _ = case(fam, 0, v)
            label = oracle(world, obs["envelope"])["label"]
            want = "violation" if label else "benign"
            gold = minimal_evidence(obs, label)
            by_id = {e["event_id"]: e for e in obs["events"]}
            with self.subTest(family=fam, variant=v):
                self.assertEqual(rule_monitor([by_id[i] for i in gold], obs["envelope"])["verdict"], want)
                for i in gold:
                    rest = [by_id[j] for j in gold if j != i]
                    self.assertNotEqual(rule_monitor(rest, obs["envelope"])["verdict"], want, f"{i} is redundant")
                self.assertGreaterEqual(len({by_id[i]["worker_id"] for i in gold}), 2)

    def test_unreachable_label_gives_empty_gold(self):
        obs = case("A1", 0, "flip_a")[0]
        self.assertEqual(minimal_evidence(obs, 1), [])


@unittest.skipUnless((ROOT / "data/observed/trajectories.jsonl").exists(), "committed data/ not present")
class CommittedDataTests(unittest.TestCase):
    def test_committed_files_match_regeneration_from_current_code(self):
        with tempfile.TemporaryDirectory() as d:
            summary = generate(Path(d))
        for rel in DATA_FILES:
            with self.subTest(file=rel):
                committed = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
                self.assertEqual(committed, summary["hashes"][rel], f"{rel} is stale relative to the generator")

    def test_committed_files_pass_the_audit_and_gate(self):
        self.assertTrue(leakage_audit(ROOT)["ok"])
        val = load_jsonl(ROOT / "data/eval/validity.jsonl")
        self.assertEqual(len(val), N_BASE)
        self.assertTrue(all(v["passed"] for v in val))


if __name__ == "__main__":
    unittest.main()
