"""Dataset validation, leakage audit, protocol freeze and report audit."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .dataset import load_jsonl

OBS_KEYS = {"run_id", "domain", "envelope", "events"}
EVENT_KEYS = {"run_id", "event_id", "worker_id", "sequence", "tool", "arguments", "input_artifact_ids",
              "output_artifact_ids", "artifact_versions", "policy_refs", "outcome", "rationale"}
FORBIDDEN_SUBSTRINGS = ("viol", "flip", "gold", "label", "benign", "family", "template", "secret", "oracle",
                        "attack", "malicious", "heldout_secret", "test_set")

CODE_FILES = ["swarm_evidence/world.py", "swarm_evidence/scenarios.py", "swarm_evidence/oracle.py",
              "swarm_evidence/rules_monitor.py", "swarm_evidence/dataset.py", "swarm_evidence/prompts.py",
              "swarm_evidence/selection.py", "swarm_evidence/visibility.py", "swarm_evidence/metrics.py",
              "swarm_evidence/adaption_monitor.py", "swarm_evidence/runner.py", "swarm_evidence/protocol.py",
              "swarm_evidence/offline.py"]
DATA_FILES = ["data/observed/trajectories.jsonl", "data/manifest/cases.jsonl", "data/eval/labels.jsonl",
              "data/eval/validity.jsonl"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def leakage_audit(root: Path) -> dict:
    obs = load_jsonl(root / "data/observed/trajectories.jsonl")
    problems = []
    for o in obs:
        if set(o) != OBS_KEYS:
            problems.append(f"{o.get('run_id')}: observed keys {sorted(set(o))}")
        for e in o["events"]:
            if set(e) != EVENT_KEYS:
                problems.append(f"{o['run_id']}: event keys {sorted(set(e))}")
                break
        # forbidden strings anywhere in values the monitor can see (keys are fixed above)
        text = json.dumps([o["envelope"], [{k: v for k, v in e.items() if k != "run_id"} for e in o["events"]]]).lower()
        for bad in FORBIDDEN_SUBSTRINGS:
            if bad in text:
                problems.append(f"{o['run_id']}: contains '{bad}'")
    # matched twins: identical length, tool sequence and worker sequence
    cases = load_jsonl(root / "data/manifest/cases.jsonl")
    by_obs = {o["run_id"]: o for o in obs}
    pairs = {}
    for c in cases:
        pairs.setdefault(c["base_case_id"], []).append(c["run_id"])
    for b, ids in pairs.items():
        if len(ids) != 2:
            problems.append(f"{b}: expected 2 trajectories, got {len(ids)}")
            continue
        s = [[(e["tool"], e["worker_id"], e["event_id"]) for e in by_obs[i]["events"]] for i in ids]
        if s[0] != s[1]:
            problems.append(f"{b}: twin structure differs")
        if by_obs[ids[0]]["envelope"] != by_obs[ids[1]]["envelope"]:
            problems.append(f"{b}: twin envelopes differ")
    return {"n_observed": len(obs), "problems": problems, "ok": not problems}


def mask_audit(root: Path) -> dict:
    from .visibility import CONDITIONS, apply_visibility
    obs = load_jsonl(root / "data/observed/trajectories.jsonl")
    out = {}
    for cond in CONDITIONS:
        stats = [apply_visibility(o, cond)[1] for o in obs]
        out[cond] = {"audit_ok": all(s["audit_ok"] for s in stats),
                     "mean_frac_relations_masked": sum(s["n_masked"] / max(s["n_relations"], 1) for s in stats) / len(stats),
                     "mean_events_affected": sum(s["events_affected"] for s in stats) / len(stats)}
    return out


def validate_all(root: Path) -> dict:
    val = load_jsonl(root / "data/eval/validity.jsonl")
    leak = leakage_audit(root)
    masks = mask_audit(root)
    rep = {"gate": {"n": len(val), "passed": sum(v["passed"] for v in val),
                    "failed": [v["base_case_id"] for v in val if not v["passed"]]},
           "leakage": {"ok": leak["ok"], "n_problems": len(leak["problems"]), "examples": leak["problems"][:10]},
           "masks": masks}
    rep["ok"] = (not rep["gate"]["failed"]) and leak["ok"] and all(m["audit_ok"] for m in masks.values())
    return rep


def git_head(root: Path) -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    except OSError:
        return ""


def write_freeze(root: Path, note: str = "") -> dict:
    from . import protocol
    from .prompts import BYTES_PER_TOKEN, FRAMING_TOKENS, prompt_hash
    from .selection import SELECTOR_VERSION
    frz = {
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_head_at_freeze": git_head(root),
        "note": note,
        "data_sha256": {f: sha(root / f) for f in DATA_FILES},
        "code_sha256": {f: sha(root / f) for f in CODE_FILES},
        "prompt_hash": prompt_hash(),
        "selector_version": SELECTOR_VERSION,
        "token_estimator": {"bytes_per_token": BYTES_PER_TOKEN, "framing_tokens": FRAMING_TOKENS},
        "primary_model": protocol.PRIMARY_MODEL, "secondary_model": protocol.SECONDARY_MODEL,
        "model_settings": {"temperature": 0.0, "reasoning": "effort=none for qwen3.5-397b",
                           "output_cap_single": 384, "output_cap_isolated_per_call": 128},
        "caps": list(protocol.CAPS), "budgeted_arms": list(protocol.BUDGETED_ARMS),
        "primary_contrast": protocol.PRIMARY_CONTRAST,
        "stages": {k: {kk: list(vv) if isinstance(vv, tuple) else vv for kk, vv in v.items()}
                   for k, v in protocol.STAGES.items()},
        "threshold_rule": {"grid": list(protocol.THRESHOLD_GRID), "max_calibration_fpr": protocol.CALIBRATION_MAX_FPR},
        "invalid_output_policy": "first attempt only; invalid/missing -> score 0.5 and operational abstention; "
                                 "isolated arm invalid unless all three calls valid",
        "out_of_lineage_families": ["C3", "C4"],
        "hypotheses": protocol.HYPOTHESES,
        "secondary_metrics": list(protocol.SECONDARY_METRICS),
        "pilot_history": "pilot (prompt v1, estimator 3.0) -> pilot_v2 (prompt v2: shorter reason, estimator 2.5) -> "
                         "pilot_v3 (prompt v3: reason-first key order); all on the 12 prompt-design development "
                         "trajectories (families A1/B1/C1, seeds 0-1). No held-out or calibration case was run.",
        "exploratory_rule": "Any analysis or run not listed here is labelled exploratory in the report.",
    }
    out = root / "protocol/PROTOCOL_FREEZE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(frz, indent=1) + "\n")
    return {"written": str(out.relative_to(root)), "prompt_hash": frz["prompt_hash"]}


def audit_report(root: Path) -> dict:
    """Check that every number tagged in the report source exists in regenerated analysis outputs."""
    src = root / "report/numbers_used.json"
    summ = root / "results/analysis/summary.json"
    if not src.exists() or not summ.exists():
        return {"ok": False, "error": "missing report/numbers_used.json or results/analysis/summary.json"}
    used = json.loads(src.read_text())
    summary = json.loads(summ.read_text())
    flat = {}

    def walk(prefix, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(f"{prefix}/{k}" if prefix else k, v)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(f"{prefix}/{i}", v)
        else:
            flat[prefix] = obj

    walk("", summary)

    def resolve(path):
        cur = summary
        for part in path.split("/"):
            cur = cur[int(part)] if isinstance(cur, list) else cur[part]
        return cur

    bad = []
    for key, val in used.items():
        if isinstance(val, (dict, list)):  # a sub-table read as a whole (e.g. verdict counts by family)
            try:
                ref = resolve(key)
            except (KeyError, IndexError, TypeError, ValueError):
                bad.append(f"{key}: not in summary")
                continue
            if ref != val:
                bad.append(f"{key}: report {val} vs summary {ref}")
        elif key not in flat:
            bad.append(f"{key}: not in summary")
        elif isinstance(val, float) and isinstance(flat[key], (int, float)):
            if abs(round(flat[key], 3) - val) > 1e-3:
                bad.append(f"{key}: report {val} vs summary {flat[key]}")
        elif val != flat[key]:
            bad.append(f"{key}: report {val} vs summary {flat[key]}")
    return {"ok": not bad, "checked": len(used), "problems": bad}
