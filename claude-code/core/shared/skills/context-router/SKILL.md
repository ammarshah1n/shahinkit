---
name: context-router
description: Route requests to smallest authoritative project and memory context.
---

# Context Router

Use before work needing prior project context, durable memory, or handoff recovery.

## Routing Order

1. Project instructions outrank all other context.
2. `PROJECT_STATE.md` supplies current status and blockers.
3. `NEXT.md` supplies current restart action.
4. Relevant `HANDOFF.md` supplies session detail when state or next action needs explanation.
5. `LEARNINGS.md` and `CORRECTIONS.md` supply durable reusable guidance.
6. Optional Basic Memory augments retrieval; verify returned claims against Markdown before treating them as current.

## Selection Rules

- Load only files relevant to request. Do not sweep memory directories.
- Prefer current dated state over older handoffs.
- Prefer explicit project rules over learned guidance.
- Surface conflicts, dates, and unknowns; do not merge contradictory sources silently.
- Search for an existing note before creating one.

## Write Routing

| Content | Destination |
|---|---|
| Current work, blockers, verification | `PROJECT_STATE.md` |
| One exact resume action | `NEXT.md` |
| Session outcome and context | `HANDOFF.md` |
| Reusable verified lesson | `LEARNINGS.md` |
| User correction or prevention rule | `CORRECTIONS.md` |

Do not write same item to multiple state authorities. Link between entries when needed.
