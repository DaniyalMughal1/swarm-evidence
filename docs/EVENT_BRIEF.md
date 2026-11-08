# Event brief and scoring strategy

Verified November 8, 2026 against the [official event page](https://apartresearch.com/sprints/swarm-alignment-2026). This is an operational checklist and our interpretation, not organizer endorsement of the project.

## What to deliver

| Item | Requirement |
|---|---|
| Main artifact | Research report PDF in the current linked official template |
| Length | At most 8 main-text pages; references and appendices excluded; template recommends around 4 |
| PDF upload | At most 25 MB |
| Front matter | Project title, 150–250-word abstract, authors and affiliations |
| Required appendix | Limitations and Dual-Use / Ethical Considerations |
| Code | Public repo optional under event rules; required for this project by its owner |
| Video | Optional, 3–5 minutes |
| Other attachments | Optional slides, project image and additional-material link; form caps uploaded slides/images at 25 MB each |
| Deadline | Nov 8, 2026, 23:59 AoE = Nov 9, 11:59 UTC = Nov 9, 06:59 Toronto |
| Submission | Form on the event page; select every applicable track |

The form requests title, summary, PDF, publication-interest choice, team name, location, and member names/emails. Discord and Scholar profiles are optional. The user supplies authorship information and submits. To replace a submission before cutoff, use the same project title. Check the confirmation email and attached PDF; projects are not immediately public during judging.

## What they are actually looking for

Our interpretation: judges need a specific question about failures or control **between agents**, a working research artifact, convincing comparison, and a short paper that supports a useful conclusion. A polished product alone will not answer the rubric. The event explicitly welcomes environments, evaluations, attacks, defenses, monitors and forensic tools. Cross-track work is allowed, and all tracks share the same scoring system.

The repeated research pattern across examples is: define a mechanism; build a contained test; compare a plausible baseline; measure safety and legitimate usefulness; state what does not transfer. For our project, the most valuable result would be a reproducible account of when dependency-based evidence selection is worth its cost and when it fails.

## The four tracks

| Track | Central question | Good evidence | Fit for tonight |
|---|---|---|---|
| 1. Sandboxes and Testbeds | Can populations be contained, observed and rerun? | Seeded replay, boundary tests, shared-resource controls, proxy-model validity | Secondary fit through the reproducible benchmark; three workers do not establish 5–20-agent population behavior |
| 2. Science of Agent Networks | How do roles, coordination and failures change with population/network structure? | Topology interventions; equal-token/attempt controls; spread and scaling curves | Attractive but more live rollout variance and cost |
| 3. Strengthening Agent Infrastructure | How do identity, permissions, reputation and commitments survive copying and collusion? | Adversarial protocol tests and externally enforced controls | Feasible, but many obvious lineage/revocation ideas already have close prior work |
| 4. Oversight and Control | What can a monitor infer or prevent from incomplete, untrusted group evidence? | Known ground truth, legitimate controls, partial-observation curves, usefulness costs | Primary fit |

### Full example-project inventory, condensed

Track 1: contained escape testing; shared-tool budgets and reproducibility; cheap-model proxy validity; composed permissions; covert channels under task pressure.

Track 2: discovering an unadvertised message board; splitting refused tasks; infection by topology; compromised replicas and model diversity; shared-memory corruption; spread of selfish behavior; refusal shopping versus matched retries on one worker.

Track 3: identities across renaming/copying; protocol impersonation; collusion-resistant reputation; privilege narrowing in delegation; agent-enforced versus external checks; escalation up/down a hierarchy; reliable whistleblowing under false reports; group strategy-proof research mechanisms; gateway-controlled lineage/audit; typed communication protocols.

Track 4: real-trace forensics; cartel detection from sampled evidence; failure attribution; replica monitors; no-channel collusion through shared priors; split-attack monitoring; gateway-only telemetry; distributed research sabotage; approval laundering; monitor persuasion; sanctioned-channel controls; governance roles; sandbagging detection; covert-work duration; checking claimed completion against state; distinguishing worker, reference-answer and grading faults.

These are suggested directions, not tasks every submission must implement. The chosen proposal combines split-attack monitoring, research-sabotage cases, and reliable state-based ground truth without claiming to cover the whole list.

## Rubric: target the evidence needed for 5/5

The event scores three dimensions from 1 to 5. We cannot guarantee scores or a prize.

| Dimension | Difference between solid and exceptional | What this project must show |
|---|---|---|
| Impact and innovation | Beyond a routine application: a valuable original contribution; at the top, a critical new approach or research direction with a clear path to impact | Explicit comparison to FlowReview, GroupGuard and NARCBench; a defensible context-budget question; useful evidence-selection and failure-boundary measurements |
| Execution | Beyond technical competence: thorough validation; at the top, rigorous ambitious work with novel, surprising or unusually well-validated findings | Executed-state labels; matched twins; held-out template families; genuine cross-agent necessity; fair token/cost controls; deterministic baseline; corruption audit; uncertainty and all failures |
| Presentation | Beyond comprehensibility: easy to follow; at the top, exemplary clarity about complex work | One-sentence question, one worked example, two or three readable figures, exact denominators, clear limitations, easy reproduction |

Do not manufacture novelty or surprising findings to meet this table. A null result with decisive controls can be more credible than a large headline gain caused by a weak baseline. The main scoring risk is novelty: budgeted provenance selection is a narrower contribution than a new control protocol. The evidence must make that narrower contribution worthwhile.

## Participation, credits and follow-up

Remote participation and solo teams are allowed. Teams up to five are recommended, larger teams allowed. A person may participate in at most two projects. Attendance at all talks is not required. Prior work is allowed if disclosed; only sprint work is judged. AI assistance is permitted, and the team owns responsibility for claims, references and results.

The advertised global cash pool is $4,000 (places 1–5: $2,000 / $1,000 / $600 / $200 / $200), with $1,000 Adaption credits per winning-team member. The separate LA prize pool requires local participation. Fellowship fast-track means accelerated consideration, not automatic admission. Results are ordinarily announced 1–2 weeks after the judging deadline. [Event source](https://apartresearch.com/sprints/swarm-alignment-2026).

Participants are offered $500 in Adaption Platform credits and three months Premium. Claim by signing up with the sprint-registration email; account activation and spend must be verified. See [Adaption setup](ADAPTION_SETUP.md).

For help use the [event Discord](https://discord.gg/XswWBvugYs), help-desk channel and @Support, or sprints@apartresearch.com. No organizer messages have been sent for this project.

Submission terms retain the team's copyright while granting Apart broad nonexclusive rights to process, share and publish the submission for its stated purposes; submission represents named members' agreement. Prize terms include equal division among team members, payment forms and deadlines. Review the [actual terms](https://apartresearch.com/sprints/prize-terms) before submitting; this summary is not a legal interpretation or tax advice.
