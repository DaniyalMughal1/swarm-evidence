"""CLI: python -m swarm_evidence <command> [options]

Commands
  generate      build the synthetic dataset and run the validity gate
  validate      re-check dataset files: gate results, leakage audit, mask audit
  offline       model-independent evidence-retention + rule-monitor evaluation (--split dev|test)
  freeze        write protocol/PROTOCOL_FREEZE.json (hashes of data, code, prompts, plan)
  run           execute a stage with the Adaption monitor (--stage, --model, --stage-budget)
  analyze       regenerate every table/figure from saved results
  audit-report  check report numbers against regenerated analysis outputs
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cmd_generate(args):
    from .dataset import generate
    s = generate(ROOT)
    print(json.dumps(s, indent=1))
    return 0 if not s["gate_failed"] else 1


def cmd_validate(args):
    from .audit import validate_all
    rep = validate_all(ROOT)
    print(json.dumps(rep, indent=1))
    return 0 if rep["ok"] else 1


def cmd_offline(args):
    from .dataset import load_jsonl
    from .offline import evaluate, summarize
    from .selection import METHODS
    from .protocol import CAPS
    from .visibility import apply_visibility
    obs = {o["run_id"]: o for o in load_jsonl(ROOT / "data/observed/trajectories.jsonl")}
    cases = {c["run_id"]: c for c in load_jsonl(ROOT / "data/manifest/cases.jsonl")}
    labels = {r["run_id"]: r for r in load_jsonl(ROOT / "data/eval/labels.jsonl")}
    if args.split == "test":
        frz = ROOT / "protocol/PROTOCOL_FREEZE.json"
        if not frz.exists():
            print("refusing: held-out offline results require a frozen protocol (run `freeze` first)")
            return 2
    subset = {"dev": ("prompt_design", "calibration"), "test": ("test",), "control": ("control",)}[args.split]
    ids = sorted(r for r, c in cases.items() if c["subset"] in subset)
    caps = [int(x) for x in args.caps.split(",")] if args.caps else list(CAPS)
    all_rows = []
    for vis in args.visibility.split(","):
        view = {r: apply_visibility(obs[r], vis)[0] for r in ids}
        rows = evaluate(ids, view, labels, cases, list(METHODS), caps)
        for r in rows:
            r["visibility"] = vis
        all_rows += rows
        for s in summarize(rows):
            print(vis, json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in s.items()}))
    out = ROOT / f"results/offline/{args.split}_offline.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r) + "\n" for r in all_rows))
    print("wrote", out.relative_to(ROOT))
    return 0


def cmd_freeze(args):
    from .audit import write_freeze
    print(json.dumps(write_freeze(ROOT, note=args.note), indent=1))
    return 0


def cmd_run(args):
    from .adaption_monitor import AdaptionMonitor, load_dotenv
    from .dataset import load_jsonl
    from .protocol import STAGES, stage_run_ids
    from .runner import Store, execute, plan_calls
    loaded = load_dotenv(ROOT / ".env")
    if "ADAPTION_API_KEY" not in loaded and not os.environ.get("ADAPTION_API_KEY"):
        print("ADAPTION_API_KEY not available; live runs are opt-in")
        return 2
    ceiling = float(os.environ.get("SWARM_MAX_CREDITS", "0") or 0)
    if ceiling <= 0:
        print("SWARM_MAX_CREDITS must be a positive cumulative ceiling")
        return 2
    if args.stage != "pilot" and not args.allow_unfrozen and args.stage != "calibration":
        if not (ROOT / "protocol/PROTOCOL_FREEZE.json").exists():
            print("refusing: held-out stages require a frozen protocol")
            return 2
    model = args.model or os.environ.get("ADAPTION_MODEL")
    obs = {o["run_id"]: o for o in load_jsonl(ROOT / "data/observed/trajectories.jsonl")}
    cases = load_jsonl(ROOT / "data/manifest/cases.jsonl")
    spec = STAGES[args.stage]
    run_ids = stage_run_ids(args.stage, cases)
    arms = args.arms.split(",") if args.arms else spec["arms"]
    caps = [int(x) for x in args.caps.split(",")] if args.caps else spec["caps"]
    vis = args.visibility.split(",") if args.visibility else spec["visibility"]
    stage_name = args.stage if model == os.environ.get("ADAPTION_MODEL") and not args.tag else f"{args.stage}{args.tag or ''}"
    specs = []
    for rep in range(args.replicates):
        specs += plan_calls(stage_name, arms, caps, vis, run_ids, obs, model, replicate=rep)
    if not all(s["mask_audit_ok"] for s in specs):
        print("refusing: visibility mask audit failed")
        return 2
    store = Store(ROOT / "results/runs.sqlite")
    from .adaption_monitor import max_cost
    from .runner import EST_INPUT_MARGIN
    worst = sum(max_cost(model, int(s["est_input_tokens"] * EST_INPUT_MARGIN), s["max_output_tokens"])
                for s in specs if not store.has(s["run_key"]))
    print(f"stage={stage_name} model={model} calls={len(specs)} pending_worst_case={worst:.4f} "
          f"spent_so_far={store.spent():.4f} ceiling={ceiling} stage_budget={args.stage_budget}")
    if args.dry_run:
        return 0
    mon = AdaptionMonitor(model)
    summary = execute(specs, mon, store, ceiling=ceiling, stage_budget=args.stage_budget,
                      concurrency=args.concurrency, stop_at_utc=args.stop_at_utc, rpm=args.rpm)
    print(json.dumps(summary, indent=1))
    return 0


def cmd_analyze(args):
    from .analysis import run_analysis
    run_analysis(ROOT)
    return 0


def cmd_audit_report(args):
    from .audit import audit_report
    rep = audit_report(ROOT)
    print(json.dumps(rep, indent=1))
    return 0 if rep["ok"] else 1


def main(argv=None):
    p = argparse.ArgumentParser(prog="swarm_evidence")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("generate")
    sub.add_parser("validate")
    o = sub.add_parser("offline")
    o.add_argument("--split", choices=["dev", "test", "control"], default="dev")
    o.add_argument("--caps", default="")
    o.add_argument("--visibility", default="full")
    f = sub.add_parser("freeze")
    f.add_argument("--note", default="")
    r = sub.add_parser("run")
    r.add_argument("--stage", required=True)
    r.add_argument("--model", default="")
    r.add_argument("--stage-budget", type=float, required=True)
    r.add_argument("--arms", default="")
    r.add_argument("--caps", default="")
    r.add_argument("--visibility", default="")
    r.add_argument("--replicates", type=int, default=1)
    r.add_argument("--concurrency", type=int, default=6)
    r.add_argument("--rpm", type=float, default=40.0)
    r.add_argument("--tag", default="")
    r.add_argument("--stop-at-utc", default=None)
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--allow-unfrozen", action="store_true")
    sub.add_parser("analyze")
    sub.add_parser("audit-report")
    a = p.parse_args(argv)
    fn = {"generate": cmd_generate, "validate": cmd_validate, "offline": cmd_offline, "freeze": cmd_freeze,
          "run": cmd_run, "analyze": cmd_analyze, "audit-report": cmd_audit_report}[a.cmd]
    return fn(a)


if __name__ == "__main__":
    sys.exit(main())
