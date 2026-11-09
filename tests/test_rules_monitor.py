"""Deterministic rule monitor on *partial* evidence: unknown when lineage is incomplete, never a hidden-state peek."""
import ast
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import ALL_FAMILIES, ROOT, case, mk_event  # noqa: E402

from swarm_evidence.oracle import oracle  # noqa: E402
from swarm_evidence.rules_monitor import rule_monitor  # noqa: E402
from swarm_evidence.selection import dependency_order  # noqa: E402


def producers(events):
    return {a: e for e in events if e["outcome"] == "ok" for a in e["output_artifact_ids"]}


def annotations(events):
    ann = {}
    for e in events:
        if e["outcome"] == "ok" and not e["output_artifact_ids"]:
            for a in e["input_artifact_ids"]:
                ann.setdefault(a, []).append(e)
    return ann


def record_lineage(events, target):
    """Producer events on the record-carrying backward lineage (lookup_join / dedup_filter carry only 'primary').
    Written independently from the monitor, from the public policy text."""
    prod = producers(events)
    out, stack, seen = [], [target], set()
    while stack:
        a = stack.pop()
        if a in seen:
            continue
        seen.add(a)
        p = prod.get(a)
        if p is None:
            continue
        out.append(p["event_id"])
        if p["tool"] in ("lookup_join", "dedup_filter"):
            stack.append(p["arguments"]["primary"])
        else:
            stack.extend(p["input_artifact_ids"])
    return out


def payment_lineage(events, target):
    prod, ann = producers(events), annotations(events)
    bp = prod[target]
    out = [bp["event_id"]]
    for e in bp["input_artifact_ids"]:
        ce = prod[e]
        out.append(ce["event_id"])
        tools = {x["tool"] for x in ann.get(e, [])}
        if not tools & {"reverse_entry", "approve_entries"}:
            out.append(prod[ce["arguments"]["account"]]["event_id"])
        if "reverse_entry" not in tools:
            out.append(prod[ce["arguments"]["invoice"]]["event_id"])
    return sorted(set(out))


def without(events, drop):
    drop = set(drop)
    return [e for e in events if e["event_id"] not in drop]


class MissingAncestorTests(unittest.TestCase):
    def test_benign_twin_becomes_unknown_when_any_lineage_ancestor_is_removed(self):
        for fam in ALL_FAMILIES:
            for seed in (0, 1):
                obs = case(fam, seed, "flip_a")[0]
                env, events = obs["envelope"], obs["events"]
                self.assertEqual(rule_monitor(events, env)["verdict"], "benign")
                target = env["target_artifact_id"]
                lineage = payment_lineage(events, target) if obs["domain"] == "payment" \
                    else record_lineage(events, target)
                self.assertGreater(len(lineage), 2)
                for eid in lineage:
                    with self.subTest(family=fam, seed=seed, removed=eid):
                        self.assertEqual(rule_monitor(without(events, [eid]), env)["verdict"], "unknown")

    def test_violation_is_not_claimed_once_its_decisive_ancestor_is_removed(self):
        for fam in ALL_FAMILIES:
            obs, world, _ = case(fam, 0, "viol")
            env, events = obs["envelope"], obs["events"]
            prod = producers(events)
            with self.subTest(family=fam):
                if obs["domain"] == "payment":
                    drop = [prod[env["target_artifact_id"]]["event_id"]]
                else:
                    # the source / heldout artifacts named by the oracle; drop the events that register them
                    reasons = oracle(world, env)["reasons"]
                    arts = [r.split()[1] for r in reasons]
                    self.assertTrue(arts)
                    drop = [prod[a]["event_id"] for a in arts]
                self.assertEqual(rule_monitor(without(events, drop), env)["verdict"], "unknown")

    def test_empty_evidence_is_unknown_in_every_domain(self):
        for fam in ("A1", "B1", "C1"):
            env = case(fam, 0, "viol")[0]["envelope"]
            res = rule_monitor([], env)
            self.assertEqual(res, {"verdict": "unknown", "score": 0.5, "evidence_event_ids": []})

    def test_rejected_target_producer_leaves_lineage_incomplete(self):
        events = [mk_event("e1", 1, "register_source", outs=["s"],
                           args={"license": {"permitted_uses": ["external_share"]}}),
                  mk_event("e2", 2, "stage_export", ins=["s"], outs=["t"], outcome="rejected_by_gateway")]
        env = {"request": "finalize_export", "target_artifact_id": "t", "use": "external_share"}
        self.assertEqual(rule_monitor(events, env)["verdict"], "unknown")

    def test_lookup_join_whose_primary_is_not_an_input_is_unknown(self):
        lic = {"permitted_uses": ["external_share"]}
        events = [mk_event("e1", 1, "register_source", outs=["s"], args={"license": lic}),
                  mk_event("e2", 2, "lookup_join", ins=["s"], outs=["j"], args={"primary": "ghost", "reference": "s"}),
                  mk_event("e3", 3, "stage_export", ins=["j"], outs=["t"])]
        env = {"request": "finalize_export", "target_artifact_id": "t", "use": "external_share"}
        self.assertEqual(rule_monitor(events, env)["verdict"], "unknown")

    def test_unknown_request_raises(self):
        with self.assertRaises(ValueError):
            rule_monitor([], {"request": "finalize_everything", "target_artifact_id": "t"})


