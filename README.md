# Swarm Evidence

**Does a budget-limited monitor catch cross-agent policy violations more often when it reads the evidence that recorded artifact dependencies point to?**

Swarm Evidence is a controlled experiment built for the [Swarm Alignment Hackathon](https://apartresearch.com/sprints/swarm-alignment-2026), November 2026. Primary track: Multi-Agent Oversight and Control. Secondary track: Sandboxes and Testbeds. The report PDF is at [report/swarm_evidence_report.pdf](report/swarm_evidence_report.pdf).

In plain terms: one AI worker registers data under a restrictive license, a second transforms and merges it, and a third stages the merged file for export. Each step is allowed locally, but the composition violates policy. A monitor cannot afford to read every event, so it has to choose what to read. We compare seven ways of choosing at a fixed token budget, scored by an LLM monitor and by a deterministic checker given the same evidence.

## Findings

- **Retrieval.** Walking recorded dependencies backward from the action under review kept almost all of the decisive evidence at a 2,000-token cap. Lexical, BM25, lexical+PRF, chronological and shuffled-graph selection kept a quarter to about a third of it. Isolated per-worker review saw no events at this cap, because its repeated prompt overhead used up each worker's share.
- **Detection.** With the primary monitor (Qwen 3.5 397B) at 2,000 tokens, held-out AUROC was 0.75 with dependency evidence and 0.55 with lexical retrieval. This pre-registered primary contrast is **not resolved**: only 6 held-out template families were tested, and the family-bootstrap interval for the difference includes zero. With the pre-registered second model (Gemma 4 31B) the same comparison was 0.92 versus 0.53, an interval that excludes zero. That is a secondary result; with six families these intervals are descriptive and do not establish a general advantage.
- **More context did not help Qwen.** Reading the whole log without a cap (about 8× the tokens) scored 0.55 with Qwen, and most of its false alarms cited unrelated legitimate work. This is one model in one synthetic setting, not evidence that more context generally hurts: Gemma's whole-log score (0.78) was lower than its dependency score but well above Qwen's. At 6,000 tokens the non-graph baselines saw more evidence, but it brought false alarms. The gap to dependency selection widened against three of the four non-graph baselines and narrowed only against lexical+PRF, so the pre-registered prediction that it would shrink (H3) was not supported.
- **Judgment depended on the model.** On the *same* selected evidence, a short deterministic checker made no false alarms, while Qwen flagged every legitimate twin in the two families where a policy clause says which inputs carry records (join and deduplication *references*). Gemma flagged none of them, so this failure is model-specific.
- **The boundary is predictable.** Dependency selection misses evidence that is not an ancestor of the target (for example, an earlier payment of the same invoice). Masking dependency metadata cut its evidence recall from 0.96 to 0.44–0.65 and the LLM's AUROC from 0.75 to 0.53–0.63, while lexical retrieval was barely affected.

Exact numbers, generated from saved records:

<!-- results:start -->
**qwen3.5-397b, 2,000-token cap** (60 held-out trajectories, 6 unseen families)

| Method | AUROC (family 95% CI) | Violation verdicts TP/FP | Abstain | Invalid | Gold recall | Billed input tokens | Over cap | Rule monitor AUROC |
|---|---|---|---|---|---|---|---|---|
| Dependency | 0.75 (0.50–0.95) | 25/12 | 0 | 0 | 0.96 | 1155 | 0 | 0.92 |
| Lexical | 0.55 (0.52–0.61) | 0/0 | 59 | 0 | 0.25 | 1653 | 0 | 0.50 |
| Chronological | 0.53 (0.47–0.61) | 3/3 | 51 | 0 | 0.36 | 1634 | 0 | 0.50 |
| BM25 | 0.56 (0.52–0.62) | 1/0 | 59 | 0 | 0.34 | 1583 | 0 | 0.50 |
| Lexical+PRF | 0.45 (0.33–0.54) | 0/0 | 60 | 0 | 0.27 | 1660 | 0 | 0.50 |
| Shuffled graph | 0.46 (0.37–0.50) | 0/0 | 57 | 0 | 0.25 | 1133 | 0 | 0.50 |
| Isolated (3 calls) | 0.50 (0.50–0.50) | 0/0 | 60 | 0 | 0.00 | 1328 | 0 | 0.50 |

**qwen3.5-397b, 6,000-token cap** (60 held-out trajectories, 6 unseen families)

| Method | AUROC (family 95% CI) | Violation verdicts TP/FP | Abstain | Invalid | Gold recall | Billed input tokens | Over cap | Rule monitor AUROC |
|---|---|---|---|---|---|---|---|---|
| Dependency | 0.77 (0.59–0.93) | 25/12 | 0 | 0 | 0.96 | 1155 | 0 | 0.92 |
| Lexical | 0.44 (0.28–0.57) | 9/13 | 28 | 0 | 0.70 | 5534 | 4 | 0.62 |
| Chronological | 0.47 (0.31–0.58) | 9/10 | 41 | 0 | 0.64 | 5478 | 0 | 0.58 |
| BM25 | 0.48 (0.38–0.62) | 7/7 | 41 | 1 | 0.61 | 5446 | 4 | 0.60 |
| Lexical+PRF | 0.60 (0.50–0.68) | 10/5 | 37 | 0 | 0.64 | 5528 | 2 | 0.62 |
| Shuffled graph | 0.51 (0.44–0.58) | 1/0 | 58 | 0 | 0.25 | 1133 | 0 | 0.50 |
| Isolated (3 calls) | 0.50 (0.50–0.50) | 1/1 | 48 | 10 | 0.53 | 4879 | 0 | 0.50 |

Full log, no cap (qwen3.5-397b): AUROC 0.55, mean 9327 billed input tokens, 0 invalid outputs.

Primary contrast (qwen3.5-397b, 2k, full visibility): dependency − lexical AUROC = +0.20 (paired family bootstrap 95% CI -0.07 to +0.41; 4 of 6 families favour dependency).

**gemma-4-31b-it, 2,000-token cap** (60 held-out trajectories, 6 unseen families)

| Method | AUROC (family 95% CI) | Violation verdicts TP/FP | Abstain | Invalid | Gold recall | Billed input tokens | Over cap | Rule monitor AUROC |
|---|---|---|---|---|---|---|---|---|
| Dependency | 0.92 (0.76–1.00) | 24/0 | 0 | 5 | 0.96 | 1190 | 0 | 0.92 |
| Lexical | 0.53 (0.50–0.59) | 0/0 | 43 | 0 | 0.25 | 1705 | 0 | 0.50 |
| Chronological | 0.48 (0.43–0.50) | 0/0 | 42 | 2 | 0.36 | 1686 | 0 | 0.50 |
| BM25 | 0.53 (0.50–0.57) | 0/0 | 43 | 0 | 0.34 | 1640 | 0 | 0.50 |
| Lexical+PRF | 0.47 (0.40–0.53) | 0/0 | 47 | 0 | 0.27 | 1712 | 0 | 0.50 |
| Shuffled graph | 0.52 (0.50–0.58) | 0/0 | 56 | 0 | 0.25 | 1168 | 0 | 0.50 |
| Isolated (3 calls) | 0.48 (0.45–0.50) | 0/0 | 58 | 2 | 0.00 | 1367 | 0 | 0.50 |

Full log, no cap (gemma-4-31b-it): AUROC 0.78, mean 9628 billed input tokens, 8 invalid outputs.

Same contrast, secondary model (gemma-4-31b-it, 2k, full visibility): dependency − lexical AUROC = +0.39 (paired family bootstrap 95% CI +0.17 to +0.50; 5 of 6 families favour dependency).

Total model spend: 6.607 Adaption credits over 4138 recorded calls (pilots, both models, exploratory runs and transport-error reservations).
<!-- results:end -->

## What is in the repository

| Path | Contents |
|---|---|
| `swarm_evidence/world.py`, `scenarios.py`, `oracle.py` | Deterministic three-worker simulator in three domains (export permissions, training contamination, payment batches), 12 template families plus 3 single-worker controls, matched twins, and an oracle that labels from hidden state |
| `swarm_evidence/dataset.py` | Generation and the composition-validity gate: opposite labels, identical twin structure, rule/oracle agreement, counterfactual worker views, and gold minimal evidence spanning at least 2 workers |
| `swarm_evidence/selection.py` | Seven budgeted selectors: dependency, lexical, BM25, lexical+PRF, chronological, shuffled graph, isolated; plus an uncapped full log |
| `swarm_evidence/rules_monitor.py` | Deterministic monitor over the *selected* events only (violation / benign / unknown) |
| `swarm_evidence/visibility.py` | Missing-dependency-metadata masking (random 25% / 50%, cross-worker bridges), with an audit |
| `swarm_evidence/adaption_monitor.py`, `runner.py` | Adaption-hosted LLM monitor with strict parsing; SQLite-checkpointed runner with a hard cumulative credit ceiling, per-stage caps, rate pacing and logged retries |
| `swarm_evidence/analysis.py`, `figures.py`, `metrics.py` | AUROC/AUPRC, family-clustered bootstrap, Wilson intervals, frozen thresholds, tables and figures |
| `data/` | Released synthetic data. `observed/` is what monitors may see, `manifest/` holds splits, `eval/` holds labels, gold evidence and gate results (evaluation only) |
| `protocol/PROTOCOL_FREEZE.json` | The pre-registered protocol (hashes of code, data and prompts), committed before any held-out call. `POST_FREEZE_CHANGES.md` lists every later change |
| `results/calls/` | Every model call: run key, stage, arm, cap, visibility, prompt hash, input hash, shown event IDs, raw and parsed output, billed tokens, cost, latency |
| `results/analysis/`, `results/offline/`, `figures/` | Regenerated summary, tables, predictions, model-independent results and figures |
| `report/` | Official Apart template, report builder, report content, PDF, and `numbers_used.json` for the number audit |
| `tests/` | 185 offline stdlib tests (4 expected failures pin documented gaps) |
| `docs/`, `research/` | Research pack: event brief, 32 readings, 11 recordings, related work, plan and spec |

## Reproduce

Requires Python 3.11+. Plotting, PDF and report building need `matplotlib`, `python-docx` and `pymupdf`; live runs need the `adaption` SDK (version 0.19.0 was used).

```bash
python3 -m unittest discover -s tests -v
```

```bash
python3 -m swarm_evidence generate
```

```bash
python3 -m swarm_evidence validate
```

```bash
python3 -m swarm_evidence offline --split test --caps 2000,6000 --visibility full,random25,random50,bridges
```

```bash
python3 -m swarm_evidence analyze
```

`generate` rebuilds byte-identical data files (a test checks this). `validate` reports the stored validity-gate results and re-runs the leakage and mask audits. `analyze` regenerates every table and figure from `results/calls/`. `python3 report/build_report.py` rebuilds the PDF; it needs LibreOffice. `python3 -m swarm_evidence audit-report` checks every result value the report draws from the summary against it (fixed design numbers typed into the text are not covered).

Live model calls are opt-in. Put `ADAPTION_API_KEY`, `ADAPTION_MODEL` and `SWARM_MAX_CREDITS` in a local `.env` (gitignored), then run a stage, for example:

```bash
python3 -m swarm_evidence run --stage stage1 --stage-budget 5 --rpm 24
```

Completed calls are skipped on resume. `scripts/run_primary_chain.sh` runs the primary model's pre-registered stages in order; `scripts/run_followup_chain.sh` runs the second model's stages and the labelled exploratory checks.

## Honest scope

- The setting is synthetic and scripted: three known workers, a trusted complete recorder, and a common finalization point. These results do not cover unknown swarms, tampered logs or emergent collusion.
- Six held-out template families (30 matched pairs) give wide, descriptive intervals. Seeds within a family are not independent mechanisms.
- The rule monitor was written with knowledge of the tool semantics. It shows what structured evidence permits; it is not a deployable detector.
- Two hosted models were tested at temperature 0. The primary model (Qwen 3.5 397B) ran with reasoning disabled. Its role-rule errors are specific to that model in this setting; the second model (Gemma 4 31B) did not make them. Gemma's stronger result is secondary and rests on the same six families.
- The full-log result is one model in one synthetic setting. It does not show that more context generally makes monitoring worse; Gemma's full-log score (0.78) was lower than its dependency score (0.92) but well above Qwen's 0.55.
- The exploratory reasoning-enabled run is inconclusive: 71 of 120 outputs were cut off at the 4,096-token output cap before an answer was written.
- All pre-registered trajectories are replayed scripts. A small exploratory live slice (12 seeds × 2 conditions, one domain, an instructed violation) used model-driven workers; there the worker disclosed the restricted table in its notes, which makes detection easier.
- Known gaps: isolated review sees no events at 2,000 tokens; 10 calls at 6,000 tokens billed slightly over the cap; invalid outputs are scored 0.5 and counted; four expected-failure tests pin documented gaps (rule-monitor over-flagging in two hand-built worlds, IDs inside notes not masked, isolated per-call budget). See `protocol/POST_FREEZE_CHANGES.md` for every change after the freeze.

## Prior work and provenance

Closely related work already covers much of this ground: composed-flow authorization with lineage (FlowReview, arXiv:2610.00371), graph-based collusion defense (GroupGuard, arXiv:2603.13940), distributed attacks against per-instance monitors (arXiv:2607.07368), and collusion detection from model internals (arXiv:2604.01151). Our increment is the controlled comparison of evidence-selection policies at a fixed context budget and the boundary it measures. See [docs/RELATED_WORK.md](docs/RELATED_WORK.md).

All code and data were written during the sprint on November 8, 2026; no earlier project code was reused. Codex assisted with research and planning. Claude (Claude Code) implemented the experiment, ran it and drafted the report under the author's direction. The human author is responsible for the final claims.

MIT license for original code and prose. Linked papers, talks, the official template and datasets keep their own terms.
