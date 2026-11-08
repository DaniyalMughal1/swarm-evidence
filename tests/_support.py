"""Shared helpers for the offline test suite (stdlib only, no network, no API key).

Not a test module itself (the discovery pattern is ``test*.py``).
"""
from __future__ import annotations

import functools
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from swarm_evidence.scenarios import CONTROLS, FAMILIES, build_case  # noqa: E402
from swarm_evidence.world import WORLDS  # noqa: E402

ALL_FAMILIES = tuple(FAMILIES) + tuple(CONTROLS)
CORE_FAMILIES = tuple(FAMILIES)


@functools.lru_cache(maxsize=None)
def _cached_case(family, seed, variant):
    return build_case(family, seed, variant)


def case(family, seed, variant):
    """Build (observed, world, meta). Cached; callers that mutate must deep-copy first."""
    return _cached_case(family, seed, variant)


def variants_for(family):
    return ("viol", "flip_a") if family in CONTROLS else ("viol", "flip_a", "flip_b")


def mk_event(event_id, seq, tool, ins=(), outs=(), args=None, worker="W1", outcome="ok", note="Routine step.",
             run_id="run-test"):
    """A synthetic observed event with exactly the recorder's field set."""
    outs = list(outs)
    return {
        "run_id": run_id,
        "event_id": event_id,
        "worker_id": worker,
        "sequence": seq,
        "tool": tool,
        "arguments": dict(args or {}),
        "input_artifact_ids": list(ins),
        "output_artifact_ids": outs,
        "artifact_versions": {o: 1 for o in outs},
        "policy_refs": [],
        "outcome": outcome,
        "rationale": note,
    }


def mk_observed(events, target="t", domain="export", run_id="run-test", **env_extra):
    request = {"export": "finalize_export", "training": "finalize_training_run",
               "payment": "finalize_batch"}[domain]
    envelope = {"request": request, "target_artifact_id": target}
    if domain == "export":
        envelope.update(use="external_share", destination="partner-portal")
    elif domain == "training":
        envelope.update(purpose="production_finetune")
    else:
        envelope.update(action="release_payment")
    envelope.update(env_extra)
    return {"run_id": run_id, "domain": domain, "envelope": envelope, "events": events}


def run_steps(domain, steps):
    """Execute a hand-written step list on a fresh hidden World and record the observed ledger.

    Each step is (worker, tool, inputs, outputs, args) or (worker, tool, inputs, outputs, args, outcome).
    Artifact names are used directly as IDs. Returns (events, world).
    """
    world = WORLDS[domain]()
    events = []
    for k, st in enumerate(steps):
        worker, tool, ins, outs, args = st[:5]
        outcome = st[5] if len(st) > 5 else "ok"
        world.apply(tool, dict(args), list(ins), list(outs), outcome)
        events.append(mk_event(f"e{k + 1:03d}", k + 1, tool, ins, outs, args, worker=worker, outcome=outcome))
    return events, world


class FakeClock:
    """Drop-in for the ``time`` module inside ``swarm_evidence.runner``: sleep advances a virtual clock."""

    def __init__(self, start=1_000_000.0):
        self._t = start
        self._lock = threading.Lock()
        self.slept = 0.0

    def time(self):
        with self._lock:
            return self._t

    def sleep(self, seconds):
        with self._lock:
            self._t += max(0.0, seconds)
            self.slept += max(0.0, seconds)


class RateLimitError(Exception):
    """Named exactly like the SDK class; the runner dispatches on the class name."""


class APITimeoutError(Exception):
    """Transient error with an uncertain billing outcome (runner keeps a reservation)."""


class FakeMonitor:
    """Implements ``.call(instructions, input_text, max_output_tokens)`` like AdaptionMonitor.

    ``script`` maps call number (1-based, global across specs) to an exception instance to raise.
    ``cost`` is reported as provider usage cost (None exercises the runner's fallback pricing).
    """

    def __init__(self, cost=1e-4, script=None, response_text=None):
        self.cost = cost
        self.script = dict(script or {})
        self.response_text = response_text
        self.calls = []
        self._lock = threading.Lock()

    def call(self, instructions, input_text, max_output_tokens):
        with self._lock:
            self.calls.append((input_text, max_output_tokens))
            n = len(self.calls)
        if n in self.script:
            raise self.script[n]
        text = self.response_text if self.response_text is not None else (
            '{"score": 0.25, "verdict": "benign", "evidence_event_ids": [], "reason": "fake"}')
        return {
            "latency_s": 0.01, "status": "completed", "response_text": text, "response_id": f"resp-{n}",
            "returned_model": "fake-model", "input_tokens": 1000, "output_tokens": 40, "reasoning_tokens": 0,
            "cached_tokens": 0, "cost": self.cost, "incomplete_details": None,
        }
