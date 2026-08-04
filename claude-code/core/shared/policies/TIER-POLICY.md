# Tier Policy

## Defaults Down

| Task shape | Default route | Gate |
|---|---|---|
| Mechanical extraction, mapping, formatting, renames, file lists, repetitive edits | `{{GRUNT_MODEL}}` | Exact spec; deterministic verification. |
| Research, reading, source discovery, current docs, external facts | `{{RESEARCH_MODEL}}` | Findings must include source path/URL and uncertainty. |
| Bounded implementation/review from exact spec | `{{WORKER_CMD}}` with the cheapest model that satisfies the spec | Controller reviews diff/output before acceptance. |
| Architecture, product taste, final synthesis, final acceptance, integrity-critical judgement | Controller only | Do not delegate. |
| Controller-tier subagent | Forbidden by default | Prompt must include `[CONTROLLER-TIER-JUSTIFIED: reason]`. |

## Controller-Tier Marker

Required literal marker:

```text
[CONTROLLER-TIER-JUSTIFIED: reason]
```

Valid reasons are concrete:
- Integrity-critical work where a mistake cannot be caught deterministically.
- Architecture/taste/final synthesis work that the controller must own.
- Cross-cutting ambiguity where cheaper workers cannot safely preserve context.

Invalid reasons:
- "Better quality" without a specific failure mode.
- "Faster to ask the strong model."
- "Unsure which route to use."

## Why Laziness Must Write Its Own Justification

Premium-tier delegation hides cost and context burn. The marker forces the caller to state the reason at the dispatch point, makes exceptions searchable, and turns lazy routing into an auditable decision. If the caller cannot write the one-line reason, it is not justified.

## Acceptance

- No marker -> no controller-tier dispatch.
- Marker present -> controller still reviews output before it can count as accepted.
- Worker "done" claims are evidence requests, not facts.
