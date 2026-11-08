"""Strict model-output parser, .env loading and pricing. Never instantiates AdaptionMonitor (no SDK, no network)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import ROOT  # noqa: E402

from swarm_evidence.adaption_monitor import PRICES, VERDICTS, load_dotenv, max_cost, parse_output  # noqa: E402

SHOWN = ["e-000001", "e-000002", "e-000003"]


def payload(**over):
    obj = {"score": 0.8, "verdict": "violation", "evidence_event_ids": ["e-000001"], "reason": "Restricted source."}
    obj.update(over)
    return json.dumps(obj)


class ParseValidTests(unittest.TestCase):
    def test_plain_json(self):
        res = parse_output(payload(), SHOWN)
        self.assertTrue(res["valid"])
        self.assertIsNone(res["error"])
        self.assertEqual(res["score"], 0.8)
        self.assertEqual(res["verdict"], "violation")
        self.assertEqual(res["evidence_event_ids"], ["e-000001"])
        self.assertEqual(res["unsupported_ids"], [])
        self.assertEqual(res["extra_keys"], [])

    def test_single_fence_with_or_without_language_tag(self):
        for text in ("```json\n" + payload() + "\n```", "```\n" + payload() + "\n```",
                     "  ```json  \n" + payload() + "\n```\n"):
            with self.subTest(text=text[:12]):
                self.assertTrue(parse_output(text, SHOWN)["valid"])

    def test_boundary_scores_and_integers(self):
        for s in (0, 1, 0.0, 1.0, 0.5):
            with self.subTest(score=s):
                res = parse_output(payload(score=s), SHOWN)
                self.assertTrue(res["valid"])
                self.assertIsInstance(res["score"], float)

    def test_every_verdict_accepted(self):
        for v in VERDICTS:
            self.assertTrue(parse_output(payload(verdict=v), SHOWN)["valid"])

    def test_unsupported_ids_recorded_not_fatal(self):
        res = parse_output(payload(evidence_event_ids=["e-000002", "e-999999", "e-000002"]), SHOWN)
        self.assertTrue(res["valid"])
        self.assertEqual(res["unsupported_ids"], ["e-999999"])
        self.assertEqual(res["evidence_event_ids"], ["e-000002", "e-999999", "e-000002"])

    def test_empty_evidence_list_is_valid(self):
        res = parse_output(payload(verdict="insufficient_evidence", evidence_event_ids=[]), SHOWN)
        self.assertTrue(res["valid"])
        self.assertEqual(res["unsupported_ids"], [])

    def test_extra_keys_recorded(self):
        res = parse_output(payload(confidence="high", aaa=1), SHOWN)
        self.assertTrue(res["valid"])
        self.assertEqual(res["extra_keys"], ["aaa", "confidence"])


class ParseInvalidTests(unittest.TestCase):
    def assertError(self, text, error):
        res = parse_output(text, SHOWN)
        self.assertFalse(res["valid"], text)
        self.assertEqual(res["error"], error, text)
        self.assertIsNone(res["score"])
        return res

    def test_no_text_and_bad_json(self):
        self.assertError(None, "no_text")
        self.assertError("", "json_decode")
        self.assertError("I think this is a violation.", "json_decode")
        self.assertError("Answer: " + payload(), "json_decode")
        self.assertError(payload()[:-1], "json_decode")
        self.assertError("{'score': 0.5}", "json_decode")

    def test_two_fenced_blocks_rejected(self):
        two = "```json\n" + payload() + "\n```\n```json\n" + payload(score=0.1) + "\n```"
        self.assertError(two, "json_decode")

    def test_non_object_rejected(self):
        self.assertError("[" + payload() + "]", "not_object")
        self.assertError("0.7", "not_object")

    def test_bad_scores(self):
        for s in (-0.01, 1.01, 2, "0.5", None, [0.5]):
            with self.subTest(score=s):
                self.assertError(payload(score=s), "bad_score")
        self.assertError(payload(score=True), "bad_score")
        self.assertError(payload(score=False), "bad_score")
        for literal in ("NaN", "Infinity", "-Infinity", "1e400"):
            with self.subTest(literal=literal):
                text = payload(score=0.5).replace("0.5", literal, 1)
                self.assertError(text, "bad_score")

    def test_missing_fields(self):
        for field, error in (("score", "bad_score"), ("verdict", "bad_verdict"),
                             ("evidence_event_ids", "bad_evidence_ids"), ("reason", "bad_reason")):
            with self.subTest(field=field):
                obj = json.loads(payload())
                del obj[field]
                self.assertError(json.dumps(obj), error)

    def test_bad_verdicts(self):
        for v in ("Violation", "unknown", "abstain", "", None, ["violation"], 1):
            with self.subTest(verdict=v):
                self.assertError(payload(verdict=v), "bad_verdict")

    def test_bad_evidence_ids(self):
        for ids in ("e-000001", None, {"id": "e-000001"}, ["e-000001", 7], [["e-000001"]], [None]):
            with self.subTest(ids=ids):
                self.assertError(payload(evidence_event_ids=ids), "bad_evidence_ids")

    def test_bad_reason(self):
        for r in (None, 3, ["x"]):
            with self.subTest(reason=r):
                self.assertError(payload(reason=r), "bad_reason")

    # SOURCE BUG: adaption_monitor.py:78 calls math.isfinite(s) on any int, which raises OverflowError for an
    # integer too large for a float, so the "strict parser" crashes instead of returning error="bad_score".
    # Concrete input: '{"score": 999...9 (400 digits), "verdict": "benign", "evidence_event_ids": [], "reason": "x"}'.
    # In runner.execute the exception escapes after the (billed) response arrived, so the call row is never stored.
    # Fixed after the freeze (see protocol/POST_FREEZE_CHANGES.md); kept as a regression test.
    def test_huge_integer_score_is_rejected_not_raised(self):
        text = '{"score": ' + "9" * 400 + ', "verdict": "benign", "evidence_event_ids": [], "reason": "x"}'
        self.assertError(text, "bad_score")


class DotenvTests(unittest.TestCase):
    def test_loads_names_only_and_skips_comments_blanks_and_empty_values(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / ".env"
            p.write_text("# comment\n\nSWARM_TEST_A=alpha\nSWARM_TEST_B = \"quoted value\"\nSWARM_TEST_C='single'\n"
                         "SWARM_TEST_EMPTY=\nnot a pair\nSWARM_TEST_EQ=a=b=c\n")
            with mock.patch.dict(os.environ, {}, clear=False):
                loaded = load_dotenv(p)
                self.assertEqual(loaded, ["SWARM_TEST_A", "SWARM_TEST_B", "SWARM_TEST_C", "SWARM_TEST_EQ"])
                self.assertEqual(os.environ["SWARM_TEST_A"], "alpha")
                self.assertEqual(os.environ["SWARM_TEST_B"], "quoted value")
                self.assertEqual(os.environ["SWARM_TEST_C"], "single")
                self.assertEqual(os.environ["SWARM_TEST_EQ"], "a=b=c")
                self.assertNotIn("SWARM_TEST_EMPTY", os.environ)
                for name in loaded:
                    self.assertNotIn(os.environ[name], loaded, "return value must never contain secret values")
        self.assertNotIn("SWARM_TEST_A", os.environ, "mock.patch.dict restores the environment")

    def test_missing_file_is_a_noop(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(load_dotenv(Path(d) / "absent.env"), [])


class PricingTests(unittest.TestCase):
    def test_max_cost_arithmetic(self):
        pin, pout = PRICES["qwen3.5-397b"]
        self.assertAlmostEqual(max_cost("qwen3.5-397b", 1_000_000, 0), pin)
        self.assertAlmostEqual(max_cost("qwen3.5-397b", 0, 1_000_000), pout)
        self.assertAlmostEqual(max_cost("gemma-4-31b-it", 2600, 384), (2600 * 0.09 + 384 * 0.34) / 1e6)

    def test_unknown_model_is_an_error_not_free(self):
        with self.assertRaises(KeyError):
            max_cost("unpriced-model", 10, 10)


class OfflineImportTests(unittest.TestCase):
    def test_offline_modules_do_not_import_the_sdk(self):
        code = ("import sys; sys.path.insert(0, %r)\n"
                "import swarm_evidence.adaption_monitor, swarm_evidence.runner, swarm_evidence.selection, "
                "swarm_evidence.visibility, swarm_evidence.rules_monitor, swarm_evidence.dataset, "
                "swarm_evidence.metrics, swarm_evidence.offline, swarm_evidence.audit\n"
                "bad = [m for m in ('adaption', 'matplotlib', 'httpx', 'numpy') if m in sys.modules]\n"
                "print(','.join(bad))\n" % str(ROOT))
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=str(ROOT), timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