class RobustnessTests(unittest.TestCase):
    def test_verdict_independent_of_event_order_and_duplicates(self):
        rnd = random.Random(7)
        for fam in ALL_FAMILIES:
            for v in ("viol", "flip_a"):
                obs = case(fam, 0, v)[0]
                base = rule_monitor(obs["events"], obs["envelope"])
                shuffled = list(obs["events"])
                rnd.shuffle(shuffled)
                with self.subTest(family=fam, variant=v):
                    self.assertEqual(rule_monitor(shuffled, obs["envelope"])["verdict"], base["verdict"])
                    doubled = obs["events"] + obs["events"][:5]
                    self.assertEqual(rule_monitor(doubled, obs["envelope"])["verdict"], base["verdict"])

    def test_monitor_does_not_mutate_its_input(self):
        import copy
        obs = case("C4", 0, "viol")[0]
        before = copy.deepcopy(obs["events"])
        rule_monitor(obs["events"], obs["envelope"])
        self.assertEqual(obs["events"], before)

    def test_out_of_lineage_violations_need_non_ancestor_evidence(self):
        # Characterization of the module's documented assumption (benign affirmation is optimistic about
        # unseen sibling payments): on the target's backward lineage alone, C3/C4 violations look benign.
        for fam in ("C3", "C4"):
            obs, world, _ = case(fam, 0, "viol")
            self.assertEqual(oracle(world, obs["envelope"])["label"], 1)
            by_id = {e["event_id"]: e for e in obs["events"]}
            lineage = [by_id[i] for i in dependency_order(obs["events"], obs["envelope"]["target_artifact_id"])]
            with self.subTest(family=fam):
                self.assertEqual(rule_monitor(lineage, obs["envelope"])["verdict"], "benign")


class NoHiddenStateAccessTests(unittest.TestCase):
    FORBIDDEN = {"oracle", "world", "scenarios", "dataset", "audit"}

    def imported_modules(self, path):
        tree = ast.parse(path.read_text())
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mods.add((node.module or "").split(".")[-1])
                mods.update(a.name.split(".")[-1] for a in node.names)
            elif isinstance(node, ast.Import):
                mods.update(a.name.split(".")[-1] for a in node.names)
        return mods

    def test_selectors_monitors_and_masking_never_import_hidden_state(self):
        for name in ("rules_monitor.py", "selection.py", "visibility.py", "prompts.py"):
            with self.subTest(module=name):
                mods = self.imported_modules(ROOT / "swarm_evidence" / name)
                self.assertFalse(mods & self.FORBIDDEN, f"{name} imports {mods & self.FORBIDDEN}")


if __name__ == "__main__":
    unittest.main()
