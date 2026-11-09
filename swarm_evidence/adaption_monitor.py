"""Adaption hosted-model monitor: strict output parsing, usage capture, no key logging."""
from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path

VERDICTS = ("violation", "benign", "insufficient_evidence")

# Credits per million tokens (1 credit = 1 USD per the account). Published rates retrieved
# 2026-11-08 and cross-checked against provider-reported `usage.cost` on access-check calls.
PRICES = {
    "qwen3.5-397b": (0.55, 3.50),
    "gemma-4-31b-it": (0.09, 0.34),
    "glm-5.2": (1.40, 4.40),
    "gemma-4-26b-a4b-it": (0.0765, 0.255),
    "qwen3.8-27b": (0.039, 1.25),
    "deepseek-v4-flash": (0.04444, 0.13332),
    "glm-53-flash": (0.15, 0.50),
}
# Reasoning is disabled so that the output cap counts every generated token.
MODEL_EXTRA = {
    "qwen3.5-397b": {"reasoning": {"effort": "none"}},
}
# Exploratory (post-freeze) monitor variants: label -> (provider model id, extra request body).
# Billed reasoning tokens are part of output_tokens and therefore of the recorded cost.
VARIANTS = {
    "qwen3.5-397b+reasoning": ("qwen3.5-397b", {"reasoning": {"effort": "medium"}}),
}
for _label, (_base, _extra) in VARIANTS.items():
    PRICES[_label] = PRICES[_base]


def load_dotenv(path: str | Path = ".env") -> list:
    """Load KEY=VALUE lines into os.environ. Returns the key *names* loaded (never values)."""
    loaded = []
    p = Path(path)
    if not p.exists():
        return loaded
    for line in p.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        if v:
            os.environ[k.strip()] = v
            loaded.append(k.strip())
    return loaded


def max_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pin, pout = PRICES[model]
    return (input_tokens * pin + output_tokens * pout) / 1e6


FENCE_RE = re.compile(r"^```(?:json)?[ \t]*\n(.*)\n```$", re.S)


def parse_output(text: str, shown_ids) -> dict:
    """Strict parser (frozen). Accepts one JSON object, optionally wrapped in a single
    markdown code fence. Required: score (finite number in [0,1]), verdict (one of VERDICTS),
    evidence_event_ids (list of strings), reason (string). Extra keys are recorded, not fatal."""
    res = {"valid": False, "error": None, "score": None, "verdict": None, "evidence_event_ids": [],
           "reason": None, "unsupported_ids": [], "extra_keys": []}
    if text is None:
        res["error"] = "no_text"
        return res
    t = text.strip()
    m = FENCE_RE.match(t)
    if m:
        t = m.group(1).strip()
    try:
        obj = json.loads(t)
    except (json.JSONDecodeError, ValueError):
        res["error"] = "json_decode"
        return res
    if not isinstance(obj, dict):
        res["error"] = "not_object"
        return res
    s = obj.get("score")
    try:
        finite = isinstance(s, (int, float)) and not isinstance(s, bool) and math.isfinite(s)
    except OverflowError:  # integers too large for float conversion
        finite = False
    if not finite or not 0 <= s <= 1:
        res["error"] = "bad_score"
        return res
    v = obj.get("verdict")
    if v not in VERDICTS:
        res["error"] = "bad_verdict"
        return res
    ids = obj.get("evidence_event_ids")
    if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
        res["error"] = "bad_evidence_ids"
        return res
    reason = obj.get("reason")
    if not isinstance(reason, str):
        res["error"] = "bad_reason"
        return res
    shown = set(shown_ids)
    res.update(valid=True, score=float(s), verdict=v, evidence_event_ids=ids, reason=reason,
               unsupported_ids=[x for x in ids if x not in shown],
               extra_keys=sorted(set(obj) - {"score", "verdict", "evidence_event_ids", "reason"}))
    return res


class AdaptionMonitor:
    def __init__(self, model: str, temperature: float = 0.0, timeout: float = 120.0):
        from adaption import Adaption  # imported lazily so offline tests need no SDK

        self.model = model
        self.provider_model, self.extra = VARIANTS.get(model, (model, MODEL_EXTRA.get(model)))
        self.temperature = temperature
        self.client = Adaption(max_retries=0, timeout=timeout)

    def call(self, instructions: str, input_text: str, max_output_tokens: int) -> dict:
        """One transport attempt. Raises on transport errors so the runner can log/retry."""
        t0 = time.time()
        r = self.client.responses.create(model=self.provider_model, instructions=instructions, input=input_text,
                                         max_output_tokens=max_output_tokens, temperature=self.temperature,
                                         extra_body=self.extra or None)
        d = r.model_dump()
        usage = d.get("usage") or {}
        out_details = usage.get("output_tokens_details") or {}
        return {
            "latency_s": round(time.time() - t0, 3),
            "status": d.get("status"),
            "response_text": r.output_text,
            "response_id": d.get("id"),
            "returned_model": d.get("model"),
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
            "reasoning_tokens": out_details.get("reasoning_tokens"),
            "cached_tokens": (usage.get("input_tokens_details") or {}).get("cached_tokens"),
            "cost": usage.get("cost"),
            "incomplete_details": d.get("incomplete_details"),
        }
