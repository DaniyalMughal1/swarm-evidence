"""Checkpointed, budget-guarded execution of monitor calls.

* Every call has a stable run key (case, observed-view hash, method, selector version, model,
  prompt hash, cap, visibility, call index, replicate). Completed first attempts are immutable;
  re-running a stage skips keys already present (idempotent resume).
* A hard cumulative credit ceiling covers all stages, pilots and retries. Before each call the
  runner reserves the call's worst-case cost (estimated input with margin + full output cap);
  transport failures with an uncertain billing outcome keep a reservation in the ledger.
* Transport retries (rate limits, connection errors, timeouts, 5xx) are logged per attempt and
  never produce extra model samples once a response body has been received.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from .adaption_monitor import max_cost, parse_output
from .prompts import INSTRUCTIONS, build_input, estimate_tokens, prompt_hash
from .selection import SELECTOR_VERSION, select
from .visibility import apply_visibility

OUTPUT_CAP_SINGLE = 384
OUTPUT_CAP_ISOLATED = 128
EST_INPUT_MARGIN = 1.3  # reservation margin on estimated input tokens

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
  run_key TEXT PRIMARY KEY, stage TEXT, arm TEXT, cap INTEGER, visibility TEXT, run_id TEXT,
  call_index INTEGER, replicate INTEGER, model TEXT, prompt_hash TEXT, selector_version TEXT,
  view_hash TEXT, input_sha TEXT, n_shown INTEGER, shown_ids TEXT, est_input_tokens INTEGER,
  max_output_tokens INTEGER, status TEXT, response_text TEXT, parsed TEXT, parse_error TEXT,
  input_tokens INTEGER, output_tokens INTEGER, reasoning_tokens INTEGER, cost REAL, latency_s REAL,
  response_id TEXT, returned_model TEXT, transport_attempts INTEGER, created_at TEXT);
CREATE TABLE IF NOT EXISTS attempts (
  run_key TEXT, attempt INTEGER, error_type TEXT, error TEXT, reserved_cost REAL, created_at TEXT);
CREATE TABLE IF NOT EXISTS ledger_adjustments (
  label TEXT, cost REAL, note TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS stage_log (
  stage TEXT, event TEXT, detail TEXT, created_at TEXT);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.executescript(SCHEMA)
        self.lock = threading.Lock()

    def has(self, run_key):
        with self.lock:
            return self.conn.execute("SELECT 1 FROM calls WHERE run_key=?", (run_key,)).fetchone() is not None

    def spent(self):
        with self.lock:
            c = self.conn.execute("SELECT COALESCE(SUM(cost),0) FROM calls").fetchone()[0]
            a = self.conn.execute("SELECT COALESCE(SUM(reserved_cost),0) FROM attempts").fetchone()[0]
            l = self.conn.execute("SELECT COALESCE(SUM(cost),0) FROM ledger_adjustments").fetchone()[0]
        return float(c) + float(a) + float(l)

    def insert_call(self, row):
        cols = ",".join(row)
        q = ",".join("?" for _ in row)
        with self.lock:
            self.conn.execute(f"INSERT OR IGNORE INTO calls ({cols}) VALUES ({q})", list(row.values()))
            self.conn.commit()

    def insert_attempt(self, run_key, attempt, etype, err, reserved):
        with self.lock:
            self.conn.execute("INSERT INTO attempts VALUES (?,?,?,?,?,?)", (run_key, attempt, etype, err[:500],
                                                                          reserved, now()))
            self.conn.commit()

    def log(self, stage, event, detail):
        with self.lock:
            self.conn.execute("INSERT INTO stage_log VALUES (?,?,?,?)", (stage, event, json.dumps(detail), now()))
            self.conn.commit()

    def adjust(self, label, cost, note):
        with self.lock:
            self.conn.execute("INSERT INTO ledger_adjustments VALUES (?,?,?,?)", (label, cost, note, now()))
            self.conn.commit()

    def rows(self, where="1=1", params=()):
        with self.lock:
            cur = self.conn.execute(f"SELECT * FROM calls WHERE {where}", params)
            names = [d[0] for d in cur.description]
            return [dict(zip(names, r)) for r in cur.fetchall()]


def view_hash(observed):
    return hashlib.sha256(json.dumps(observed, sort_keys=True).encode()).hexdigest()[:16]


def plan_calls(stage, arms, caps, visibilities, run_ids, observed_by_id, model, replicate=0):
    """Deterministic call specs for a stage (selection happens here, before any model call)."""
    specs = []
    ph = prompt_hash()
    for vis in visibilities:
        for cap in caps:
            for arm in arms:
                for rid in run_ids:
                    base = observed_by_id[rid]
                    obs, audit = apply_visibility(base, vis)
                    vh = view_hash(obs)
                    calls = select(arm, obs, cap)
                    by_id = {e["event_id"]: e for e in obs["events"]}
                    for ci, c in enumerate(calls):
                        evs = [by_id[i] for i in c["event_ids"]]
                        text = build_input(obs["domain"], obs["envelope"], evs, c["view_note"])
                        est = estimate_tokens(INSTRUCTIONS) + estimate_tokens(text) + 24
                        key_src = json.dumps([rid, vh, arm, SELECTOR_VERSION, model, ph,
                                              cap if arm != "full" else None, vis, ci, replicate])
                        specs.append({
                            "run_key": hashlib.sha256(key_src.encode()).hexdigest()[:24],
                            "stage": stage, "arm": arm, "cap": cap if arm != "full" else None,
                            "visibility": vis, "run_id": rid, "call_index": ci, "replicate": replicate,
                            "model": model, "prompt_hash": ph, "selector_version": SELECTOR_VERSION,
                            "view_hash": vh, "input_text": text,
                            "input_sha": hashlib.sha256(text.encode()).hexdigest()[:16],
                            "shown_ids": c["event_ids"], "est_input_tokens": est,
                            "max_output_tokens": OUTPUT_CAP_ISOLATED if arm == "isolated" else OUTPUT_CAP_SINGLE,
                            "mask_audit_ok": audit["audit_ok"],
                        })
                if arm == "full":
                    pass
    # de-duplicate (the full arm is cap-independent)
    seen, out = set(), []
    for s in specs:
        if s["run_key"] not in seen:
            seen.add(s["run_key"])
            out.append(s)
    return out


class RateGate:
    """Process-wide pacing: minimum spacing between call starts, and a global pause after a 429."""

    def __init__(self, rpm: float):
        self.interval = 60.0 / rpm if rpm > 0 else 0.0
        self.lock = threading.Lock()
        self.next_start = 0.0
        self.paused_until = 0.0
        self.n_429 = 0

    def wait(self):
        while True:
            with self.lock:
                t = time.time()
                start = max(self.next_start, self.paused_until)
                if t >= start:
                    self.next_start = t + self.interval
                    return
                delay = start - t
            time.sleep(min(delay, 5.0))

    def on_rate_limit(self, seconds: float = 60.0):
        with self.lock:
            self.n_429 += 1
            self.paused_until = max(self.paused_until, time.time() + seconds)
            self.interval *= 1.15  # back off the steady-state rate after each limit hit


TRANSIENT = ("RateLimitError", "APIConnectionError", "APITimeoutError", "InternalServerError")
UNCERTAIN_BILLING = ("APITimeoutError", "InternalServerError", "APIConnectionError")


def execute(specs, monitor, store: Store, ceiling: float, stage_budget: float, concurrency: int = 6,
            max_attempts: int = 8, stop_at_utc: str | None = None, progress_every: int = 25, rpm: float = 40.0):
    """Run pending specs. Returns a summary dict with stop reasons."""
    pending = [s for s in specs if not store.has(s["run_key"])]
    stage = specs[0]["stage"] if specs else "?"
    start_spent = store.spent()
    reserved = {"v": 0.0}
    gate = RateGate(rpm)
    rlock = threading.Lock()
    stop = {"reason": None}
    store.log(stage, "start", {"n_specs": len(specs), "n_pending": len(pending), "spent_before": start_spent,
                               "ceiling": ceiling, "stage_budget": stage_budget})

    def worst(s):
        return max_cost(s["model"], int(s["est_input_tokens"] * EST_INPUT_MARGIN), s["max_output_tokens"])

    def try_reserve(s):
        w = worst(s)
        with rlock:
            spent = store.spent()
            if stop["reason"]:
                return None
            if stop_at_utc and now() >= stop_at_utc:
                stop["reason"] = "time_stop"
                return None
            if spent + reserved["v"] + w > ceiling:
                stop["reason"] = "global_ceiling"
                return None
            if (spent - start_spent) + reserved["v"] + w > stage_budget:
                stop["reason"] = "stage_budget"
                return None
            reserved["v"] += w
            return w

    def release(w):
        with rlock:
            reserved["v"] -= w

    def one(s):
        w = try_reserve(s)
        if w is None:
            return "skipped"
        try:
            attempt, res, last_err = 0, None, None
            while attempt < max_attempts:
                attempt += 1
                gate.wait()
                try:
                    res = monitor.call(INSTRUCTIONS, s["input_text"], s["max_output_tokens"])
                    break
                except Exception as e:  # transport-level failure: log and maybe retry
                    et = type(e).__name__
                    last_err = f"{et}: {e}"
                    reserved_cost = w if et in UNCERTAIN_BILLING else 0.0
                    store.insert_attempt(s["run_key"], attempt, et, str(e), reserved_cost)
                    if et not in TRANSIENT:
                        break
                    if et == "RateLimitError":
                        gate.on_rate_limit(60.0)
                    else:
                        time.sleep(min(2 ** attempt, 30))
            row = {k: s[k] for k in ("run_key", "stage", "arm", "cap", "visibility", "run_id", "call_index",
                                     "replicate", "model", "prompt_hash", "selector_version", "view_hash",
                                     "input_sha", "est_input_tokens", "max_output_tokens")}
            row["n_shown"] = len(s["shown_ids"])
            row["shown_ids"] = json.dumps(s["shown_ids"])
            row["created_at"] = now()
            row["transport_attempts"] = attempt
            if res is None:
                row.update(status="transport_error", parse_error=last_err, cost=0.0)
            else:
                parsed = parse_output(res["response_text"], s["shown_ids"])
                row.update(status=res["status"], response_text=res["response_text"], parsed=json.dumps(parsed),
                           parse_error=parsed["error"], input_tokens=res["input_tokens"],
                           output_tokens=res["output_tokens"], reasoning_tokens=res["reasoning_tokens"],
                           cost=res["cost"] if res["cost"] is not None else
                           max_cost(s["model"], res["input_tokens"] or 0, res["output_tokens"] or 0),
                           latency_s=res["latency_s"], response_id=res["response_id"],
                           returned_model=res["returned_model"])
            store.insert_call(row)
            return row["status"]
        finally:
            release(w)

    done = 0
    statuses = {}
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futs = [ex.submit(one, s) for s in pending]
        for f in as_completed(futs):
            st = f.result()
            statuses[st] = statuses.get(st, 0) + 1
            done += 1
            if progress_every and done % progress_every == 0:
                print(f"  [{stage}] {done}/{len(pending)} spent={store.spent():.4f}", flush=True)
    summary = {"stage": stage, "n_specs": len(specs), "n_pending_at_start": len(pending), "statuses": statuses,
               "spent_before": start_spent, "spent_after": store.spent(), "stop_reason": stop["reason"],
               "rate_limit_events": gate.n_429, "final_interval_s": round(gate.interval, 3)}
    store.log(stage, "end", summary)
    return summary
