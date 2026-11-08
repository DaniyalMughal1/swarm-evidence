"""The report-number audit: scalars, sub-tables read as a whole, and missing keys."""
import json
import tempfile
import unittest
from pathlib import Path

from swarm_evidence.audit import audit_report

SUMMARY = {
    "models": {"qwen3.5-397b": {
        "arms": {"dependency@2000": {"auroc": 0.7544444, "verdict_violation_fp": 12,
                                     "auroc_ci_family": [0.5027, 0.95]}},
        "verdicts_by_family": {"dependency@2000": {"A4": {"viol->violation": 5, "legit->violation": 5}}},
    }},
}


class AuditReportTests(unittest.TestCase):
    def run_audit(self, used):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "report").mkdir()
            (root / "results/analysis").mkdir(parents=True)
            (root / "results/analysis/summary.json").write_text(json.dumps(SUMMARY))
            (root / "report/numbers_used.json").write_text(json.dumps(used))
            return audit_report(root)

    def test_matching_scalars_list_items_and_subtables_pass(self):
        r = self.run_audit({
            "models/qwen3.5-397b/arms/dependency@2000/auroc": 0.754,
            "models/qwen3.5-397b/arms/dependency@2000/verdict_violation_fp": 12,
            "models/qwen3.5-397b/arms/dependency@2000/auroc_ci_family/0": 0.503,
            "models/qwen3.5-397b/verdicts_by_family/dependency@2000/A4": {"viol->violation": 5, "legit->violation": 5},
        })
        self.assertTrue(r["ok"], r)
        self.assertEqual(r["checked"], 4)

    def test_changed_scalar_fails(self):
        r = self.run_audit({"models/qwen3.5-397b/arms/dependency@2000/verdict_violation_fp": 11})
        self.assertFalse(r["ok"])

    def test_changed_float_beyond_rounding_fails(self):
        r = self.run_audit({"models/qwen3.5-397b/arms/dependency@2000/auroc": 0.76})
        self.assertFalse(r["ok"])

    def test_changed_subtable_fails(self):
        r = self.run_audit({"models/qwen3.5-397b/verdicts_by_family/dependency@2000/A4": {"viol->violation": 4}})
        self.assertFalse(r["ok"])

    def test_missing_key_fails(self):
        r = self.run_audit({"models/qwen3.5-397b/arms/lexical@2000/auroc": 0.55})
        self.assertFalse(r["ok"])
        self.assertIn("not in summary", r["problems"][0])

    def test_missing_subtable_fails(self):
        r = self.run_audit({"models/qwen3.5-397b/verdicts_by_family/dependency@2000/B2": {"viol->violation": 5}})
        self.assertFalse(r["ok"])


if __name__ == "__main__":
    unittest.main()
