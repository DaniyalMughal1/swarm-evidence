"""Model-independent evaluation: evidence retention and the deterministic rule monitor
on exactly the evidence each selector chooses."""
from __future__ import annotations

import statistics
from collections import defaultdict

from .metrics import auroc
from .prompts import event_cost, overhead_tokens
from .rules_monitor import rule_monitor
from .selection import select


def aggregate_rule(outs):
    score = max(x["score"] for x in outs)
    if any(x["verdict"] == "violation" for x in outs):
        v = "violation"
    elif all(x["verdict"] == "benign" for x in outs):
        v = "benign"
    else:
        v = "unknown"
    return score, v


def evaluate(run_ids, obs, labels, cases, methods, caps):
    rows = []
    for cap in caps:
        for m in methods:
            for r in run_ids:
                o = obs[r]
                calls = select(m, o, cap)
                by = {e["event_id"]: e for e in o["events"]}
                sel = {i for c in calls for i in c["event_ids"]}
                gold = set(labels[r]["gold_event_ids"])
                outs = [rule_monitor([by[i] for i in c["event_ids"]], o["envelope"]) for c in calls]
                score, verdict = aggregate_rule(outs)
                rows.append({"run_id": r, "method": m, "cap": cap, "family": cases[r]["family"],
                             "split": cases[r]["split"], "label": labels[r]["label"],
                             "n_selected": len(sel), "n_events": len(o["events"]),
                             "selected_tokens": sum(c["used"] + c["overhead"] for c in calls),
                             "gold_recall": len(sel & gold) / len(gold), "gold_complete": gold <= sel,
                             "rule_score": score, "rule_verdict": verdict})
    return rows


def summarize(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["cap"], r["method"])].append(r)
    out = []
    for (cap, m), rs in sorted(groups.items()):
        ys = [r["label"] for r in rs]
        out.append({"cap": cap, "method": m, "n": len(rs),
                    "gold_recall": statistics.mean(r["gold_recall"] for r in rs),
                    "gold_complete": statistics.mean(r["gold_complete"] for r in rs),
                    "rule_auroc": auroc([r["rule_score"] for r in rs], ys),
                    "rule_unknown": statistics.mean(r["rule_verdict"] == "unknown" for r in rs),
                    "rule_tp": sum(r["rule_verdict"] == "violation" and r["label"] == 1 for r in rs),
                    "rule_fp": sum(r["rule_verdict"] == "violation" and r["label"] == 0 for r in rs),
                    "rule_fn_benign": sum(r["rule_verdict"] == "benign" and r["label"] == 1 for r in rs),
                    "mean_tokens": statistics.mean(r["selected_tokens"] for r in rs)})
    return out


def full_lengths(run_ids, obs):
    return [overhead_tokens(obs[r]["domain"], obs[r]["envelope"]) + sum(event_cost(e) for e in obs[r]["events"])
            for r in run_ids]
