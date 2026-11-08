> **Status update (November 8, 2026):** this brief has been executed. See the README for results, `protocol/` for the frozen protocol and post-freeze changes, and `report/` for the PDF. The brief below is preserved as written.

# Build Swarm Evidence and finish a submission-ready report

## Objective

Implement and evaluate the study in `docs/PROJECT_PLAN.md` and `docs/IMPLEMENTATION_SPEC.md`, then produce a truthful report in the official Apart template. Work toward submission readiness tonight. The public repository owner is **DaniyalMughal1**. The user will register and submit; do not contact organizers or submit on their behalf.

The question: **Under a fixed monitoring context budget, does backward selection through recorded artifact dependencies improve detection of composed policy violations over non-graph retrieval?** Primary track 4; secondary track 1. We are studying a known, centrally instrumented three-worker workflow, not discovering unknown swarms or proving spontaneous collusion.

## What is already done

The event's four tracks, 32 suggested readings, all 11 recording transcripts, official report template, submission rules, closest prior work, and sponsor inference access have been investigated. See the guides rather than repeating this research. Primary-source access levels are documented. The plan received independent review and was revised to address budget, leakage, inference, and novelty risks. There is no implementation and no result yet.

FlowReview already studies composed-action authorization and incomplete usable lineage. GroupGuard already uses graph monitoring. Multi-Agent AI Control already studies fragmentation and joint-monitor comparisons. John Kitaoka explicitly proposed corroborating relevant agents in his talk. Our candidate contribution is the **context-budget-controlled selection comparison and measured failure boundary**, not a new general control architecture. Reassess this claim against the actual result.

## Read in order

1. `AGENTS.md`, `docs/PROJECT_PLAN.md`, `docs/IMPLEMENTATION_SPEC.md`.
2. `docs/ADAPTION_SETUP.md`, `docs/RELATED_WORK.md`.
3. `report/REPORT_OUTLINE.md`, `docs/SUBMISSION_CHECKLIST.md`.
4. Consult `docs/READING_GUIDE.md` and `docs/RECORDINGS.md` when needed; do not consume the day rereading everything.

## First actions

Check current time. Target completion November 8 at 23:00 Toronto; official cutoff November 9 at 06:59 Toronto. Preserve two hours for analysis, writing, and PDF review.

Check whether an Adaption key is available locally without printing it. Confirm the participant's credited balance, hosted-model access, and current per-model rates. The user expects the advertised $500 platform credits and three months Premium; activation is not yet verified. Never assume a credit unit equals a dollar. No outside API budget is authorized.

If credentials or credits are pending, build and test the entire offline simulator, selectors, restricted deterministic monitor, metric code, plotting pipeline, and report structure. A model-independent evidence-retention experiment is useful, but cannot be presented as measured LLM detection performance. Keep the live-run requirement visibly pending; report an access limitation if it remains unresolved.

## Deliverables

- Executable synthetic workflows with policy/state oracle, matched legitimate/violating twins, stable IDs, and separate gold files.
- Five deterministic selection methods; a restricted deterministic monitor; an Adaption model monitor; checkpointed runner; exact model and prompt versions.
- Frozen dataset/protocol manifest with template-family split, dependency visibility treatment, token budgets, retry policy, and primary contrast.
- Completed main comparison on held-out cases. Run extensions in the specified order only after measuring throughput and cost.
- Per-case predictions, costs, evidence retention, errors and abstentions; analysis code that regenerates every reported number and figure.
- Two or three readable figures: evidence-selection example, performance versus budget, and missing-metadata degradation if completed.
- Official-template report PDF, max eight main-text pages, 150–250-word abstract, authors/affiliations, references, required limitations/dual-use appendix, and accurate AI-use statement.
- Updated README with exact reproduction commands, measured results, preexisting-work disclosure, public artifact links, and limitations. Optional 3–5-minute video script is supplied in the checklist.

## Non-negotiable research checks

Ground truth comes from executed local state, not an LLM judge. Core cases need evidence from at least two workers; include counterfactual-completion checks and separate single-worker controls. Gold minimal evidence sets are evaluation-only.

All methods see the same observed fields and use the same rendering. Selector input never contains labels, attack names, a gold violation index, or hidden oracle state. A trace's finalization trigger must occur in both twins.

Count every repeated instruction and output in isolated monitoring. Use the same model and fixed per-trajectory caps. Show actual use as well as caps. Do not describe unequal realized spending as exactly matched spending.

Do not remove a graph edge while retaining the same relation in inputs, outputs, names or free text and call it missing evidence. Either scrub the metadata everywhere or explicitly study a corrupted index. Distinguish omitted events.

No silent test-set tuning, fabricated successful attacks, selective deletion of invalid outputs, or treating seed repeats as independent templates. Record failures and null results. First-attempt scoring and invalid-output handling are fixed in the specification.

## Stages and stopping

Implement offline correctness first. Run a development pilot, then commit a protocol hash before held-out inference. First finish the primary dependency-versus-lexical contrast at the small cap with full visibility. Add chronological, shuffled, and isolated controls; then larger budget; then missing-metadata stress tests. Live workers and another model are conditional extensions. Stop starting extensions at the report-protection deadline.

If dependency retrieval loses, report why. If a deterministic monitor matches the LLM, that is a useful result about where learned oversight is unnecessary. If every method is perfect, inspect the development task's difficulty and context truncation before freezing; do not quietly redesign the held-out set after observing it. If the experiment is too small for statistical claims, state that plainly.

## Definition of done

A fresh clone runs offline tests and regenerates figures from committed, sanitized results. Every abstract number traces to saved data. Citations match actual paper titles/versions. The PDF uses the official template, renders correctly, and satisfies the checklist. No placeholder or invented author information remains. The user has the final PDF, repo link, exact submission steps, and any unresolved limitations.

Proceed with the authorized implementation; ask only for information that cannot be inferred or supplied locally, such as missing access or author affiliations. Do not stop after scaffolding or a plan.
