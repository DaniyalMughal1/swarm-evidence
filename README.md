# Swarm Evidence

**Research preparation and implementation handoff, November 8, 2026. No experiments or research results yet.**

Can a monitor catch violations split across agents by selecting evidence through artifact dependencies, while staying within the same context budget as ordinary log review?

Prepared for the [Swarm Alignment Hackathon](https://apartresearch.com/sprints/swarm-alignment-2026). Intended primary track: Multi-Agent Oversight and Control; secondary: Sandboxes and Testbeds. The proposed contribution is a controlled measurement of evidence selection under limited context, not the invention of graph monitoring or agent provenance.

## Start here

1. [Claude handoff](CLAUDE_HANDOFF.md): what to build, run, and deliver next.
2. [Project plan](docs/PROJECT_PLAN.md) and [implementation specification](docs/IMPLEMENTATION_SPEC.md): hypothesis, controls, staged experiments, costs, and acceptance gates.
3. [Event brief](docs/EVENT_BRIEF.md) and [submission checklist](docs/SUBMISSION_CHECKLIST.md): requirements, rubric, deadline, and final upload steps.
4. [Recording guide](docs/RECORDINGS.md): all 11 recordings, durations, timestamped notes, and retrieval instructions.
5. [Reading guide](docs/READING_GUIDE.md): all 32 suggested readings, source access levels, and implications.
6. [Related work and project choice](docs/RELATED_WORK.md): closest competing approaches and what remains worth testing.
7. [Adaption setup](docs/ADAPTION_SETUP.md): sponsor-credit workflow and verified inference documentation.
8. [Report outline](report/REPORT_OUTLINE.md): official section structure, evidence placeholders, and required appendix.

## What exists now

The research pack includes the event inventory, recording and reading catalogs, source-based research notes, a reviewed experimental design, and a concrete build specification. All eleven public recording transcripts were retrieved during preparation; original notes are published here, while full transcripts remain local. See [research coverage](docs/RESEARCH_COVERAGE.md) for access limitations. A source listing is not a claim that every paper was read in full.

The simulator, model adapter, benchmark runs, figures, and completed paper are the next implementation phase. Nothing in this repository should be cited as an empirical finding from Swarm Evidence until those artifacts exist.

Validate the preparation pack with Python 3.11+:

```bash
python3 scripts/check_pack.py
```

## Deadline and access

The official cutoff is **November 9, 2026 at 06:59 Toronto / 11:59 UTC**, corresponding to November 8 at 23:59 Anywhere on Earth. Aim to finish on November 8. Register through the event page, then sign up at [Adaption](https://adaptionlabs.ai/app) with the same email. Confirm sponsor credits before making model calls. Budget authority is limited to credited funds; no out-of-pocket fallback is assumed.

## Research integrity and provenance

This preparation pack was created during the sprint on November 8. No previous project code was imported. Any later reuse must be identified as preexisting in this README and the report. Codex assisted with source discovery, transcript extraction, synthesis, and planning. Claude is intended to implement the experiment; human authors must verify the final claims and submission.

MIT applies to original repository code and prose. Linked papers, talks, official templates, and datasets retain their own rights and terms. Full third-party papers and transcripts are not included in the public repository.
