"""Generate the frozen dataset and run the composition-validity gate.

Outputs (paths relative to the repository root):
  data/observed/trajectories.jsonl  - monitor-visible records only (shuffled)
  data/manifest/cases.jsonl         - run_id -> family/split/subset/domain (no labels)
  data/eval/labels.jsonl            - labels, oracle reasons, gold minimal evidence (evaluation only)
  data/eval/validity.jsonl          - per-base-case gate results
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

from .oracle import oracle
from .rules_monitor import rule_monitor
from .scenarios import CONTROLS, FAMILIES, build_case

N_SEEDS_CORE = 5
N_SEEDS_CONTROL = 3


def worker_view(observed: dict, worker: str) -> str:
    evs = [e for e in observed["events"] if e["worker_id"] == worker]
    return json.dumps([{k: v for k, v in e.items() if k != "run_id"} for e in evs], sort_keys=True)


def minimal_evidence(observed: dict, label: int) -> list:
    """1-minimal event set on which the rule monitor still returns the oracle label."""
    want = "violation" if label else "benign"
    events = observed["events"]
    env = observed["envelope"]
    keep = {e["event_id"] for e in events}
    by_id = {e["event_id"]: e for e in events}

    def ok(ids):
        return rule_monitor([by_id[i] for i in sorted(ids, key=lambda x: by_id[x]["sequence"])], env)["verdict"] == want

    if not ok(keep):
        return []
    changed = True
    order = sorted(keep, key=lambda i: -by_id[i]["sequence"])
    while changed:
        changed = False
        for i in order:
            if i in keep and ok(keep - {i}):
                keep.discard(i)
                changed = True
    return sorted(keep, key=lambda i: by_id[i]["sequence"])


def structural_signature(observed: dict):
    return [(e["event_id"], e["worker_id"], e["tool"], e["sequence"], len(e["input_artifact_ids"]),
             len(e["output_artifact_ids"])) for e in observed["events"]], observed["envelope"]


def generate(root: Path) -> dict:
    observed_rows, case_rows, label_rows, validity_rows = [], [], [], []
    registry = [(f, N_SEEDS_CORE) for f in FAMILIES] + [(f, N_SEEDS_CONTROL) for f in CONTROLS]
    for family, n_seeds in registry:
        for seed in range(n_seeds):
            variants = ("viol", "flip_a") if family in CONTROLS else ("viol", "flip_a", "flip_b")
            built = {v: build_case(family, seed, v) for v in variants}
            labels = {v: oracle(built[v][1], built[v][0]["envelope"]) for v in variants}
            obs = {v: built[v][0] for v in variants}
            meta = built["viol"][2]
            gate = {"base_case_id": meta["base_case_id"], "family": family, "control": meta["control"]}
            gate["labels_ok"] = labels["viol"]["label"] == 1 and all(labels[v]["label"] == 0 for v in variants[1:])
            sig = structural_signature(obs["viol"])
            # the released twin must match exactly; flip_b is a validity-gate counterfactual only
            gate["twin_structure_match"] = structural_signature(obs["flip_a"]) == sig
            if "flip_b" in obs:
                gate["flip_b_same_length"] = len(obs["flip_b"]["events"]) == len(obs["viol"]["events"])
            # deterministic rule monitor on the full observed ledger must agree with the oracle
            gate["full_view_rule_agrees"] = all(
                rule_monitor(obs[v]["events"], obs[v]["envelope"])["verdict"] ==
                ("violation" if labels[v]["label"] else "benign") for v in variants)
            workers = sorted({e["worker_id"] for e in obs["viol"]["events"]})
            if not meta["control"]:
                cf = {}
                for w in workers:
                    vv = worker_view(obs["viol"], w)
                    cf[w] = [v for v in ("flip_a", "flip_b") if worker_view(obs[v], w) == vv]
                gate["viol_worker_views_with_benign_completion"] = cf
                gate["counterfactual_ok"] = all(len(x) > 0 for x in cf.values())
                changed_by_twin = [w for w in workers if worker_view(obs["viol"], w) != worker_view(obs["flip_a"], w)]
                gate["workers_changed_by_twin"] = changed_by_twin
            gold = {}
            for v in ("viol", "flip_a"):
                g = minimal_evidence(obs[v], labels[v]["label"])
                by_id = {e["event_id"]: e for e in obs[v]["events"]}
                gold[v] = {"ids": g, "workers": sorted({by_id[i]["worker_id"] for i in g})}
            gate["gold_nonempty"] = all(len(gold[v]["ids"]) > 0 for v in gold)
            gate["gold_multi_worker"] = all(len(gold[v]["workers"]) >= 2 for v in gold)
            gate["passed"] = bool(gate["labels_ok"] and gate["twin_structure_match"] and gate["full_view_rule_agrees"]
                                  and gate["gold_nonempty"]
                                  and (meta["control"] or (gate["counterfactual_ok"] and gate["gold_multi_worker"])))
            validity_rows.append(gate)
            for v in ("viol", "flip_a"):
                o, _, m = built[v]
                observed_rows.append(o)
                case_rows.append({"run_id": o["run_id"], "base_case_id": m["base_case_id"], "family": family,
                                  "domain": m["domain"], "split": m["split"], "subset": m["subset"],
                                  "control": m["control"], "n_events": len(o["events"])})
                label_rows.append({"run_id": o["run_id"], "label": labels[v]["label"],
                                   "oracle_reasons": labels[v]["reasons"], "variant": v,
                                   "base_case_id": m["base_case_id"], "family": family,
                                   "gold_event_ids": gold[v]["ids"], "gold_workers": gold[v]["workers"],
                                   "core_event_ids": m["core_event_ids"]})
    rnd = random.Random(20261108)
    rnd.shuffle(observed_rows)
    case_rows.sort(key=lambda r: r["run_id"])
    label_rows.sort(key=lambda r: r["run_id"])
    out = {
        "data/observed/trajectories.jsonl": observed_rows,
        "data/manifest/cases.jsonl": case_rows,
        "data/eval/labels.jsonl": label_rows,
        "data/eval/validity.jsonl": validity_rows,
    }
    hashes = {}
    for rel, rows in out.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        text = "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows)
        p.write_text(text)
        hashes[rel] = hashlib.sha256(text.encode()).hexdigest()
    summary = {
        "n_trajectories": len(observed_rows),
        "n_base_cases": len(validity_rows),
        "gate_passed": sum(r["passed"] for r in validity_rows),
        "gate_failed": [r["base_case_id"] for r in validity_rows if not r["passed"]],
        "hashes": hashes,
    }
    return summary


def load_jsonl(path: Path) -> list:
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]
