# Swarm Evidence

**Does a budget-limited monitor catch cross-agent policy violations more often when it reads the evidence that recorded artifact dependencies point to?**

Swarm Evidence is a controlled experiment built for the [Swarm Alignment Hackathon](https://apartresearch.com/sprints/swarm-alignment-2026), November 2026. Primary track: Multi-Agent Oversight and Control. Secondary track: Sandboxes and Testbeds. The report PDF is at [report/swarm_evidence_report.pdf](report/swarm_evidence_report.pdf).

In plain terms: one AI worker registers data under a restrictive license, a second transforms and merges it, and a third stages the merged file for export. Each step is allowed locally, but the composition violates policy. A monitor cannot afford to read every event, so it has to choose what to read. We compare seven ways of choosing at a fixed token budget, scored by an LLM monitor and by a deterministic checker given the same evidence.

## Findings

- **Retrieval.** Walking recorded dependencies backward from the action under review kept almost all of the decisive evidence at a 2,000-token cap. Lexical, BM25, lexical+PRF, chronological and shuffled-graph selection kept a quarter to about a third of it. Isolated per-worker review saw no events at this cap, because its repeated prompt overhead used up each worker's share.
- **Detection.** With the LLM monitor at 2,000 tokens, held-out AUROC was 0.75 with dependency evidence and 0.55 with lexical retrieval. This pre-registered primary contrast is **not resolved**: only 6 held-out template families were tested, and the family-bootstrap interval for the difference includes zero.
- **More context did not help.** Reading the whole log without a cap (about 8× the tokens) scored 0.55, and most of its false alarms cited unrelated legitimate work. At 6,000 tokens the non-graph baselines saw more evidence, but their extra evidence brought false alarms, and the gap to dependency selection widened instead of shrinking as pre-registered.
- **Judgment was the bottleneck.** On the *same* selected evidence, a short deterministic checker made no false alarms, while the 397B model flagged every legitimate twin in the two families where a policy clause says which inputs carry records (join and deduplication *references*).
- **The boundary is predictable.** Dependency selection misses evidence that is not an ancestor of the target (for example, an earlier payment of the same invoice). It also loses ground to lexical retrieval when dependency metadata is removed.

Exact numbers, generated from saved records:

<!-- results:start -->
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

`generate` rebuilds byte-identical data files (a test checks this). `validate` runs the gate, the leakage audit and the mask audits. `analyze` regenerates every table and figure from `results/calls/`. `python3 report/build_report.py` rebuilds the PDF; it needs LibreOffice. `python3 -m swarm_evidence audit-report` checks every report number against the summary.

Live model calls are opt-in. Put `ADAPTION_API_KEY`, `ADAPTION_MODEL` and `SWARM_MAX_CREDITS` in a local `.env` (gitignored), then run a stage, for example:

```bash
python3 -m swarm_evidence run --stage stage1 --stage-budget 5 --rpm 24
```

Completed calls are skipped on resume. `scripts/run_primary_chain.sh` and `scripts/run_followup_chain.sh` run the full pre-registered order.

## Honest scope

- The setting is synthetic and scripted: three known workers, a trusted complete recorder, and a common finalization point. These results do not cover unknown swarms, tampered logs or emergent collusion.
- Six held-out template families (30 matched pairs) give wide, descriptive intervals. Seeds within a family are not independent mechanisms.
- The rule monitor was written with knowledge of the tool semantics. It shows what structured evidence permits; it is not a deployable detector.
- Two hosted models were tested at temperature 0. The primary model ran with reasoning disabled; a labelled exploratory run checks reasoning.
- The live-agent validation slice was not run.

## Prior work and provenance

Closely related work already covers much of this ground: composed-flow authorization with lineage (FlowReview, arXiv:2610.00371), graph-based collusion defense (GroupGuard, arXiv:2603.13940), distributed attacks against per-instance monitors (arXiv:2607.07368), and collusion detection from model internals (arXiv:2604.01151). Our increment is the controlled comparison of evidence-selection policies at a fixed context budget and the boundary it measures. See [docs/RELATED_WORK.md](docs/RELATED_WORK.md).

All code and data were written during the sprint on November 8, 2026; no earlier project code was reused. Codex assisted with research and planning. Claude (Claude Code) implemented the experiment, ran it and drafted the report under the author's direction. The human author is responsible for the final claims.

MIT license for original code and prose. Linked papers, talks, the official template and datasets keep their own terms.
