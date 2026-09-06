---
name: onboard
description: Set the budget profile that decides which model each role uses and how aggressively work is delegated, and the explanation level used when talking to you. Asks which hosts you use, what you pay for, and whether you have coded before, offers presets or a local picker page, previews the change, and applies only on approval.
---

# Onboard

Run for `/onboard`, "set up my models", "I'm paying for X, optimise it", or when
delegation feels wrong for the subscription in use.

Hosts are **asked, never detected**. Subscription tier is **self-declared**: no
host exposes plan or remaining quota to an agent. Never infer either.

## 1. Ask

Ask all three questions in one turn. Do not ask them one at a time.

1. Which do you use — Claude Code, Codex, OpenCode? More than one is normal.
2. For each: no subscription, entry, mid, or top tier.
3. Have you written code before, or would you rather have everything explained
   in plain English? Ask it that plainly; never infer fluency from the fact
   that the user is running a terminal.

Map the answers to a preset:

| Answers | Preset |
|---|---|
| Entry tier anywhere, or unsure | `default` |
| Mid tier on at least one host | `plus` |
| Top tier on every host named | `max` |

State the mapping and the preset you intend to use before going further.

## 2. Offer the picker

Presets are the fast path. Offer the picker only when the user wants to see the
alternatives or hand-pick roles:

```text
open "<install root>/.shahinkit-data/picker.html"
```

The page is offline and self-contained. It shows every preset side by side, lets
any role be overridden, and copies a profile to the clipboard. The user pastes it
back. Take the pasted JSON as the profile verbatim — do not re-derive it.

## 3. Write the profile

Write the chosen profile to `<install root>/.shahinkit-data/budget.json`. It must
validate against `core/shared/models/budget.schema.json`: `schema_version`,
`hosts`, `preset`, complete `roles` for every declared host, and `delegation`.

Preset values come from `core/shared/models/presets.json`. Never invent a model
name; use only what the presets and that host's roster contain.

## 3b. Write the explanation level

Write one word to `<install root>/.shahinkit-data/explain-mode`: `plain` when the
user has not coded or asked for plain English, `technical` otherwise. It is a
user-owned file, not part of the budget profile and not installer owned, so it
survives every re-render and needs no preview or approval step.

`plain` changes how every later answer reads: each technical term is expanded on
first use, each command, file, error, and recommendation is described in what it
does and why it matters, and nothing is left as bare jargon. It never removes
technical substance, warnings, risk, or uncertainty, and code, commands, diffs,
and paths stay exact. Say that the user can switch any time with `explain
simply` or `technical mode`, which rewrites this same file.

When the file is missing — every install that predates this behaviour — ask
question 3 on its own at the start of the session, write the answer, and stop
asking. Do not re-run the whole budget interview to collect it.

## 4. Preview, then apply

Render through the manager and show the preview. Apply only after explicit
approval. The profile changes agent model assignments, reasoning effort, and the
delegation thresholds stated in host instructions.

Report what changed per role, plainly:

```text
implementation  gpt-5.6-luna high  ->  gpt-5.6-terra high
review          gpt-5.6-terra high ->  gpt-5.6-terra xhigh
delegation      strict (>2 files)  ->  moderate (>3 files)
```

## 5. Mention the escape hatch once

Path opt-out lives at `<install root>/.shahinkit-data/opt-out` — one absolute
path prefix per line, `#` for comments. Any session whose working directory sits
at or under a listed path gets no ShahinKit lifecycle context at all: no Prime
pointer, no Caveman restatement, no worker-scope note. The file is not installer
owned, so hand edits survive every re-render. A missing file means no opt-outs.

Create it only when asked. Mention it once; do not offer it repeatedly.

## Boundaries

- Never guess a subscription tier, an explanation level, or billing state.
- Never ask the explanation question more than once per recorded answer.
- Never set a worker role above the controller.
- `mechanical` stays at `low` or `medium` effort; reasoning spend on
  deterministic work buys nothing.
- Changing the profile is a config change, not a code change: preview and
  approval are required, and no other file is touched in the same step.
