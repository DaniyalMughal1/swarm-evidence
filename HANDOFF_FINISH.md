# Handoff: finish Swarm Evidence

> **Final status (November 8, 2026, evening, Toronto).** Everything below this box is the historical handoff written at 14:15; its progress counts, estimates and "missing author details" step are out of date. Current state:
> - All pre-registered stages finished for qwen3.5-397b (stages 1–4, controls, calibration) and for gemma-4-31b-it (stages 1–3 and calibration; masking and controls were run for the primary model only). Exploratory runs (reasoning-enabled monitor, temperature-0 repeat, live slice) finished and are reported in Appendix C; the reasoning run is inconclusive because 71 of 120 outputs hit the output cap.
> - The final analysis, figures, README results block and report PDF are regenerated from `results/calls/` and committed. `report/build_report.py` passes without `REPORT_DRAFT`, `python -m swarm_evidence audit-report` passes, and the offline tests pass with the 4 documented expected failures.
> - Every change after the freeze, including those prompted by an independent AI-assisted review (OpenAI Codex), is in `protocol/POST_FREEZE_CHANGES.md`.
> - Author: Daniyal Mughal, Independent Researcher. The human-review sentence in `report/llm_statement.txt` describes the author's reading as stated by the author; edit it if that changes before submission.
> - Remaining for the author: final read of the PDF, approval to merge `implement-experiment` into `main`, and the submission itself.


Official deadline: **2026-11-09 06:59 Toronto** (Nov 8 23:59 AoE). Self-imposed target: submission-ready by **23:00 Toronto, Nov 8**. The user registers and submits. Do not contact the organizers.

Repo: the local `swarm-evidence` checkout (the absolute path is kept out of public files). The work is on branch `implement-experiment`, not yet pushed. `main` holds only the research pack. Use `.venv/bin/python` (Python 3.12 with adaption 0.19.0, matplotlib, python-docx, pymupdf). LibreOffice is at `/Applications/LibreOffice.app`.

Read first: `AGENTS.md`, `protocol/PROTOCOL_FREEZE.json`, `protocol/POST_FREEZE_CHANGES.md`, this file.

## 1. State right now

- **Implemented and committed:** simulator (3 domains, 12 families plus 3 controls, 69/69 base cases pass the validity gate), 7 selectors plus a full-log arm, a rule monitor, the Adaption monitor, a checkpointed runner (800-credit ceiling from `.env`), metrics, analysis, figures, a report builder over the official template, and 179 offline tests (pass on both interpreters, with 4 documented expected failures).
- **Protocol frozen** at commit `d27f932`, before any held-out call. Every later change is in `protocol/POST_FREEZE_CHANGES.md`. Do not change the frozen code paths or re-run held-out stages to chase results.
- **Spend:** about 1.53 credits so far, out of an 800 ceiling and 1,000 balance. 1 credit = $1. Spend is not the constraint. The **per-user rate limit (about 17–24 calls/min, shared across models)** is.
- **Key:** `ADAPTION_API_KEY` is in `.env` (gitignored, mode 600). Never print or commit it. `ADAPTION_MODEL=qwen3.5-397b`, `SWARM_MAX_CREDITS=800`.

### Background processes still running (started from the original session)

| Process | Log | Does |
|---|---|---|
| `scripts/run_primary_chain.sh` | `results/logs/primary_chain.log` | Qwen held-out stages in order: stage1 ✅, stage2 ✅, controls ✅, **calibration (in progress at 14:13, 279/570)**, then stage3 (540 calls, 6k cap), then stage4 (720 calls, metadata masking). Expected to finish around **15:20–15:40**. Prints `=== chain done` at the end. |
| `scripts/run_followup_chain.sh` | `results/logs/followup_chain.log` | Waits for `chain done`, then runs: gemma stage1 and stage2 → exploratory Qwen reasoning-enabled stage1 → exploratory temperature-0 repeat → **exploratory live-agent slice** (`python -m swarm_evidence live --seeds 12`) → gemma calibration → gemma stage3. Expected to finish around **17:30–18:00**. |

Check progress:

```bash
cd ".../swarm-evidence" && grep "^===" results/logs/*.log && sqlite3 results/runs.sqlite "select model, stage, count(*), sum(parse_error is not null), round(sum(cost),3) from calls group by 1,2;"
```

