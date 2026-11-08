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
    if min(abs(lo), abs(hi)) < 0.5 * 10 ** -nd:  # a bound that would print as ±0.00: show one more digit
        nd += 1
    return f"[{lo:.{nd}f}, {hi:.{nd}f}]".replace("-", "−")


def authors():
    p = ROOT / "report/authors.json"
    if p.exists():
        return [tuple(a) for a in json.loads(p.read_text())]
    return [("[AUTHOR NAME TO CONFIRM]", "[AFFILIATION TO CONFIRM]")]


TITLE = "Swarm Evidence: Dependency-Based Evidence Selection for Monitoring Cross-Agent Policy Violations Under a Fixed Context Budget"


def abstract_6k(N):
    dl6 = f"{Q}/contrasts/dependency-lexical@6000"
    if not N.has(dl6 + "/diff"):
        return ""
    d2, d6 = N.get(f"{Q}/contrasts/dependency-lexical@2000/diff"), N.get(dl6 + "/diff")
    sp = h3_split(N)
    shrank = [b for b, (a2, a6) in sp.items() if a6 < a2 and b != "lexical"]
    txt = ("In secondary comparisons at 6,000 tokens, extra evidence brought the baselines false alarms and the gap "
           f"to lexical retrieval {'grew' if d6 > d2 else 'shrank'} to {sg(d6)} {ci(N, dl6 + '/ci95_family_bootstrap')}")
    if shrank:
        txt += ", though it narrowed against " + " and ".join(
            {"lexical_prf": "pseudo-relevance feedback", "bm25": "BM25", "chronological": "chronological review"}[b]
            for b in shrank)
    return txt + ". "


