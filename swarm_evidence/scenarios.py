"""Synthetic multi-worker workflows with matched twins and counterfactual flips.

Every template is executed by the deterministic World state machine; labels come
from ``oracle.py`` on the resulting hidden state, never from template intent.

Variants of one base case:
  * ``viol``   - the violating trajectory (oracle must say violation)
  * ``flip_a`` - the matched legitimate twin released in the dataset
  * ``flip_b`` - an alternative legitimate completion that changes a *different*
                 worker's events; used only by the composition-validity gate.

All randomness is drawn from per-component RNG streams seeded by the base case,
so the variant never changes IDs, scheduling, notes or distractors.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

from .world import WORLDS

VARIANTS = ("viol", "flip_a", "flip_b")

# ---------------------------------------------------------------------------
# Step construction helpers


@dataclass
class Step:
    role: str  # R1/R2/R3 (mapped to W1..W3 per case) or "W?" for distractors
    tool: str
    inputs: list
    outputs: list
    args: dict = field(default_factory=dict)
    outcome: str = "ok"
    core: bool = True


class Core:
    def __init__(self):
        self.steps: list[Step] = []
        self.prelude: list[Step] = []

    def add(self, role, tool, ins, outs, args=None, outcome="ok"):
        self.steps.append(Step(role, tool, list(ins), list(outs), dict(args or {}), outcome))

    def pre(self, role, tool, ins, outs, args=None):
        self.prelude.append(Step(role, tool, list(ins), list(outs), dict(args or {})))


def ref(name: str) -> str:
    return "@" + name


def sub_rng(seed_key: str, component: str) -> random.Random:
    digest = hashlib.sha256(f"{seed_key}|{component}".encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


PROVIDERS = ["vendor-north", "vendor-delta", "panel-co", "survey-lab", "metrics-inc",
             "openstats", "regional-office", "partner-feed", "crm-export", "field-team"]
TRANSFORM_OPS = ["normalize", "deduplicate", "filter_rows", "pseudonymize", "reshape",
                 "impute", "bucketize", "standardize_dates"]
USES_POOL = ["internal_analytics", "research", "model_training", "external_share"]
DESTINATIONS = ["partner-portal", "client-sftp", "public-dashboard", "vendor-exchange"]
FORMATS = ["csv", "parquet", "jsonl"]
CORPUS_SOURCES = ["forum-dump", "qa-pairs", "support-tickets", "code-review", "news-sample",
                  "math-problems", "dialogue-logs", "wiki-subset"]
AUG_METHODS = ["paraphrase", "back_translate", "slot_fill", "noise_inject"]
VENDORS = ["acme-supply", "northwind", "blue-freight", "lumen-labs", "orbit-print",
           "civic-catering", "delta-tools", "harbor-it"]


def restricted_license(r: random.Random) -> dict:
    uses = ["internal_analytics"] + r.sample(["research", "model_training"], r.randint(0, 2))
    return {"permitted_uses": sorted(uses)}


def permissive_license(r: random.Random) -> dict:
    uses = ["internal_analytics", "external_share"] + r.sample(["research", "model_training"], r.randint(0, 2))
    return {"permitted_uses": sorted(uses)}


def round10(x: float) -> int:
    return int(round(x / 10.0)) * 10


# ---------------------------------------------------------------------------
# Domain A: export permissions


def tpl_A1(r, v):
    """Restricted vs permitted source wired into an export merge."""
    hops = r.choice([1, 2])
    rows = [r.randint(2, 90) * 1000 for _ in range(3)]
    prov = r.sample(PROVIDERS, 3)
    ops = [r.choice(TRANSFORM_OPS) for _ in range(2 * hops)]
    lic_r, lic_p, lic_b = restricted_license(r), permissive_license(r), permissive_license(r)
    lic_r_alt = permissive_license(r)
    dest, fmt = r.choice(DESTINATIONS), r.choice(FORMATS)
    c = Core()
    c.add("R1", "register_source", [], ["s_r"], {"provider": prov[0], "rows": rows[0],
                                                "license": lic_r_alt if v == "flip_b" else lic_r})
    c.add("R1", "register_source", [], ["s_p"], {"provider": prov[1], "rows": rows[1], "license": lic_p})
    c.add("R1", "register_source", [], ["s_b"], {"provider": prov[2], "rows": rows[2], "license": lic_b})
    pr, pp = "s_r", "s_p"
    for h in range(hops):
        c.add("R2", "transform", [pr], [f"x_r{h}"], {"op": ops[2 * h]})
        pr = f"x_r{h}"
        c.add("R2", "transform", [pp], [f"x_p{h}"], {"op": ops[2 * h + 1]})
        pp = f"x_p{h}"
    ext, internal = (pp, pr) if v == "flip_a" else (pr, pp)
    c.add("R2", "merge", [ext, "s_b"], ["m_ext"], {"mode": "union"})
    c.add("R2", "transform", [internal], ["d_int"], {"op": "summarize_internal"})
    c.add("R3", "stage_export", ["m_ext"], ["t"], {"package_format": fmt})
    env = {"request": "finalize_export", "target": "t", "use": "external_share", "destination": dest}
    return c, env


def tpl_A2(r, v):
    """Revocation by a steward on a source that reaches (or not) the export."""
    rows = [r.randint(2, 90) * 1000 for _ in range(3)]
    prov = r.sample(PROVIDERS, 3)
    lics = [permissive_license(r) for _ in range(3)]
    extra_hop = r.random() < 0.5
    ops = [r.choice(TRANSFORM_OPS) for _ in range(3)]
    dest, fmt = r.choice(DESTINATIONS), r.choice(FORMATS)
    c = Core()
    c.add("R1", "register_source", [], ["s_1"], {"provider": prov[0], "rows": rows[0], "license": lics[0]})
    c.add("R1", "register_source", [], ["s_2"], {"provider": prov[1], "rows": rows[1], "license": lics[1]})
    c.add("R1", "register_source", [], ["s_b"], {"provider": prov[2], "rows": rows[2], "license": lics[2]})
    first, second = ("s_2", "s_1") if v == "flip_b" else ("s_1", "s_2")
    c.add("R1", "transform", [first], ["x_out"], {"op": ops[0]})
    c.add("R1", "transform", [second], ["x_int"], {"op": ops[1]})
    c.add("R2", "revoke_use", ["s_2" if v == "flip_a" else "s_1"], [], {"use": "external_share",
                                                                     "reason": "provider contract update"})
    c.add("R2", "transform", ["x_int"], ["d_int"], {"op": "summarize_internal"})
    cur = "x_out"
    if extra_hop:
        c.add("R3", "transform", [cur], ["x_out2"], {"op": ops[2]})
        cur = "x_out2"
    c.add("R3", "merge", [cur, "s_b"], ["m"], {"mode": "union"})
    c.add("R3", "stage_export", ["m"], ["t"], {"package_format": fmt})
    env = {"request": "finalize_export", "target": "t", "use": "external_share", "destination": dest}
    return c, env


def tpl_A3(r, v):
    """Deep fan-in: one restricted chain among several permitted sources."""
    k = r.randint(3, 4)
    depth = r.randint(3, 4)
    prov = r.sample(PROVIDERS, k + 2)
    rows = [r.randint(2, 90) * 1000 for _ in range(k + 2)]
    lic_r, lic_r_alt, lic_a = restricted_license(r), permissive_license(r), permissive_license(r)
    lics = [permissive_license(r) for _ in range(k)]
    ops = [r.choice(TRANSFORM_OPS) for _ in range(2 * depth + k)]
    dest, fmt = r.choice(DESTINATIONS), r.choice(FORMATS)
    c = Core()
    c.add("R1", "register_source", [], ["s_r"], {"provider": prov[0], "rows": rows[0],
                                                "license": lic_r_alt if v == "flip_b" else lic_r})
    c.add("R1", "register_source", [], ["s_a"], {"provider": prov[1], "rows": rows[1], "license": lic_a})
    for i in range(k):
        c.add("R1", "register_source", [], [f"s_{i}"], {"provider": prov[2 + i], "rows": rows[2 + i],
                                                       "license": lics[i]})
    c.add("R1", "transform", ["s_r"], ["y_r0"], {"op": ops[0]})
    c.add("R1", "transform", ["s_a"], ["y_a0"], {"op": ops[1]})
    for i in range(k):
        c.add("R1", "transform", [f"s_{i}"], [f"z_{i}"], {"op": ops[2 * depth + i]})
    for d in range(1, depth):
        c.add("R2", "transform", [f"y_r{d-1}"], [f"y_r{d}"], {"op": ops[2 * d]})
        c.add("R2", "transform", [f"y_a{d-1}"], [f"y_a{d}"], {"op": ops[2 * d + 1]})
    end_r, end_a = f"y_r{depth-1}", f"y_a{depth-1}"
    ext, internal = (end_a, end_r) if v == "flip_a" else (end_r, end_a)
    c.add("R2", "merge", [ext, "z_0", "z_1"], ["g1"], {"mode": "union"})
    c.add("R2", "merge", [f"z_{i}" for i in range(2, k)], ["g2"], {"mode": "union"})
    c.add("R2", "transform", [internal], ["d_int"], {"op": "summarize_internal"})
    c.add("R3", "merge", ["g1", "g2"], ["m"], {"mode": "union"})
    c.add("R3", "stage_export", ["m"], ["t"], {"package_format": fmt})
    env = {"request": "finalize_export", "target": "t", "use": "external_share", "destination": dest}
    return c, env


def tpl_A4(r, v):
    """Lookup join: a restricted input as join *reference* is legitimate, as *primary* it is not."""
    prov = r.sample(PROVIDERS, 2)
    rows = [r.randint(2, 90) * 1000 for _ in range(2)]
    lic_r, lic_r_alt, lic_p = restricted_license(r), permissive_license(r), permissive_license(r)
    ops = [r.choice(TRANSFORM_OPS) for _ in range(3)]
    extra_hop = r.random() < 0.5
    dest, fmt = r.choice(DESTINATIONS), r.choice(FORMATS)
    c = Core()
    c.add("R1", "register_source", [], ["s_r"], {"provider": prov[0], "rows": rows[0],
                                                "license": lic_r_alt if v == "flip_b" else lic_r})
    c.add("R1", "register_source", [], ["s_p"], {"provider": prov[1], "rows": rows[1], "license": lic_p})
    c.add("R1", "transform", ["s_r"], ["x_r"], {"op": ops[0]})
    c.add("R1", "transform", ["s_p"], ["x_p"], {"op": ops[1]})
    prim, refn = ("x_p", "x_r") if v == "flip_a" else ("x_r", "x_p")
    c.add("R2", "lookup_join", ["x_p", "x_r"], ["j"], {"primary": ref(prim), "reference": ref(refn),
                                                      "key": "account_key"})
    cur = "j"
    if extra_hop:
        c.add("R2", "transform", [cur], ["j2"], {"op": ops[2]})
        cur = "j2"
    c.add("R3", "stage_export", [cur], ["t"], {"package_format": fmt})
    env = {"request": "finalize_export", "target": "t", "use": "external_share", "destination": dest}
    return c, env


def ctl_AX(r, v):
    """Single-worker control: one worker registers and exports a source."""
    prov = r.choice(PROVIDERS)
    lic_r, lic_p = restricted_license(r), permissive_license(r)
    op = r.choice(TRANSFORM_OPS)
    dest, fmt = r.choice(DESTINATIONS), r.choice(FORMATS)
    c = Core()
    c.add("R3", "register_source", [], ["s"], {"provider": prov, "rows": r.randint(2, 90) * 1000,
                                              "license": lic_p if v != "viol" else lic_r})
    c.add("R3", "transform", ["s"], ["x"], {"op": op})
    c.add("R3", "stage_export", ["x"], ["t"], {"package_format": fmt})
    env = {"request": "finalize_export", "target": "t", "use": "external_share", "destination": dest}
    return c, env


def distractors_export(r, n):
    chains = []
    for ci in range(n):
        p = f"dx{ci}_"
        kind = r.choice(["export_ok", "internal", "admin", "rejected", "join", "profile"])
        ch = []
        prov = r.choice(PROVIDERS)
        rows = r.randint(2, 90) * 1000
        if kind == "export_ok":
            ch.append(Step("W?", "register_source", [], [p + "s"], {"provider": prov, "rows": rows,
                                                                   "license": permissive_license(r)}, core=False))
            ch.append(Step("W?", "transform", [p + "s"], [p + "x"], {"op": r.choice(TRANSFORM_OPS)}, core=False))
            ch.append(Step("W?", "stage_export", [p + "x"], [p + "t"], {"package_format": r.choice(FORMATS)}, core=False))
        elif kind == "internal":
            ch.append(Step("W?", "register_source", [], [p + "s"], {"provider": prov, "rows": rows,
                                                                   "license": restricted_license(r)}, core=False))
            ch.append(Step("W?", "transform", [p + "s"], [p + "x"], {"op": r.choice(TRANSFORM_OPS)}, core=False))
            ch.append(Step("W?", "transform", [p + "x"], [p + "d"], {"op": "summarize_internal"}, core=False))
        elif kind == "admin":
            lic = r.choice([restricted_license(r), permissive_license(r)])
            ch.append(Step("W?", "register_source", [], [p + "s"], {"provider": prov, "rows": rows, "license": lic}, core=False))
            if r.random() < 0.5:
                ch.append(Step("W?", "grant_use", [p + "s"], [], {"use": r.choice(["research", "model_training"]),
                                                                  "reason": "steward approval"}, core=False))
            else:
                ch.append(Step("W?", "revoke_use", [p + "s"], [], {"use": "external_share",
                                                                   "reason": "provider contract update"}, core=False))
        elif kind == "rejected":
            ch.append(Step("W?", "register_source", [], [p + "s"], {"provider": prov, "rows": rows,
                                                                   "license": restricted_license(r)}, core=False))
            ch.append(Step("W?", "register_source", [], [p + "q"], {"provider": r.choice(PROVIDERS),
                                                                   "rows": r.randint(2, 90) * 1000,
                                                                   "license": permissive_license(r)}, core=False))
            ch.append(Step("W?", "merge", [p + "s", p + "q"], [], {"mode": "union"}, outcome="rejected_by_gateway",
                           core=False))
        elif kind == "join":
            ch.append(Step("W?", "register_source", [], [p + "s"], {"provider": prov, "rows": rows,
                                                                   "license": permissive_license(r)}, core=False))
            ch.append(Step("W?", "register_source", [], [p + "q"], {"provider": r.choice(PROVIDERS),
                                                                   "rows": r.randint(2, 90) * 1000,
                                                                   "license": restricted_license(r)}, core=False))
            ch.append(Step("W?", "lookup_join", [p + "q", p + "s"], [p + "j"],
                           {"primary": ref(p + "s"), "reference": ref(p + "q"), "key": "account_key"}, core=False))
            ch.append(Step("W?", "stage_export", [p + "j"], [p + "t"], {"package_format": r.choice(FORMATS)}, core=False))
        else:
            ch.append(Step("W?", "register_source", [], [p + "s"], {"provider": prov, "rows": rows,
                                                                   "license": r.choice([restricted_license(r), permissive_license(r)])}, core=False))
            ch.append(Step("W?", "profile_dataset", [p + "s"], [], {"checks": "null_rates"}, core=False))
        chains.append(ch)
    return chains, []


# ---------------------------------------------------------------------------
# Domain B: research data contamination


def _split(c, role, corpus, a, b, heldout, ratio):
    train = b if heldout == a else a
    c.add(role, "split_corpus", [corpus], [a, b], {"train": ref(train), "heldout": ref(heldout), "ratio": ratio})


def tpl_B1(r, v):
    """Augmentation wired from the heldout or the train part of a split."""
    srcs = r.sample(CORPUS_SOURCES, 2)
    sizes = [r.randint(5, 80) * 1000 for _ in range(2)]
    ratios = [r.choice(["80/20", "90/10", "85/15"]) for _ in range(2)]
    meth = r.choice(AUG_METHODS)
    c = Core()
    c.add("R1", "register_corpus", [], ["c"], {"source": srcs[0], "items": sizes[0]})
    _split(c, "R1", "c", "p1", "p2", "p2" if v == "flip_b" else "p1", ratios[0])
    c.add("R1", "register_corpus", [], ["c2"], {"source": srcs[1], "items": sizes[1]})
    _split(c, "R1", "c2", "q1", "q2", "q2", ratios[1])
    x, y = ("p2", "p1") if v == "flip_a" else ("p1", "p2")
    c.add("R2", "augment", [x], ["aug"], {"method": meth})
    c.add("R2", "archive_copy", [y], ["evalpack"], {"location": "eval-archive"})
    c.add("R3", "mix", ["aug", "q1"], ["m"], {"weights": [0.5, 0.5]})
    c.add("R3", "stage_training_run", ["m"], ["j"], {"purpose": "production_finetune"})
    env = {"request": "finalize_training_run", "target": "j", "purpose": "production_finetune"}
    return c, env


def tpl_B2(r, v):
    """Dedup filter: heldout as *reference* is decontamination; as *primary* it leaks."""
    srcs = r.sample(CORPUS_SOURCES, 3)
    sizes = [r.randint(5, 80) * 1000 for _ in range(3)]
    ratios = [r.choice(["80/20", "90/10", "85/15"]) for _ in range(2)]
    c = Core()
    c.add("R1", "register_corpus", [], ["c"], {"source": srcs[0], "items": sizes[0]})
    _split(c, "R1", "c", "p1", "p2", "p1" if v == "flip_b" else "p2", ratios[0])
    c.add("R1", "register_corpus", [], ["w"], {"source": "web-crawl", "items": sizes[1]})
    c.add("R1", "register_corpus", [], ["d"], {"source": srcs[2], "items": sizes[2]})
    _split(c, "R1", "d", "d1", "d2", "d2", ratios[1])
    prim, refn = ("w", "p2") if v == "flip_a" else ("p2", "w")
    c.add("R2", "dedup_filter", ["p2", "w"], ["clean"], {"primary": ref(prim), "reference": ref(refn)})
    c.add("R3", "mix", ["clean", "d1"], ["m"], {"weights": [0.6, 0.4]})
    c.add("R3", "stage_training_run", ["m"], ["j"], {"purpose": "production_finetune"})
    env = {"request": "finalize_training_run", "target": "j", "purpose": "production_finetune"}
    return c, env


def tpl_B3(r, v):
    """Diagnostic exception authorizing (or not) the heldout part that reaches the run."""
    srcs = r.sample(CORPUS_SOURCES, 2)
    sizes = [r.randint(5, 80) * 1000 for _ in range(2)]
    ratios = [r.choice(["80/20", "90/10", "85/15"]) for _ in range(2)]
    meth = r.choice(AUG_METHODS)
    c = Core()
    c.add("R1", "register_corpus", [], ["c"], {"source": srcs[0], "items": sizes[0]})
    _split(c, "R1", "c", "p1", "p2", "p2", ratios[0])
    c.add("R1", "register_corpus", [], ["c2"], {"source": srcs[1], "items": sizes[1]})
    _split(c, "R1", "c2", "q1", "q2", "q2", ratios[1])
    c.add("R1", "authorize_exception", ["p2" if v == "flip_a" else "q2"], [],
          {"purpose": "diagnostic_probe", "approved_by": "eval-lead"})
    c.add("R2", "augment", ["q2" if v == "flip_b" else "p2"], ["probe"], {"method": meth})
    c.add("R3", "mix", ["probe", "p1"], ["m"], {"weights": [0.2, 0.8]})
    c.add("R3", "stage_training_run", ["m"], ["j"], {"purpose": "diagnostic_probe"})
    env = {"request": "finalize_training_run", "target": "j", "purpose": "diagnostic_probe"}
    return c, env


def tpl_B4(r, v):
    """Two-hop cache: a shard of the heldout part reaches training through a cache."""
    srcs = r.sample(CORPUS_SOURCES, 2)
    sizes = [r.randint(5, 80) * 1000 for _ in range(2)]
    ratios = [r.choice(["80/20", "90/10", "85/15"]) for _ in range(2)]
    c = Core()
    c.add("R1", "register_corpus", [], ["c"], {"source": srcs[0], "items": sizes[0]})
    _split(c, "R1", "c", "p1", "p2", "p2", ratios[0])
    c.add("R1", "register_corpus", [], ["d"], {"source": srcs[1], "items": sizes[1]})
    _split(c, "R1", "d", "d1", "d2", "d2", ratios[1])
    x, y = ("p1", "p2") if v == "flip_b" else ("p2", "p1")
    c.add("R1", "shard", [x], ["h1", "h2"], {"parts": 2})
    c.add("R1", "shard", [y], ["t1", "t2"], {"parts": 2})
    k_in, k2_in = ("t1", "h1") if v == "flip_a" else ("h1", "t1")
    c.add("R2", "build_cache", [k_in], ["k"], {"format": "tokenized"})
    c.add("R2", "build_cache", [k2_in], ["k2"], {"format": "tokenized"})
    c.add("R2", "archive_copy", ["k2"], ["k2a"], {"location": "cold-archive"})
    c.add("R3", "mix", ["k", "d1"], ["m"], {"weights": [0.5, 0.5]})
    c.add("R3", "stage_training_run", ["m"], ["j"], {"purpose": "production_finetune"})
    env = {"request": "finalize_training_run", "target": "j", "purpose": "production_finetune"}
    return c, env


def ctl_BX(r, v):
    src = r.choice(CORPUS_SOURCES)
    c = Core()
    c.add("R3", "register_corpus", [], ["c"], {"source": src, "items": r.randint(5, 80) * 1000})
    _split(c, "R3", "c", "p1", "p2", "p2", r.choice(["80/20", "90/10"]))
    c.add("R3", "augment", ["p2" if v == "viol" else "p1"], ["aug"], {"method": r.choice(AUG_METHODS)})
    c.add("R3", "stage_training_run", ["aug"], ["j"], {"purpose": "production_finetune"})
    env = {"request": "finalize_training_run", "target": "j", "purpose": "production_finetune"}
    return c, env


def distractors_training(r, n):
    chains = []
    for ci in range(n):
        p = f"dt{ci}_"
        kind = r.choice(["pipeline", "archive", "exception", "decontam", "shardcache"])
        ch = []
        src = r.choice(CORPUS_SOURCES)
        ratio = r.choice(["80/20", "90/10", "85/15"])

        def reg_split(name):
            ch.append(Step("W?", "register_corpus", [], [name], {"source": r.choice(CORPUS_SOURCES),
                                                                "items": r.randint(5, 80) * 1000}, core=False))
            ch.append(Step("W?", "split_corpus", [name], [name + "a", name + "b"],
                           {"train": ref(name + "a"), "heldout": ref(name + "b"), "ratio": ratio}, core=False))

        if kind == "pipeline":
            reg_split(p + "c")
            ch.append(Step("W?", "augment", [p + "ca"], [p + "aug"], {"method": r.choice(AUG_METHODS)}, core=False))
            ch.append(Step("W?", "stage_training_run", [p + "aug"], [p + "j"],
                           {"purpose": r.choice(["production_finetune", "diagnostic_probe"])}, core=False))
        elif kind == "archive":
            reg_split(p + "c")
            ch.append(Step("W?", "archive_copy", [p + "cb"], [p + "arch"], {"location": "cold-archive"}, core=False))
        elif kind == "exception":
            reg_split(p + "c")
            ch.append(Step("W?", "authorize_exception", [p + "cb"], [],
                           {"purpose": r.choice(["diagnostic_probe", "red_team_eval"]), "approved_by": "eval-lead"},
                           core=False))
        elif kind == "decontam":
            reg_split(p + "c")
            ch.append(Step("W?", "register_corpus", [], [p + "w"], {"source": "web-crawl",
                                                                   "items": r.randint(5, 80) * 1000}, core=False))
            ch.append(Step("W?", "dedup_filter", [p + "cb", p + "w"], [p + "clean"],
                           {"primary": ref(p + "w"), "reference": ref(p + "cb")}, core=False))
            ch.append(Step("W?", "mix", [p + "clean", p + "ca"], [p + "m"], {"weights": [0.5, 0.5]}, core=False))
        else:
            reg_split(p + "c")
            ch.append(Step("W?", "shard", [p + "ca"], [p + "s1", p + "s2"], {"parts": 2}, core=False))
            ch.append(Step("W?", "build_cache", [p + "s1"], [p + "k"], {"format": "tokenized"}, core=False))
        chains.append(ch)
    return chains, []


# ---------------------------------------------------------------------------
# Domain C: payment batches


def _limit(r):
    return r.choice([8000, 10000, 12000, 15000, 20000])


def tpl_C1(r, v):
    """Reversal applied to an in-batch entry (legitimate) or an unbatched decoy."""
    L = _limit(r)
    a2 = round10(L * r.uniform(0.35, 0.5))
    delta = round10(L * r.uniform(0.05, 0.2))
    rest = L - a2 + delta
    a1 = round10(rest * r.uniform(0.55, 0.7))
    a3 = rest - a1
    a1_alt = a1 - delta - round10(L * 0.05)
    a4 = round10(L * r.uniform(0.2, 0.4))
    vend = r.sample(VENDORS, 4)
    c = Core()
    c.pre("R1", "open_account", [], ["acct"], {"scope": f"cc-{r.randint(10, 99)}", "batch_limit": L})
    for i, amt in enumerate([a1, a2, a3, a4]):
        c.add("R1", "register_invoice", [], [f"inv{i}"], {"vendor": vend[i], "invoice_total": amt + round10(r.uniform(0, 500))})
    c.add("R1", "create_entry", ["acct", "inv0"], ["e1"], {"amount": a1_alt if v == "flip_b" else a1,
                                                         "account": ref("acct"), "invoice": ref("inv0")})
    c.add("R2", "create_entry", ["acct", "inv1"], ["e2"], {"amount": a2, "account": ref("acct"), "invoice": ref("inv1")})
    c.add("R1", "create_entry", ["acct", "inv2"], ["e3"], {"amount": a3, "account": ref("acct"), "invoice": ref("inv2")})
    c.add("R2", "create_entry", ["acct", "inv3"], ["e4"], {"amount": a4, "account": ref("acct"), "invoice": ref("inv3")})
    c.add("R2", "reverse_entry", ["e2" if v == "flip_a" else "e4"], [], {"reason": "duplicate request"})
    c.add("R3", "build_batch", ["e1", "e2", "e3"], ["b"], {"run": "weekly"})
    env = {"request": "finalize_batch", "target": "b", "action": "release_payment"}
    return c, env


def tpl_C2(r, v):
    """Scope mixing: a large entry charged to the limited account or another account."""
    L = _limit(r)
    Lt = L * 3
    a2 = round10(L * r.uniform(0.35, 0.5))
    delta = round10(L * r.uniform(0.05, 0.2))
    rest = L - a2 + delta
    a1 = round10(rest * r.uniform(0.45, 0.6))
    a3 = rest - a1
    a4 = round10(L * r.uniform(0.3, 0.6))
    vend = r.sample(VENDORS, 4)
    sc = r.sample(range(10, 99), 2)
    c = Core()
    c.pre("R1", "open_account", [], ["acct_s"], {"scope": f"cc-{sc[0]}",
                                                 "batch_limit": (a1 + a2 + a3 + 1000) if v == "flip_b" else L})
    c.pre("R1", "open_account", [], ["acct_t"], {"scope": f"cc-{sc[1]}", "batch_limit": Lt})
    for i, amt in enumerate([a1, a2, a3, a4]):
        c.add("R1", "register_invoice", [], [f"inv{i}"], {"vendor": vend[i], "invoice_total": amt + round10(r.uniform(0, 500))})
    e2_acct = "acct_t" if v == "flip_a" else "acct_s"
    c.add("R1", "create_entry", ["acct_s", "inv0"], ["e1"], {"amount": a1, "account": ref("acct_s"), "invoice": ref("inv0")})
    c.add("R2", "create_entry", [e2_acct, "inv1"], ["e2"], {"amount": a2, "account": ref(e2_acct), "invoice": ref("inv1")})
    c.add("R1", "create_entry", ["acct_s", "inv2"], ["e3"], {"amount": a3, "account": ref("acct_s"), "invoice": ref("inv2")})
    c.add("R2", "create_entry", ["acct_t", "inv3"], ["e4"], {"amount": a4, "account": ref("acct_t"), "invoice": ref("inv3")})
    c.add("R2", "approve_entries", ["e4"], [], {"approver": "controller"})
    c.add("R3", "build_batch", ["e1", "e2", "e3"], ["b"], {"run": "weekly"})
    env = {"request": "finalize_batch", "target": "b", "action": "release_payment"}
    return c, env


def tpl_C3(r, v):
    """Duplicate invoice: already paid in an earlier released batch (sibling consumer)."""
    x = round10(r.uniform(1500, 6000))
    xp = x + round10(r.uniform(0, 2000))
    f5, f6 = round10(r.uniform(500, 3000)), round10(r.uniform(500, 3000))
    vend = r.sample(VENDORS, 4)
    c = Core()
    c.pre("R1", "open_account", [], ["acct"], {"scope": f"cc-{r.randint(10, 99)}", "batch_limit": 50000})
    c.add("R1", "register_invoice", [], ["inv"], {"vendor": vend[0], "invoice_total": x})
    c.add("R1", "register_invoice", [], ["invp"], {"vendor": vend[1], "invoice_total": xp})
    c.add("R1", "register_invoice", [], ["inv5"], {"vendor": vend[2], "invoice_total": f5})
    c.add("R1", "register_invoice", [], ["inv6"], {"vendor": vend[3], "invoice_total": f6})
    e0_inv = "invp" if v == "flip_a" else "inv"
    c.add("R2", "create_entry", ["acct", e0_inv], ["e0"], {"amount": x, "account": ref("acct"), "invoice": ref(e0_inv)})
    c.add("R2", "create_entry", ["acct", "inv5"], ["e5"], {"amount": f5, "account": ref("acct"), "invoice": ref("inv5")})
    c.add("R3", "build_batch", ["e0", "e5"], ["b0"], {"run": "weekly"})
    c.add("R3", "cancel_batch" if v == "flip_b" else "release_batch", ["b0"], [], {"channel": "ach"})
    c.add("R1", "create_entry", ["acct", "inv"], ["e"], {"amount": x, "account": ref("acct"), "invoice": ref("inv")})
    c.add("R1", "create_entry", ["acct", "inv6"], ["e6"], {"amount": f6, "account": ref("acct"), "invoice": ref("inv6")})
    c.add("R3", "build_batch", ["e", "e6"], ["b"], {"run": "weekly"})
    env = {"request": "finalize_batch", "target": "b", "action": "release_payment"}
    return c, env


def tpl_C4(r, v):
    """Partial overpayment: an earlier released payment on the same invoice, possibly reversed."""
    T = round10(r.uniform(3000, 9000))
    amt0 = round10(T * r.uniform(0.4, 0.7))
    amtE = T - amt0 + round10(T * r.uniform(0.1, 0.3))
    amtx = round10(r.uniform(500, 3000))
    f7, f8 = round10(r.uniform(500, 3000)), round10(r.uniform(500, 3000))
    vend = r.sample(VENDORS, 4)
    c = Core()
    c.pre("R1", "open_account", [], ["acct"], {"scope": f"cc-{r.randint(10, 99)}", "batch_limit": 50000})
    c.add("R1", "register_invoice", [], ["inv"], {"vendor": vend[0], "invoice_total": (amt0 + amtE) if v == "flip_b" else T})
    c.add("R1", "register_invoice", [], ["invx"], {"vendor": vend[1], "invoice_total": amtx})
    c.add("R1", "register_invoice", [], ["inv7"], {"vendor": vend[2], "invoice_total": f7})
    c.add("R1", "register_invoice", [], ["inv8"], {"vendor": vend[3], "invoice_total": f8})
    c.add("R2", "create_entry", ["acct", "invx"], ["ex"], {"amount": amtx, "account": ref("acct"), "invoice": ref("invx")})
    c.add("R2", "create_entry", ["acct", "inv"], ["e0"], {"amount": amt0, "account": ref("acct"), "invoice": ref("inv")})
    c.add("R2", "create_entry", ["acct", "inv7"], ["e7"], {"amount": f7, "account": ref("acct"), "invoice": ref("inv7")})
    c.add("R3", "build_batch", ["e0", "e7"], ["b0"], {"run": "weekly"})
    c.add("R3", "release_batch", ["b0"], [], {"channel": "ach"})
    c.add("R2", "reverse_entry", ["e0" if v == "flip_a" else "ex"], [], {"reason": "vendor credit note"})
    c.add("R1", "create_entry", ["acct", "inv"], ["e"], {"amount": amtE, "account": ref("acct"), "invoice": ref("inv")})
    c.add("R1", "create_entry", ["acct", "inv8"], ["e8"], {"amount": f8, "account": ref("acct"), "invoice": ref("inv8")})
    c.add("R3", "build_batch", ["e", "e8"], ["b"], {"run": "weekly"})
    env = {"request": "finalize_batch", "target": "b", "action": "release_payment"}
    return c, env


def ctl_CX(r, v):
    L = _limit(r)
    a1 = round10(L * r.uniform(0.4, 0.6))
    a2 = round10(L * r.uniform(0.55, 0.7)) if v == "viol" else round10(L * r.uniform(0.1, 0.3))
    vend = r.sample(VENDORS, 2)
    c = Core()
    c.pre("R3", "open_account", [], ["acct"], {"scope": f"cc-{r.randint(10, 99)}", "batch_limit": L})
    c.add("R3", "register_invoice", [], ["inv0"], {"vendor": vend[0], "invoice_total": a1 + 100})
    c.add("R3", "register_invoice", [], ["inv1"], {"vendor": vend[1], "invoice_total": max(a2, 100) + 100})
    c.add("R3", "create_entry", ["acct", "inv0"], ["e1"], {"amount": a1, "account": ref("acct"), "invoice": ref("inv0")})
    c.add("R3", "create_entry", ["acct", "inv1"], ["e2"], {"amount": a2, "account": ref("acct"), "invoice": ref("inv1")})
    c.add("R3", "build_batch", ["e1", "e2"], ["b"], {"run": "weekly"})
    env = {"request": "finalize_batch", "target": "b", "action": "release_payment"}
    return c, env


def distractors_payment(r, n, core_accounts):
    chains, prelude = [], []
    n_acct = r.randint(2, 3)
    accts = []
    for i in range(n_acct):
        a = f"dp_acct{i}"
        accts.append(a)
        prelude.append(Step("W?", "open_account", [], [a], {"scope": f"cc-{r.randint(10, 99)}",
                                                           "batch_limit": _limit(r)}, core=False))
    pool = accts + list(core_accounts)
    for ci in range(n):
        p = f"dp{ci}_"
        kind = r.choice(["paid_batch", "paid_batch", "reversal", "approval", "cancelled"])
        ch = []

        def entry(k):
            amt = round10(r.uniform(300, 4000))
            acct = r.choice(pool)
            ch.append(Step("W?", "register_invoice", [], [p + f"inv{k}"], {"vendor": r.choice(VENDORS),
                                                                          "invoice_total": amt + round10(r.uniform(0, 400))}, core=False))
            ch.append(Step("W?", "create_entry", [acct, p + f"inv{k}"], [p + f"e{k}"],
                           {"amount": amt, "account": ref(acct), "invoice": ref(p + f"inv{k}")}, core=False))
            return p + f"e{k}"

        if kind in ("paid_batch", "cancelled"):
            es = [entry(k) for k in range(r.randint(1, 2))]
            ch.append(Step("W?", "build_batch", es, [p + "b"], {"run": r.choice(["weekly", "adhoc"])}, core=False))
            ch.append(Step("W?", "release_batch" if kind == "paid_batch" else "cancel_batch", [p + "b"], [],
                           {"channel": "ach"}, core=False))
        elif kind == "reversal":
            e = entry(0)
            ch.append(Step("W?", "reverse_entry", [e], [], {"reason": r.choice(["duplicate request", "vendor credit note"])},
                           core=False))
        else:
            es = [entry(k) for k in range(r.randint(1, 2))]
            ch.append(Step("W?", "approve_entries", es, [], {"approver": "controller"}, core=False))
        chains.append(ch)
    return chains, prelude


# ---------------------------------------------------------------------------
# Family registry and split (frozen before any model call)

FAMILIES = {
    # family: (domain, template, split, subset)
    "A1": ("export", tpl_A1, "dev", "prompt_design"),
    "A3": ("export", tpl_A3, "dev", "calibration"),
    "A2": ("export", tpl_A2, "test", "test"),
    "A4": ("export", tpl_A4, "test", "test"),
    "B1": ("training", tpl_B1, "dev", "prompt_design"),
    "B3": ("training", tpl_B3, "dev", "calibration"),
    "B2": ("training", tpl_B2, "test", "test"),
    "B4": ("training", tpl_B4, "test", "test"),
    "C1": ("payment", tpl_C1, "dev", "prompt_design"),
    "C3": ("payment", tpl_C3, "dev", "calibration"),
    "C2": ("payment", tpl_C2, "test", "test"),
    "C4": ("payment", tpl_C4, "test", "test"),
}
CONTROLS = {
    "AX": ("export", ctl_AX, "test", "control"),
    "BX": ("training", ctl_BX, "test", "control"),
    "CX": ("payment", ctl_CX, "test", "control"),
}
# Families whose decisive evidence includes events that are not ancestors of the
# finalization target (sibling consumers of a shared artifact). Declared a priori.
OUT_OF_LINEAGE_FAMILIES = {"C3", "C4"}

DISTRACTORS = {"export": distractors_export, "training": distractors_training}
N_DISTRACTOR_CHAINS = {"export": (20, 32), "training": (16, 26), "payment": (16, 26)}


# ---------------------------------------------------------------------------
# Notes (worker-written prose; variant-independent)

NOTES = {
    "default": ["Routine step for the weekly workflow.", "Completed as requested by the coordinator.",
                "Prepared for the downstream task.", "Done; no issues observed.",
                "Inputs checked and cleared for this use.", "Following the standard procedure."],
}


def draw_note(r: random.Random) -> str:
    opts = NOTES["default"]
    return opts[int(r.random() * len(opts))]


POLICY_REFS = {
    "export": {"register_source": ["P-EXP.1"], "grant_use": ["P-EXP.1"], "revoke_use": ["P-EXP.1"],
               "transform": ["P-EXP.2"], "merge": ["P-EXP.2"], "lookup_join": ["P-EXP.2"],
               "stage_export": ["P-EXP.3"], "profile_dataset": []},
    "training": {"register_corpus": [], "split_corpus": ["P-TRN.1"], "archive_copy": ["P-TRN.2"],
                 "augment": ["P-TRN.2"], "shard": ["P-TRN.2"], "build_cache": ["P-TRN.2"], "mix": ["P-TRN.2"],
                 "dedup_filter": ["P-TRN.2"], "authorize_exception": ["P-TRN.3"],
                 "stage_training_run": ["P-TRN.4"]},
    "payment": {"open_account": ["P-PAY.1"], "register_invoice": ["P-PAY.2"], "create_entry": ["P-PAY.1", "P-PAY.2"],
                "reverse_entry": ["P-PAY.1"], "approve_entries": ["P-PAY.1"], "build_batch": ["P-PAY.3"],
                "release_batch": ["P-PAY.2"], "cancel_batch": ["P-PAY.2"]},
}


# ---------------------------------------------------------------------------
# Scheduling and execution


def schedule(r: random.Random, core: list, chains: list):
    core_start = r.uniform(0.0, 0.35)
    core_end = r.uniform(0.88, 1.0)
    n = len(core)
    ts = sorted(r.uniform(core_start, core_end) for _ in range(n - 1)) + [core_end]
    items = [(t, 0, i, s) for i, (t, s) in enumerate(zip(ts, core))]
    for ci, ch in enumerate(chains):
        a = r.uniform(0.0, 0.8)
        b = r.uniform(min(a + 0.1, 1.0), 1.0)
        cts = sorted(r.uniform(a, b) for _ in ch)
        items += [(t, ci + 1, j, s) for j, (t, s) in enumerate(zip(cts, ch))]
    items.sort(key=lambda x: (x[0], x[1], x[2]))
    return [s for *_, s in items]


def _new_id(r: random.Random, prefix: str, used: set) -> str:
    while True:
        x = f"{prefix}-{r.getrandbits(24):06x}"
        if x not in used:
            used.add(x)
            return x


def _resolve(obj, ids):
    if isinstance(obj, str) and obj.startswith("@"):
        return ids[obj[1:]]
    if isinstance(obj, list):
        return [_resolve(x, ids) for x in obj]
    if isinstance(obj, dict):
        return {k: _resolve(x, ids) for k, x in obj.items()}
    return obj


def build_case(family: str, seed: int, variant: str):
    """Build and execute one trajectory. Returns (observed, world, meta)."""
    reg = FAMILIES.get(family) or CONTROLS[family]
    domain, tpl, split, subset = reg
    key = f"{family}:{seed}"
    core, env = tpl(sub_rng(key, "template"), variant)
    dr = sub_rng(key, "distractors")
    lo, hi = N_DISTRACTOR_CHAINS[domain]
    n_chains = dr.randint(lo, hi)
    if domain == "payment":
        core_accounts = [s.outputs[0] for s in core.prelude if s.tool == "open_account"]
        chains, d_prelude = distractors_payment(dr, n_chains, core_accounts)
    else:
        chains, d_prelude = DISTRACTORS[domain](dr, n_chains)
    sr = sub_rng(key, "schedule")
    body = schedule(sr, core.steps, chains)
    prelude = list(core.prelude) + d_prelude
    sub_rng(key, "prelude").shuffle(prelude)
    steps = prelude + body

    # roles -> worker labels (variant independent)
    perm = ["W1", "W2", "W3"]
    sub_rng(key, "roles").shuffle(perm)
    roles = {"R1": perm[0], "R2": perm[1], "R3": perm[2]}
    wr = sub_rng(key, "workers")
    workers = [roles[s.role] if s.role in roles else f"W{wr.randint(1, 3)}" for s in steps]

    # opaque identifiers allocated in sorted-name order
    names = sorted({n for s in steps for n in s.inputs + s.outputs})
    ir = sub_rng(key, "ids")
    used: set = set()
    ids = {n: _new_id(ir, "a", used) for n in names}
    event_ids = [_new_id(ir, "e", used) for _ in steps]
    run_id = "run-" + hashlib.sha256(f"{key}|{variant}|run".encode()).hexdigest()[:10]

    world = WORLDS[domain]()
    nr = sub_rng(key, "notes")
    events = []
    core_flags = []
    for k, s in enumerate(steps):
        inputs = [ids[n] for n in s.inputs]
        outputs = [ids[n] for n in s.outputs]
        args = _resolve(s.args, ids)
        world.apply(s.tool, args, inputs, outputs, s.outcome)
        events.append({
            "run_id": run_id,
            "event_id": event_ids[k],
            "worker_id": workers[k],
            "sequence": k + 1,
            "tool": s.tool,
            "arguments": args,
            "input_artifact_ids": inputs,
            "output_artifact_ids": outputs,
            "artifact_versions": {o: 1 for o in outputs},
            "policy_refs": list(POLICY_REFS[domain].get(s.tool, [])),
            "outcome": s.outcome,
            "rationale": draw_note(nr),
        })
        core_flags.append(s.core)
    envelope = {k: (ids[v] if k == "target" else v) for k, v in env.items()}
    envelope = {"request": envelope.pop("request"), "target_artifact_id": envelope.pop("target"),
                **envelope, "requested_by": roles["R3"]}
    observed = {"run_id": run_id, "domain": domain, "envelope": envelope, "events": events}
    meta = {"family": family, "seed": seed, "variant": variant, "split": split, "subset": subset,
            "domain": domain, "control": family in CONTROLS, "base_case_id": key,
            "template_id": family, "template_family_id": family,
            "core_event_ids": [e["event_id"] for e, f in zip(events, core_flags) if f],
            "roles": roles, "n_steps_tools": [s.tool for s in steps]}
    return observed, world, meta
