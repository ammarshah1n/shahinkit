---
name: prime
description: Read the smallest useful project context at session start without editing files.
---

# Prime

Use this at session start to load enough project context to continue safely. Prime is read-only.

## Read Order

1. Local instruction file, such as `AGENTS.md`, `CLAUDE.md`, or the project-specific equivalent.
2. `NEXT.md`.
3. `HANDOFF.md`.
4. `BUILD_STATE.md`.
5. `docs/MEMORY_CONTEXT.md`.
6. `VAULT-INDEX.md`, when present.

## Rules

- Do not edit files during prime.
- Prefer the first relevant file in the read order over broad searching.
- Summarize current state, active constraints, next action, and obvious blockers.
- Stop once the smallest useful context is loaded.
