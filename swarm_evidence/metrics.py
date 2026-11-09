"""Metrics with explicit edge-case behavior and family-clustered bootstrap."""
from __future__ import annotations

import math
import random


def auroc(scores, labels):
    """Mann-Whitney AUROC with ties counted 1/2. Returns None for single-class input."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return None
    total = 0.0
    for p in pos:
        for n in neg:
            total += 1.0 if p > n else 0.5 if p == n else 0.0
    return total / (len(pos) * len(neg))


def auprc(scores, labels):
    """Average precision (step interpolation, ties broken pessimistically). None if no positives."""
    n_pos = sum(1 for y in labels if y == 1)
    if n_pos == 0:
        return None
    # pessimistic tie handling: within equal scores, negatives first
    order = sorted(zip(scores, labels), key=lambda t: (-t[0], t[1]))
    tp = fp = 0
    ap = 0.0
    i = 0
    while i < len(order):
        j = i
        while j < len(order) and order[j][0] == order[i][0]:
            j += 1
        block = order[i:j]
        btp = sum(1 for _, y in block if y == 1)
        bfp = len(block) - btp
        tp += btp
        fp += bfp
        if btp:
            ap += (btp / n_pos) * (tp / (tp + fp))
        i = j
    return ap


def wilson(k, n, z=1.959964):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centre - half), min(1.0, centre + half))


def cluster_bootstrap_diff(rows_a, rows_b, cluster_key, n_boot=10000, seed=0):
    """Paired family-clustered bootstrap of AUROC(a) - AUROC(b).

    rows_*: dict run_id -> (score, label, cluster). Both arms must cover the same run_ids.
    Resamples whole clusters with replacement; returns (point, lo, hi, n_clusters, n_valid_boot).
    """
    assert set(rows_a) == set(rows_b), "arms must be paired on identical trajectories"
    clusters = sorted({v[2] for v in rows_a.values()})
    by_c = {c: [r for r, v in rows_a.items() if v[2] == c] for c in clusters}

    def diff(run_ids):
        sa = [rows_a[r][0] for r in run_ids]
        sb = [rows_b[r][0] for r in run_ids]
        ys = [rows_a[r][1] for r in run_ids]
        a, b = auroc(sa, ys), auroc(sb, ys)
        if a is None or b is None:
            return None
        return a - b

    point = diff([r for c in clusters for r in by_c[c]])
    rnd = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        pick = [rnd.choice(clusters) for _ in clusters]
        d = diff([r for c in pick for r in by_c[c]])
        if d is not None:
            boots.append(d)
    boots.sort()
    if not boots:
        return point, None, None, len(clusters), 0
    lo = boots[int(0.025 * (len(boots) - 1))]
    hi = boots[int(math.ceil(0.975 * (len(boots) - 1)))]
    return point, lo, hi, len(clusters), len(boots)


def cluster_bootstrap_auroc(rows, n_boot=10000, seed=0):
    """Family-clustered percentile interval for a single arm's AUROC."""
    clusters = sorted({v[2] for v in rows.values()})
    by_c = {c: [r for r, v in rows.items() if v[2] == c] for c in clusters}
    rnd = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        pick = [rnd.choice(clusters) for _ in clusters]
        ids = [r for c in pick for r in by_c[c]]
        a = auroc([rows[r][0] for r in ids], [rows[r][1] for r in ids])
        if a is not None:
            boots.append(a)
    boots.sort()
    if not boots:
        return None, None
    return boots[int(0.025 * (len(boots) - 1))], boots[int(math.ceil(0.975 * (len(boots) - 1)))]
