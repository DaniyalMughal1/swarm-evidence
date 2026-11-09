# Swarm Evidence: Selecting Cross-Agent Evidence Under a Fixed Monitoring Budget

> Superseded by the final report: `report/swarm_evidence_report.pdf` (built by `report/build_report.py` from `report/content.py`). This outline is kept for provenance.

**DRAFT OUTLINE ONLY. No experiments have been run. Do not submit this file as a completed paper.**

Use the [official Google Doc template](https://docs.google.com/document/d/1_1_27EyZriMlc8n8EBE2YScaeyMjm-8xjR097nmHXAE/copy?usp=sharing). Its section order is reproduced here as a planning aid; this Markdown is not a substitute for the required formatted report. Preserve the template's title/author styling and event footnote. Target 4–6 main pages; hard cap 8.

Authors: [TO COMPLETE: verified names and affiliations]. With Apart Research.

Event footnote: Research conducted at the Swarm Alignment Hackathon, November 2026.

## Abstract

[WRITE LAST: 150–250 words. State the problem, exact tested setting, comparison and actual sample counts, measured primary result with uncertainty, and bounded takeaway. Do not turn the predicted advantage into a result. Avoid opening with unsupported broad incident claims.]

## 1. Introduction

Monitoring one worker can miss facts supplied by another. Reading every event is costly, and the relevant context may be incomplete. We ask whether selecting evidence through recorded artifact dependencies improves policy-violation detection at a fixed monitoring context budget compared with non-graph retrieval.

[CITE verified related work. State why the answer changes a practical monitoring decision. Specify that the setting is a known, centrally instrumented workflow.]

Candidate contribution list, to retain only if completed:

1. An executable synthetic benchmark with state-based labels, matched legitimate cases and audited cross-agent evidence requirements.
2. A controlled comparison of evidence-selection policies under fixed caps, with rule-based and learned monitoring.
3. A measured boundary under missing dependency metadata, with cost and uncertainty.

## 2. Related Work

[About half a page. Explicitly distinguish FlowReview's composed authorization and lineage treatment; Multi-Agent AI Control's distributed attacks and joint-monitor checks; GroupGuard's graph monitoring; NARCBench's interpretability-based detection; AI Control's safety/usefulness framing. See `docs/RELATED_WORK.md`. Do not claim these ideas originated here.]

## 3. Methods

### Setting and threat model

[Actual workers, domains, local tools, permission policies, finalization trigger, recorder trust, attacker control and monitor access. Clearly separate scripted replay and any live-agent extension. No hidden activations are assumed.]

### Data and labels

[Actual base pairs, trajectories, template families, seeds and split counts. State oracle definition, minimal sufficient evidence checks, counterfactual-view checks, hard benign controls and excluded invalid cases with reasons.]

### Evidence selection and monitors

[Actual frozen algorithms, model ID/version, tokenizer, input/output caps, actual tokens, identical rendering, isolated-call aggregation, deterministic restricted baseline and full-state diagnostic. Explain no gold leakage.]

### Evaluation

[Primary hypothesis, family-clustered intervals or descriptive limitation, calibration threshold, first-attempt failure policy, coverage, metadata-corruption definition, run-stage stopping, total credited cost.]

Figure 1: [A real benchmark example showing permitted and violating composition, relevant events and selected evidence. Make caption explain the trust boundary and show synthetic data.]

## 4. Results

**NOT RUN. No result values are populated.**

Table 1 should report each method's AUROC, TPR/FPR raw counts, benign acceptance, abstentions/invalids, selected tokens, latency and cost on the same held-out cohort. Include rule-monitor results. Every value must be generated from saved run records.

Figure 2: [Primary paired method comparison and budget curve with uncertainty, sample/family counts and realized spending.]

Figure 3, if completed: [Performance and evidence retention as metadata visibility degrades. Distinguish missing metadata from corrupted indices.]

[Report failure cases and null results. If optional experiments were not run, omit their result headings or mark them as future work rather than imply completion.]

## 5. Discussion and Limitations

[Interpret the measured result. Does better retrieval help, or does the model fail even with evidence? Does a deterministic monitor suffice? How much comes from evidence retention versus reasoning? What would invalidate the interpretation?]

[Discuss family count, artificial prevalence, known workflow structure, telemetry trust, domain transfer, calibration uncertainty, model/provider specificity, incomplete billing visibility and optional experiments not completed.]

## 6. Conclusion

[One or two short paragraphs stating only the measured finding and its implications. No claim of deployed safety, spontaneous collusion or universal novelty.]

## Code and Data

Code: [Swarm Evidence repository](https://github.com/DaniyalMughal1/swarm-evidence).

Data: [TO COMPLETE: versioned synthetic data and sanitized per-case results]. Reproduction command: [TO COMPLETE: tested command]. Commit/data manifest hashes: [TO COMPLETE].

## Author Contributions (optional)

[TO COMPLETE: actual human contributions. AI tools are disclosed separately, not invented as human coauthors.]

## References

[Populate a consistent bibliography using verified titles/authors/years/venues/versions. Do not mechanically cite all 32 readings. Start with the closest works in the related-work guide; confirm metadata against primary sources.]

## Appendix A. Limitations and Dual-Use / Ethical Considerations

### Scope and uncertainty

Draft language to reconcile with completed implementation: This study uses synthetic, centrally instrumented workflows with a trusted event recorder and a known finalization point. It does not establish identification of unknown colluding subgroups, resistance to recorder compromise, detection of disconnected covert channels, spontaneous collective agency, or safety in deployed agent populations. Repeated seeds from the same template do not establish broad independence. Balanced synthetic labels do not reflect operational prevalence.

Incomplete evidence can make a decision underdetermined. A monitor's abstention is not evidence of safety. Retrospective detection also does not establish that an online intervention would have prevented the event without harming legitimate work. [ADD actual sample/model/cost/time limitations and how each affects interpretation.]

### Dual use and release decisions

Draft language to verify: Distributed-violation examples and monitor failure analyses could help others choose actions that are harder to detect. We therefore use fake records, local simulated tools and destinations, and avoid publishing executable payloads against third-party services. The evaluation is intended to improve oversight and identify limits, not to enable covert operations. [VERIFY actual release; describe any withheld details and why.]

The public artifact should contain only original synthetic data and sanitized model outputs. Do not redistribute access-restricted logs, credentials, personal data or full third-party recordings. Record dataset licenses and attribution for any imported material. [VERIFY no provider/account metadata leaked.]

### Appendix B. Reproduction details

[Full prompts, schema, selector pseudocode, exact cap accounting, dataset-family manifest, visibility audit, calibration, bootstrap code/version, full per-case tables, failure records, model availability date and costs.]

### LLM Usage Statement

Draft factual status at preparation: Codex assisted with source discovery, transcript extraction, research synthesis and experiment planning. Claude is intended to assist with implementation and analysis. [REPLACE with actual completed usage, including models used to generate experimental predictions, and state exactly what human verification occurred. Do not claim all results were independently verified until they were.]

The official template encourages the final report to be primarily written by the team. Human authors must check and own every claim, reference and result.