```bash
ps -axo pid,command | grep -E "run_primary_chain|run_followup_chain|swarm_evidence (run|live)" | grep -v grep
```

- If these processes died when the original session closed, **restart them**. Everything is checkpointed by run key, so completed calls are skipped. Run `./scripts/run_primary_chain.sh > results/logs/primary_chain.log 2>&1 &`, then the follow-up chain the same way; it waits for the primary log's `chain done` line. If the primary chain had already finished, check the log's tail first.
- **Never run two chains that call the API at once.** The rate limit is shared, so a 429 pauses all threads for 60 s.
- **Time cutoff:** if it is past roughly 19:30 and gemma calibration or stage3 is unfinished, stop it (`kill <pid>` of the `run_followup_chain.sh` and its python child) and report those stages as not run. They are the lowest priority. Before stopping, record a small reservation for in-flight calls: `Store(...).adjust("killed_inflight_reservation", 0.002, "...")`. Priority order: Qwen stages > gemma stage1/2 > reasoning check > live slice > repeat > gemma calibration/stage3.

## 2. Results so far (held out, Qwen, 2,000-token cap, 60 trajectories, 6 families)

- **Primary contrast:** dependency AUROC **0.75** (family CI 0.50–0.95) vs lexical **0.55** (0.52–0.61). Difference **+0.20, CI [−0.07, +0.41]**, with 4 of 6 families positive. Point estimate positive, **not resolved at the family level**.
- **Gold-evidence recall:** dependency 0.96, lexical 0.25, chronological 0.36, BM25 0.34, lexical+PRF 0.27, shuffled 0.25, isolated 0.00.
- **Verdicts:**
  - Dependency: 25/30 violations flagged, **12/30 legitimate twins flagged**.
  - Lexical abstains on 59/60. All arms produced 0 invalid outputs and 0 cap overruns.
- **Error taxonomy (dependency, LLM):**
  - A4 and B2 (role semantics: join/dedup *reference*): every legitimate twin is flagged, so AUROC is 0.5 for those families.
  - C4 (out-of-lineage, pre-registered H2): all 5 violations are missed.
  - A2 and C2 are perfect.
- **Rule monitor** on the same dependency evidence: AUROC **0.92** with 0 false positives. It fails only on C4.
- **Full log, no cap** (mean 9,327 billed tokens, 8× dependency): AUROC **0.55**, 21/30 legitimate twins flagged, and **17 of those 21 false alarms cite unrelated legitimate work**. None of dependency's 12 do. Dependency minus full = +0.20 [−0.004, 0.386].
- **Other contrasts, dependency minus X at 2k:** vs shuffled +0.29 [0.02, 0.51]; vs isolated +0.25 [0.01, 0.45]; vs lexical+PRF +0.31 [0.06, 0.51]; vs chronological +0.22 [−0.06, 0.45]; vs BM25 +0.19 [−0.07, 0.41].
- **Controls** (single-worker, 9 pairs): dependency 1.00, full 0.97, lexical 0.70, isolated 0.50 (isolated shows no events at 2k).
- **Offline, model-independent, held out:** under masking, dependency recall drops 0.96 → 0.65 (25%) → 0.44 (50%) → 0.52 (bridges). Lexical is unchanged (0.25 at 2k, 0.70 at 6k).
- **Live slice smoke test** (seed 0): W2 complied with the request to fold in the restricted panel but *disclosed* it in its notes. The oracle labels it a violation and the matched run legitimate.

## 3. Remaining steps, in order

