"""Budgeted evidence-selection policies. Inputs: one observed record (public policy,
finalization envelope, event ledger). No labels, gold evidence or hidden state.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import re

from .prompts import POLICIES, event_cost, overhead_tokens, render_event

SELECTOR_VERSION = "v1"
METHODS = ("chronological", "lexical", "bm25", "lexical_prf", "dependency", "shuffled", "isolated")
ISOLATED_VIEW_NOTE = ", only worker {w}'s events"

STOPWORDS = frozenset("""a an and are as at be by for from has if in is it its of on or that the this to was were
with not any one only than then from into whose which when what who all each per its their them they these those
been being can may must no nor so such do does did done had have having he she we you your our us i me my""".split())

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokens(text: str) -> set:
    return {t for t in TOKEN_RE.findall(text.lower()) if len(t) > 1 and t not in STOPWORDS}


def _fill(order, budget, events_by_id):
    chosen, used, skipped = [], 0, 0
    for eid in order:
        c = event_cost(events_by_id[eid])
        if used + c <= budget:
            chosen.append(eid)
            used += c
        else:
            skipped += 1
    return chosen, used, skipped


def graph_index(events):
    producer, annotations = {}, {}
    for e in events:
        for a in e["output_artifact_ids"]:
            producer[a] = e["event_id"]
        if not e["output_artifact_ids"]:
            for a in e["input_artifact_ids"]:
                annotations.setdefault(a, []).append(e["event_id"])
    return producer, annotations


def dependency_order(events, target):
    """Backward BFS over producer-consumer relations; annotation events attach at their artifact's distance."""
    by_id = {e["event_id"]: e for e in events}
    producer, annotations = graph_index(events)
    dist = {target: 0}
    frontier = [target]
    rank = {}
    while frontier:
        nxt = []
        for a in frontier:
            d = dist[a]
            p = producer.get(a)
            if p is not None:
                rank[p] = min(rank.get(p, math.inf), d)
                for i in by_id[p]["input_artifact_ids"]:
                    if i not in dist:
                        dist[i] = d + 1
                        nxt.append(i)
        frontier = nxt
    for a, d in dist.items():
        for an in annotations.get(a, []):
            rank[an] = min(rank.get(an, math.inf), d + 0.5)
    return sorted(rank, key=lambda x: (rank[x], -by_id[x]["sequence"], x))


def shuffle_permutation(events, target, run_id):
    """Fixed relabeling of event nodes; the target's producer stays fixed."""
    producer, _ = graph_index(events)
    fixed = producer.get(target)
    ids = sorted(e["event_id"] for e in events if e["event_id"] != fixed)
    perm = list(ids)
    seed = int(hashlib.sha256(f"{run_id}|shuffle|{SELECTOR_VERSION}".encode()).hexdigest()[:16], 16)
    random.Random(seed).shuffle(perm)
    mapping = dict(zip(ids, perm))
    if fixed is not None:
        mapping[fixed] = fixed
    return mapping


def lexical_order(observed):
    env = observed["envelope"]
    target = env["target_artifact_id"]
    query = tokens(POLICIES[observed["domain"]] + " " + json.dumps(env))
    scored = []
    for e in observed["events"]:
        text = render_event(e)
        s = 4 * (target in text) + len(tokens(text) & query)
        scored.append((-s, -e["sequence"], e["event_id"]))
    scored.sort()
    return [x[2] for x in scored]


def bm25_order(observed, k1=1.2, b=0.75):
    """Okapi BM25 over the trajectory's events (IDF computed within the trajectory).
    Query: public policy + finalization envelope tokens; documents: rendered events."""
    env = observed["envelope"]
    query = tokens(POLICIES[observed["domain"]] + " " + json.dumps(env))
    docs = []
    for e in observed["events"]:
        toks = [t for t in TOKEN_RE.findall(render_event(e).lower()) if len(t) > 1 and t not in STOPWORDS]
        docs.append((e, toks))
    n = len(docs)
    avgdl = sum(len(t) for _, t in docs) / max(n, 1)
    df = {}
    for _, toks in docs:
        for t in set(toks):
            df[t] = df.get(t, 0) + 1
    scored = []
    for e, toks in docs:
        tf = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        s = 0.0
        for q in query:
            if q in tf:
                idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))
                s += idf * tf[q] * (k1 + 1) / (tf[q] + k1 * (1 - b + b * len(toks) / avgdl))
        scored.append((-round(s, 9), -e["sequence"], e["event_id"]))
    scored.sort()
    return [x[2] for x in scored]


PRF_TOP_K = 3


def lexical_prf_order(observed, k=PRF_TOP_K):
    """Lexical retrieval with one round of pseudo-relevance feedback: the query is
    expanded with every token (including artifact IDs) of the top-k first-round events.
    No graph traversal or producer/consumer direction is used."""
    env = observed["envelope"]
    target = env["target_artifact_id"]
    first = lexical_order(observed)
    by_id = {e["event_id"]: e for e in observed["events"]}
    query = tokens(POLICIES[observed["domain"]] + " " + json.dumps(env))
    for eid in first[:k]:
        query |= tokens(render_event(by_id[eid]))
    scored = []
    for e in observed["events"]:
        text = render_event(e)
        s = 4 * (target in text) + len(tokens(text) & query)
        scored.append((-s, -e["sequence"], e["event_id"]))
    scored.sort()
    return [x[2] for x in scored]


def select(method: str, observed: dict, cap: int):
    """Return a list of calls; each call is {view_note, event_ids, budget, used, skipped, overhead}."""
    events = observed["events"]
    by_id = {e["event_id"]: e for e in events}
    env = observed["envelope"]
    dom = observed["domain"]
    target = env["target_artifact_id"]
    if method == "full":
        oh = overhead_tokens(dom, env)
        ids = [e["event_id"] for e in events]
        return [{"view_note": "", "event_ids": ids, "budget": None, "overhead": oh,
                 "used": sum(event_cost(by_id[i]) for i in ids), "skipped": 0, "candidates": len(ids)}]
    if method == "isolated":
        calls = []
        for w in ("W1", "W2", "W3"):
            note = ISOLATED_VIEW_NOTE.format(w=w)
            oh = overhead_tokens(dom, env, note)
            budget = cap // 3 - oh
            view = [e for e in events if e["worker_id"] == w]
            order = [e["event_id"] for e in sorted(view, key=lambda e: -e["sequence"])]
            chosen, used, skipped = _fill(order, max(budget, 0), by_id)
            calls.append({"view_note": note, "event_ids": chosen, "budget": budget, "overhead": oh,
                          "used": used, "skipped": skipped, "candidates": len(order), "worker": w})
        return calls
    oh = overhead_tokens(dom, env)
    budget = cap - oh
    if method == "chronological":
        order = [e["event_id"] for e in sorted(events, key=lambda e: -e["sequence"])]
    elif method == "lexical":
        order = lexical_order(observed)
    elif method == "lexical_prf":
        order = lexical_prf_order(observed)
    elif method == "bm25":
        order = bm25_order(observed)
    elif method == "dependency":
        order = dependency_order(events, target)
    elif method == "shuffled":
        mapping = shuffle_permutation(events, target, observed["run_id"])
        order = [mapping[x] for x in dependency_order(events, target)]
    else:
        raise ValueError(method)
    chosen, used, skipped = _fill(order, max(budget, 0), by_id)
    return [{"view_note": "", "event_ids": chosen, "budget": budget, "overhead": oh, "used": used,
             "skipped": skipped, "candidates": len(order)}]
