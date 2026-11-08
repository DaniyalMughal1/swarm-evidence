# Final submission checklist

Source: [event guidelines and form](https://apartresearch.com/sprints/swarm-alignment-2026). Official deadline: November 8, 23:59 AoE; November 9, 06:59 Toronto. Target ready by November 8, 23:00 Toronto. Recheck current time before starting any optional work.

## User actions

- [ ] Register for the sprint and create the Adaption account with the same email.
- [ ] Verify credited access; store an API key locally if live inference is desired.
- [ ] Confirm author names, affiliations, team name, emails, location, and publication-interest choice.
- [ ] Read and approve the actual research claims and submission terms.
- [ ] Submit through the event page and verify the confirmation email/PDF.

## Research gates

- [ ] All results come from saved executions; no draft/example values remain.
- [ ] Ground truth and minimal evidence are separate from monitor inputs.
- [ ] Cross-agent necessity, legitimate twins and deterministic baselines checked.
- [ ] Held-out split and primary protocol frozen before viewing results.
- [ ] Every method's actual tokens, costs, invalid outputs and abstentions included.
- [ ] Family counts, uncertainty, selected evidence and corruption semantics disclosed.
- [ ] Null results and stopped extensions honestly reported.
- [ ] Reproduction works from a fresh clone using public, sanitized artifacts.

## Report gates

- [ ] Use the [current official template](https://docs.google.com/document/d/1_1_27EyZriMlc8n8EBE2YScaeyMjm-8xjR097nmHXAE/copy?usp=sharing), not an old email attachment.
- [ ] PDF no larger than 25 MB; at most 8 pages before references/appendices.
- [ ] Title, verified author information and 150–250-word abstract present.
- [ ] Methods contain actual model IDs, prompts, sample counts, split, budgets and metrics.
- [ ] Figures numbered, legible and captioned; exact denominators visible.
- [ ] Required **Limitations and Dual-Use / Ethical Considerations** appendix present even though the generic template calls appendices optional.
- [ ] Accurate LLM-use statement; no claim of human independent verification until it happens.
- [ ] Prior work and any reused pre-sprint code identified in report and README.
- [ ] Every reference title, author/version and URL verified; no inaccessible-source findings represented as verified.
- [ ] All template guidance and placeholder markers removed. Render and inspect every page.

## Upload gates

- [ ] Select track 4 and, if the finished artifact supports it, track 1.
- [ ] Public GitHub link opens without login and README matches completed work.
- [ ] Submit title, summary, final PDF, team details and publication preference.
- [ ] Optional recording is accessible, 3–5 minutes and shows actual artifacts.
- [ ] Optional slides/image respect form size limits; additional-material links work.
- [ ] Confirm the email contains the correct title/PDF. Check spam before assuming failure.
- [ ] If replacing anything before cutoff, resubmit with exactly the same title.

## Optional four-minute demo

0:00–0:30: state the question in plain language. Show one permitted multi-worker workflow and its violating twin.

0:30–1:20: show the actual relevant events and why a single worker's view cannot decide. Show where dependency selection goes and what the baseline retrieves under the same cap.

1:20–2:30: show measured held-out results with counts, uncertainty and cost. Include the deterministic baseline. If there is no improvement, explain the observed failure.

2:30–3:15: show a missing-metadata example if that stage ran. State the trusted-recorder assumption and what is not covered.

3:15–4:00: show the public repo, one reproduction command, and the practical takeaway. Do not spend the video on installation or an elaborate UI.

Finish the PDF before recording. The written report is the judged artifact; a video cannot rescue unsupported results.
