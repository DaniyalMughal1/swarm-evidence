# Adaption access and experiment budget

The user selected the event's sponsor credits as the experiment resource. Do not assume additional paid API access. No model call, account activation, or credited balance has been verified for this project yet.

## Claim access

1. Register on the [sprint page](https://apartresearch.com/sprints/swarm-alignment-2026).
2. Sign up at [Adaption](https://adaptionlabs.ai/app) with the same email. The event advertises $500 platform credits and three months Premium.
3. Check the onboarding email and dashboard for actual activation, credited units, balance, limits and expiration. A late Sunday registration may need support; the page's pre-event email promise does not establish immediate activation now.
4. In Settings → API keys, create a key and store it locally as `ADAPTION_API_KEY`. Do not paste it into chat, Git, a notebook output or the report.
5. Use the [Adaption Discord](https://discord.gg/8hjcFWY8) if needed. The user must send any support request; none has been sent by this project.

## Verified inference path

Adaption is not restricted to dataset creation and training. The [current quickstart](https://docs.adaptionlabs.ai/inference-stacks/quickstart/) documents direct model inference with Python SDK version 0.16.0 or newer. The [hosted model page](https://docs.adaptionlabs.ai/inference-stacks/models/) documents per-token prices and model availability by key. These pages were retrieved November 8, 2026.

```python
from adaption import Adaption

client = Adaption()  # Reads ADAPTION_API_KEY locally.
available = client.models.list(type="hosted").data
model_ids = [model.id for model in available]
# Select an accessible model after checking rates and the credited balance.
response = client.responses.create(model=chosen_model, input=prompt)
text = response.output_text
```

This is an integration sketch: `chosen_model` and `prompt` must be supplied by the runner. Verify output caps, usage fields, reasoning-token billing, sampling support, timeouts, and retry behavior in the installed SDK. Pin the installed SDK and tokenizer versions in the implemented repository.

## Price snapshot, not a spending authorization

Published rates below are **credits per million tokens**, not necessarily US dollars. Cached-input discounts are omitted for conservative planning. Model availability can differ by key; list it first. [Official rates](https://docs.adaptionlabs.ai/inference-stacks/models/).

| Hosted model | Input credits / M | Output credits / M |
|---|---:|---:|
| gemma-4-31b-it | 0.09 | 0.34 |
| glm-5.2 | 1.40 | 4.40 |
| qwen3.5-397b | 0.55 | 3.50 |
| gemma-4-26b-a4b-it | 0.0765 | 0.255 |
| qwen3.8-27b | 0.039 | 1.25 |
| deepseek-v4-flash | 0.04444 | 0.13332 |
| glm-53-flash | 0.15 | 0.50 |

Candidate primary monitor: qwen3.5-397b if accessible and pilot parsing is reliable; candidate second-family check: gemma-4-31b-it. This is a research-design choice, not a claim that one is best. Choose on development behavior and current access, then freeze. Do not pick the model using held-out performance.

At the published Qwen rate, planned stages 1–4 imply at most 5.28 million capped input tokens and 0.50688 million capped output tokens, about **4.67808 published credit units**, before development, retries, diagnostics, worker rollouts, and any separately billed internal reasoning. This is arithmetic over planned caps, not a measured invoice or a dollar estimate. The primary two-method stage alone implies 0.24M input and 0.04608M output, about 0.29328 units on that same restricted basis. If provider billing/cap semantics differ, replace these projections before running.

Maintain a cost ledger with request ID, model, billed input/cached/output/reasoning tokens, billed credits if provided, estimated cost otherwise, latency, status and retry count. Check balance before/after the pilot. Reserve at least 20% of credited balance and protect the report deadline. Do not enable auto-recharge or switch to a separately paid provider without new authorization.

## Where the other sponsor features fit

AutoScientist automates data/training iteration; Adaptive Data transforms or expands datasets; Invent-a-Dataset creates candidate data from prompts. The event advertises broad multilingual support. These can help generate *development surface variations*, but they do not supply trustworthy evaluation labels. Check synthetic validity with the executable oracle and manually inspect examples.

Do not fine-tune on the critical path. Workshop guidance places dataset generation and training on asynchronous queues; reported demonstration times are not service guarantees. A later small-monitor training extension must use development data only, compare the same base model before/after training, and disclose synthetic-source and contamination risks.

The logistics recording's statement that there were no separate API credits should not be interpreted as proof Adaption lacks inference: the workshop at 40:28–43:38 and current documentation explicitly describe it. No separate OpenAI/Anthropic/OpenRouter grant has been established.
