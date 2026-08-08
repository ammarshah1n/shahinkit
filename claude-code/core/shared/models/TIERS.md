# Model Tiers

Adapter input for budget-aware role resolution. Values are observed from each
host's own model roster, not assumed.

## Rosters

### Claude Code

| Model | Position | Notes |
|---|---|---|
| `opus` | Frontier | Controller tier. Highest cost per token. |
| `sonnet` | Balanced | Worker default for research, implementation, review. |
| `haiku` | Small | Mechanical and deterministic work. |

Claude Code plans gate **usage quota, not model access**. A Pro subscriber and a
Max subscriber can both select `opus`; the Max subscriber can afford to spend it.
So on this host the budget profile changes *how much the controller does inline*,
not which models a role may name.

### Codex

Roster reported by the Codex CLI:

| Model | Codex description | Supported efforts |
|---|---|---|
| `gpt-5.6-sol` | Latest frontier agentic coding model | low, medium, high, xhigh, max, ultra |
| `gpt-5.6-terra` | Balanced agentic coding model for everyday work | low, medium, high, xhigh, max, ultra |
| `gpt-5.6-luna` | Fast and affordable agentic coding model | low, medium, high, xhigh, max |
| `gpt-5.4-mini` | Small, fast, cost-efficient model for simpler coding tasks | low, medium, high, xhigh |

Tier order: `sol` > `terra` > `luna` > `mini`.

Codex plans gate **model access as well as quota**. `luna` is the affordable
agentic rung between `terra` and `mini`, and is what makes a genuine low-budget
profile possible: real agentic coding without frontier cost.

### OpenCode

Same roster as Codex, namespaced `openai/`.

## Effort Is a Separate Axis

Prior to this document every non-mechanical Codex role ran `high`. That is wrong
in both directions:

- **Review is under-served by a flat effort.** Review is adversarial reading
  where a miss is silent. It is the one worker role worth spending above the
  implementation role, because a cheap reviewer approves cheap mistakes.
- **Research is over-served.** Source extraction and enumeration are recall
  tasks. `medium` on a capable model beats `high` on a weak one at lower cost.
- **Mechanical must stay `low`.** Reasoning effort on deterministic work is
  spend with no corresponding accuracy gain.

Roles therefore resolve a `(model, effort)` pair, never a model alone.

## Role Intent

| Role | Work shape | What decides the tier |
|---|---|---|
| `controller` | Architecture, taste, synthesis, acceptance | Never economised. Frontier at every budget. |
| `research` | Reading, source discovery, current facts | Recall over reasoning. Effort down, comprehension up. |
| `implementation` | Bounded change from an exact spec | Scales with budget. The main token sink. |
| `review` | Adversarial critique, verification | Buy above implementation. Silent-failure risk. |
| `mechanical` | Extraction, mapping, formatting | Cheapest available, `low` effort, always. |

## Resolution Rule

The budget preset supplies each role's `(model, effort)` pair per host. Roles
never inherit from the controller or from each other — see `roles.schema.json`.
