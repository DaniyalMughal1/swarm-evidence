# Every schedule recording

All **11** recording links on the schedule were extracted. Total published duration: **8 hours 49 minutes 9 seconds**. Public caption tracks were retrieved for all eleven and research-relevant passages reviewed. These notes are original synthesis, not a claim to have watched every video or verified every spoken claim. Automatic captions can misrecognize names and numbers; timestamps are approximate offsets in each recording.

For the shortest useful viewing route: Kitaoka’s threat-model/budget/Q&A segments, Adaption’s inference segment, Jurgis’s evidence-trust discussion, then Yan/Sikora’s reproduction advice. Current written event rules take precedence over spoken logistics.

| ID | Recording | Scheduled UTC | Duration |
|---|---|---|---|
| V01 | [Adaption workshop](https://us06web.zoom.us/rec/share/MoHLrr8zPSlCkc0Gwubi2sW5-BDKK8hDrWsS9bBMf-m4Urhz1iEqXe9-kWdjdhaa.bAmJvTHee2iK4mgc) | 2026-11-05 13:15 | 0:55:43 |
| V02 | [John Kitaoka — securing systems against agent swarms](https://us06web.zoom.us/rec/share/OkOtOYVrZQ-AcL8KW67GljV9aSwr9_fpUkSwPnSOi9gfbSKvtgQ-Hmv-iISMs0e3.ws_5jHI_LbDWFMVV) | 2026-11-05 15:00 | 1:00:02 |
| V03 | [Grant Fleming — adversarially optimized swarms](https://us06web.zoom.us/rec/share/pcTdhZyUb5iQ61WCsTJOTpanXYni2P47SvozCVq-BKhPg6_cGO3VDkzozs4xwHah.9Jz23XWlGZa03bA9) | 2026-11-05 22:00 | 0:58:15 |
| V04 | [Nguyen Tran — logistics](https://us06web.zoom.us/rec/share/rMUl0k0JCmN7Qs8cuMrXiXQjONccIgvp7SLc37UT_6BmaMvec0MGxTaaRanxJWFR.JLX29Mo6bBQqrnww) | 2026-11-06 13:30 | 0:58:56 |
| V05 | [John Yan and Elvis Sikora — getting started with swarm incidents](https://us06web.zoom.us/rec/share/gOe4dpuABPxMRIrx-xkqSxLDDaYDQW8qeiym12IYpShp6iq1IkI7O8JwTLQNzJ71.sh2YTRNpHZWbiS_i) | 2026-11-06 18:00 | 0:28:23 |
| V06 | [Rowan Howard-Jones — swarm investigation](https://us06web.zoom.us/rec/share/CPYCqBq2YRdQczggQMYlXNYpP6HJXlKdEZK4mKcJlT5S0cd1KHiXahEoX8Ycu52K.XTMOYyvML7pKrsLP) | 2026-11-06 19:00 | 0:48:57 |
| V07 | [Elias Stengel-Eskin — emergent communication](https://us06web.zoom.us/rec/share/5hdxZjVfeJzmvZVX4RexSGjFW3DYi0MwwYNw3hlLrZgQwonxZPyg6io03GXoo781.djuxVD-HTEEPHxdA) | 2026-11-06 20:15 | 0:58:11 |
| V08 | [Judd — kickoff](https://us06web.zoom.us/rec/share/1d4YC_CQLFIA8bY6EuAOpNovn0A16TUQ6ec2XWEHwN4bWOTlXVBkWqXeanyC7XLn.QTe7t5x9ZKnW8HwA) | 2026-11-06 21:30 | 0:48:54 |
| V09 | [Kamil — logistics](https://us06web.zoom.us/rec/share/o1v_ZDFrQa91lqwK1jUlyBVsoeMXUv29EPXYLv0AE0dfMJSMRYXYNUwANJOb_AhR.2uEr_XTuLQUOWUq6) | 2026-11-06 22:30 | 0:28:55 |
| V10 | [Justin Shenk — observing agent swarms](https://us06web.zoom.us/rec/share/-deJ2gMShsUX8VvSXJ2sjt1fnYpUHBCh_llwuhNEPfGo6qnTypE3oB5IlgZs3Xo.fGIecdFLP9kGW7_U) | 2026-11-07 13:00 | 0:23:23 |
| V11 | [Jurgis Kemeklis — AI control](https://us06web.zoom.us/rec/share/ANUGOErR5--7C_W3sexzuffjo2nvbm0yyTzAgwIqNXvjp2cikjrkq3FvNKOoLd8b.6-M-WkvIHdsyQgXh) | 2026-11-07 19:00 | 0:59:30 |

## V01. Adaption workshop

[Open recording](https://us06web.zoom.us/rec/share/MoHLrr8zPSlCkc0Gwubi2sW5-BDKK8hDrWsS9bBMf-m4Urhz1iEqXe9-kWdjdhaa.bAmJvTHee2iK4mgc).

- **01:42; 40:28–43:38:** Hosted inference is available in addition to data generation and training. Current official docs independently confirm the API path.
- **15:11–16:00; 47:03–49:52:** Small monitors trained or evaluated on synthetic traces are an application direction. Compare quality, latency and cost against the unfine-tuned base.
- **12:51; 20:11–20:26; 23:22:** Training/data generation have queue time; dashboard credit units need checking. Demonstration timings are not guarantees.

**Project implication:** Use hosted inference first. Keep dataset invention optional and never use generated prose as ground truth.


## V02. John Kitaoka — securing systems against agent swarms

[Open recording](https://us06web.zoom.us/rec/share/OkOtOYVrZQ-AcL8KW67GljV9aSwr9_fpUkSwPnSOi9gfbSKvtgQ-Hmv-iISMs0e3.ws_5jHI_LbDWFMVV).

- **12:42–15:33:** Define the threat model; distributed actions can require corroboration across agents.
- **18:07–19:52:** Preliminary examples illustrate weak local detection and potential benefit of joint context. We do not reuse the spoken percentages as validated benchmark results.
- **28:35–31:59:** Control token/attempt budgets and address how a monitor chooses which agents to aggregate.
- **56:11–57:25:** Q&A explicitly proposes corroborating relevant actions across agents. Credit this as motivation, not our invention.

**Project implication:** Most relevant talk. Compare retrieval policies at fixed context caps; explicitly cite the idea’s provenance.


## V03. Grant Fleming — adversarially optimized swarms

[Open recording](https://us06web.zoom.us/rec/share/pcTdhZyUb5iQ61WCsTJOTpanXYni2P47SvozCVq-BKhPg6_cGO3VDkzozs4xwHah.9Jz23XWlGZa03bA9).

- **Talk demonstration:** A group of helpful-seeming personas pressures a debugging agent toward a forbidden token-handling action. The local demonstration uses adversarial social context.
- **Closing Q&A, approximately 55:00:** A many-agent attack needs a matched single-agent turns/tokens control to identify a group effect.

**Project implication:** Do not confuse additional persuasion budget with a uniquely multi-agent vulnerability. Use only synthetic local payloads.


## V04. Nguyen Tran — logistics

[Open recording](https://us06web.zoom.us/rec/share/rMUl0k0JCmN7Qs8cuMrXiXQjONccIgvp7SLc37UT_6BmaMvec0MGxTaaRanxJWFR.JLX29Mo6bBQqrnww).

- **Logistics presentation:** Covers event structure, tracks, resources, report expectations and participation questions. The current website is authoritative if wording differs.
- **41:42:** The comment about no separate API sponsorship should be read alongside the Adaption workshop and current inference docs.

**Project implication:** Use the current Guidelines template and rubric; do not assume another provider’s credits exist.


## V05. John Yan and Elvis Sikora — getting started with swarm incidents

[Open recording](https://us06web.zoom.us/rec/share/gOe4dpuABPxMRIrx-xkqSxLDDaYDQW8qeiym12IYpShp6iq1IkI7O8JwTLQNzJ71.sh2YTRNpHZWbiS_i).

- **Main talk and shared slide-links document:** Use incident registries and public artifacts to form a causal hypothesis; reproduce manageable components when full lab access is unavailable.
- **Linked playbook:** Separate discovering a channel, using it, spreading a behavior and successful harm. Keep near misses and bounded null results.

**Project implication:** Study a small mechanism with executable outcomes. A synthetic reproduction tests a hypothesis; it does not independently confirm the original incident.


## V06. Rowan Howard-Jones — swarm investigation

[Open recording](https://us06web.zoom.us/rec/share/CPYCqBq2YRdQczggQMYlXNYpP6HJXlKdEZK4mKcJlT5S0cd1KHiXahEoX8Ycu52K.XTMOYyvML7pKrsLP).

- **24:14:** Detectors based on current limitation-workarounds can become brittle as agent capabilities change.
- **33:46; 36:11:** Adversaries can trade off cost against visibility; a detector trained on observed incidents may overfit current samples.

**Project implication:** Differentiate fleet from swarm, preserve attribution uncertainty, and hold out mechanisms rather than just paraphrases.


## V07. Elias Stengel-Eskin — emergent communication

[Open recording](https://us06web.zoom.us/rec/share/5hdxZjVfeJzmvZVX4RexSGjFW3DYi0MwwYNw3hlLrZgQwonxZPyg6io03GXoo781.djuxVD-HTEEPHxdA).

- **36:22:** Communication constraints can induce compressed language and abbreviations.
- **47:41:** The described cooperative setting is distinct from adversarial monitoring.
- **50:44:** Public communication data may support follow-up detector research.

**Project implication:** Include benign coordination. Shorthand, non-English text, or unusual syntax alone is not a malicious label.


## V08. Judd — kickoff

[Open recording](https://us06web.zoom.us/rec/share/1d4YC_CQLFIA8bY6EuAOpNovn0A16TUQ6ec2XWEHwN4bWOTlXVBkWqXeanyC7XLn.QTe7t5x9ZKnW8HwA).

- **Opening, approximately 03:00:** Research usefulness, independent thinking and publication/dual-use judgment matter.
- **23:32:** Be willing to change a failing approach rather than spend the whole weekend defending it.

**Project implication:** A rigorous, bounded finding is more valuable than an unsupported ambitious story. Assess novelty against current work.


## V09. Kamil — logistics

[Open recording](https://us06web.zoom.us/rec/share/o1v_ZDFrQa91lqwK1jUlyBVsoeMXUv29EPXYLv0AE0dfMJSMRYXYNUwANJOb_AhR.2uEr_XTuLQUOWUq6).

- **Main logistics talk:** Explains participation and submission logistics. Verify deadlines, formatting and resubmission rules against the current event page.

**Project implication:** Protect writing and submission time. The report, required appendix and working links come before an optional video.


## V10. Justin Shenk — observing agent swarms

[Open recording](https://us06web.zoom.us/rec/share/-deJ2gMShsUX8VvSXJ2sjt1fnYpUHBCh_llwuhNEPfGo6qnTypE3oB5IlgZs3Xo.fGIecdFLP9kGW7_U).

- **07:07–07:25:** Distinguishes centrally managed fleets from emergent swarms.
- **09:28:** Operational descriptions should support prediction and validation, not merely analogy.
- **17:45; 19:22:** Concentrated activity is not by itself causal leadership; identity/revocation remain important questions.

**Project implication:** Use operational definitions and interventions. Our known three-worker workflow does not establish emergent collective agency.


## V11. Jurgis Kemeklis — AI control

[Open recording](https://us06web.zoom.us/rec/share/ANUGOErR5--7C_W3sexzuffjo2nvbm0yyTzAgwIqNXvjp2cikjrkq3FvNKOoLd8b.6-M-WkvIHdsyQgXh).

- **00:22–00:36:** Missing actions or evidence are a problem for oversight.
- **27:42:** Control evaluates safety alongside usefulness under an adversarial assumption.
- **36:33–37:25:** Multiple monitors and larger context bring scaling and evidence-selection questions.
- **53:44–54:26:** Log manipulation limits what a monitor can infer.

**Project implication:** Separate detection from prevention, measure legitimate acceptance, and disclose the trusted-recorder boundary.


## Slides and linked workshop documents

[Yan/Sikora slide-links document](https://docs.google.com/document/d/1Ykhw87lfvDrV7IOq22ESEicQfvbNf3l3gXAEhnur1hk/edit?usp=sharing) links to [a task-framing replication](https://docs.google.com/document/d/1pYyJAGPE-muTiXRX_QCuT1GXwyrPN-vpJzwVnxSeGVE/edit), [the incident-science playbook](https://docs.google.com/document/d/1oR1YQbLEbS-emeWRS8nLx91pYrgQSwU7OrRTGxiN8pg/edit), [swarms.wiki](https://swarms.wiki/), and [a Hugging Face incident reproduction](https://www.lesswrong.com/posts/fMnC6ZD37qrnZAFYz/openai-huggingface-a-reproduction-and-lessons-for-alignment). It also links to [public discussion of a recent incident](https://x.com/Marcus_J_W/status/2118093146483810386/quotes); that discussion is not independent evidence for our result.

The two linked Google documents were retrieved. The replication uses a public benchmark as a substitute for an internal one and explicitly notes task/base-rate differences and uncertainty in an ablation. The playbook favors mechanism-level reproduction, controlled steering, held-fixed checkpoints and honest nulls. Some example descriptions in its draft are marked for publication confirmation; this pack does not republish those tentative details as established findings.

## Retrieve captions yourself

`research/recordings.json` contains stable share links, duration and hashes of the caption files retrieved on November 8. It deliberately omits signed media URLs and raw transcripts. With yt-dlp installed:

```bash
python3 scripts/fetch_recordings.py --destination work/recordings
```

The script fetches captions only, not video. Public share links may later expire or require login; retrieval success today is not a permanent availability promise. Keep fetched transcripts out of Git. Full transcripts from this preparation are already retained in the local workspace, outside the public repository.
