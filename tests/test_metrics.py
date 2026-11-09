"""Known-answer metric tests and family-clustered bootstrap pairing."""
import os
import random
import sys
import types
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _support  # noqa: E402,F401

from swarm_evidence import metrics  # noqa: E402
from swarm_evidence.metrics import auprc, auroc, cluster_bootstrap_auroc, cluster_bootstrap_diff, wilson  # noqa: E402


class AurocTests(unittest.TestCase):
    def test_single_class_is_none(self):
        self.assertIsNone(auroc([0.1, 0.9], [1, 1]))
        self.assertIsNone(auroc([0.1, 0.9], [0, 0]))
        self.assertIsNone(auroc([], []))

    def test_known_values(self):
        self.assertEqual(auroc([0.9, 0.8, 0.2, 0.1], [1, 1, 0, 0]), 1.0)
        self.assertEqual(auroc([0.1, 0.2, 0.8, 0.9], [1, 1, 0, 0]), 0.0)
        self.assertEqual(auroc([0.5, 0.5, 0.5, 0.5], [1, 0, 1, 0]), 0.5)
        self.assertEqual(auroc([0.1, 0.4, 0.35, 0.8], [0, 0, 1, 1]), 0.75)
        # one tie between a positive and a negative counts one half
        self.assertEqual(auroc([0.7, 0.5, 0.5], [1, 1, 0]), 0.75)

    def test_rule_monitor_scores(self):
        # violation=1.0, unknown=0.5, benign=0.0
        self.assertEqual(auroc([1.0, 0.5, 0.5, 0.0], [1, 1, 0, 0]), 0.875)


class AuprcTests(unittest.TestCase):
    def test_no_positives_is_none(self):
        self.assertIsNone(auprc([0.2, 0.3], [0, 0]))

    def test_known_values(self):
        self.assertAlmostEqual(auprc([0.9, 0.8, 0.2], [1, 1, 0]), 1.0)
        self.assertAlmostEqual(auprc([0.9, 0.8, 0.7, 0.6], [1, 0, 1, 0]), 0.5 + 0.5 * 2 / 3)
        self.assertAlmostEqual(auprc([0.9, 0.1], [0, 1]), 0.5)
        self.assertAlmostEqual(auprc([0.3, 0.3], [1, 1]), 1.0)

    def test_ties_are_pessimistic(self):
        self.assertAlmostEqual(auprc([0.5, 0.5], [1, 0]), 0.5)
        self.assertAlmostEqual(auprc([0.9, 0.5, 0.5], [1, 1, 0]), 0.5 + 0.5 * 2 / 3)


class WilsonTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(wilson(0, 0), (None, None))

    def test_known_values_and_bounds(self):
        lo, hi = wilson(5, 10)
        self.assertAlmostEqual(lo, 0.2366, places=3)
        self.assertAlmostEqual(hi, 0.7634, places=3)
        lo, hi = wilson(0, 10)
        self.assertEqual(lo, 0.0)
        self.assertAlmostEqual(hi, 0.2775, places=3)
        lo, hi = wilson(10, 10)
        self.assertAlmostEqual(lo, 0.7225, places=3)
        self.assertAlmostEqual(hi, 1.0, places=12)  # exact 1 mathematically; float gives 0.9999999999999999
        for k in range(0, 21):
            lo, hi = wilson(k, 20)
            self.assertLessEqual(0.0, lo)
            self.assertLessEqual(lo, k / 20 + 1e-12)
            self.assertLessEqual(k / 20, hi + 1e-12)
            self.assertLessEqual(hi, 1.0)


def rows(spec):
    """spec: list of (run_id, score, label, cluster)."""
    return {r: (s, y, c) for r, s, y, c in spec}


class ClusterBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.base = [("r1", 0.9, 1, "F1"), ("r2", 0.1, 0, "F1"), ("r3", 0.8, 1, "F2"), ("r4", 0.3, 0, "F2"),
                     ("r5", 0.4, 1, "F3"), ("r6", 0.6, 0, "F3")]

    def test_arms_must_be_paired(self):
        a = rows(self.base)
        b = rows(self.base[:-1])
        with self.assertRaises(AssertionError):
            cluster_bootstrap_diff(a, b, cluster_key=None, n_boot=10)
        b2 = dict(rows(self.base), r_extra=(0.5, 0, "F9"))
        with self.assertRaises(AssertionError):
            cluster_bootstrap_diff(a, b2, cluster_key=None, n_boot=10)

    def test_identical_arms_give_zero_interval(self):
        a = rows(self.base)
        point, lo, hi, n_clusters, n_valid = cluster_bootstrap_diff(a, dict(a), cluster_key=None, n_boot=500)
        self.assertEqual((point, lo, hi), (0.0, 0.0, 0.0))
        self.assertEqual(n_clusters, 3)
        self.assertGreater(n_valid, 0)
        self.assertLessEqual(n_valid, 500)

    def test_point_estimate_is_the_paired_auroc_difference(self):
        a = rows(self.base)
        b = rows([(r, 1 - s, y, c) for r, s, y, c in self.base])
        point, *_ = cluster_bootstrap_diff(a, b, cluster_key=None, n_boot=50)
        ys = [y for _, _, y, _ in self.base]
        expected = auroc([s for _, s, _, _ in self.base], ys) - auroc([1 - s for _, s, _, _ in self.base], ys)
        self.assertAlmostEqual(point, expected)

    def test_resamples_whole_clusters(self):
        seen = []

        class RecordingRandom(random.Random):
            def choice(self, seq):
                seen.append(tuple(seq))
                return super().choice(seq)

        a = rows(self.base)
        b = rows([(r, 0.5, y, c) for r, _, y, c in self.base])
        with mock.patch.object(metrics, "random", types.SimpleNamespace(Random=RecordingRandom)):
            cluster_bootstrap_diff(a, b, cluster_key=None, n_boot=200, seed=3)
        self.assertEqual(len(seen), 200 * 3, "one draw per cluster per replicate")
        self.assertEqual(set(seen), {("F1", "F2", "F3")}, "draws must be over cluster IDs, never run IDs")

    def test_interval_endpoints_come_from_cluster_unions(self):
        # with 2 clusters every replicate is X, Y or X+Y; any row-level resampling would create other values
        spec = [("x1", 0.9, 1, "X"), ("x2", 0.2, 0, "X"), ("x3", 0.6, 0, "X"),
                ("y1", 0.4, 1, "Y"), ("y2", 0.5, 0, "Y")]
        a = rows(spec)
        b = rows([(r, 0.5, y, c) for r, _, y, c in spec])

        def d(ids):
            ys = [a[i][1] for i in ids]
            return auroc([a[i][0] for i in ids], ys) - auroc([b[i][0] for i in ids], ys)

        allowed = {round(d(["x1", "x2", "x3"]), 12), round(d(["y1", "y2"]), 12),
                   round(d(["x1", "x2", "x3", "y1", "y2"]), 12)}
        _, lo, hi, n_clusters, _ = cluster_bootstrap_diff(a, b, cluster_key=None, n_boot=400, seed=1)
        self.assertEqual(n_clusters, 2)
        self.assertIn(round(lo, 12), allowed)
        self.assertIn(round(hi, 12), allowed)
        self.assertLessEqual(lo, hi)

    def test_deterministic_given_seed(self):
        a = rows(self.base)
        b = rows([(r, 0.5, y, c) for r, _, y, c in self.base])
        self.assertEqual(cluster_bootstrap_diff(a, b, None, n_boot=300, seed=0),
                         cluster_bootstrap_diff(a, b, None, n_boot=300, seed=0))

    def test_single_class_everywhere_has_no_valid_replicates(self):
        a = rows([("r1", 0.9, 1, "F1"), ("r2", 0.2, 1, "F2")])
        point, lo, hi, n_clusters, n_valid = cluster_bootstrap_diff(a, dict(a), None, n_boot=50)
        self.assertEqual((point, lo, hi, n_valid), (None, None, None, 0))
        self.assertEqual(n_clusters, 2)

    def test_single_arm_interval(self):
        perfect = rows([("r1", 0.9, 1, "F1"), ("r2", 0.1, 0, "F1"), ("r3", 0.7, 1, "F2"), ("r4", 0.2, 0, "F2")])
        self.assertEqual(cluster_bootstrap_auroc(perfect, n_boot=200), (1.0, 1.0))
        one_class = rows([("r1", 0.9, 1, "F1"), ("r2", 0.1, 1, "F2")])
        self.assertEqual(cluster_bootstrap_auroc(one_class, n_boot=50), (None, None))


if __name__ == "__main__":
    unittest.main()
