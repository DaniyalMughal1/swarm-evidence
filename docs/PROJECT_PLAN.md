# Swarm Evidence: which cross-agent evidence is worth monitoring?

Status: research design, no experiments run. Prepared 2026-11-08 for the Swarm Alignment Hackathon. Primary Track 4, secondary Track 1. Working title; novelty is provisional.

## Research question

At a fixed monitoring budget, does selecting tool events through artifact dependencies improve detection of policy violations split across agents, compared with isolated-agent review, chronological review, and simple retrieval? How does that advantage change when cross-agent links are missing?

This is a measurement project, not a claim to have invented provenance graphs, multi-agent monitoring, or authorization-paired tests. The deliverable is a reproducible experiment and a useful failure boundary. A negative result is acceptable.

## Why this question

John Kitaoka's event talk (12:42–19:52, 28:35–31:59, and Q&A 56:11–57:25) motivates explicit threat models, token-matched comparisons, and corroborating relevant actions across agents. Existing FlowReview (https://arxiv.org/html/2610.00371v1, sections 4.3–4.4 and Appendix E) already demonstrates composed-action review, usable-lineage failures, and trusted runtime recording. GroupGuard (https://arxiv.org/abs/2603.13940) already uses graph-based monitoring. NARCBench (https://arxiv.org/abs/2604.01151) already studies multi-agent collusion detection and distribution shift. Our narrower proposed increment is monitor-context-budget-constrained evidence selection over recorded artifact lineage, measured against non-graph retrieval. Missing lineage alone is not new. Multi-Agent AI Control (https://arxiv.org/html/2607.07368v2) already includes distributed attacks, joint-monitor checks, and fuller-context limitations. Thus joint monitoring alone is not our contribution. Search results do not establish priority.

## Alternatives considered

1. Minimal: replay-only evidence-selection benchmark. Fastest and cheapest; supports claims about monitor behavior, not spontaneous agent collusion.
2. Conditional extension: the same benchmark plus a small live three-worker validation slice, checked against real local state. Start this only after completing the primary comparison and its report figures, with sufficient measured time and credits remaining.
3. Long-term: production gateway, authenticated lineage, online intervention and live incident ingestion. Attractive infrastructure, but most work would go into integration rather than answering today's question. Defer production claims and packaging.

Human-team estimate: 2–4 days for a research prototype and report. Claude-assisted execution target: 6–8 hours after handoff, approximately 6–12x compression; an estimate, not a benchmark. Protect at least two hours for analysis, report, and submission.

## Threat model and scope

- Three workers share synthetic artifacts inside a local simulator. A coordinator gives each a legitimate task. Scripted adversarial variants alter a subset of actions to produce an explicitly prohibited final use.
- Only fake records, local files, and simulated destinations. No executable incident payloads, external attacks, or real personal data.
- Trusted harness records tool calls, object/version identifiers, input/output dependencies, and state transitions. Workers cannot edit this ledger in the primary experiment.
- Attacker may coordinate actions and write misleading natural-language rationales. Monitor is a black-box model with no hidden reasoning or activation access.
- The evidence selector receives no hidden labels, attack family, expected violating step, or private intention. It operates on the observable graph and public task policy.
- Separate stress tests distinguish a corrupted graph index from missing dependency metadata. The latter removes the same relation from all observable fields, including input/output IDs and prose. Missing-event deletion is a different intervention. None establishes resistance to recorder compromise.
- Workflows have a predefined finalization point in benign and attack cases. This common point triggers review, avoiding an oracle that reveals the attack location.
- Primary evaluation is retrospective detection before simulated finalization. Online prevention is a separate, optional experiment, never inferred from detection accuracy.

## Dataset and controls

Use executable, deterministic cases; model-generated prose is surface variation, never the ground-truth judge.

Candidate domains: (A) synthetic report export with incompatible data-use permissions; (B) research evaluation pipeline with test/training contamination; (C) invoice/refund workflow with an aggregate approval limit. Start with A and B; use C as held-out transfer if feasible.