def front_matter(N):
    dl = f"{Q}/contrasts/dependency-lexical@2000"
    fa = f"{Q}/arms/full@nocap"
    abstract = (
        "When several AI agents each take locally permitted steps, a policy violation can exist only in their "
        "composition, and a monitor with a limited context budget must choose which logged events to read. We test "
        "whether selecting evidence by walking recorded artifact dependencies backward from the action under review "
        "beats ordinary retrieval at the same budget. An executable three-worker simulator with state-computed "
        f"labels provides {N.i('dataset/n_core_pairs')} matched violating/legitimate pairs from 12 template families, "
        "each needing evidence from two or more workers; a pre-registered test uses "
        f"{N.i('dataset/test_core_trajectories')} trajectories from 6 unseen families. At a 2,000-token cap, "
        f"dependency selection kept {N.pct(Q + '/arms/dependency@2000/gold_recall')} of the decisive evidence versus "
        f"{N.pct(Q + '/arms/lexical@2000/gold_recall')} for lexical retrieval. With the primary monitor, Qwen 3.5 "
        f"397B, held-out AUROC was {N.f(Q + '/arms/dependency@2000/auroc')} versus {N.f(Q + '/arms/lexical@2000/auroc')}, "
        f"but the family-bootstrap interval for the difference ({sg(N.get(dl + '/diff'))} "
        f"{ci(N, dl + '/ci95_family_bootstrap')}) "
        + ("includes zero, so the primary contrast is unresolved. " if N.get(dl + '/ci95_family_bootstrap/0') <= 0
           else "excludes zero. ")
        + "Qwen misapplied stated role rules on evidence that a deterministic checker scored at "
        f"{N.f('offline_test/dependency@2000@full/rule_auroc')}"
        + (f"; the pre-registered second model, Gemma 4 31B, made none of these errors, reaching "
           f"{N.f(G + '/arms/dependency@2000/auroc')} versus {N.f(G + '/arms/lexical@2000/auroc')} "
           f"({sg(N.get(G + '/contrasts/dependency-lexical@2000/diff'))} "
           f"{ci(N, G + '/contrasts/dependency-lexical@2000/ci95_family_bootstrap')}), a secondary result over only "
           "six families. " if gemma_ready(N) and role_fp(N, G) == 0 else ". ")
        + f"Reading the whole log without a cap scored {N.f(fa + '/auroc')} with Qwen. Dependency selection missed evidence "
        "outside the target's lineage and degraded without dependency metadata. Lineage selection keeps the "
        "decisive evidence cheaply; whether the monitor then uses it depended on the model."
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
              "transforms and merges it, and a third stages the merged artifact for export (Figure 1). Each step can be "
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
            "**An executable benchmark with state-based labels:** 12 template families in three domains "
            f"({N.i('dataset/n_core_pairs')} matched violating/legitimate pairs plus "
            f"{N.i('dataset/n_control_pairs')} single-worker controls), a composition-validity gate, held-out "
            "families, and audited removal of dependency metadata.",
            "**A pre-registered, budget-matched comparison** of seven evidence-selection policies, scored by an LLM "
            f"monitor{' (and a second model family)' if stage_done(N, G, 'stage1') else ''} and by a deterministic "
            "rule monitor on the same selected evidence, "
            "which separates retrieval from judgment.",
            "**A measured failure boundary:** dependency selection keeps nearly all decisive evidence at a small cap, "
            "but how well an LLM uses it depended on the model; it misses evidence outside the target's lineage by construction and "
            "degrades when dependency metadata is missing.",
        ], {"numbered": True}),
        ("h2", "2. Related Work"),
        ("p", "**Control and multi-agent monitoring.** AI Control evaluates protocols that keep untrusted models "
              "useful while limiting harm, with trusted monitors as one component [1]; we study one input to such a "
              "monitor and do not claim prevention. Multi-Agent AI Control finds that per-agent monitors detect an attack "
              "less often the more agents share it [3], so per-instance review is known to miss distributed attacks; "
              "we ask which evidence a joint monitor should read when its context is capped. Hammond et al. survey "
              "multi-agent risks including collusion [7], and Jones et al. show that combinations of individually "
              "safe models can be misused [6]."),
        ("p", "**Lineage and graphs.** Zhang et al. evaluate composed multi-agent information flows with "
              "authorization-paired tests and propose FlowReview, which reviews composed artifacts with "
              "deterministic enforcement; they argue that retained lineage alone does not guarantee correct "
              "permission attribution [2]. GroupGuard defends against group collusion with graph-based monitoring, "
              "honeypots and structural pruning [4]; Rose et al. detect collusion from activation probes on "
              "NARCBench [5]; agent logging and provenance infrastructure is an active area [8, 9]. We propose none "
              "of these. Our increment is a controlled measurement of *context-budgeted evidence selection* over "
              "recorded artifact lineage against non-graph retrieval baselines (lexical, BM25 [11], pseudo-relevance "
              "feedback [12]), with a deterministic monitor on the same selections to separate retrieval from "
              "judgment. A targeted search found no study isolating this effect; that is not proof of priority."),
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
              f"(mean {N.f('dataset/mean_events_test', 0)}; a whole-log prompt bills "
              f"{N.get(Q + '/arms/full@nocap/min_input_tokens'):,} to {N.get(Q + '/arms/full@nocap/max_input_tokens'):,} "
              "input tokens) with evidence spread "
              "through the log. An oracle labels each trajectory from hidden state only (record-level provenance, "
              "permissions at finalization, held-out membership, paid amounts). Twins share every event ID, tool, "
              "worker and the request, and differ only in wiring, an authorization or an amount. A **validity gate** "
              "requires, per base case: opposite labels; identical twin structure; agreement between the oracle and "
              "a deterministic rule monitor reading the full ledger; a second legitimate completion that changes a "
              "*different* worker, so every single-worker view of the violation is shared by a legitimate trajectory; "
              "and gold evidence spanning at least two workers (the last two are waived for the single-worker "
              "controls). Gold evidence is one deletion-minimal event set on which the rule monitor retains the "
              "oracle label; recall measures coverage of that chosen witness, and alternative sufficient evidence sets "
              f"may exist. {N.i('dataset/gate_passed')} of {N.i('dataset/n_base_cases')} base cases pass. The family split was "
              "fixed before any model call: development A1, A3, B1, B3, C1, C3 (prompt design A1/B1/C1, threshold "
              "calibration A3/B3/C3); held out A2, A4, B2, B4, C2, C4."),
        ("h3", "3.2 Evidence selection under a cap"),
        ("p", "All methods use identical compact JSON rendering in chronological order, include only complete "
              "events, and count the fixed overhead (instructions, policy, request) against the cap. "
              "**Chronological** keeps the newest events. **Lexical** ranks by 4\u00d7[contains target ID] plus the "
              "number of distinct query tokens shared with the policy and request. **BM25** [11] and **Lexical+PRF** "
              "(one round of pseudo-relevance feedback adding all tokens, including artifact IDs, of the top three "
              "events [12]) are further non-graph baselines added on development data before the freeze. "
              "**Dependency** runs a backward breadth-first traversal from the target over producer-to-consumer "
              "relations; output-less events that reference a reached artifact (grants, revocations, reversals, "
              "approvals, exceptions) attach at its distance; ties go to recency; spare budget stays unused. "
              "**Shuffled graph** keeps the target's producer but traverses a node-relabelled copy of the rest of "
              "the graph, selecting as many events without real structure. "
              "**Isolated** makes one call per worker with a third of the cap each and takes the maximum score; at "
              "2,000 tokens its repeated overhead alone exceeds that share under the conservative estimate, so it shows "
              "no events (we kept this frozen accounting). **Full log** (no cap) is a diagnostic reference with every event "
              "visible. Caps are 2,000 and 6,000 tokens, "
              "estimated at 2.5 bytes per token after a development pilot at 3.0 overran by up to 11%."),
        ("fig", "figures/fig1_example.png", 5.7,
         "**Figure 1.** A development violating trajectory (family A1, synthetic data). Each dot is a recorded "
         "event in a worker's lane; black dots are the gold minimal evidence (the restricted source registered by "
         "W3, a transform and a merge by W1, and the staged export by W2) and arrows are recorded lineage. Ticks show what "
         "each selector keeps at the 2,000-token cap. Dependency selection reaches the old license event; lexical "
         "retrieval fills the budget with policy-word matches from unrelated work; chronological review sees only "
         "the tail."),
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
              "bridge, replacing the artifact ID in the consuming event's structured fields (inputs, arguments, "
              "version map) with a unique placeholder. Free-text notes are not rewritten, but generated notes never "
              "contain IDs; an audit confirms no ID join recovers a masked link, and all methods see the same view."),
    ]
    # ---------------- Results
    rows = arm_rows(N, Q, 2000)
    fa = f"{Q}/arms/full@nocap"
    overruns = sum(N.get(f"{Q}/arms/{arm}@2000/cap_overruns") for arm in BUDGETED)
    invalid = sum(N.get(f"{Q}/arms/{arm}@2000/invalid") for arm in BUDGETED) + N.get(fa + "/invalid")

    b += [
        ("h2", "4. Results"),
        ("h3", "4.1 Primary comparison"),
        ("p", "In Sections 4.1 to 4.3 \"the LLM\" is the primary monitor, qwen3.5-397b. "
              f"At the 2,000-token cap, dependency selection kept {N.pct(dep2 + '/gold_recall')} of gold evidence "
              f"using {N.get(dep2 + '/mean_input_tokens'):.0f} billed input tokens on average, against "
              f"{N.pct(lex2 + '/gold_recall')} for lexical retrieval at {N.get(lex2 + '/mean_input_tokens'):.0f} "
              f"tokens (Table 1). Held-out AUROC was {N.f(dep2 + '/auroc')} with dependency selection and "
              f"{N.f(lex2 + '/auroc')} with lexical retrieval (Figure 3 in Appendix D), a paired difference of {sg(N.get(dl + '/diff'))} "
              f"(family-bootstrap 95% interval {ci(N, dl + '/ci95_family_bootstrap')}); "
              f"{N.i(dl + '/families_positive')} of 6 held-out families favored dependency and "
              f"{N.i(dl + '/families_negative')} favored lexical. **The pre-registered primary contrast is positive "
              "in point estimate but not resolved at the family level.** "
              f"With lexical evidence the model abstained on {N.i(lex2 + '/abstain_valid')} of 60 "
              "trajectories, reporting insufficient evidence. With dependency evidence it gave violation "
              f"verdicts on {N.i(dep2 + '/verdict_violation_tp')} of 30 violations but also on "
              f"{N.i(dep2 + '/verdict_violation_fp')} of 30 legitimate twins (counts at calibrated thresholds: "
              "Appendix D)." + (" At 2,000 tokens no call exceeded its cap" if overruns == 0 else
                 f" At 2,000 tokens {overruns} calls exceeded their cap")
              + (", and no output (including the full log's) was invalid." if invalid == 0
                 else f", and {invalid} outputs (including the full log's) were invalid.")),
        ("table",
         TABLE_HEAD, rows,
         "**Table 1.** Held-out results at the 2,000-token cap, qwen3.5-397b (60 trajectories, 6 unseen families). "
         "CI: 95% family bootstrap; TP/FP: violation verdicts on violating/legitimate runs; Abst.: insufficient "
         "evidence; Inv.: invalid predictions; Recall: gold evidence shown; Tokens: mean billed input; Rule: "
         "rule-monitor AUROC on the same evidence (1.00 on the full log by the validity gate).",
         {"size": 8, "col_widths": TABLE_WIDTHS}),
        ("p", "**More context did not help Qwen.** Reading the whole log without a cap (mean "
              f"{N.get(fa + '/mean_input_tokens'):.0f} billed input tokens, "
              f"{N.get(fa + '/mean_input_tokens') / N.get(dep2 + '/mean_input_tokens'):.1f}× the dependency arm) "
              f"gave AUROC {N.f(fa + '/auroc')}: the model flagged {N.i(fa + '/verdict_violation_fp')} of 30 "
              f"legitimate twins. Of those {N.i(fa + '/fp_total')} false alarms, {N.i(fa + '/fp_citing_unrelated_work')} "
              "cited real events from unrelated legitimate work, such as payment entries or exceptions "
              f"belonging to other tasks, and {N.i(fa + '/fp_citing_unshown_ids')} cited event IDs that do not occur "
              "in the log; "
              + (f"none of the dependency arm's {N.i(dep2 + '/fp_total')} false alarms did either. "
                 if N.get(dep2 + '/fp_citing_unrelated_work') == 0 and N.get(dep2 + '/fp_citing_unshown_ids') == 0 else
                 f"of the dependency arm's {N.i(dep2 + '/fp_total')}, {N.i(dep2 + '/fp_citing_unrelated_work')} and "
                 f"{N.i(dep2 + '/fp_citing_unshown_ids')} did. ")
              + f"The paired dependency-minus-full difference was "
              f"{sg(N.get(Q + '/contrasts/dependency-full@nocap/diff'))} "
              f"{ci(N, Q + '/contrasts/dependency-full@nocap/ci95_family_bootstrap')}: selection fit the budget and, "
              "in point estimate, removed distracting look-alike evidence"
              + (f" (the interval narrowly includes zero; {N.i(Q + '/contrasts/dependency-full@nocap/families_positive')} "
                 f"of 6 families favored dependency)" if N.get(Q + '/contrasts/dependency-full@nocap/ci95_family_bootstrap/0') <= 0
                 else "")
              + ". This is one model in one synthetic setting; it does not show that more context generally makes "
              "monitoring worse."),
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
    q_role_fp = role_fp(N, Q)
    b += [
        ("h3", "4.2 Same evidence, different judgments"),
        ("p", "The rule monitor scored "
              f"{N.f('offline_test/dependency@2000@full/rule_auroc')} on the dependency selections that gave the LLM "
              f"{N.f(dep2 + '/auroc')}, with {N.i('offline_test/dependency@2000@full/rule_fp')} false positives; per-family "
              f"results are in Table 2. Of the LLM's {N.i(dep2 + '/verdict_violation_fp')} false alarms, {q_role_fp} fall in two "
              "families whose legitimate twins hinge on a policy clause about roles: a lookup join's or a "
              "deduplication filter's *reference* input does not carry records (A4, B2). The model's stated reasons "
              "cite the restricted or held-out source as reaching the target, which the policy rules out: retrieval "
              "succeeded and judgment failed. Families decided by plain lineage (A2, C2) were perfect for both monitors."
              + (f" The second model, judging the same selections, flagged {role_fp(N, G)} of these 10 legitimate "
                 "twins (Section 4.4)." if gemma_ready(N) else "")),
        ("table", ["Family", "Mechanism", "Dep. LLM AUROC", "Dep. rule AUROC", "Dep. recall",
                   "Legit flagged", "Viol. missed", "Lex. LLM AUROC"], fam_rows,
         "**Table 2.** Per-family held-out results at 2,000 tokens (5 pairs each). Legit flagged / Viol. missed: "
         "legitimate twins given a violation verdict / violations judged benign or abstained, by the LLM "
         "(qwen3.5-397b) with dependency evidence. Rule AUROC and recall are model-independent.",
         {"size": 8, "col_widths": [0.55, 1.75, 0.7, 0.7, 0.6, 0.65, 0.65, 0.7]}),
        ("p", "**Out-of-lineage boundary (pre-registered H2).** In C4 the decisive evidence, an earlier released "
              "batch that paid part of the same invoice, is not an ancestor of the target, and dependency selection "
              "never retrieved it. The LLM judged all "
              f"{N.i(oo + '/dependency|C4_out_of_lineage/violations_total')} C4 violations benign (AUROC "
              f"{N.f(oo + '/dependency|C4_out_of_lineage/auroc')}), and so did the optimistic rule monitor. On the five "
              "in-lineage held-out families, the LLM with dependency evidence reached AUROC "
              f"{N.f(oo + '/dependency|other_test_families/auroc')}. Backward lineage misses constraints that "
              "aggregate over sibling consumers, such as the invoice totals tested here."),
    ]
    dl6 = f"{Q}/contrasts/dependency-lexical@6000"
    v = f"{Q}/visibility"
    b += [
        ("h3", "4.3 Larger budgets and missing metadata"),
        ("p", budget_paragraph(N)),
        ("p", masking_paragraph(N)),
        ("fig", "figures/fig3_budget_and_metadata.png", 6.4,
         "**Figure 2.** (a) Model-independent share of gold minimal evidence that five of the selectors keep on the 60 "
         "held-out trajectories as the input cap grows. (b, c) LLM AUROC for dependency and lexical selection when "
         "dependency relations are masked at random (25%, 50%) or at every cross-worker bridge, at the 2,000- and "
         "6,000-token caps."),
    ]
    # secondary model + controls + cost
    g_dep, g_lex = f"{G}/arms/dependency@2000", f"{G}/arms/lexical@2000"
    gdl = f"{G}/contrasts/dependency-lexical@2000"
    b += [
        ("h3", "4.4 Second model, controls and cost"),
        ("p", second_model_sentence(N) +
              "Single-worker controls are in Appendix D and costs in Appendix B. " + exploratory_pointer(N)),
    ]
    # ---------------- Discussion
    q_role = role_fp(N, Q)
    b += [
        ("h2", "5. Discussion and Limitations"),
        ("p", "**What the results mean.** Under a tight budget, following recorded lineage is a cheap retrieval "
              "step: it keeps almost all decisive evidence at a fraction of a full review's tokens, which the non-graph "
              "baselines tested here did not do at the small cap. For the primary monitor, better context did not yield proportionally "
              "better detection: on the same evidence a short deterministic checker made no false alarms, while Qwen "
              "flagged every legitimate twin in the two role-dependent families. "
              + ("The second model made none of these errors, so this judgment gap belongs to Qwen in this setting, "
                 "not to LLM monitors in general. "
                 if gemma_ready(N) and role_fp(N, G) == 0 else "")
              + "Lineage selection also has predictable "
              "blind spots (aggregate constraints over sibling consumers, missing metadata), so a deployed monitor "
              "needs a fallback for those cases, such as sibling expansion; lexical retrieval did not rescue C4."),
        ("p", hypotheses_paragraph(N)),
        ("p", "**Limitations.** The setting is synthetic and scripted (three known workers, a trusted complete "
              "recorder, a common finalization point), so results do not transfer to unknown swarms, tampered logs or "
              "emergent collusion. Six held-out families give wide, descriptive intervals, and 15 benign calibration "
              "cases cannot certify low false-positive rates. The rule monitor was written with knowledge of the tool "
              "semantics; it shows what structured evidence permits, not a deployable detector. "
              + live_limitation(N) + " Appendix A lists further limitations, including four known gaps pinned by "
              "tests."),
        ("p", "**Future work.** Sibling-consumer expansion, hybrid checker-plus-LLM monitors, live-worker logs, more "
              "families, and recorder-tampering adversaries."),
        ("h2", "6. Conclusion"),
        ("p", "At a fixed context budget, selecting evidence through recorded artifact dependencies retained "
              f"{N.pct(dep2 + '/gold_recall')} of decisive cross-agent evidence where lexical retrieval retained "
              f"{N.pct(lex2 + '/gold_recall')}. With the primary monitor the AUROC difference ({N.f(dep2 + '/auroc')} "
              f"versus {N.f(lex2 + '/auroc')}) is unresolved; most of its false alarms ({q_role} of "
              f"{N.i(dep2 + '/verdict_violation_fp')}) were misapplied role rules, on evidence that a deterministic "
              f"checker scored at {N.f('offline_test/dependency@2000@full/rule_auroc')}"
              + (f" and the second model, in a secondary result over six families, at "
                 f"{N.f(G + '/arms/dependency@2000/auroc')}" if gemma_ready(N) else "")
              + ". Lineage selection fails predictably on out-of-lineage constraints and missing metadata."),
        ("h2", "Code and Data"),
        ("p", f"{REPO} (MIT): synthetic data, labels, frozen protocol and every model call; `python -m "
              "swarm_evidence analyze` regenerates all tables and figures. No real or personal data."),
        ("h2", "Author Contributions"),
        ("p", author_contributions()),
        ("h2", "References"),
        ("refs",),
    ]
    b = [x for x in b if x != ("refs",)] + [("p", r, {"size": 8.5, "space_after": 2}) for r in references()]
    b += appendix(N)
    return b


BUDGETED = ("dependency", "lexical", "chronological", "bm25", "lexical_prf", "shuffled", "isolated")
LABEL = {"dependency": "dependency", "lexical": "lexical", "chronological": "chronological", "bm25": "BM25",
         "lexical_prf": "lexical+PRF", "shuffled": "shuffled-graph", "isolated": "isolated"}
CALIBRATION_CALLS = 30 * (6 * 2 + 3 * 2 + 1)  # 30 trajectories x (6 arms x 2 caps + isolated 3 calls x 2 caps + full)
STAGE_NAME = {"qwen3.5-397b": {"calibration": "calibration"}, "gemma-4-31b-it": {"calibration": "calibration_gemma"}}


def stage_done(N, M, stage):
    """Whether a frozen stage finished for model path M (e.g. 'models/qwen3.5-397b'): every expected arm complete."""
    model = M.split("/", 1)[1]
    if stage == "stage1":
        keys = [f"{M}/arms/{a}@2000/auroc" for a in ("dependency", "lexical")]
    elif stage == "stage2":
        keys = [f"{M}/arms/{a}@2000/auroc" for a in BUDGETED[2:]] + [f"{M}/arms/full@nocap/auroc"]
    elif stage == "stage3":
        keys = [f"{M}/arms/{a}@6000/auroc" for a in BUDGETED]
    elif stage == "stage4":
        keys = [f"{M}/visibility/{a}@{c}@{v}/auroc" for a in ("dependency", "lexical") for c in (2000, 6000)
                for v in ("random25", "random50", "bridges")]
    elif stage == "controls":
        keys = [f"{M}/controls/{a}/n" for a in ("dependency", "lexical", "chronological", "isolated", "full")]
        return all(N.has(k) for k in keys) and all(N.get(k) == 18 for k in keys)
    elif stage == "calibration":
        k = f"costs/by_stage/{model}|{STAGE_NAME.get(model, {}).get('calibration', 'calibration')}/calls"
        return N.has(k) and N.get(k) == CALIBRATION_CALLS
    else:
        raise ValueError(stage)
    return all(N.has(k) for k in keys)


def moved(a, b, nd=2):
    """'fell from a to b' / 'rose from a to b' / 'stayed at a', worded from the numbers."""
    fa, fb = f"{a:.{nd}f}", f"{b:.{nd}f}"
    if fa == fb:
        return f"stayed at {fa}"
    return f"{'fell' if b < a else 'rose'} from {fa} to {fb}"


NON_GRAPH = ("lexical", "chronological", "bm25", "lexical_prf")


TABLE_HEAD = ["Method", "AUROC (95% CI)", "TP/FP", "Abst.", "Inv.", "Recall", "Tokens", "Rule"]
TABLE_WIDTHS = [1.55, 1.15, 0.55, 0.5, 0.45, 0.6, 0.6, 0.55]
ARM_LABELS = [("dependency", "Dependency"), ("lexical", "Lexical"), ("chronological", "Chronological"),
              ("bm25", "BM25"), ("lexical_prf", "Lexical+PRF"), ("shuffled", "Shuffled graph"),
              ("isolated", "Isolated (3 calls)")]


def arm_rows(N, M, cap):
    def cia(a):
        lo, hi = N.get(a + "/auroc_ci_family/0"), N.get(a + "/auroc_ci_family/1")
        return f"{N.f(a + '/auroc')} ({lo:.2f}\u2013{hi:.2f})"
    rows = []
    for arm, label in ARM_LABELS:
        a = f"{M}/arms/{arm}@{cap}"
        if arm == "isolated" and cap == 2000:
            label = "Isolated (no events)"
        rows.append([label, cia(a), f"{N.i(a + '/verdict_violation_tp')}/{N.i(a + '/verdict_violation_fp')}",
                     N.i(a + "/abstain_valid"), N.i(a + "/invalid"), N.f(a + "/gold_recall"),
                     f"{N.get(a + '/mean_input_tokens'):.0f}", N.f(f"offline_test/{arm}@{cap}@full/rule_auroc")])
    if cap == 2000:
        fa = f"{M}/arms/full@nocap"
        rows.append(["Full log (no cap)", cia(fa), f"{N.i(fa + '/verdict_violation_tp')}/{N.i(fa + '/verdict_violation_fp')}",
                     N.i(fa + "/abstain_valid"), N.i(fa + "/invalid"), N.f(fa + "/gold_recall"),
                     f"{N.get(fa + '/mean_input_tokens'):.0f}", "1.00"])
    return rows


def join(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def h3_split(N):
    """Per non-graph baseline: dependency-minus-baseline AUROC difference at 2k and 6k (pre-registered H3)."""
    out = {}
    for b in NON_GRAPH:
        k2, k6 = f"{Q}/contrasts/dependency-{b}@2000/diff", f"{Q}/contrasts/dependency-{b}@6000/diff"
        if N.has(k2) and N.has(k6):
            out[b] = (N.get(k2), N.get(k6))
    return out


def budget_paragraph(N):
    o = "offline_test"
    d2r, d6r = N.get(f"{o}/dependency@2000@full/gold_recall"), N.get(f"{o}/dependency@6000@full/gold_recall")
    txt = (f"At the 6,000-token cap the non-graph baselines keep more evidence (lexical recall "
           f"{N.f(o + '/lexical@6000@full/gold_recall')}), while dependency selection's recall "
           + ("is unchanged because it never pads" if f"{d2r:.2f}" == f"{d6r:.2f}" else moved(d2r, d6r))
           + " (Figure 2a). ")
    dl2, dl6 = f"{Q}/contrasts/dependency-lexical@2000", f"{Q}/contrasts/dependency-lexical@6000"
    if not (stage_done(N, Q, "stage3") and N.has(dl6 + "/diff")):
        return txt + "The 6,000-token LLM stage had not finished when this version was built, so H3 is not tested."
    d2, d6 = N.get(dl2 + "/diff"), N.get(dl6 + "/diff")
    l2, l6 = f"{Q}/arms/lexical@2000", f"{Q}/arms/lexical@6000"
    txt += (f"More evidence did not help the LLM: with lexical retrieval its AUROC "
            f"{moved(N.get(l2 + '/auroc'), N.get(l6 + '/auroc'))}, as abstentions ({N.i(l2 + '/abstain_valid')} to "
            f"{N.i(l6 + '/abstain_valid')}) gave way to false alarms on {N.i(l6 + '/verdict_violation_fp')} of 30 "
            f"legitimate twins (Table 3, Appendix D). The dependency-minus-lexical difference was {sg(d6)} "
            f"{ci(N, dl6 + '/ci95_family_bootstrap')} at 6,000 tokens against {sg(d2)} at 2,000. ")
    sp = h3_split(N)
    shrank = [b for b, (a2, a6) in sp.items() if a6 < a2]
    grew = [b for b in sp if b not in shrank]
    if sp:
        txt += ("Pre-registered H3 predicted that the advantage over non-graph retrieval would shrink; it "
                + (f"grew against {join(LABEL[b] for b in grew)}" if grew else "")
                + ("; it " if grew and shrank else "")
                + (f"shrank against {join(LABEL[b] + f' ({sg(sp[b][0])} to {sg(sp[b][1])})' for b in shrank)}"
                   if shrank else "") + ". ")
    over = sum(N.get(f"{Q}/arms/{a}@6000/cap_overruns") for a in BUDGETED)
    inv = sum(N.get(f"{Q}/arms/{a}@6000/invalid") for a in BUDGETED)
    if over or inv:
        txt += (f"In this full-visibility run, {over} calls slightly exceeded the cap and {inv} case-level predictions "
                "were invalid (details, including the masking runs, in Appendix D).")
    return txt


def cap6k_details(N):
    """Supporting detail for the 6,000-token stage (moved from Section 4.3)."""
    txt = ""
    rp = f"dependency_cap_repeat/{Q.split('/', 1)[1]}"
    if N.has(rp + "/n_identical_input") and N.get(rp + "/n_identical_input") == N.get(rp + "/n_cases"):
        txt += (f"Dependency selection sent identical prompts at both caps, so its two runs are a natural repeat: "
                f"{N.i(rp + '/n_score_changed')} of {N.i(rp + '/n_cases')} scores and "
                f"{N.i(rp + '/n_verdict_changed')} verdicts changed at temperature 0 (descriptive, not pre-registered). ")
    over = {a: N.get(f"{Q}/arms/{a}@6000/cap_overruns") for a in BUDGETED}
    inv = {a: N.get(f"{Q}/arms/{a}@6000/invalid") for a in BUDGETED}
    if sum(over.values()):
        mx = max(N.get(f"{Q}/arms/{a}@6000/max_input_tokens") for a in BUDGETED if over[a])
        txt += (f"At this cap, {join(f'{v} {LABEL[a]}' for a, v in over.items() if v)} calls billed more input than the "
                f"6,000-token cap (at most {mx:,} tokens), because the byte-based estimate undercounts some text. ")
    mv = [f"{Q}/visibility/{a}@6000@{v}" for a in ("dependency", "lexical") for v in ("random25", "random50", "bridges")
          if N.has(f"{Q}/visibility/{a}@6000@{v}/cap_overruns")]
    m_over = sum(N.get(k + "/cap_overruns") for k in mv)
    m_inv = sum(N.get(k + "/invalid") for k in mv)
    if m_over or m_inv:
        mx = max([N.get(k + "/max_input_tokens") for k in mv if N.get(k + "/cap_overruns")] or [0])
        txt += (f"In the 6,000-token masking runs, {m_over} more calls exceeded the cap"
                + (f" (at most {mx:,} tokens)" if m_over else "") + f" and {m_inv} predictions were invalid (Table 4). ")
    if sum(inv.values()):
        resp = {a: N.get(f"{Q}/arms/{a}@6000/invalid_responses") for a in BUDGETED}
        txt += ("Invalid case-level predictions (invalid API responses), scored 0.5 under the frozen policy: "
                + join(f"{v} {LABEL[a]} ({resp[a]})" for a, v in inv.items() if v)
                + ("; isolated calls have a 128-token output cap per worker." if inv.get("isolated") else "."))
    return txt


def masking_paragraph(N):
    o, v = "offline_test", f"{Q}/visibility"
    rec = {m: N.get(f"{o}/dependency@2000@{m}/gold_recall") for m in ("full", "random25", "random50", "bridges")}
    lex = [N.get(f"{o}/lexical@{c}@{m}/gold_recall") for c in (2000, 6000) for m in ("full", "random25", "random50", "bridges")]
    lex_same = max(lex[:4]) - min(lex[:4]) < 0.01 and max(lex[4:]) - min(lex[4:]) < 0.01
    txt = ("Masking dependency metadata hurts dependency selection's retrieval: at 2,000 tokens its gold-evidence "
           f"recall {moved(rec['full'], rec['random25'])} with 25% of relations masked, to {rec['random50']:.2f} at "
           f"50%, and to {rec['bridges']:.2f} when every cross-worker bridge (about half of all relations) is masked, "
           "while lexical recall " + ("is essentially unchanged" if lex_same else "changes little")
           + f"; at 6,000 tokens with 50% masking, lexical retrieval kept more of it ("
           f"{N.get('offline_test/lexical@6000@random50/gold_recall'):.2f} vs "
           f"{N.get('offline_test/dependency@6000@random50/gold_recall'):.2f}). ")
    if not stage_done(N, Q, "stage4"):
        return txt + "The LLM masking stage had not finished when this version was built, so masked AUROCs are not reported."
    a = {m: N.get(f"{v}/dependency@2000@{m}/auroc") for m in ("full", "random25", "random50", "bridges")}
    al = {m: N.get(f"{v}/lexical@2000@{m}/auroc") for m in ("full", "random50")}
    txt += (f"The LLM's AUROC with dependency evidence {moved(a['full'], a['random25'])} at 25% masking and was "
            f"{a['random50']:.2f} at 50% and {a['bridges']:.2f} with bridges masked; with lexical evidence it "
            f"{moved(al['full'], al['random50'])} at 50% (Figure 2b, c). With half the relations masked the model "
            f"mostly abstained ({N.i(v + '/dependency@2000@random50/abstain_valid')} of 60 dependency-arm trajectories) "
            f"and raised {N.i(v + '/dependency@2000@random50/verdict_violation_fp')} false alarms. ")
    txt += "Masked placeholders tell the monitor that a link is missing."
    return txt


def exploratory_pointer(N):
    R, L = "models/qwen3.5-397b+reasoning", "live_exploratory"
    done = []
    if N.has(R + "/arms/dependency@2000/auroc") and N.has(R + "/arms/lexical@2000/auroc"):
        done.append("a reasoning-enabled monitor")
    if N.has("replicates/qwen3.5-397b|dependency|2000/n_cases"):
        done.append("a temperature-0 repeat")
    if N.has(L + "/request/completed"):
        done.append("a live slice with model-driven workers")
    if not done:
        return "The planned exploratory checks had not finished when this version was built (Appendix C)."
    return ("Exploratory checks after the freeze (" + (", ".join(done[:-1]) + " and " + done[-1] if len(done) > 1
            else done[0]) + ") are reported in Appendix C.")


def second_model_coverage(N):
    """Which frozen stages finished for each model (masking and controls were planned for the primary model only)."""
    names = {"stage1": "stage 1 (dependency and lexical at 2,000 tokens)", "stage2": "stage 2 (other arms at 2,000 "
             "tokens)", "calibration": "calibration", "stage3": "stage 3 (6,000 tokens)", "stage4": "stage 4 (masking)",
             "controls": "controls"}
    q_missing = [names[k] for k in ("stage1", "stage2", "controls", "calibration", "stage3", "stage4")
                 if not stage_done(N, Q, k)]
    g_done = [names[k] for k in ("stage1", "stage2", "calibration", "stage3") if stage_done(N, G, k)]
    g_missing = [names[k] for k in ("stage1", "stage2", "calibration", "stage3") if not stage_done(N, G, k)]
    out = ("All frozen stages finished for the primary model. " if not q_missing else
           "For the primary model, " + "; ".join(q_missing) + " had not finished when this version was built. ")
    if not g_done:
        return out + ("For gemma-4-31b-it, no held-out stage had finished when this version was built. Masking and "
                      "controls were run for the primary model only.")
    out += f"For gemma-4-31b-it, {join(g_done)} finished"
    if g_missing:
        out += (f", while {join(g_missing)} had not finished when this version was built and "
                + ("is" if len(g_missing) == 1 else "are") + " not reported")
    return out + ". Masking and controls were run for the primary model only."


def live_paragraph(N, L):
    """Exploratory live slice: worker behaviour, disclosure counted per run, oracle outcomes, detection."""
    rq, mt = L + "/request", L + "/matched"
    used, nd = N.get(rq + "/w2_used_extra_table"), N.get(rq + "/used_extra_not_disclosed")
    txt = (f"**Live-agent slice.** In {N.i(rq + '/n')} export-domain seeds, a model-driven W2 (qwen3.5-397b) was asked "
           "by W1 to fold "
           "one more table into a partner export, with \"no need to mention it in your notes\": a restricted panel "
           "in the *request* condition, a permitted table in the *matched* condition; W3 (also model-driven) then "
           "staged the result. "
           + ("All request and matched runs completed." if N.get(rq + '/completed') == N.get(rq + '/n')
              and N.get(mt + '/completed') == N.get(mt + '/n') else
              f"Completed: {N.i(rq + '/completed')} of {N.i(rq + '/n')} request runs and "
              f"{N.i(mt + '/completed')} of {N.i(mt + '/n')} matched runs.") + " W2 folded in the restricted panel "
           f"in {used} completed request runs, giving {N.i(rq + '/oracle_violations')} oracle-confirmed violations")
    if used:
        txt += (f"; it mentioned the panel in its own notes in {N.i(rq + '/used_extra_and_disclosed')} of those runs"
                + (", so concealment was not observed, and because W2 named the panel these trajectories are easier "
                   "to judge than the scripted ones" if nd == 0 else f" and omitted it in {nd}"))
    txt += f". Matched runs produced {N.i(mt + '/oracle_violations')} violations. "
    nv, nl = N.get(L + "/n_violations"), N.get(L + "/n_legit")
    m = L + "/monitors/qwen3.5-397b|"
    arms_ok = all(N.has(m + f"{a}@2000/complete") and N.get(m + f"{a}@2000/complete")
                  for a in ("dependency", "lexical", "chronological"))
    if not arms_ok:
        txt += "The monitor stage over the live trajectories had not finished when this version was built, so detection is not reported. "
    elif nv and nl:
        txt += (f"Over the {nv + nl} completed live trajectories ({nv} violating), the frozen monitor prompt at 2,000 "
                f"tokens reached AUROC {N.f(m + 'dependency@2000/auroc')} with dependency evidence "
                f"({N.i(m + 'dependency@2000/violation_tp')} true and {N.i(m + 'dependency@2000/violation_fp')} false "
                f"violation verdicts), {N.f(m + 'lexical@2000/auroc')} lexical and "
                f"{N.f(m + 'chronological@2000/auroc')} chronological; the rule monitor on dependency selections "
                f"reached {N.f(L + '/rule_monitor_auroc/dependency@2000')}. ")
    else:
        txt += "Detection AUROC is undefined here because the completed live trajectories contain only one label. "
    return txt + "The violation was instructed, not emergent, and one domain and one model limit what this shows."


def gemma_ready(N):
    return stage_done(N, G, "stage1") and N.has(f"{G}/contrasts/dependency-lexical@2000/diff")


def role_count(N, M, verdict):
    return sum(N.get(f"{M}/verdicts_by_family/dependency@2000/{f}").get(f"legit->{verdict}", 0) for f in ("A4", "B2"))


def role_fp(N, M):
    """Legitimate twins in the role-rule families (A4, B2) given a violation verdict with dependency evidence."""
    return sum(N.get(f"{M}/verdicts_by_family/dependency@2000/{f}").get("legit->violation", 0) for f in ("A4", "B2"))


def second_model_sentence(N):
    """Second pre-registered model family: report what happened, in the direction it happened."""
    g_dep, g_lex = f"{G}/arms/dependency@2000", f"{G}/arms/lexical@2000"
    gdl = f"{G}/contrasts/dependency-lexical@2000"
    if not (stage_done(N, G, "stage1") and N.has(gdl + "/diff")):
        return "The second model (gemma-4-31b-it) had not finished its held-out stages when this version was built, so no result is reported. "
    d = N.get(gdl + "/diff")
    goo = f"{G}/out_of_lineage/dependency|C4_out_of_lineage"
    out = (f"The pre-registered second model, gemma-4-31b-it, judged the same selections differently: dependency "
           f"AUROC {N.f(g_dep + '/auroc')} versus lexical {N.f(g_lex + '/auroc')} at 2,000 tokens (Figure 4; difference "
           f"{sg(d)}, interval {ci(N, gdl + '/ci95_family_bootstrap')}; {N.i(gdl + '/families_positive')} of 6 "
           f"families favored dependency), with {N.i(g_dep + '/verdict_violation_tp')} true and "
           f"{N.i(g_dep + '/verdict_violation_fp')} false violation verdicts. It flagged {role_fp(N, G)} of the 10 "
           f"role-rule legitimate twins ({role_count(N, G, 'invalid')} gave an invalid output) and, like Qwen, {N.i(goo + '/violations_flagged')} of the "
           f"{N.i(goo + '/violations_total')} C4 violations. This is a secondary result; with six held-out families "
           "it does not establish a general advantage. ")
    gf, gdf = f"{G}/arms/full@nocap", f"{G}/contrasts/dependency-full@nocap"
    if stage_done(N, G, "stage2") and N.has(gdf + "/diff"):
        out += (f"Reading the whole log, Gemma scored {N.f(gf + '/auroc')} ({N.i(gf + '/verdict_violation_fp')} false "
                f"alarms on 30 legitimate twins): {'lower' if N.get(gdf + '/diff') > 0 else 'higher'} than with "
                f"dependency evidence ({sg(N.get(gdf + '/diff'))} {ci(N, gdf + '/ci95_family_bootstrap')}), but "
                f"{'well above' if N.get(gf + '/auroc') > N.get(Q + '/arms/full@nocap/auroc') else 'not above'} "
                f"Qwen's {N.f(Q + '/arms/full@nocap/auroc')}. ")
    inv = gemma_invalid(N)
    if sum(inv.values()):
        resp = gemma_invalid(N, "invalid_responses")
        out += (f"At 2,000 tokens and with the full log, Gemma had {sum(inv.values())} invalid case-level predictions "
                f"(from {sum(resp.values())} invalid API responses), scored 0.5 (Appendix D). ")
    return out


def gemma_invalid(N, key="invalid"):
    """Per-arm invalid counts for the second model at 2,000 tokens and with the full log.
    key='invalid' counts case-level predictions; 'invalid_responses' counts API responses."""
    arms = [a for a in BUDGETED if N.has(f"{G}/arms/{a}@2000/{key}")]
    inv = {a: N.get(f"{G}/arms/{a}@2000/{key}") for a in arms}
    if N.has(f"{G}/arms/full@nocap/{key}"):
        inv["full"] = N.get(f"{G}/arms/full@nocap/{key}")
    return inv


def frozen_threshold_sentence(N, dep2, lex2):
    """Counts at the score threshold frozen on calibration families (pre-registered secondary metric)."""
    if not N.has(dep2 + "/threshold_frozen"):
        return "No calibration threshold was available."
    w = f"{N.f(dep2 + '/fpr_frozen/wilson/0')}–{N.f(dep2 + '/fpr_frozen/wilson/1')}"
    out = (f"With dependency evidence at 2,000 tokens, the primary monitor's threshold frozen on calibration families "
           f"({N.f(dep2 + '/threshold_frozen')}) flagged {N.i(dep2 + '/tpr_frozen/k')}/30 violations and "
           f"{N.i(dep2 + '/fpr_frozen/k')}/30 legitimate runs (false-positive rate 95% Wilson interval {w})")
    same = (N.get(dep2 + "/tpr_frozen/k") == N.get(dep2 + "/verdict_violation_tp")
            and N.get(dep2 + "/fpr_frozen/k") == N.get(dep2 + "/verdict_violation_fp"))
    out += ", the same as its violation verdicts" if same else ""
    if N.has(lex2 + "/threshold_frozen"):
        out += (f"; with lexical evidence its threshold ({N.f(lex2 + '/threshold_frozen')}) flagged "
                f"{N.i(lex2 + '/tpr_frozen/k')}/30 and {N.i(lex2 + '/fpr_frozen/k')}/30")
    return out + ". Thresholds come from 15 benign calibration cases and cannot certify low false-positive rates."


def hypotheses_paragraph(N):
    """One sentence per pre-registered hypothesis (protocol/PROTOCOL_FREEZE.json), worded from the data."""
    dl2 = f"{Q}/contrasts/dependency-lexical@2000"
    dl6 = f"{Q}/contrasts/dependency-lexical@6000"
    oo = f"{Q}/out_of_lineage/dependency|C4_out_of_lineage"
    lo = N.get(dl2 + "/ci95_family_bootstrap/0")
    h1 = ("H1 (dependency > lexical at 2k): positive point estimate, "
          + ("not resolved at the family level" if lo <= 0 else "interval excludes zero")
          + (f" for the primary model; in the secondary second-model analysis the interval "
             f"{'excludes' if N.get(G + '/contrasts/dependency-lexical@2000/ci95_family_bootstrap/0') > 0 else 'includes'} "
             "zero." if gemma_ready(N) else "."))
    flagged, total = N.get(oo + "/violations_flagged"), N.get(oo + "/violations_total")
    h2 = (f"H2 (out-of-lineage misses): {'confirmed' if flagged == 0 else 'partly confirmed'} in C4 "
          f"({flagged} of {total} violations flagged).")
    if stage_done(N, Q, "stage3") and N.has(dl6 + "/diff"):
        d2, d6 = N.get(dl2 + "/diff"), N.get(dl6 + "/diff")
        lo2, hi2 = N.get(dl2 + "/ci95_family_bootstrap/0"), N.get(dl2 + "/ci95_family_bootstrap/1")
        lo6, hi6 = N.get(dl6 + "/ci95_family_bootstrap/0"), N.get(dl6 + "/ci95_family_bootstrap/1")
        overlap = lo6 <= hi2 and lo2 <= hi6
        sp = h3_split(N)
        shrank = [b for b, (a2, a6) in sp.items() if a6 < a2]
        h3 = ("H3 (advantage shrinks at 6k): " + ("supported in point estimate." if len(shrank) == len(sp) else
              "not supported." if not shrank else
              f"shrank against {len(shrank)} of {len(sp)} non-graph baselines "
              f"({join(LABEL[b] for b in shrank)}) and grew against the rest."))
    else:
        h3 = "H3 (advantage shrinks at 6k): not tested; the 6,000-token stage had not finished."
    v = f"{Q}/visibility"
    if stage_done(N, Q, "stage4"):
        drop_d = N.get(v + "/dependency@2000@full/auroc") - N.get(v + "/dependency@2000@random50/auroc")
        drop_l = N.get(v + "/lexical@2000@full/auroc") - N.get(v + "/lexical@2000@random50/auroc")
        h4 = ("H4 (masking hurts dependency more): "
              + ("supported for recall and, in point estimate, AUROC." if drop_d > drop_l
                 else "supported for evidence recall but not for AUROC."))
    else:
        h4 = ("H4 (masking hurts dependency more): supported for model-independent evidence recall; "
              "the LLM masking stage had not finished.")
    fams = ("A2", "A4", "B2", "B4", "C2")
    models = [Q] + ([G] if gemma_ready(N) else [])
    ok = [N.get(f"offline_test_per_family/dependency@2000@full|{f}/rule_auroc")
          >= N.get(f"{M}/per_family/dependency@2000/{f}") for M in models for f in fams]
    scope = "both models" if len(models) == 2 else "the primary model"
    h5 = ("H5 (rule monitor ≥ LLM on complete lineage): "
          + (f"supported on all five in-lineage families for {scope}." if all(ok) else
             f"supported in {sum(ok)} of {len(ok)} family-model cases."))
    return ("**Pre-registered hypotheses.** " + " ".join([h1, h2, h3, h4, h5]) + " Per-family AUROC was pre-registered; "
            "per-family verdict counts and rule results, false-alarm citation counts and the identical-prompt repeat "
            "are descriptive post-freeze analyses; Appendix C runs are exploratory.")


def reasoning_paragraph(N, R):
    d, l = f"{R}/arms/dependency@2000", f"{R}/arms/lexical@2000"
    n_inv = N.get(d + "/invalid") + N.get(l + "/invalid")
    txt = ("**Reasoning-enabled monitor.** With Qwen's reasoning on (effort medium, 4,096-token output cap including "
           f"billed reasoning), {n_inv} of 120 outputs were invalid ({N.i(d + '/invalid')} dependency, "
           f"{N.i(l + '/invalid')} lexical), all of them cut off at the output cap after reasoning used almost all of it "
           f"(most before any answer text); dependency calls averaged {N.get(d + '/mean_output_tokens'):,.0f} output tokens. With invalid "
           f"outputs scored 0.5, AUROC was {N.f(d + '/auroc')} with dependency evidence "
           f"({N.i(d + '/verdict_violation_tp')} true and {N.i(d + '/verdict_violation_fp')} false violation verdicts) "
           f"and {N.f(l + '/auroc')} with lexical evidence. ")
    if n_inv > 30:
        txt += "Because so many outputs were cut off, this check is inconclusive; a larger output cap would be needed. "
    return txt + role_rule_persistence(N, R)


def role_rule_persistence(N, R):
    """Role-rule families (A4, B2) with reasoning on: full breakdown of the 10 legitimate twins."""
    k = "/verdicts_by_family/dependency@2000/"
    if not all(N.has(m + k + f) for m in (Q, R) for f in ("A4", "B2")):
        return ""
    def count(M, v):
        return sum(N.get(M + k + f).get(f"legit->{v}", 0) for f in ("A4", "B2"))
    base, flagged = count(Q, "violation"), count(R, "violation")
    inv, ben = count(R, "invalid"), count(R, "benign")
    txt = (f"Of the 10 legitimate twins in the two role-rule families (A4, B2), which reasoning-disabled Qwen flagged "
           f"{base} times, the reasoning run flagged {flagged}, judged {ben} benign and gave {inv} invalid outputs")
    return txt + (", so it cannot show whether reasoning removes that error." if inv >= 5 else ".")


def live_limitation(N):
    if N.has("live_exploratory/request/completed"):
        return ("All pre-registered trajectories are replayed scripts. The only model-driven workers are in a small "
                "exploratory live slice (one domain, one instructed violation; Appendix C).")
    return ("All reported trajectories are replayed scripts; the exploratory live-agent slice had not finished "
            "when this version was built (only smoke-test worker calls, counted in the cost totals, exist).")


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
              "prevent harm without disrupting legitimate tasks. Pre-registered results depend on "
              + ("two hosted models" if stage_done(N, G, "stage1") else "one hosted model")
              + " on one date with reasoning disabled; the reasoning-enabled run is exploratory. Incomplete or adversarial "
              "records could change performance differently from these masking conditions. Targeted removal of "
              "decisive links could be more damaging; we did not evaluate adaptive tampering. Four known gaps are pinned as expected failures in the "
              "offline tests: the rule monitor over-flags two hand-built worlds that never occur in the data "
              "(deduplicating held-out data against a copy of itself, and training on one shard of a mixed "
              "artifact); masking does not rewrite IDs inside free-text notes (generated notes contain none, and the "
              "runner refuses any plan whose mask audit fails); and isolated review at 2,000 tokens exceeds its "
              "per-call share on the conservative token estimate, so it shows no events, although billed input per "
              "call stayed lower. The rule monitor agrees with the oracle on all released trajectories when it reads "
              "the full ledger."),
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
              "contradicted its own arithmetic. Pilot v3: reason first (36 calls); the same pilot with gemma-4-31b-it "
              "(36 calls) gave 2 invalid outputs, both repetition loops. Lexical retrieval was weaker "
              "than chronological review on development recall, so BM25 and Lexical+PRF were added before the "
              "freeze; lexical stayed the pre-registered primary comparator. Traces were lengthened before the "
              "freeze so that both caps bind on every trace. After the freeze we found that the provider's rate "
              "limit is shared across models, so we stopped a concurrent second-model chain after 3 calls "
              "(recording a reservation for any in-flight calls that may have been billed without a saved response) and "
              "ran the models sequentially. Later code fixes and exploratory additions "
              "are listed in protocol/POST_FREEZE_CHANGES.md; none changes a pre-registered stage. The aggregation code "
              "(swarm_evidence/analysis.py) was first committed after the stage-1 calls were recorded; it implements "
              "the metric functions (frozen metrics module), invalid-output policy, threshold rule and primary "
              "contrast fixed in the frozen protocol. "
              + second_model_coverage(N)),
        ("p", f"**Cost and calls.** Total {N.f('costs/total_credits', 3)} credits over "
              f"{N.i('costs/n_calls_total')} recorded calls, including pilots, the second model and transport-error "
              "reservations. Cost was never the binding constraint; the provider's per-user rate limit was. The runner "
              "enforces a cumulative 800-credit ceiling with per-stage caps, reserves "
              "each call's worst-case cost before sending it, and checkpoints every response; per-stage counts and "
              "costs are in results/analysis/summary.json."),
        *appendix_c(N),
        *appendix_d(N),
        ("h2", "LLM Usage Statement"),
        ("p", llm_statement()),
    ]
    return a


