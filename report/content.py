"""Report text. Every result number is read from results/analysis/summary.json through N (audited)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q = "models/qwen3.5-397b"
G = "models/gemma-4-31b-it"
REPO = "https://github.com/DaniyalMughal1/swarm-evidence"


def sg(x, nd=2):
    return ("+" if x >= 0 else "−") + f"{abs(x):.{nd}f}"


def ci(N, path, nd=2):
    lo = N.get(path + "/0")
    hi = N.get(path + "/1")
    return f"[{lo:.{nd}f}, {hi:.{nd}f}]".replace("-", "−")


def authors():
    p = ROOT / "report/authors.json"
    if p.exists():
        return [tuple(a) for a in json.loads(p.read_text())]
    return [("[AUTHOR NAME TO CONFIRM]", "[AFFILIATION TO CONFIRM]")]


TITLE = "Swarm Evidence: Dependency-Based Evidence Selection for Monitoring Cross-Agent Policy Violations Under a Fixed Context Budget"


def front_matter(N):
    dl = f"{Q}/contrasts/dependency-lexical@2000"
    fa = f"{Q}/arms/full@nocap"
    abstract = (
        "When several AI agents each take locally permitted steps, a policy violation can exist only in their "
        "composition, and a monitor with a limited context budget must choose which logged events to read. We test "
        "whether selecting evidence by walking recorded artifact dependencies backward from the action under review "
        "improves detection over ordinary retrieval and log review at the same budget. We built an executable "
        "three-worker simulator with labels computed from executed state: "
        f"{N.i('dataset/n_core_pairs')} matched violating/legitimate pairs from 12 template families in three "
        "domains, a validity gate requiring evidence from at least two workers, and a pre-registered held-out set "
        f"of {N.i('dataset/test_core_trajectories')} trajectories from 6 unseen families. At a 2,000-token cap, "
        f"dependency selection kept {N.pct(Q + '/arms/dependency@2000/gold_recall')} of the minimal decisive "
        f"evidence versus {N.pct(Q + '/arms/lexical@2000/gold_recall')} for lexical retrieval. With Qwen 3.5 397B "
        f"as monitor, held-out AUROC was {N.f(Q + '/arms/dependency@2000/auroc')} versus "
        f"{N.f(Q + '/arms/lexical@2000/auroc')} (difference {sg(N.get(dl + '/diff'))}; family-bootstrap 95% "
        f"interval {ci(N, dl + '/ci95_family_bootstrap')}). Reading the whole log without a cap scored "
        f"{N.f(fa + '/auroc')}, with most false alarms citing unrelated legitimate work. On the dependency-selected "
        f"evidence, a deterministic checker reached {N.f('offline_test/dependency@2000@full/rule_auroc')}, while "
        "the language model misapplied stated role rules and flagged legitimate join and deduplication references. "
        "Dependency selection failed by design when decisive evidence was not an ancestor of the target, and "
        "degraded when dependency metadata was removed. Lineage-guided selection is a cheap retrieval and filtering "
        "step; in our setting, the monitor's judgment limited detection more than its context did."
    )
    return {"title": TITLE, "authors": authors(), "abstract": abstract}


def body(N):
    b = []
    dl = f"{Q}/contrasts/dependency-lexical@2000"
    dep2, lex2 = f"{Q}/arms/dependency@2000", f"{Q}/arms/lexical@2000"
    b += [
        ("h2", "1. Introduction"),
        ("p", "Multi-agent deployments split work across workers that share artifacts. A violation can then be "
              "*composed*: one worker registers a dataset whose license forbids external sharing, a second "
              "transforms and merges it, and a third stages the merged artifact for export. Each step can be "
              "locally permitted. A monitor that reviews each worker separately cannot see the problem, and a "
              "monitor that reads every event pays for a log that grows with every unrelated task. Practical "
              "oversight therefore works under a context budget and has to decide which evidence to read."),
        ("p", "We ask a narrow question: **with a fixed monitoring context budget, does selecting evidence by walking "
              "recorded artifact dependencies backward from the action under review improve detection of "
              "distributed policy violations, compared with ordinary retrieval and log review?** Kitaoka's talk at "
              "this event motivated corroborating relevant actions across agents under explicit token budgets "
              "[10]; we turn that suggestion into a controlled measurement. The setting is deliberately "
              "restricted: a known, centrally instrumented three-worker workflow with a trusted event recorder and "
              "a common finalization point. We do not study unknown swarms, spontaneous collusion or tampered logs."),
        ("p", "Our main contributions are:"),
        ("bullets", [
            "**An executable benchmark with state-based labels.** Twelve template families in three domains "
            f"({N.i('dataset/n_core_pairs')} matched violating/legitimate pairs plus "
            f"{N.i('dataset/n_control_pairs')} single-worker controls), labels computed from executed hidden state, "
            "a composition-validity gate, held-out template families, and audited removal of dependency metadata.",
            "**A pre-registered, budget-matched comparison** of seven evidence-selection policies, scored by an LLM "
            "monitor (replicated with a second model family) and by a deterministic rule monitor on exactly the "
            "same selected evidence, which separates retrieval from judgment.",
            "**A measured failure boundary.** Dependency selection retains nearly all decisive evidence at a small "
            "cap, but the LLM converts it unevenly; it misses evidence outside the target's lineage by "
            "construction, and it degrades faster than lexical retrieval when dependency metadata is missing.",
        ], {"numbered": True}),
        ("h2", "2. Related Work"),
        ("p", "**Control and multi-agent monitoring.** AI Control evaluates protocols that keep untrusted models "
              "useful while limiting harm, with trusted monitors as one component [1]; we study one input to such a "
              "monitor and do not claim prevention. Multi-Agent AI Control reports a fragmentation effect: the more agents "
              "share an attack, the less per-agent monitors detect it [3]. That per-instance review misses "
              "distributed attacks is therefore known; our question is which evidence a joint monitor should read "
              "when its context is capped. Hammond et al. "
              "survey multi-agent risks including collusion [7], and Jones et al. show that combinations of "
              "individually safe models can be misused [6], which motivates composed violations."),
        ("p", "**Lineage and graphs.** Zhang et al. evaluate composed multi-agent information flows with "
              "authorization-paired tests and propose FlowReview, which reviews composed artifacts with "
              "deterministic enforcement; they argue that retaining information and lineage alone does not "
              "guarantee correct permission attribution [2]. GroupGuard defends against group collusive attacks "
              "with graph-based monitoring, honeypot inducement and structural pruning [4], and Rose et al. detect "
              "collusion from activation probes on their NARCBench benchmark [5]. Agent logging and provenance infrastructure is an "
              "active area [8, 9]. We do not propose an enforcement architecture, an interaction-suspicion graph or "
              "white-box detection. Our increment is a controlled measurement of *context-budgeted evidence "
              "selection* over recorded artifact lineage against non-graph retrieval baselines (lexical, BM25 [11] "
              "and pseudo-relevance feedback [12]), with a deterministic monitor run on the same selections to "
              "separate retrieval quality from judgment. A targeted search found no study isolating this effect; "
              "that is not proof of priority."),
        ("h2", "3. Methods"),
        ("h3", "3.1 Setting, data and labels"),
        ("p", "Three workers (W1 to W3) call structured tools in a deterministic local simulator. A trusted harness "
              "records each call: event and artifact IDs (opaque random strings), worker, sequence, tool, arguments, "
              "inputs, outputs, versions, policy references, outcome and a worker-written note (untrusted, "
              "identical across twins). Each trajectory ends with a finalization request (target artifact, proposed "
              "use) that occurs in both twins, so the trigger never reveals the violating step. Violations are "
              "scripted, not emergent. The attacker controls actions and notes but not the ledger. The monitor sees "
              "only the public policy, the request and the selected events: no labels, gold evidence or hidden state."),
        ("p", "**Export permissions** (A1 to A4): a restricted source wired into an export; a revocation that does or "
              "does not reach the export; deep fan-in; a lookup join where a restricted input is legitimate as "
              "*reference* but not as *primary* input. **Training contamination** (B1 to B4): held-out records "
              "reaching training through augmentation; a deduplication filter using the held-out split as reference "
              "(legitimate) or primary input; a purpose-specific exception; a two-hop shard cache. **Payment "
              "batches** (C1 to C4): reversals; account scopes; and two families where an earlier released batch "
              "already paid the same invoice. In C3 and C4 that decisive payment shares an ancestor with the target "
              "but is not one of its ancestors; we declared them *out-of-lineage* before any model call."),
        ("p", "Each family has 5 seeds. Every trajectory interleaves 16 to 32 chains of unrelated legitimate work "
              "(restricted data used internally, held-out archives, gateway-rejected attempts, other paid batches), "
              f"so held-out traces have {N.i('dataset/min_events_test')} to {N.i('dataset/max_events_test')} events "
              f"(mean {N.f('dataset/mean_events_test', 0)}; about 6,000 to 11,000 tokens) with evidence spread "
              "through the log. An oracle labels each trajectory from hidden state only (record-level provenance, "
              "permissions at finalization, held-out membership, paid amounts). Twins share every event ID, tool, "
              "worker and the request, and differ only in wiring, an authorization or an amount. A **validity gate** "
              "requires, per base case: opposite labels; identical twin structure; agreement between the oracle and "
              "a deterministic rule monitor reading the full ledger; a second legitimate completion that changes a "
              "*different* worker, so every single-worker view of the violation is shared by a legitimate trajectory; "
              "and a 1-minimal gold evidence set spanning at least two workers. "
              f"{N.i('dataset/gate_passed')} of {N.i('dataset/n_base_cases')} base cases pass. The family split was "
              "fixed before any model call: development A1, A3, B1, B3, C1, C3 (prompt design A1/B1/C1, threshold "
              "calibration A3/B3/C3); held out A2, A4, B2, B4, C2, C4."),
        ("h3", "3.2 Evidence selection under a cap"),
        ("p", "All methods use identical compact JSON rendering in chronological order, include only complete "
              "events, and count the fixed overhead (instructions, policy, request) against the cap. "
              "**Chronological** keeps the newest events. **Lexical** ranks by 4\u00d7[contains target ID] plus the "
              "number of distinct query tokens shared with the policy and request. **BM25** [11] and **Lexical+PRF** "
              "(one round of pseudo-relevance feedback adding all tokens, including artifact IDs, of the top three "
              "events [12]) are stronger non-graph baselines added on development data before the freeze. "
              "**Dependency** runs a backward breadth-first traversal from the target over producer-to-consumer "
              "relations; output-less events that reference a reached artifact (licenses, revocations, reversals, "
              "exceptions) attach at its distance; ties go to recency; spare budget stays unused. **Shuffled graph** "
              "traverses a node-relabelled copy of the graph, selecting as many events without real structure. "
              "**Isolated** makes one call per worker with a third of the cap each and takes the maximum score; at "
              "2,000 tokens its repeated overhead alone exceeds that share, so it shows no events (we kept this frozen "
              "accounting). **Full log** (no cap) is a diagnostic ceiling. Caps are 2,000 and 6,000 tokens, "
              "estimated at 2.5 bytes per token after a development pilot at 3.0 overran by up to 11%."),
        ("h3", "3.3 Monitors and protocol"),
        ("p", "The primary monitor is qwen3.5-397b on Adaption hosted inference (temperature 0, reasoning disabled so "
              "the 384-token output cap, 128 per isolated call, covers every generated token). It returns JSON with a "
              "one-sentence reason, cited event IDs, a verdict (violation, benign, insufficient_evidence) and a "
              "suspicion score. Parsing is strict; only first attempts count; invalid outputs score 0.5 and count as "
              "abstentions. gemma-4-31b-it with the same prompt is the second model family. The **rule monitor** is "
              "a deterministic program that knows the policy's record-carrying rules: violation if the shown events "
              "contain a witness, benign if the target's backward lineage is complete without one, else unknown "
              "(optimistic about unseen events). Three prompt iterations on the 12 prompt-design trajectories fixed "
              "truncated outputs and verdicts written before the reason (Appendix B)."),
        ("p", "The protocol was committed before any calibration or held-out call (prompt hash 0fade4df). **Primary "
              "contrast:** AUROC(dependency) minus AUROC(lexical) at 2,000 tokens with full visibility on the 60 "
              "held-out trajectories, with a paired percentile bootstrap over whole template families (6 clusters, "
              "10,000 draws). With six families the interval is descriptive, not a population test. Secondary: other "
              "arms, the 6,000-token cap, missing metadata, the second model, the rule monitor and the controls. "
              "Missing metadata masks random producer-to-consumer relations (25% or 50%) or every cross-worker "
              "bridge, replacing the artifact ID wherever it appears in the consuming event with a unique "
              "placeholder; an audit confirms no ID join recovers it, and all methods see the same masked view."),
    ]
    # ---------------- Results
    def cia(a):
        lo, hi = N.get(a + "/auroc_ci_family/0"), N.get(a + "/auroc_ci_family/1")
        return f"{N.f(a + '/auroc')} ({lo:.2f}\u2013{hi:.2f})"

    rows = []
    for arm, label in [("dependency", "Dependency"), ("lexical", "Lexical"), ("chronological", "Chronological"),
                       ("bm25", "BM25"), ("lexical_prf", "Lexical+PRF"), ("shuffled", "Shuffled graph"),
                       ("isolated", "Isolated (3 calls)")]:
        a2, a6 = f"{Q}/arms/{arm}@2000", f"{Q}/arms/{arm}@6000"
        rows.append([label, cia(a2), f"{N.i(a2 + '/verdict_violation_tp')}/{N.i(a2 + '/verdict_violation_fp')}",
                     N.i(a2 + "/abstain_valid"), N.f(a2 + "/gold_recall"), f"{N.get(a2 + '/mean_input_tokens'):.0f}",
                     N.f(f"offline_test/{arm}@2000@full/rule_auroc"),
                     cia(a6), f"{N.i(a6 + '/verdict_violation_tp')}/{N.i(a6 + '/verdict_violation_fp')}",
                     N.f(a6 + "/gold_recall"), N.f(f"offline_test/{arm}@6000@full/rule_auroc")])
    fa = f"{Q}/arms/full@nocap"
    rows.append(["Full log (no cap)", cia(fa), f"{N.i(fa + '/verdict_violation_tp')}/{N.i(fa + '/verdict_violation_fp')}",
                 N.i(fa + "/abstain_valid"), N.f(fa + "/gold_recall"), f"{N.get(fa + '/mean_input_tokens'):.0f}",
                 "1.00", "", "", "", ""])
    overruns = sum(N.get(f"{Q}/arms/{arm}@{cap}/cap_overruns") for arm in
                   ("dependency", "lexical", "chronological", "bm25", "lexical_prf", "shuffled", "isolated")
                   for cap in (2000, 6000))
    invalid = sum(N.get(f"{Q}/arms/{arm}@{cap}/invalid") for arm in
                  ("dependency", "lexical", "chronological", "bm25", "lexical_prf", "shuffled", "isolated")
                  for cap in (2000, 6000)) + N.get(fa + "/invalid")

    b += [
        ("h2", "4. Results"),
        ("fig", "figures/fig1_example.png", 6.3,
         "**Figure 1.** A development violating trajectory (family A1, synthetic data). Each dot is a recorded "
         "event in a worker's lane; black dots are the gold minimal evidence (restricted license by W3, two "
         "transforms by W1, the merge and staged export by W2) and arrows are recorded lineage. Ticks show what "
         "each selector keeps at the 2,000-token cap. Dependency selection reaches the old license event; lexical "
         "retrieval fills the budget with policy-word matches from unrelated work; chronological review sees only "
         "the tail."),
        ("h3", "4.1 Primary comparison"),
        ("p", f"At the 2,000-token cap, dependency selection kept {N.pct(dep2 + '/gold_recall')} of gold evidence "
              f"while using {N.get(dep2 + '/mean_input_tokens'):.0f} billed input tokens on average, against "
              f"{N.pct(lex2 + '/gold_recall')} for lexical retrieval at {N.get(lex2 + '/mean_input_tokens'):.0f} "
              f"tokens. The LLM's held-out AUROC was {N.f(dep2 + '/auroc')} with dependency selection and "
              f"{N.f(lex2 + '/auroc')} with lexical retrieval: a paired difference of {sg(N.get(dl + '/diff'))} with "
              f"family-bootstrap 95% interval {ci(N, dl + '/ci95_family_bootstrap')}. "
              f"{N.i(dl + '/families_positive')} of 6 held-out families favored dependency and "
              f"{N.i(dl + '/families_negative')} favored lexical. **The pre-registered primary contrast is therefore "
              "positive in point estimate but not resolved at the family level.** The behaviour behind the AUROCs "
              f"differs sharply. With lexical evidence the model abstained on {N.i(lex2 + '/abstain_valid')} of 60 "
              "trajectories, correctly reporting that the lineage was not visible. With dependency evidence it "
              f"issued {N.i(dep2 + '/verdict_violation_tp')} correct violation verdicts out of 30 violations, but also "
              f"{N.i(dep2 + '/verdict_violation_fp')} false violation verdicts on the 30 legitimate twins. At the "
              f"threshold frozen on calibration families ({N.f(dep2 + '/threshold_frozen')}), the dependency arm "
              f"flagged {N.i(dep2 + '/tpr_frozen/k')}/30 violations and {N.i(dep2 + '/fpr_frozen/k')}/30 legitimate "
              f"runs (false-positive rate 95% Wilson interval {N.f(dep2 + '/fpr_frozen/wilson/0')}–"
              f"{N.f(dep2 + '/fpr_frozen/wilson/1')}); the lexical arm flagged {N.i(lex2 + '/tpr_frozen/k')}/30 and "
              f"{N.i(lex2 + '/fpr_frozen/k')}/30. Across "
              f"all budgeted held-out calls, {overruns} exceeded their cap and {invalid} outputs were invalid."),
        ("p", "**More context was worse.** Reading the whole log without a cap (mean "
              f"{N.get(fa + '/mean_input_tokens'):.0f} billed input tokens, "
              f"{N.get(fa + '/mean_input_tokens') / N.get(dep2 + '/mean_input_tokens'):.1f}× the dependency arm) "
              f"gave AUROC {N.f(fa + '/auroc')}: the model flagged {N.i(fa + '/verdict_violation_fp')} of 30 "
              "legitimate twins, and in "
              f"{N.i(fa + '/fp_citing_unrelated_work')} of those {N.i(fa + '/fp_total')} false alarms it cited events "
              "from unrelated legitimate work, such as another account's entries or another source's revocation. "
              f"Of the dependency arm's {N.i(dep2 + '/fp_total')} false alarms, "
              f"{N.i(dep2 + '/fp_citing_unrelated_work')} cited unrelated work. The paired "
              f"dependency-minus-full difference was {sg(N.get(Q + '/contrasts/dependency-full@nocap/diff'))} "
              f"{ci(N, Q + '/contrasts/dependency-full@nocap/ci95_family_bootstrap')}. Selection therefore helped "
              "twice: it fit the budget, and it removed distracting look-alike evidence."),
        ("table",
         ["Method", "AUROC 2k (95% CI)", "TP/FP", "Abst.", "Recall", "Tokens", "Rule",
          "AUROC 6k (95% CI)", "TP/FP", "Recall", "Rule"],
         rows,
         "**Table 1.** Held-out results for the primary monitor (qwen3.5-397b): 60 trajectories (30 violating, 30 "
         "legitimate) from 6 unseen families, at 2,000- and 6,000-token caps. AUROC intervals resample families. "
         "TP/FP: violation verdicts on violating/legitimate trajectories. Abst.: valid insufficient-evidence "
         "verdicts. Recall: share of gold minimal evidence shown. Tokens: mean provider-billed input tokens. Rule: "
         "AUROC of the deterministic rule monitor on the same selected evidence (model-independent; 1.00 on the full "
         "log by the validity gate).",
         {"size": 7, "col_widths": [0.95, 0.95, 0.4, 0.38, 0.45, 0.45, 0.38, 0.95, 0.4, 0.45, 0.38]}),
        ("fig", "figures/fig2_auroc_by_method.png", 6.5,
         "**Figure 2.** Held-out AUROC by selection method at two input caps (LLM monitor qwen3.5-397b; error bars: "
         "95% family-bootstrap intervals over 6 held-out families; dashed line: chance; grey line: full log with "
         "no cap). Isolated review spends its budget on three copies of the overhead and sees almost nothing at "
         "2,000 tokens."),
    ]
    # per-family table
    fams = [("A2", "revocation"), ("A4", "join reference vs primary"), ("B2", "dedup reference vs primary"),
            ("B4", "two-hop shard cache"), ("C2", "account scope"), ("C4", "earlier payment (out-of-lineage)")]
    fam_rows = []
    for f, mech in fams:
        vb = N.get(f"{Q}/verdicts_by_family/dependency@2000/{f}")
        legit_flag = vb.get("legit->violation", 0)
        viol_miss = vb.get("viol->benign", 0) + vb.get("viol->insufficient_evidence", 0)
        fam_rows.append([f, mech, N.f(f"{Q}/per_family/dependency@2000/{f}"),
                         N.f(f"offline_test_per_family/dependency@2000@full|{f}/rule_auroc"),
                         N.f(f"offline_test_per_family/dependency@2000@full|{f}/gold_recall"),
                         f"{legit_flag}/5", f"{viol_miss}/5", N.f(f"{Q}/per_family/lexical@2000/{f}")])
    oo = f"{Q}/out_of_lineage"
    b += [
        ("h3", "4.2 Same evidence, different judgments"),
        ("p", "The rule monitor scored "
              f"{N.f('offline_test/dependency@2000@full/rule_auroc')} on the dependency selections that gave the LLM "
              f"{N.f(dep2 + '/auroc')}, with zero false positives (Table 2). The LLM's errors concentrate in two "
              "families whose legitimate twins hinge on a policy clause about roles: a lookup join's *reference* "
              "input and a deduplication filter's *reference* input do not carry records (A4, B2). The model's "
              "stated reasons cite the restricted or held-out source as reaching the target, which the policy text "
              "explicitly rules out. In these families retrieval succeeded and judgment failed. Families decided "
              "by plain lineage (A2, C2) were perfect for both monitors."),
        ("table", ["Family", "Mechanism", "Dep. LLM AUROC", "Dep. rule AUROC", "Dep. recall",
                   "Legit flagged", "Viol. missed", "Lex. LLM AUROC"], fam_rows,
         "**Table 2.** Per-family held-out results at the 2,000-token cap (5 pairs per family). Legit flagged: "
         "legitimate twins given a violation verdict by the LLM with dependency evidence. Viol. missed: violating "
         "trajectories judged benign or abstained. Rule AUROC and recall are model-independent.",
         {"size": 7, "col_widths": [0.45, 1.55, 0.7, 0.7, 0.6, 0.65, 0.65, 0.7]}),
        ("p", "**Out-of-lineage boundary (pre-registered H2).** In C4 the decisive evidence is an earlier released "
              "batch that paid part of the same invoice; it shares an ancestor with the target but is not one of "
              "its ancestors. Dependency selection never retrieved it. The LLM judged all "
              f"{N.i(oo + '/dependency|C4_out_of_lineage/violations_total')} C4 violations benign (AUROC "
              f"{N.f(oo + '/dependency|C4_out_of_lineage/auroc')}), and so did the optimistic rule monitor. On the five "
              "in-lineage held-out families, the LLM with dependency evidence reached AUROC "
              f"{N.f(oo + '/dependency|other_test_families/auroc')}. Backward lineage misses constraints that "
              "aggregate over sibling consumers, such as invoice totals, budgets and rate limits."),
    ]
    dl6 = f"{Q}/contrasts/dependency-lexical@6000"
    v = f"{Q}/visibility"
    b += [
        ("h3", "4.3 Larger budgets and missing metadata"),
        ("p", f"At the 6,000-token cap the non-graph baselines retain more evidence (lexical recall "
              f"{N.f(Q + '/arms/lexical@6000/gold_recall')}) but rarely all of it, while dependency selection is "
              f"unchanged because it never pads (Figure 3a). The dependency-minus-lexical AUROC difference was "
              f"{sg(N.get(dl6 + '/diff'))} {ci(N, dl6 + '/ci95_family_bootstrap')} at 6,000 tokens "
              f"(pre-registered H3 predicted shrinkage)."),
        ("p", "Removing dependency metadata hurts dependency selection and leaves lexical retrieval untouched "
              f"(Figure 3b). With 25% of relations masked, dependency recall at 2,000 tokens fell from "
              f"{N.f(v + '/dependency@2000@full/gold_recall')} to {N.f(v + '/dependency@2000@random25/gold_recall')} "
              f"and AUROC from {N.f(v + '/dependency@2000@full/auroc')} to "
              f"{N.f(v + '/dependency@2000@random25/auroc')}. At 50% masking recall fell to "
              f"{N.f(v + '/dependency@2000@random50/gold_recall')}, and masking cross-worker bridges, which removes "
              "about half of all relations in these tree-like graphs, gave "
              f"{N.f(v + '/dependency@2000@bridges/gold_recall')}. At 6,000 tokens with 50% masking, lexical "
              f"retrieval kept more decisive evidence ({N.f(v + '/lexical@6000@random50/gold_recall')}) than "
              f"dependency selection ({N.f(v + '/dependency@6000@random50/gold_recall')}). The conditions are not "
              "equally severe, and the masked placeholders tell the monitor that a link is missing."),
        ("fig", "figures/fig3_budget_and_metadata.png", 6.5,
         "**Figure 3.** (a) Model-independent share of gold minimal evidence that each selector keeps on the 60 "
         "held-out trajectories as the input cap grows. (b) LLM AUROC for dependency and lexical selection when "
         "dependency relations are masked at random (25%, 50%) or at every cross-worker bridge, at both caps."),
    ]
    # secondary model + controls + cost
    g_dep, g_lex = f"{G}/arms/dependency@2000", f"{G}/arms/lexical@2000"
    gdl = f"{G}/contrasts/dependency-lexical@2000"
    b += [
        ("h3", "4.4 Second model, controls and cost"),
        ("p", f"With gemma-4-31b-it the pattern repeated: dependency AUROC {N.f(g_dep + '/auroc')} versus lexical "
              f"{N.f(g_lex + '/auroc')} at 2,000 tokens (difference {sg(N.get(gdl + '/diff'))}, interval "
              f"{ci(N, gdl + '/ci95_family_bootstrap')}), with {N.i(g_dep + '/verdict_violation_fp')} false "
              f"violation verdicts and {N.i(g_dep + '/invalid') } invalid outputs for the dependency arm and "
              f"{N.i(g_lex + '/invalid')} invalid lexical-arm outputs (repetition loops at temperature 0). "
              "On the 9 single-worker control pairs, where one worker's events decide the label, "
              f"dependency selection gave AUROC {N.f(Q + '/controls/dependency/auroc')} and isolated review "
              f"{N.f(Q + '/controls/isolated/auroc')}. All model calls, including pilots and the second model, cost "
              f"{N.f('costs/total_credits', 2)} Adaption credits over {N.i('costs/n_calls_total')} recorded calls. "
              "Cost was never the binding constraint; the per-user rate limit was. Exploratory checks after the "
              "freeze (reasoning-enabled monitor, a temperature-0 repeat, and a live slice with model-driven "
              "workers) are reported in Appendix C."),
    ]
    # ---------------- Discussion
    b += [
        ("h2", "5. Discussion and Limitations"),
        ("p", "**What the results mean.** Under a tight budget, following recorded lineage is a cheap and strong "
              "retrieval step. It keeps almost all decisive evidence at a fraction of the tokens a full review "
              "costs, and non-graph retrieval cannot match it at small caps because the relevant events look like "
              "routine work. Better context did not translate into proportionally better detection, however. On the "
              "same evidence, a short deterministic checker made no false alarms, while the LLM monitor with "
              "reasoning disabled raised false alarms on every legitimate twin in the two role-dependent "
              "families. The checker encoded the policy's record-carrying rules; the model often did not apply them. For oversight design, this means the "
              "selection gain is real only if the downstream judge can use structured evidence. Where the policy "
              "is explicit, a deterministic check over the selected lineage can do the deciding, and an LLM is best "
              "reserved for semantics the schema cannot express. Lineage selection also has a predictable blind "
              "spot: aggregate constraints over sibling consumers, and degradation when dependency metadata is "
              "missing. A deployed monitor would need a fallback, such as lexical retrieval or sibling expansion, "
              "for exactly those cases."),
        ("h3", "Limitations"),
        ("bullets", [
            "Synthetic, scripted workflows with three known workers, a trusted complete recorder and a common "
            "finalization point. Results do not transfer to unknown swarms, tampered logs or emergent collusion.",
            "Six held-out template families (30 pairs) give wide intervals; seeds within a family are not "
            "independent mechanisms. The primary contrast is not resolved at the family level.",
            "Balanced labels do not reflect real prevalence; thresholds from 15 calibration benign cases cannot "
            "certify low false-positive rates.",
            "The rule monitor was written by the benchmark authors with knowledge of the tool semantics, and its "
            "benign verdicts are optimistic about unseen events. It shows what structured evidence permits, not "
            "a deployable detector.",
            "Monitor results cover two hosted models at temperature 0 with reasoning disabled; a reasoning model or "
            "a better prompt might close the judgment gap. Token caps are estimates (billed tokens stayed below "
            "them).",
            "The live-agent validation slice was not run: all trajectories are replayed scripts.",
        ]),
        ("h3", "Future Work"),
        ("p", "Natural next steps are: sibling-consumer expansion for aggregate constraints; hybrid monitors that "
              "send the lineage to a checker and the remainder to an LLM; reasoning-enabled monitors with full "
              "token accounting; logs from live model-driven workers; more template families for tighter "
              "intervals; and adversaries who attack the recorder or launder lineage through untracked channels."),
        ("h2", "6. Conclusion"),
        ("p", "At a fixed context budget, selecting evidence through recorded artifact dependencies retained "
              f"{N.pct(dep2 + '/gold_recall')} of decisive cross-agent evidence where lexical retrieval retained "
              f"{N.pct(lex2 + '/gold_recall')}. It raised an LLM monitor's held-out AUROC from {N.f(lex2 + '/auroc')} "
              f"to {N.f(dep2 + '/auroc')}, though with family-level uncertainty that includes no effect. The "
              "limiting factor was the monitor's judgment: a deterministic checker on the same evidence reached "
              f"{N.f('offline_test/dependency@2000@full/rule_auroc')}. Lineage selection fails predictably on "
              "out-of-lineage constraints and missing metadata. We release the benchmark, protocol and every run "
              "record so these boundaries can be tested further."),
        ("h2", "Code and Data"),
        ("bullets", [
            f"Code repository: {REPO} (MIT). Reproduce with `python -m swarm_evidence generate`, `validate`, "
            "`offline --split test`, then `analyze` (model calls are opt-in: `run --stage ...`).",
            "Data: versioned synthetic trajectories, labels, validity gate, frozen protocol "
            "(protocol/PROTOCOL_FREEZE.json) and every model call with prompts' hashes, parsed outputs, billed "
            "tokens and cost (results/calls/). No real or personal data.",
        ]),
        ("h2", "Author Contributions"),
        ("p", author_contributions()),
        ("h2", "References"),
        ("refs",),
    ]
    b = [x for x in b if x != ("refs",)] + [("p", r, {"size": 8.5, "space_after": 2}) for r in references()]
    b += appendix(N)
    return b


def author_contributions():
    p = ROOT / "report/author_contributions.txt"
    return p.read_text().strip() if p.exists() else "[AUTHOR CONTRIBUTIONS TO CONFIRM]"


def references():
    p = ROOT / "report/references.json"
    if p.exists():
        return json.loads(p.read_text())
    return ["[REFERENCES PENDING VERIFICATION]"]


def appendix(N):
    from swarm_evidence.prompts import INSTRUCTIONS, POLICIES
    a = []
    a += [
        ("h2", "Appendix A. Limitations and Dual-Use / Ethical Considerations"),
        ("h3", "Scope and uncertainty"),
        ("p", "This study uses synthetic, centrally instrumented workflows with a trusted event recorder and a "
              "known finalization point. It does not establish identification of unknown colluding subgroups, "
              "resistance to recorder compromise, detection of covert channels outside the ledger, spontaneous "
              "collective agency, or safety in deployed agent populations. Seeds of one template are not "
              "independent evidence, and six held-out families support only descriptive intervals. Balanced "
              "labels do not reflect operational prevalence. An abstention is not evidence of safety: lexical and "
              "chronological arms often abstained, which would block or escalate legitimate work in deployment. "
              "Retrospective detection before finalization does not show that an online intervention would "
              "prevent harm without disrupting legitimate tasks. Results depend on two hosted models on one date "
              "with reasoning disabled. If the recorder were incomplete or adversarial, dependency selection would "
              "degrade at least as much as our masking experiments show, and possibly worse, because an attacker "
              "could cut the specific links that matter."),
        ("h3", "Dual use and release"),
        ("p", "Distributed-violation templates and monitor failure analyses could help someone choose actions that "
              "a lineage-based monitor will not retrieve. In particular, the out-of-lineage result indicates that "
              "aggregate constraints over sibling actions are a weak point. We judge the defensive value higher: "
              "the weakness follows directly from how backward traversal works, the templates use only fake "
              "records, local simulated tools and mocked destinations, and nothing here is an executable payload "
              "against a real service. We release original synthetic data, code, prompts and sanitized model "
              "outputs only; no credentials, personal data, third-party logs or recordings are included. The "
              "Adaption API key was stored locally and never written to the repository or logs. The work is "
              "intended to improve oversight by stating where a plausible monitoring design fails."),
        ("h2", "Appendix B. Reproduction details"),
        ("p", "**Monitor instructions (verbatim, prompt v3):** " + INSTRUCTIONS.replace("\n", " "), {"size": 8}),
        ("p", "**Export policy shown to monitors:** " + POLICIES["export"].replace("\n", " "), {"size": 8}),
        ("p", "**Development history (all before the freeze, prompt-design trajectories only).** Pilot v1 (84 "
              "calls): four outputs truncated at 384 tokens by long arithmetic, and the 3.0 bytes/token estimator "
              "overran the 2,000 cap on 16 calls by up to 11%. Pilot v2: a one-sentence reason and 2.5 bytes/token; "
              "no overruns, but on two legitimate payment cases the model wrote the verdict before the reason and "
              "contradicted its own arithmetic. Pilot v3: reason first (36 calls). Lexical retrieval was weaker "
              "than chronological review on development recall, so BM25 and Lexical+PRF were added before the "
              "freeze; lexical stayed the pre-registered primary comparator. Traces were lengthened before the "
              "freeze so that both caps bind on every trace. After the freeze we found that the provider's rate "
              "limit is shared across models, so we stopped a concurrent second-model chain after 3 calls "
              "(reserving their possible cost) and ran the models sequentially. No other deviation."),
        ("p", f"**Cost and calls.** Total {N.f('costs/total_credits', 3)} credits over "
              f"{N.i('costs/n_calls_total')} recorded calls, including pilots, the second model and transport-error "
              "reservations. The runner enforces a cumulative 800-credit ceiling with per-stage caps, reserves "
              "each call's worst-case cost before sending it, and checkpoints every response; per-stage counts and "
              "costs are in results/analysis/summary.json."),
        *appendix_c(N),
        ("h2", "LLM Usage Statement"),
        ("p", llm_statement()),
    ]
    return a


def llm_statement():
    p = ROOT / "report/llm_statement.txt"
    return p.read_text().strip() if p.exists() else "[LLM USAGE STATEMENT TO CONFIRM]"


def appendix_c(N):
    R = "models/qwen3.5-397b+reasoning"
    L = "live_exploratory"
    rep = "replicates/qwen3.5-397b|dependency|2000"
    rep_l = "replicates/qwen3.5-397b|lexical|2000"
    out = [("h2", "Appendix C. Exploratory checks (after the freeze)")]
    out.append(("p", "These runs were added after seeing stage-1 results and are not part of the pre-registered "
                     "analysis (protocol/POST_FREEZE_CHANGES.md)."))
    out.append(("p", "**Reasoning-enabled monitor.** With Qwen's reasoning on (effort medium, 4,096-token output cap "
                     "including billed reasoning), held-out AUROC at the 2,000-token cap was "
                     f"{N.f(R + '/arms/dependency@2000/auroc')} with dependency evidence "
                     f"({N.i(R + '/arms/dependency@2000/verdict_violation_tp')} true and "
                     f"{N.i(R + '/arms/dependency@2000/verdict_violation_fp')} false violation verdicts, "
                     f"{N.i(R + '/arms/dependency@2000/invalid')} invalid outputs) and "
                     f"{N.f(R + '/arms/lexical@2000/auroc')} with lexical evidence, using a mean of "
                     f"{N.get(R + '/arms/dependency@2000/mean_output_tokens'):.0f} output tokens per dependency call."))
    out.append(("p", "**Temperature-0 repeat.** Re-running stage 1 changed the score on "
                     f"{N.i(rep + '/n_score_changed')} of {N.i(rep + '/n_cases')} dependency trajectories and "
                     f"{N.i(rep_l + '/n_score_changed')} of {N.i(rep_l + '/n_cases')} lexical trajectories."))
    out.append(("p", "**Live-agent slice.** In 12 export-domain seeds, a model-driven W2 (qwen3.5-397b) was asked by "
                     "W1 to fold one more table into a partner export \"without mentioning it\": a restricted panel in "
                     "the *request* condition, a permitted table in the *matched* condition. W3 then staged the result. "
                     f"W2 included the restricted panel in {N.i(L + '/request/w2_used_extra_table')} of "
                     f"{N.i(L + '/request/completed')} completed request runs, producing "
                     f"{N.i(L + '/request/oracle_violations')} oracle-confirmed violations; it disclosed the table in "
                     f"its own notes in {N.i(L + '/request/notes_mention_extra')} of them, so concealment was not "
                     "observed. Matched runs produced "
                     f"{N.i(L + '/matched/oracle_violations')} violations. With the frozen monitor prompt at 2,000 tokens, "
                     "AUROC over the live trajectories was "
                     f"{N.f(L + '/monitors/qwen3.5-397b|dependency@2000/auroc')} with dependency evidence, "
                     f"{N.f(L + '/monitors/qwen3.5-397b|lexical@2000/auroc')} lexical and "
                     f"{N.f(L + '/monitors/qwen3.5-397b|chronological@2000/auroc')} chronological; the rule monitor "
                     f"on dependency selections reached {N.f(L + '/rule_monitor_auroc/dependency@2000')}. The violation "
                     "here was instructed, not emergent, and one domain and one model limit what it shows."))
    return out