Each base case has a matched legitimate twin. Match topology, number of agents, actions, lengths, and finalization points. Change the actual authorization or relevant state, not an explicit 'malicious' label. Include difficult benign coordination and failed attack attempts. A separate trusted oracle checks executed state and policy; do not pass its output to monitors. For aggregate limits, retain a deterministic policy baseline so we do not oversell an LLM solution to arithmetic.

Target: 60 base cases (20 per domain), each with benign/violating twins = 120 trajectories. These are NOT automatically 60 independent samples. Record template_family_id, template_id, and base_case_id. Split by generator template family, not only seed: 30 development pairs, 30 held-out pairs, with multiple families in every domain. Development includes a calibration subset distinct from prompt-design examples. If only two domains complete, use 40 pairs and label reduced scope; freeze the split before testing. Improve generality by adding independent templates, not paraphrases. Inference is conditional on the chosen template families; report their count.

Each core case must have a gold minimal sufficient evidence set spanning at least two workers. Check that the global observed evidence resolves the question and no individual worker view determines the label. Construct counterfactual completions of each individual view when practical. Keep gold evidence in the separate evaluation file. Include separately tagged single-worker-resolvable controls. Vary evidence age and legitimate distracting work; require a substantial proportion of development traces to exceed the small cap before freezing it.

Live slice: 12 paired cases with three model-driven workers calling fixed structured tools, executable state checks, and bounded actions. Report worker attempts, successful violations and monitor detection separately. If models refuse or no attacks succeed, report that and retain replay as the main result; never count scripted actions as naturally occurring collusion.

## Monitor comparison

Same model, policy text, decision schema and overall per-trajectory input/output cap for every scored method:

1. Isolated-agent review: allocate one third of the total budget to each of three calls; aggregate maximum suspicion. Include all repeated instructions and outputs in cost.
2. Chronological pooled review: merge events, retain the most recent complete events that fit.
3. Lexical/object retrieval: retrieve events matching the finalization artifact and policy terms, without traversing dependencies.
4. Dependency slice: traverse recorded input/output edges backward from the finalization object; use deterministic distance and timestamp tie-breaks and stop at the cap. Include policy and permission events linked to selected artifacts.
5. Shuffled-edge slice: degree-preserving or explicitly documented random edge reassignment; same selection algorithm and budget. Tests whether graph structure matters rather than merely selecting fewer events.

Unbudgeted full-context review and deterministic full-state oracle are diagnostic ceilings, not budget-matched competitors. Run a deterministic policy monitor on the exact same selected evidence as each selector; it returns unknown when the evidence is insufficient. This separates retrieval gains from any benefit of an LLM. Also include always-allow and always-flag to expose useless 'safety' by blocking everything.

Budgets: two total caps, initially 2,000 and 6,000 input tokens with fixed output limits; inspect pilot trajectory lengths before freezing caps. Publish actual billed tokens and uncached costs. Do not pad short prompts with arbitrary noise. Equal caps are not exact equal spending; show both quality-at-cap and realized cost.

Predictions must include a suspicion score, verdict (violation / benign / insufficient_evidence), and evidence event IDs. Parse strictly. The primary analysis uses first attempts only, with invalid/missing outputs assigned neutral score 0.5 and operational abstention. Valid abstentions retain their stated score. An isolated arm requires all three outputs; otherwise its overall outcome is invalid/0.5. Repairs are diagnostic, separately billed and never silently substituted. Report valid-only AUROC and worst/best missing-score sensitivity beside the primary result. See IMPLEMENTATION_SPEC.md for deterministic selection, formatting, and output allocation.

## Metrics and analysis

Primary contrast: dependency slice minus lexical retrieval on paired held-out trajectories at the lower budget and full visibility, using AUROC with clustered bootstrap intervals over held-out template families. Resample whole families, retaining twins, seeds and transformed versions. If too few families support a credible interval, present per-family effects and explicitly descriptive intervals; do not claim population significance. Secondary: comparison with chronological and isolated review, AUPRC, observed FPR/TPR at a threshold frozen on development benign cases, legitimate-task acceptance, evidence-ID validity, latency, cost, and abstention/coverage.