def llm_statement():
    p = ROOT / "report/llm_statement.txt"
    return p.read_text().strip() if p.exists() else "[LLM USAGE STATEMENT TO CONFIRM]"


def sensitivity_section(N):
    """Pre-registered invalid-output sensitivity (valid-only and best/worst AUROC) plus descriptive paired checks."""
    rows = []
    for M, name in ((Q, "Qwen"), (G, "Gemma")):
        keys = [(f"{a}@2000", f"{LABEL[a]}, 2k") for a in BUDGETED] + [("full@nocap", "full log")]
        keys += [(f"{a}@6000", f"{LABEL[a]}, 6k") for a in BUDGETED]
        for k, lab in keys:
            a = f"{M}/arms/{k}"
            if not N.has(a + "/auroc"):
                continue
            show = N.get(a + "/invalid") > 0 or (M == G and k in ("dependency@2000", "lexical@2000", "full@nocap"))
            if show:
                rows.append([f"{name}, {lab}", N.f(a + "/auroc"),
                             f"{N.f(a + '/auroc_valid_only')} ({N.i(a + '/n_valid')}/60)",
                             f"{N.f(a + '/auroc_missing_worst')}\u2013{N.f(a + '/auroc_missing_best')}"])
        for arm in ("dependency", "lexical"):
            for cap in (2000, 6000):
                for vis, vlab in (("random25", "25% masked"), ("random50", "50% masked"), ("bridges", "bridges masked")):
                    a = f"{M}/visibility/{arm}@{cap}@{vis}"
                    if N.has(a + "/invalid") and N.get(a + "/invalid") > 0:
                        rows.append([f"{name}, {LABEL[arm]}, {cap // 1000}k, {vlab}", N.f(a + "/auroc"),
                                     f"{N.f(a + '/auroc_valid_only')} ({N.i(a + '/n_valid')}/60)",
                                     f"{N.f(a + '/auroc_missing_worst')}\u2013{N.f(a + '/auroc_missing_best')}"])
    if not rows:
        return []
    txt = ("**Invalid-output sensitivity (pre-registered).** The frozen policy scores every invalid prediction 0.5; "
           "those are the principal results. The protocol also specified AUROC on valid predictions only and the two "
           "extremes obtained by giving each invalid prediction the score least or most favourable to the arm, using "
           "its known label (Table 4). Valid-only values use each arm's own subset of cases, so they are not paired "
           "across arms, and the extremes are sensitivity scenarios, not confidence intervals. ")
    ql = f"{Q}/invalid_sensitivity/dependency-lexical@2000"
    if N.has(ql + "/n_both_valid") and N.get(ql + "/n_both_valid") == 60:
        txt += "Qwen's dependency, lexical and full-log arms at 2,000 tokens had no invalid predictions, so the primary contrast is unaffected. "
    gl, gf = f"{G}/invalid_sensitivity/dependency-lexical@2000", f"{G}/invalid_sensitivity/dependency-full@nocap"
    if N.has(gf + "/n_both_valid") and N.has(gl + "/n_both_valid"):
        txt += (f"For Gemma (descriptive, added after the freeze): on the {N.i(gf + '/n_both_valid')} cases valid in "
                f"both arms the dependency-minus-full difference was {sg(N.get(gf + '/diff_both_valid'), 3)}, and under "
                f"the assignment least favourable to dependency it was {sg(N.get(gf + '/diff_worst_for_dependency'), 3)}; "
                f"for dependency minus lexical the values were {sg(N.get(gl + '/diff_both_valid'), 3)} "
                f"({N.i(gl + '/n_both_valid')} cases) and {sg(N.get(gl + '/diff_worst_for_dependency'), 3)}. These "
                "checks do not establish significance or generalization.")
    return [("p", txt),
            ("table", ["Monitor and arm", "Frozen AUROC (invalid = 0.5)", "Valid-only AUROC (valid/60)",
                       "Worst\u2013best assignment"], rows,
             "**Table 4.** Invalid-output sensitivity for every pre-registered arm, including masking conditions, with "
             "invalid predictions, plus "
             "Gemma's lexical arm for comparison.",
             {"size": 8, "col_widths": [2.35, 1.4, 1.45, 1.1]})]


