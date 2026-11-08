"""Summarize a development pilot stage (dev labels only)."""
import json, sys, statistics
from pathlib import Path
from collections import defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from swarm_evidence.runner import Store
from swarm_evidence.dataset import load_jsonl
from swarm_evidence.metrics import auroc
root = Path(__file__).resolve().parents[1]
stage = sys.argv[1]
s = Store(root / "results/runs.sqlite")
rows = s.rows("stage=?", (stage,))
labels = {r["run_id"]: r for r in load_jsonl(root / "data/eval/labels.jsonl")}
cases = {c["run_id"]: c for c in load_jsonl(root / "data/manifest/cases.jsonl")}
assert all(cases[r["run_id"]]["split"] == "dev" for r in rows), "pilot report is for development cases only"
print(stage, "calls", len(rows), "invalid", sum(1 for r in rows if r["parse_error"]),
      "max out", max(r["output_tokens"] or 0 for r in rows), "max billed/est %.3f" % max(r["input_tokens"] / r["est_input_tokens"] for r in rows if r["input_tokens"]))
agg = defaultdict(list)
for r in rows:
    agg[(r["arm"], r["run_id"])].append(json.loads(r["parsed"]) if r["parsed"] else {"valid": False})
for arm in sorted({a for a, _ in agg}):
    sc, ys, c = [], [], defaultdict(int)
    for (a, rid), ps in agg.items():
        if a != arm:
            continue
        L = labels[rid]["label"]
        if not all(p.get("valid") for p in ps):
            sc.append(0.5); ys.append(L); c["invalid"] += 1; continue
        v = [p["verdict"] for p in ps]
        score = max(p["score"] for p in ps)
        verdict = "violation" if "violation" in v else ("benign" if all(x == "benign" for x in v) else "abstain")
        sc.append(score); ys.append(L); c[f"{verdict}|y={L}"] += 1
    print(f"  {arm:13s} AUROC {auroc(sc, ys):.2f}", dict(sorted(c.items())))