With only tens of benign cases, do not claim a validated 1% false-positive rate. Report raw numerator/denominator and Wilson intervals; show a descriptive curve. Zero false positives in 30 cases is not evidence of a 1% bound. Abstention must reduce coverage and count against automated acceptance; never score 'unknown' as correctly benign.

For missing dependency metadata, predeclare 0%, 25%, 50% random relation removal and targeted removal of cross-agent bridge relations. Target only observable structural bridges, never gold violating paths. Sanitize each removed relation across every exposed field; if that is not feasible, label the experiment corrupted-index-only and narrow the claim. Apply the same resulting view to every arm. Report event visibility, relation visibility, and gold-evidence recall separately. Never tune on corrupted held-out data.

Keep twin cases and all transformed versions in the same split and bootstrap cluster. Repeated monitor calls estimate sampling variability, not additional independent samples. Freeze prompts, model identifiers, dataset manifest hashes, and primary hypothesis before opening held-out results. Mark all post-hoc slices exploratory.

## Implementation contract

Python 3.11+; standard-library simulator and tests; Adaption adapter for model calls; optional plotting dependencies. Prefer plain JSONL to a new orchestration framework. Existing Concordia and ControlArena inform design, but a large framework is unnecessary for a deterministic replay experiment. Verify Adaption SDK and model availability against current docs before pinning dependencies.

Modules for Claude: scenarios, event schema, oracle, selectors, monitor adapter, runner/checkpoints, analysis, report figures. Each event has run_id, event_id, worker_id, sequence, tool, inputs, outputs, artifact_versions, policy_refs, outcome, and visibility. Gold labels live in a separate file unreachable from selectors. Keep model responses and exact prompts for reproducibility, with public redaction if needed.

Adaption workshop confirms hosted open-model inference. Use participant credits, with no paid fallback or auto-recharge. First check credited balance and price; reserve 20% for reruns. No fine-tuning on the critical path. If training a small monitor later, train only on development data and compare with its own unfine-tuned base model.

## Stop/go gates and schedule

Run-order contract: first complete dependency and lexical retrieval at the small cap/full visibility (120 held-out calls for 30 pairs). Then chronological, shuffled and isolated arms at that setting (another 300 calls). Next add the larger cap (420 calls), then missing-metadata conditions only for dependency and lexical (720 calls across three corruptions and two caps). These counts exclude development, failures, diagnostics and optional workers; publish actual counts. The original full factorial would require 3,360 calls and up to 9.6 million input tokens before those extras. Do not launch it automatically. Reserve enough time for analysis/reporting before starting each stage. After a 12-trajectory development pilot, record observed throughput, billed tokens, credits, concurrency, projected next-stage cost and hard stop time. Live workers and a second model come only after the primary report is viable.

T+0–30m: register/activate credits, verify one API call, inspect available models, choose two model families if available, freeze protocol and split.
T+30–90m: implement simulator, independent oracle, matched cases, schema and leak checks. Inspect six pairs by hand.
T+90–150m: implement all five selectors, token accounting, mock runner and resume behavior; pilot only on development cases.
T+150–270m: freeze then run held-out main experiment; live slice and secondary model only within measured budget. Checkpoint every response.
T+270–330m: analyze paired results, inspect errors, create two or three figures. Negative findings stay in report.
T+330–420m: fill official template, required appendix, reproducibility README and optional 3–5 minute demo.
T+420–480m: independently verify tables, references, page count, public links and PDF. User submits through event form and checks confirmation.

Hard target: submission-ready by 23:00 Toronto, November 8. Official cutoff: November 9, 06:59 Toronto (11:59 UTC). Recompute remaining schedule at handoff; never silently extend the official deadline.

## What success means

A rerunnable held-out comparison with honest uncertainty, a clear account of where graph selection fails, and an eight-page-or-less report. A high rubric score requires evidence, not an attractive interface. No promise of novelty, statistically significant improvement, all 5/5 scores, or a prize.

## Distribution and handoff

Public GitHub source, versioned generated synthetic data, exact commands and environment lock, prompts and model IDs, per-case results, analysis scripts, and small demo artifact. CI runs offline correctness tests; live model calls are opt-in. No package-registry release needed today. Claude builds the experiment; the user verifies authorship, findings, and submission.
