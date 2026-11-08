"""Model-independent evaluation: rule monitor on exactly the evidence each selector chooses."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import case  # noqa: E402

from swarm_evidence.dataset import minimal_evidence  # noqa: E402
from swarm_evidence.offline import aggregate_rule, evaluate, summarize  # noqa: E402
from swarm_evidence.oracle import oracle  # noqa: E402


def r(verdict):
    return {"verdict": verdict, "score": {"violation": 1.0, "benign": 0.0, "unknown": 0.5}[verdict]}


class AggregateTests(unittest.TestCase):
    def test_isolated_aggregation(self):
        self.assertEqual(aggregate_rule([r("benign"), r("violation"), r("unknown")]), (1.0, "violation"))
        self.assertEqual(aggregate_rule([r("benign"), r("benign"), r("benign")]), (0.0, "benign"))
        self.assertEqual(aggregate_rule([r("benign"), r("unknown"), r("benign")]), (0.5, "unknown"))
        self.assertEqual(aggregate_rule([r("unknown")]), (0.5, "unknown"))


class EvaluateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.obs, cls.labels, cls.cases = {}, {}, {}
        for fam in ("A2", "B2", "C2", "C4"):
            for v in ("viol", "flip_a"):
                o, world, meta = case(fam, 0, v)
                lab = oracle(world, o["envelope"])["label"]
                rid = o["run_id"]
                cls.obs[rid] = o
                cls.labels[rid] = {"label": lab, "gold_event_ids": minimal_evidence(o, lab)}
                cls.cases[rid] = {"family": fam, "split": meta["split"]}
        cls.rows = evaluate(sorted(cls.obs), cls.obs, cls.labels, cls.cases,
                            ["dependency", "lexical", "chronological", "full"], [2000, 6000])

    def test_row_fields_are_consistent(self):
        self.assertEqual(len(self.rows), len(self.obs) * 4 * 2)
        for row in self.rows:
            with self.subTest(method=row["method"], cap=row["cap"], run=row["run_id"]):
                self.assertTrue(0.0 <= row["gold_recall"] <= 1.0)
                self.assertEqual(row["gold_complete"], row["gold_recall"] == 1.0)
                self.assertLessEqual(row["n_selected"], row["n_events"])
                if row["method"] != "full":
                    self.assertLessEqual(row["selected_tokens"], row["cap"])
                self.assertIn(row["rule_verdict"], ("violation", "benign", "unknown"))

    def test_full_view_rule_matches_labels_and_never_false_alarms(self):
        for row in self.rows:
            if row["method"] == "full":
                self.assertTrue(row["gold_complete"])
                self.assertEqual(row["rule_verdict"], "violation" if row["label"] else "benign")
            # a violation verdict needs a complete witness in the shown evidence: no false alarms on benign twins
            if row["label"] == 0:
                self.assertNotEqual(row["rule_verdict"], "violation", row)

    def test_summarize_counts(self):
        summ = {(s["cap"], s["method"]): s for s in summarize(self.rows)}
        full = summ[(2000, "full")]
        self.assertEqual((full["n"], full["rule_auroc"], full["rule_unknown"]), (len(self.obs), 1.0, 0.0))
        self.assertEqual(full["rule_tp"], len(self.obs) // 2)
        self.assertEqual(full["rule_fp"], 0)


if __name__ == "__main__":
    unittest.main()
