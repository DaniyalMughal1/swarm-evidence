"""Missing dependency metadata: remove producer-consumer relations from every observer-visible field.

A relation is (artifact a, producer event p, consumer event c) with a in out(p) and a in in(c).
Masking replaces every occurrence of a inside c (inputs, arguments, version map, note) with a fresh
placeholder unique to that relation, so the relation cannot be rebuilt by equality joins on IDs.
The same masked view is given to every selection method. Whole events are never removed.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
from collections import defaultdict

CONDITIONS = ("full", "random25", "random50", "bridges")


def relations(events):
    producer = {}
    for e in events:
        for a in e["output_artifact_ids"]:
            producer[a] = e["event_id"]
    rels = []
    for e in events:
        for a in e["input_artifact_ids"]:
            if a in producer:
                rels.append((a, producer[a], e["event_id"]))
    return rels


def _bridges(nodes, edges):
    """Undirected bridges (Tarjan) on a simple graph; edges is a set of frozensets."""
    adj = defaultdict(set)
    for ed in edges:
        u, v = tuple(ed)
        adj[u].add(v)
        adj[v].add(u)
    disc, low, out, t = {}, {}, set(), [0]
    for root in sorted(nodes):
        if root in disc:
            continue
        stack = [(root, None, iter(sorted(adj[root])))]
        disc[root] = low[root] = t[0]
        t[0] += 1
        while stack:
            u, parent, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop()
                if parent is not None:
                    low[parent] = min(low[parent], low[u])
                    if low[u] > disc[parent]:
                        out.add(frozenset((parent, u)))
                continue
            if nxt == parent:
                continue
            if nxt in disc:
                low[u] = min(low[u], disc[nxt])
            else:
                disc[nxt] = low[nxt] = t[0]
                t[0] += 1
                stack.append((nxt, u, iter(sorted(adj[nxt]))))
    return out


def _edge_betweenness(nodes, edges):
    adj = defaultdict(set)
    for ed in edges:
        u, v = tuple(ed)
        adj[u].add(v)
        adj[v].add(u)
    eb = defaultdict(float)
    for s in sorted(nodes):
        stack, pred = [], defaultdict(list)
        sigma = defaultdict(float)
        sigma[s] = 1.0
        dist = {s: 0}
        queue = [s]
        while queue:
            v = queue.pop(0)
            stack.append(v)
            for w in sorted(adj[v]):
                if w not in dist:
                    dist[w] = dist[v] + 1
                    queue.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)
        delta = defaultdict(float)
        while stack:
            w = stack.pop()
            for v in pred[w]:
                c = sigma[v] / sigma[w] * (1 + delta[w])
                eb[frozenset((v, w))] += c
                delta[v] += c
    return eb


def choose_relations(observed, condition):
    events = observed["events"]
    rels = relations(events)
    if condition == "full":
        return []
    seed = int(hashlib.sha256(f"{observed['run_id']}|{condition}|mask-v1".encode()).hexdigest()[:16], 16)
    if condition in ("random25", "random50"):
        frac = 0.25 if condition == "random25" else 0.50
        k = int(round(frac * len(rels)))
        return sorted(random.Random(seed).sample(sorted(rels), k))
    if condition == "bridges":
        worker = {e["event_id"]: e["worker_id"] for e in events}
        seq = {e["event_id"]: e["sequence"] for e in events}
        nodes = {e["event_id"] for e in events}
        edges = {frozenset((p, c)) for _, p, c in rels if p != c}
        cross = [r for r in rels if worker[r[1]] != worker[r[2]]]
        br = _bridges(nodes, edges)
        chosen = [r for r in cross if frozenset((r[1], r[2])) in br]
        if chosen:
            return sorted(chosen)
        eb = _edge_betweenness(nodes, edges)
        ranked = sorted(cross, key=lambda r: (-eb[frozenset((r[1], r[2]))], seq[r[1]], seq[r[2]], r[0]))
        return sorted(ranked[: math.ceil(len(cross) / 4)])
    raise ValueError(condition)


def apply_visibility(observed, condition):
    """Return (masked_observed, audit)."""
    chosen = choose_relations(observed, condition)
    out = copy.deepcopy(observed)
    if not chosen:
        return out, {"condition": condition, "n_relations": len(relations(observed["events"])), "n_masked": 0,
                     "events_affected": 0, "audit_ok": True}
    by_id = {e["event_id"]: i for i, e in enumerate(out["events"])}
    per_consumer = defaultdict(list)
    for k, (a, p, c) in enumerate(chosen):
        per_consumer[c].append((a, f"unk-{k + 1:03d}"))
    for c, subs in per_consumer.items():
        i = by_id[c]
        text = json.dumps(out["events"][i])
        for a, ph in subs:
            text = text.replace(f'"{a}"', f'"{ph}"')
        out["events"][i] = json.loads(text)
    audit_ok = all(a not in json.dumps(out["events"][by_id[c]]) for a, _, c in chosen)
    # the producer still lists the artifact; no other masked consumer may still hold it via another field
    return out, {"condition": condition, "n_relations": len(relations(observed["events"])), "n_masked": len(chosen),
                 "events_affected": len(per_consumer), "audit_ok": audit_ok,
                 "cross_worker_masked": sum(1 for a, p, c in chosen
                                            if observed["events"][by_id[p]]["worker_id"] !=
                                            observed["events"][by_id[c]]["worker_id"])}
