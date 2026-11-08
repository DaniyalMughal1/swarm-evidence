#!/usr/bin/env python3
"""Regenerate the README results block from results/analysis/summary.json (between markers)."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "results/analysis/summary.json").read_text())
Q, G = "qwen3.5-397b", "gemma-4-31b-it"
ARMS = [("dependency", "Dependency"), ("lexical", "Lexical"), ("chronological", "Chronological"), ("bm25", "BM25"),
        ("lexical_prf", "Lexical+PRF"), ("shuffled", "Shuffled graph"), ("isolated", "Isolated (3 calls)")]


def f(x, nd=2):
    return "n/a" if x is None else f"{x:.{nd}f}"


def row(model, arm, cap):
    a = S["models"][model]["arms"].get(f"{arm}@{cap}")
    if not a or a.get("incomplete"):
        return None
    off = S.get("offline_test", {}).get(f"{arm}@{cap}@full", {})
    lo, hi = a["auroc_ci_family"]
    return (f"{f(a['auroc'])} ({f(lo)}–{f(hi)})", f"{a['verdict_violation_tp']}/{a['verdict_violation_fp']}",
            str(a["abstain_valid"]), str(a["invalid"]), f(a["gold_recall"]), f"{a['mean_input_tokens']:.0f}",
            str(a["cap_overruns"]), f(off.get("rule_auroc")))


lines = []
for model in (Q, G):
    if model not in S["models"]:
        continue
    for cap in (2000, 6000):
        rows = [(lab, row(model, arm, cap)) for arm, lab in ARMS]
        rows = [(lab, r) for lab, r in rows if r]
        if not rows:
            continue
        lines.append(f"\n**{model}, {cap:,}-token cap** (60 held-out trajectories, 6 unseen families)\n")
        lines.append("| Method | AUROC (family 95% CI) | Violation verdicts TP/FP | Abstain | Invalid | Gold recall | Billed input tokens | Over cap | Rule monitor AUROC |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for lab, r in rows:
            lines.append(f"| {lab} | " + " | ".join(r) + " |")
    full = S["models"][model]["arms"].get("full@nocap")
    if full and not full.get("incomplete"):
        lines.append(f"\nFull log, no cap ({model}): AUROC {f(full['auroc'])}, mean {full['mean_input_tokens']:.0f} billed input tokens, {full['invalid']} invalid outputs.")
    c = S["models"][model]["contrasts"].get("dependency-lexical@2000")
    if c:
        lo, hi = c["ci95_family_bootstrap"]
        label = "Primary contrast" if model == Q else "Same contrast, secondary model"
        lines.append(f"\n{label} ({model}, 2k, full visibility): dependency − lexical AUROC = "
                     f"{c['diff']:+.2f} (paired family bootstrap 95% CI {lo:+.2f} to {hi:+.2f}; "
                     f"{c['families_positive']} of {c['n_families']} families favour dependency).")
cost = S["costs"]
lines.append(f"\nTotal model spend: {cost['total_credits']:.3f} Adaption credits over {cost['n_calls_total']} recorded calls "
             "(pilots, both models, exploratory runs and transport-error reservations).")
block = "\n".join(lines).strip() + "\n"
readme = ROOT / "README.md"
text = readme.read_text()
new = re.sub(r"(<!-- results:start -->\n).*?(<!-- results:end -->)", lambda m: m.group(1) + block + m.group(2), text, flags=re.S)
readme.write_text(new)
print("README results block updated" if new != text else "no change")