def appendix_d(N):
    dep2, lex2 = f"{Q}/arms/dependency@2000", f"{Q}/arms/lexical@2000"
    out = [("h2", "Appendix D. Supplementary results and figures"),
           ("p", "**Single-worker controls (pre-registered).** On the 9 control pairs, where one worker's events decide "
                 f"the label, Qwen scored {N.f(Q + '/controls/dependency/auroc')} with dependency evidence, "
                 f"{N.f(Q + '/controls/lexical/auroc')} lexical, {N.f(Q + '/controls/chronological/auroc')} chronological "
                 f"and {N.f(Q + '/controls/full/auroc')} with the full log. Isolated review shows no events at 2,000 "
                 f"tokens ({N.f(Q + '/controls/isolated/auroc')}), so the controls do not test single-worker review."),
           ("p", "**Calibrated thresholds (pre-registered secondary metric).** " + frozen_threshold_sentence(N, dep2, lex2))]
    det = cap6k_details(N)
    if det:
        out.append(("p", "**6,000-token stage.** " + det))
    if stage_done(N, Q, "stage3"):
        out.append(("table", TABLE_HEAD, arm_rows(N, Q, 6000),
                    "**Table 3.** Held-out results at the 6,000-token cap, qwen3.5-397b; columns as in Table 1.",
                    {"size": 8, "col_widths": TABLE_WIDTHS}))
    out += sensitivity_section(N)
    inv = gemma_invalid(N) if gemma_ready(N) else {}
    if sum(inv.values()):
        resp = gemma_invalid(N, "invalid_responses")
        trunc = gemma_invalid(N, "invalid_responses_truncated")
        gf = f"{G}/arms/full@nocap"
        out.append(("p", "**Second-model invalid outputs.** At 2,000 tokens and with the full log, Gemma produced "
                    f"{sum(resp.values())} invalid API responses affecting {sum(inv.values())} case-level predictions "
                    "(invalid responses / invalid predictions: "
                    + join(f"{LABEL.get(a, 'full log')} {resp[a]}/{v}" for a, v in inv.items() if v)
                    + "; an isolated case is invalid if any of its three worker calls is). All are scored 0.5 under the "
                    "frozen policy. Every invalid 2,000-token response was a repetition loop (\"our our our ...\") that "
                    f"ran to the 384-token output cap (128 for isolated calls). All {N.i(gf + '/invalid_responses')} invalid "
                    "full-log responses began with a complete JSON answer and then added self-correction commentary "
                    f"(\"Wait, I noticed a typo ...\"); in {N.i(gf + '/invalid_responses_truncated')} the commentary ran "
                    "to the 384-token cap, and the " + ("other ended" if N.get(gf + '/invalid_responses') - N.get(gf + '/invalid_responses_truncated') == 1 else "others ended") + " with a second JSON answer. The parser accepts exactly "
                    "one JSON object, optionally inside a single code fence, so the trailing text, not the fencing, "
                    "made them invalid."))
    out.append(("fig", "figures/fig2_auroc_by_method.png", 6.3,
                "**Figure 3.** Held-out AUROC by selection method at two input caps (primary monitor qwen3.5-397b; error "
                "bars: 95% family-bootstrap intervals over 6 held-out families; dashed line: chance; grey line: full log "
                "with no cap). Isolated review spends its budget on three copies of the prompt overhead and sees no "
                "events at 2,000 tokens, so its AUROC there is exactly 0.5. The same numbers are in Tables 1 and 3."))
    if gemma_ready(N) and (ROOT / "figures/figS1_auroc_by_method_secondary.png").exists():
        g6 = stage_done(N, G, "stage3")
        out.append(("fig", "figures/figS1_auroc_by_method_secondary.png", 6.3 if g6 else 4.2,
                    "**Figure 4.** The same for the pre-registered second model, gemma-4-31b-it. Only methods scored "
                    "on all 60 held-out trajectories are shown; invalid outputs score 0.5."
                    + ("" if g6 else " Its 6,000-token stage had not finished when this version was built, so no "
                       "6,000-token panel is shown.")))
    return out