1. **Wait for the runs** (§1). Do not edit `swarm_evidence/selection.py`, `prompts.py`, `scenarios.py`, `rules_monitor.py`, `visibility.py` or the `data/` files; they are frozen.
2. **Regenerate the analysis:** `.venv/bin/python -m swarm_evidence offline --split test --caps 2000,6000 --visibility full,random25,random50,bridges`, then `.venv/bin/python -m swarm_evidence analyze`, then `.venv/bin/python scripts/readme_results.py` (fills the README results block). Check `results/analysis/summary.json` → `models/<model>/arms`, `contrasts`, `visibility`, `controls`, `live_exploratory`, `replicates`.
3. **Ask the user for author details (still missing).** Create `report/authors.json` as `[["Full Name", "Affiliation"], ...]` and `report/author_contributions.txt`. Replace the bracketed sentence at the end of `report/llm_statement.txt` with the human review that actually happened. Git shows "Daniyal Mughal"; do not use it or guess an affiliation without confirmation.
4. **Re-check every qualitative claim in `report/content.py` against the final numbers**, then rewrite where they differ:
   - §4.3: the H3 sentence ("predicted shrinkage"; say whether it happened) and the masking paragraph. AUROC under masking comes from stage4.
   - §4.4: "With gemma-4-31b-it the pattern repeated…" must be verified, or rewritten if the pattern did not repeat.
   - Appendix C: the reasoning variant, the repeat, and the live slice. "Concealment was not observed" must match `live_exploratory/request/notes_mention_extra`. If a stage did not run, remove its sentence and say so.
   - The abstract (currently 228 words; keep it at 150–250), the Discussion and the Conclusion.
   - Every number goes through `N.f/N.i/N.pct/N.get`, with `/`-separated paths (model keys contain dots).
5. **Build the PDF:** `.venv/bin/python report/build_report.py`. Do **not** set `REPORT_DRAFT`; the final build must fail on any missing key. It prints `pages` and `references_heading_page`. **The main text must end by page 8, i.e. `references_heading_page` ≤ 9.** The last draft was exactly at the limit. Trim candidates: Related Work, §3.2 prose, Discussion, and the Limitations bullets (move detail to Appendix A). Render the pages with pymupdf and look at every page (figures legible, tables not wrapping, author block centred, no `[` or `TO CONFIRM` markers left). PDF size must be under 25 MB.
6. **Audit:** `.venv/bin/python -m swarm_evidence audit-report` must report `ok: true`; it checks `report/numbers_used.json` against the summary. Then run `python3 -m unittest discover -s tests` and `python3 scripts/check_pack.py`.
7. **Commit**, using explicit paths only, never `git add -A`: `results/calls/`, `results/analysis/`, `results/offline/`, `results/token_calibration.json`, `figures/`, `data/live/`, `report/swarm_evidence_report.pdf`, `report/swarm_evidence_report.docx`, `report/numbers_used.json`, `report/authors.json`, `report/*.txt`, `README.md`, plus any code or report edits. **Never commit** `.env`, `results/runs.sqlite` or `.venv/`. Then push the branch (`git push -u origin implement-experiment`). Ask the user before merging into `main` (the public README lives there) and pushing `main`.
8. **Final checklist:** `docs/SUBMISSION_CHECKLIST.md`. The optional 3–5 minute demo script comes only after the PDF is final. Give the user the PDF path, the repo link, the exact submission steps (track 4 primary, track 1 secondary) and the unresolved limitations.

## 4. Things to know (gotchas and decisions already made)

- **Isolated arm at 2k shows zero events.** The repeated overhead per call (~700–755 estimated tokens) exceeds 2000/3. This is frozen accounting, disclosed in Methods §3.2 and POST_FREEZE. Do not "fix" it.
- **Rule monitor** has two documented soundness gaps on hand-built worlds absent from the data (expectedFailure tests). Its benign verdicts are optimistic about unseen events, which is why it misses C4. Both are stated in the report.
- **Gemma** produced degenerate "our our our" loops on 2/36 dev-pilot calls. Invalid outputs are scored 0.5 per the frozen policy. Report them; do not repair.
- **Token caps** are estimates (2.5 bytes/token, calibrated on the dev pilot; see `results/token_calibration.json`). Billed tokens stayed below the caps; `cap_overruns` is reported per arm.
- **Report builder:** `report/content.py` holds all text. `report/references.json` holds 12 references verified against arXiv, PMLR and Crossref. BM25 is cited by DOI only, without volume, because publisher records conflict. Figures come from `swarm_evidence/figures.py`: `fig1_example.png`, `fig2_auroc_by_method.png`, `fig3_budget_and_metadata.png`, and `figS1_*` for gemma (not in the report).
- **Fresh-clone reproducibility:** `analyze` regenerates everything from `results/calls/*.jsonl` when `runs.sqlite` is absent. `generate` is byte-deterministic (a test checks this).
- **Pre-registered hypotheses** are H1 to H5 in the freeze file. Report each honestly. H1 is not resolved at the family level; H2 is confirmed (C4); H5 is supported (rule monitor ≥ LLM where lineage is complete).
