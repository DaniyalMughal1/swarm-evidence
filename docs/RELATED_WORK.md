# Closest prior work and project choice

Research cutoff: November 8, 2026. This is a targeted novelty search, not proof of priority. All proposed findings remain unmeasured. The 32 event readings are in [READING_GUIDE.md](READING_GUIDE.md).

## The contribution we can defend if the experiment succeeds

Measure how **context-limited selection of observed cross-agent artifact evidence** changes detection, legitimate acceptance and cost, using non-graph retrieval controls and held-out synthetic workflows. Identify when this benefit disappears as dependency metadata is lost. The reusable contribution would be the benchmark, analysis and empirical boundary. An improvement is a hypothesis, not a result.

Do not claim first multi-agent monitoring, first provenance-based control, first split-attack detection, first trusted gateway, or first study of incomplete lineage. Those claims conflict with the work below.

## The closest comparisons

| Work | What already exists | Difference our experiment must substantiate |
|---|---|---|
| [FlowReview / Deny Without Disabling](https://arxiv.org/html/2610.00371v1) | Composed-flow authorization, legitimate/attack controls, incomplete usable lineage, trusted runtime dependency recording; sections 4.3–4.4 and Appendix E matter | We measure context-budget-limited selection against non-graph retrieval, not a new lineage enforcement architecture. Their budget variations concern attacker rounds; do not conflate them with our context caps. |
| [Multi-Agent AI Control: Distributed Attacks Hamper Per-Instance Monitors](https://arxiv.org/html/2607.07368v2) | FakeLab experiments on distributed attacks, planning and monitor strength; joint-monitor checks and fuller-context limitations | We must add an explicit evidence-selection experiment under constrained context. Merely showing joint review beats isolated review would repeat known work. FakeLab access is on request, so it is not assumed available tonight. |
| [GroupGuard](https://arxiv.org/html/2603.13940v1) | Interaction-graph monitoring, honeypot probing and pruning for coordinated manipulation | Our graph is artifact dependency evidence, not a social interaction suspicion graph. We measure selection quality and uncertainty rather than claim universal colluder identification. |
| [NARCBench](https://arxiv.org/abs/2604.01151) | Multi-agent collusion detection using interpretability, with generalization challenges | Our monitor has black-box event observations, not internal activations. Instructed violations are not spontaneous collusion. |
| [AI Control](https://arxiv.org/abs/2312.06942v5) | Adversarially evaluated protocols balancing safety and useful output | We evaluate a component of a control protocol; detection alone does not prove prevention. |
| [Adversaries Can Misuse Combinations of Safe Models](https://proceedings.mlr.press/v267/jones25a.html) | Compositional misuse across individually constrained models | We study observation and retrieval, not whether composition can unlock harmful behavior in the first place. |
| [Which Agent Causes Task Failures and When?](https://github.com/ag2ai/Agents_Failure_Attribution) | Agent/step attribution of task failures | We classify policy validity of an action chain with state-based ground truth. Attribution is secondary and can be underdetermined. |

Source depth: FlowReview selected methods/appendix reviewed; Multi-Agent AI Control abstract, monitoring discussion and budget passages reviewed; GroupGuard abstract and methodology overview reviewed; NARCBench selected v1 passages and current abstract reviewed; remaining entries at primary abstract/project-documentation level. Read the exact sections before making detailed numerical comparisons. Published headline rates are not comparable without matching threat models and denominators.

## What the talks add

Kitaoka explicitly motivates corroborating relevant actions (Q&A 56:11–57:25) and controlling monitoring cost. Credit the talk as motivation. Fleming warns about many attackers receiving more total persuasion budget. Elias's cooperative language-emergence examples show why odd-looking text is a bad maliciousness label. Jurgis highlights incomplete or manipulated logs. Shenk's fleet/swarm distinction prevents overclaiming from a centrally designed workflow. See [timestamped recording notes](RECORDINGS.md).

## Why this project over the alternatives

| Candidate | Useful outcome | Main risk tonight | Decision |
|---|---|---|---|
| Budgeted cross-agent evidence selection | Reusable controlled measurement with explicit ground truth | Novelty is narrow; synthetic cases can leak labels or be too easy | Choose, with audited composition cases and strong retrieval/rule controls |
| Tamper-evident agent black box | Reliable external logging | Cryptographic logs and forensic capture already exist; authenticity does not imply semantic correctness | Treat as an assumption, not today's headline |
| Agent revocation and delegated identity | Infrastructure stress test and fix | Lifecycle and protocol integration can dominate; close existing authorization/revocation work | Good later project, not needed for this question |
| Real-swarm forensics dashboard | Useful investigative interface | Missing logs, ambiguous identities, unavailable ground truth; interface quality can hide weak validation | Use sources for motivation; do not label historical actors from guesses |
| Emergent-language detector | Interesting oversight question | Cooperative compression can resemble concealment; robust labels and models take time | Not selected |
| N-agent refusal shopping | Simple measurable experiment | Explicitly suggested on the site; retries/extra compute confounds; limited originality without a new mechanism | Not selected |
| Training a small monitor | Sponsor-aligned efficiency study | Queues, data leakage, model availability and evaluation overhead | Optional after the primary study, with a same-base-model comparison |

Additional infrastructure searches found [HANSARD](https://arxiv.org/abs/2608.22512), [AgentFlightRecorder](https://arxiv.org/abs/2609.01931), and an [earlier Apart attested-log project](https://apartresearch.com/sprints/projects/attested-multiagent-conversation-logs-a-tamperevident-black-box-for-ai-governance-du9i). These establish that logging/provenance is a crowded direction; only abstracts/project descriptions were inspected, so no claim of superiority over their implementations is made.

## Real datasets: value and constraints

| Resource | What we can use it for | What we must not assume |
|---|---|---|
| [METR/Redwood incident report](https://metr.org/hugging-face-incident-report-aug-2026.pdf) | Motivation and concrete failure mechanisms; detailed investigation | Reconstructed observations are a complete ledger, or sampled percentages apply to all agents |
| [Swarm Traces](https://swarmtraces.org/) | Redacted reconstructed payloads and investigative context | Payload count equals independent agent count or complete causal trajectories |
| [AI Village](https://huggingface.co/datasets/aidigestorg/ai-village) | Potential future validation on long-running agent activity | Immediate access: the dataset has a manual research-access gate; training has additional restrictions. Summaries are not ground truth. |
| [Transluce agent activity](https://transluce.org/agent-activity) | Public-web observation and explicit attribution/confidence distinctions | Task-driven probes imply successful compromise; the report distinguishes attempted from evidenced outcomes |
| [collusion.wiki](https://collusion.wiki/) | Reconstructed, redacted message-board data and coordination examples | Complete internal traces, reliable self-asserted provider identity, or full retention of deleted pages |
| [swarms.wiki](https://swarms.wiki/) | Directory of incidents, tools and datasets | A registry entry independently verifies an incident; site access was unavailable to the web reader, while the linked speaker documents were accessible |

The event also links the [provider disclosure](https://openai.com/hugging-face-incident-and-misalignment/) and [ControlAI summary](https://blog.controlai.org/p/breaking-openais-rogue-ais-hit-over). Use the independent primary investigation and preserve attribution uncertainty when discussing incidents; advocacy summaries are not experimental labels.

No raw incident code is needed in our benchmark. Never run payloads from a dataset. Do not publish identities, credentials or unredacted logs. If adding real-trace validation, first verify its license/access terms, construct defensible labels, and separate it from the synthetic primary analysis.

## Risks that could still invalidate the result

1. **Easy shortcuts:** final tool arguments or artifact names reveal the answer without composition. Remedy: minimal-evidence and counterfactual-view checks.
2. **Bad retrieval baseline:** lexical selection is weak by construction. Remedy: inspect development behavior, freeze a credible baseline, add a stronger one if affordable.
3. **Artificial truncation:** decisive evidence always happens early. Remedy: vary evidence age and legitimate unrelated work; report length and evidence-retention distributions.
4. **Hidden graph leaks:** deleting an index edge leaves matching IDs elsewhere. Remedy: scrub the full observed relation or narrow the claim to index corruption.
5. **Pseudo-replication:** many seeds share a few templates. Remedy: family splits, family-level uncertainty and explicit counts.
6. **Decorative LLM:** deterministic policy logic solves everything. Remedy: run the restricted rule monitor and report when learned monitoring adds nothing.
7. **Unsupported deployment claim:** trusted complete telemetry, central finalization and known workers are special assumptions. Remedy: state these as scope limits, not solved problems.

Independent design review raised these issues and the initial 3,360-call scope. The revised plan passed a second review for implementation handoff. This is a design-quality check, not external validation or a forecast of judging scores.
