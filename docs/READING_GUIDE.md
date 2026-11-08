# All 32 suggested readings

The event lists six general resources and 26 track-specific resources (6 / 5 / 7 / 8). Each entry preserves the event link, identifies the primary source actually inspected, and distinguishes source findings from our project implications. This is a research triage and synthesis, not a claim of full-paper reading for all 32. Retrieved November 8, 2026.

Read first for this project: R01, R14, R16, R26, R27 and R28, then the newer close competitors in [RELATED_WORK.md](RELATED_WORK.md). Track-3 theory is useful context but is not on the implementation critical path.

## General

### R01. Multi-Agent Risks from Advanced AI

Hammond et al., 2025. [Event-listed source](https://arxiv.org/abs/2502.14143).

Access: Primary abstract and taxonomy reviewed.

Organizes multi-agent risks around miscoordination, conflict and collusion, with risk factors that can interact across a system.

**Limit:** A taxonomy is not an empirical estimate of incident frequency. Use it to specify the failure mechanism, not to claim every cooperative interaction is dangerous.

**Our use:** Frame the task as composed policy violation and observation failure, distinct from ordinary task error.

### R02. Distributional AGI Safety

Tomašev et al., 2025; revised 2026. [Event-listed source](https://arxiv.org/abs/2512.16856).

Access: Primary abstract reviewed.

Argues that advanced capability and risk can arise through distributed combinations of systems rather than one monolithic model.

**Limit:** An agenda does not establish that a small synthetic workflow predicts large deployed systems.

**Our use:** Motivates system-level measurement; restrict claims to the chosen workflow.

### R03. ARIA's Scaling Trust programme thesis

ARIA, Scaling Trust. [Event-listed source](https://aria.org.uk/opportunity-spaces/trust-everything-everywhere/scaling-trust/).

Access: Official program page reviewed.

Frames trust in complex interacting systems as an engineering and research challenge, including scalable ways to establish system behavior.

**Limit:** A funding thesis is context, not a validated benchmark or the hackathon judging rubric.

**Our use:** Explain who would use the evidence and what operational decision it changes.

### R04. Open Problems in Cooperative AI

Dafoe et al., 2020. [Event-listed source](https://arxiv.org/abs/2012.08630).

Access: Primary abstract reviewed.

Maps open problems in cooperative AI, including understanding, communication, commitment and institutions.

**Limit:** Cooperation between agents can harm outsiders. Increasing cooperation is not synonymous with alignment.

**Our use:** Keep the operator policy and legitimate task outcome explicit.

### R05. Infrastructure for AI Agents

Chan et al., 2025. [Event-listed source](https://arxiv.org/abs/2501.10114).

Access: Primary abstract reviewed.

Studies infrastructure that supports attribution, shapes agent interactions and helps address resulting harms.

**Limit:** An infrastructure proposal does not by itself authenticate every event or solve collusion.

**Our use:** Separate identity and logging assumptions from the monitor measurement.

### R06. Foundations of Cooperative AI

Conitzer and Oesterheld, 2023. [Event-listed source](https://ojs.aaai.org/index.php/AAAI/article/view/26791). [Primary/author source inspected](https://www.cs.cmu.edu/~15326-f24/FOCALAAAI23.pdf).

Access: Publisher blocked; author-hosted paper located and inspected at abstract level.

Explores foundations of cooperation among artificial agents, including opportunities created by inspecting or changing programs.

**Limit:** Formal strategic models depend on information and commitment assumptions absent from ordinary text-only agents.

**Our use:** Background for track 3; not a direct baseline for this study.

## Track 1

### R07. Generative Agents

Park et al., 2023. [Event-listed source](https://dl.acm.org/doi/10.1145/3586183.3606763). [Primary/author source inspected](https://arxiv.org/abs/2304.03442).

Access: Publisher blocked; primary preprint abstract reviewed.

Generative Agents combines memory, reflection and planning to produce interactive behavior in a simulated town.

**Limit:** Believable social behavior is not evidence of containment, ground-truth safety labels or secure shared tools.

**Our use:** Use richer interactions only when needed; keep this simulator deterministic and auditable.

### R08. Playing repeated games with large language models

Akata et al., 2025. [Event-listed source](https://www.nature.com/articles/s41562-025-02172-y). [Primary/author source inspected](https://www.nature.com/articles/s41562-025-02172-y.pdf).

Access: Publisher page blocked; primary PDF/search abstract reviewed.

Examines LLM behavior in repeated games and the differences between self-interested play and effective coordination.

**Limit:** Results depend on game framing, prompting and model capability. Repeated-game performance does not directly establish deployment safety.

**Our use:** Avoid an arbitrary social-dilemma demo with no causal link to the chosen threat.

### R09. LLM agents in stylised games and simulated social environments

Gandhi, Sadigh and Goodman, 2023. [Event-listed source](https://openreview.net/forum?id=MUtbsFRZwI). [Primary/author source inspected](https://arxiv.org/abs/2305.19165).

Access: OpenReview blocked; primary preprint abstract reviewed.

Strategic Reasoning with Language Models uses structured demonstrations of state, value and belief reasoning for game play and negotiation.

**Limit:** Prompted strategic competence should not be mistaken for intrinsic cooperation or spontaneous group agency.

**Our use:** Freeze prompting and distinguish capability from safety behavior.

### R10. CRUX

CRUX. [Event-listed source](https://cruxevals.com/).

Access: Official project page reviewed.

Provides open-world agent evaluation work that examines behavior in environments beyond small static tasks.

**Limit:** Open-ended behavior is expensive to label and reproduce; an evaluation project is not automatically a ready-made ground-truth dataset.

**Our use:** Useful external-validity direction after the controlled study.

### R11. Concordia, a library for generative agent simulations

Google DeepMind, Concordia. [Event-listed source](https://github.com/google-deepmind/concordia).

Access: Official repository README reviewed.

A library for generative agent simulations with a game-master style environment and configurable agent behavior.

**Limit:** The framework still needs models, environment design and validation; importing it does not make a study realistic or safe.

**Our use:** Consider if expanding into social simulations. Today plain executable state avoids unnecessary integration.

### R12. GovSim

Piatti et al., 2024. [Event-listed source](https://arxiv.org/abs/2404.16698).

Access: Primary abstract reviewed.

GovSim studies sustainable cooperation around shared resources in simulated societies of language-model agents.

**Limit:** Communication and model choices affect outcomes; success in one commons environment is not a broad safety guarantee.

**Our use:** Use as background for shared-resource domains and legitimate cooperation controls.

## Track 2

### R13. Prompt Infection

Lee and Tiwari, 2024. [Event-listed source](https://arxiv.org/abs/2410.07283).

Access: Primary abstract reviewed.

Prompt Infection studies malicious instructions spreading between communicating language-model agents and explores defenses.

**Limit:** Propagation depends on communication affordances and exposure; distinguish susceptibility from the number of opportunities to infect.

**Our use:** Treat all trace rationales as untrusted input; keep topology and exposure fixed.

### R14. Splitting tasks to evade per-agent safety filters

Jones, Dragan and Steinhardt, 2025. [Event-listed source](https://openreview.net/forum?id=GCkhEPE1FG). [Primary/author source inspected](https://proceedings.mlr.press/v267/jones25a.html).

Access: OpenReview blocked; official proceedings abstract reviewed.

Adversaries Can Misuse Combinations of Safe Models studies harmful capability unlocked by combining individually constrained systems.

**Limit:** The result is broader than merely asking multiple models until one agrees; task decomposition and complementary capabilities matter.

**Our use:** Direct motivation for compositional tests; do not claim splitting safe subtasks is a new discovery.

### R15. Coordination to resist modification or shutdown

Agrawal, Ebadian and Hammond, 2026. [Event-listed source](https://dl.acm.org/doi/abs/10.65109/HQQZ1937). [Primary/author source inspected](https://ebadian.org/preprint/multiagent_offswitch_cr.pdf).

Access: Publisher blocked; author-hosted AAMAS paper introduction reviewed.

The Multi-Agent Off-Switch Game shows within formal models that individual corrigibility need not compose under strategic interaction.

**Limit:** This is a theoretical result under stated game assumptions, not evidence that deployed agents actually resist shutdown.

**Our use:** Supports the general non-composition motivation; does not validate the monitor.

### R16. From individual cooperation properties to system outcomes

Tilli, 2026. [Event-listed source](https://openreview.net/forum?id=00KtDBoKnO). [Primary/author source inspected](https://www.lesswrong.com/posts/xgBjERzu8L9tsRrgk/agent-properties-for-safe-interactions).

Access: OpenReview browser challenge; indexed primary abstract and author companion reviewed.

Agent Properties for Multi-Agent Safety advocates studying properties that explain interaction outcomes across settings rather than relying on toy-game results alone.

**Limit:** The companion is an earlier author exposition; do not treat it as the exact final workshop paper. No full-paper review is claimed.

**Our use:** Make evidence selection a clearly isolated mechanism, and explicitly limit external validity.

### R17. Defining collective agency

Jørgensen, Weichwald and Hammond, 2026. [Event-listed source](https://openreview.net/forum?id=NacA6YRBNX). [Primary/author source inspected](https://arxiv.org/abs/2605.00248).

Access: OpenReview blocked; primary CLeaR preprint abstract reviewed.

Causal Foundations of Collective Agency formalizes when a group-level goal-directed description predicts behavior using causal games and abstraction.

**Limit:** Correlated messages, many agents, or a centrally assigned workflow alone do not establish emergent collective agency.

**Our use:** Call our setting a centrally instrumented workflow, not proof of an emergent swarm.

## Track 3

### R18. A2A agent-to-agent protocol

Google, 2025. [Event-listed source](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/).

Access: Official protocol announcement reviewed.

A2A addresses agent interoperability, discovery and collaboration across implementations.

**Limit:** Interoperability is not a guarantee that claimed identity, permissions or results are trustworthy.

**Our use:** Relevant to a future integration; no A2A implementation is needed to answer the main question.

### R19. IDs for AI Systems

Chan et al., 2024. [Event-listed source](https://arxiv.org/abs/2406.12137).

Access: Primary abstract reviewed.

IDs for AI Systems examines identification infrastructure and its role in accountability and oversight.

**Limit:** Identity requires decisions about instances, operators, copies and lifecycle; a display name is inadequate.

**Our use:** Use stable harness-issued worker IDs and disclose trusted identity assumptions.

### R20. A Watermark for Large Language Models

Kirchenbauer et al., 2023. [Event-listed source](https://proceedings.mlr.press/v202/kirchenbauer23a.html).

Access: Official proceedings abstract reviewed.

Introduces a statistical watermarking approach for identifying generated language through token-selection patterns.

**Limit:** Text provenance is different from secure agent identity, authorization or a tamper-proof runtime ledger.

**Our use:** Reject a text-watermark shortcut for authenticating which worker performed a tool action.

### R21. Cooperative AI via Decentralized Commitment Devices

Sun et al., 2023. [Event-listed source](https://arxiv.org/abs/2311.07815).

Access: Primary abstract reviewed.

Examines decentralized commitment devices as a way for artificial agents to support cooperation.

**Limit:** Credible commitment depends on enforceability and information assumptions, not merely a model promising something.

**Our use:** Keep policy facts in trusted execution state; agent statements are evidence to assess.

### R22. Game Manipulators: the Strategic Implications of Binding Contracts

Ramirez et al., 2023. [Event-listed source](https://arxiv.org/abs/2311.10586).

Access: Primary abstract reviewed.

Game Manipulators studies how binding contracts can change strategic behavior and allow an intermediary to extract value.

**Limit:** Commitment can create harmful equilibria or redistribute welfare; more enforceability is not always socially beneficial.

**Our use:** Background for adversarial commitments; not an implementation requirement.

### R23. Formal Contracts Mitigate Social Dilemmas in Multi-Agent RL

Haupt et al., 2022. [Event-listed source](https://arxiv.org/abs/2208.10469).

Access: Primary abstract reviewed.

Studies formal contracts as a mechanism for improving cooperation in multi-agent reinforcement-learning social dilemmas.

**Limit:** Contract space, observability and enforcement assumptions constrain the result; these are not automatically satisfied by LLM conversations.

**Our use:** Use explicit executable permissions, not free-form approval statements.

### R24. Program Equilibrium

Tennenholtz, 2004. [Event-listed source](https://www.sciencedirect.com/science/article/pii/S0899825604000314).

Access: Publisher restricted; indexed primary abstract reviewed.

Program Equilibrium studies strategic interaction where agents can condition on the other participants’ program descriptions.

**Limit:** Readable code and binding execution differ from unverifiable descriptions of an agent’s intentions.

**Our use:** Foundational track-3 context; avoid claiming that text self-reports implement program equilibrium.

## Track 4

### R25. Secret Collusion among AI Agents

Motwani et al., 2024. [Event-listed source](https://proceedings.neurips.cc/paper_files/paper/2024/hash/861f7dad098aec1c3560fb7add468d41-Abstract-Conference.html). [Primary/author source inspected](https://arxiv.org/abs/2402.07510).

Access: Proceedings timeout; primary preprint abstract reviewed.

Secret Collusion among AI Agents examines multi-agent deception via steganographic communication.

**Limit:** Unusual shorthand or compressed messages are not by themselves evidence of malicious hidden coordination.

**Our use:** Our artifact-lineage experiment does not detect arbitrary steganography; state this limitation.

### R26. Detecting Multi-Agent Collusion Through Multi-Agent Interpretability

Rose et al., 2026. [Event-listed source](https://arxiv.org/abs/2604.01151). [Primary/author source inspected](https://arxiv.org/html/2604.01151v1).

Access: Primary abstract and v1 methods/results passages reviewed.

NARCBench studies detecting multi-agent collusion through multi-agent interpretability, including transfer challenges across settings.

**Limit:** Internal-activation access differs from a black-box log monitor. Distinguish instructed from emergent collusion, and do not mix versions when reporting numbers.

**Our use:** Closest benchmark context; avoid claiming first multi-agent collusion detection.

### R27. AI Control: Improving Safety Despite Intentional Subversion

Greenblatt et al., 2024. [Event-listed source](https://arxiv.org/abs/2312.06942). [Primary/author source inspected](https://arxiv.org/abs/2312.06942v5).

Access: Primary abstract reviewed; v5 metadata verified.

AI Control evaluates protocols for deploying untrusted models while preventing intentionally harmful outputs, including monitoring and trusted editing.

**Limit:** Detection quality alone is not end-to-end safety; attacker strategy, protocol and usefulness matter.

**Our use:** Measure false alarms and legitimate acceptance, and distinguish retrospective detection from prevention.

### R28. Attributing failures in multi-agent systems

Zhang et al., 2025. [Event-listed source](https://openreview.net/forum?id=GazlTYxZss). [Primary/author source inspected](https://github.com/ag2ai/Agents_Failure_Attribution/blob/main/README.md).

Access: OpenReview blocked; official project README reviewed.

Which Agent Causes Task Failures and When? studies identifying the responsible agent and step in failed multi-agent workflows.

**Limit:** Assigning a failure to an agent differs from deciding whether a coordinated workflow violates a policy; reference or grading errors can also cause apparent failure.

**Our use:** Require evidence IDs and do not blame a worker when observation is insufficient.

### R29. Emergent communication between agents

Riedl, 2026. [Event-listed source](https://openreview.net/forum?id=SRn1MtMPRq). [Primary/author source inspected](https://arxiv.org/abs/2510.05174v4).

Access: OpenReview blocked; primary preprint v4 abstract reviewed.

Emergent Coordination in Multi-Agent Language Models uses information decomposition to distinguish higher-order structure from mere temporal coupling in a guessing game.

**Limit:** Prompts and identity differentiation influence results; the abstract does not establish that any communication graph is a goal-directed collective.

**Our use:** Use operational definitions and causal controls rather than anthropomorphic interpretation.

### R30. CaMeLs Can Use Computers Too

Foerster et al., 2026. [Event-listed source](https://arxiv.org/abs/2601.09923). [Primary/author source inspected](https://arxiv.org/abs/2601.09923v3).

Access: Primary v1 passages and current v3 abstract reviewed.

CaMeLs Can Use Computers Too separates trusted planning from untrusted observations. The current version describes NOVA and discusses branch-steering limitations.

**Limit:** Instruction isolation does not solve every perception or action-selection attack. Version differences matter; do not mix names/results across revisions.

**Our use:** The monitor must treat agent-authored rationale as data; our recorder is still a trusted assumption.

### R31. Mediated Multi-Agent Reinforcement Learning

Ivanov, Zisman and Chernyshev, 2023. [Event-listed source](https://arxiv.org/pdf/2306.08419.pdf). [Primary/author source inspected](https://arxiv.org/abs/2306.08419).

Access: Primary abstract reviewed.

Studies a mediator that acts for consenting agents while learning socially beneficial equilibria.

**Limit:** Social welfare maximization alone can sacrifice individual goals; incentives and the option not to participate matter.

**Our use:** Background for governance mechanisms, not evidence that a trusted monitor will remain trusted.

### R32. Stackelberg Attacks on Auctions and Transaction Fee Mechanisms

Landis and Schwartzbach, 2023. [Event-listed source](https://arxiv.org/abs/2305.02178).

Access: Primary abstract reviewed.

Shows how strategic commitments can alter auction equilibria and undermine auctioneer revenue under specific assumptions.

**Limit:** The attack relies on commitment and valuation/congestion conditions; do not extrapolate to every market or agent swarm.

**Our use:** A reason to assess who benefits from coordination, and a possible future domain.
