# Changes after the protocol freeze

The protocol was frozen in commit `d27f932` (`protocol/PROTOCOL_FREEZE.json`, prompt hash `0fade4df61f8f865`) before any calibration or held-out call. This file lists every later change and whether it could affect a reported result.

| # | Change | Reason | Effect on recorded results |
|---|---|---|---|
| 1 | A concurrent second-model chain was stopped after 3 calls. Both models then ran sequentially. A 0.002-credit reservation was recorded for possibly billed in-flight calls. | The provider's per-user rate limit is shared across models, so running both chains at once only added 60 s pauses. | None. The completed calls stay in the record, and incomplete keys are re-run on resume under the same frozen settings. |
| 2 | `parse_output` returns `bad_score` instead of raising `OverflowError` on integers too large to convert to float. `runner.execute` also records a parser exception as an invalid output instead of crashing. | Found by the offline test suite. Before the fix, a crash would have lost a billed response. | None. No recorded output triggered either path; every held-out call has a stored row. |
| 3 | `runner.execute` de-duplicates run keys within one stage. | Found by the test suite. The bug is unreachable through the CLI, because `plan_calls` already de-duplicates. | None. |
| 4 | Corrected the `visibility.py` docstring: masking rewrites JSON string values equal to the artifact ID, not substrings inside free-text notes. | The old docstring overclaimed. | None. Generated notes never contain IDs, and the mask audit passes on all 138 trajectories in every condition. |
| 5 | Added descriptive outputs to `analysis.py`: verdict counts by family and model-independent rule-monitor results by family. | Needed to explain the primary result. | These are additional descriptive tables, labelled as such. The pre-registered metrics are unchanged. |

## Properties discovered after the freeze and left unchanged

- **Isolated review at the 2,000-token cap displays no events.** The repeated fixed overhead (699–755 estimated tokens per call) exceeds the one-third allocation (666). Under the frozen accounting the isolated arm at 2k is therefore a degenerate lower bound. The three calls' combined *estimated* input exceeds 2,000 tokens, but billed tokens per call stayed below 666 (see `results/analysis/summary.json`). We report this rather than re-allocating budgets after the fact.
- **The rule monitor has two known soundness gaps** on hand-built worlds that never occur in the generated families: deduplicating held-out data against a copy of itself, and sharding a mixed artifact. Both are pinned by `expectedFailure` tests in `tests/test_oracle.py`. The full-view rule monitor agrees with the oracle on all 138 released trajectories and all gate counterfactuals.