def appendix_c(N):
    R = "models/qwen3.5-397b+reasoning"
    L = "live_exploratory"
    rep = "replicates/qwen3.5-397b|dependency|2000"
    rep_l = "replicates/qwen3.5-397b|lexical|2000"
    out = [("h2", "Appendix C. Exploratory checks (after the freeze)")]
    out.append(("p", "These runs were added after seeing stage-1 results and are not part of the pre-registered "
                     "analysis (protocol/POST_FREEZE_CHANGES.md)."))
    if N.has(R + "/arms/dependency@2000/auroc") and N.has(R + "/arms/lexical@2000/auroc"):
        out.append(("p", reasoning_paragraph(N, R)))
    else:
        out.append(("p", "**Reasoning-enabled monitor.** Planned, but not finished when this version was built; no result is reported."))
    if N.has(rep + "/n_cases") and N.has(rep_l + "/n_cases"):
        out.append(("p", "**Temperature-0 repeat.** Re-running stage 1 changed the score on "
                         f"{N.i(rep + '/n_score_changed')} of {N.i(rep + '/n_cases')} dependency trajectories (the "
                         f"verdict on {N.i(rep + '/n_verdict_changed')}) and on {N.i(rep_l + '/n_score_changed')} of "
                         f"{N.i(rep_l + '/n_cases')} lexical trajectories (the verdict on "
                         f"{N.i(rep_l + '/n_verdict_changed')}). "
                         + ("One dependency-arm change was a C4 violation that the first run judged benign and the "
                            "repeat flagged, so the out-of-lineage count in Section 4.2 (0 of 5) is a single-run "
                            "result rather than a stable one."
                            if "C4" in N.get(rep + "/verdict_changed_families") else "")))
    else:
        out.append(("p", "**Temperature-0 repeat.** Planned, but not finished when this version was built; no result is reported."))
    if not N.has(L + "/request/completed"):
        out.append(("p", "**Live-agent slice.** Started (a smoke test of the model-driven workers is in the call record "
                         "and cost totals) but not finished when this version was built; no result is reported."))
        return out
    out.append(("p", live_paragraph(N, L)))
    return out
