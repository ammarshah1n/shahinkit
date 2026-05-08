---
name: deep-plan
description: Plan non-trivial feature work through memory retrieval, codebase mapping, dependency graph, parallel batches, and review gate before code.
---

# Deep Plan

Use this before non-trivial feature work, refactors, or changes that need coordination across files or modules.

## Phases

### Phase M: Memory

- Retrieve relevant project memory, prior decisions, current state, and constraints.
- Write the distilled context to `docs/MEMORY_CONTEXT.md`.
- Note unavailable memory sources instead of inventing context.

### Phase 0: Codebase Map

- Read the smallest useful set of real files, imports, entrypoints, tests, and docs.
- Write findings to `docs/CODEBASE_MAP.md`.
- Ground claims in actual file paths and current behavior.

### Phase 1: Plan

- Write the implementation plan to `docs/superpowers/plans/YYYY-MM-DD-<slug>.md`.
- Include scope, affected files, dependency graph, validation steps, and execution route.
- Keep the plan ready for review before code changes.

## Validation Checklist

- Dependency graph is explicit.
- Parallel batch schedule is explicit.
- Every batch has a `LAUNCH SWARM` or `INLINE` decision.
- No duration claims are included.
- No blockers are left unhandled.
- Verification commands or checks are named.
- Risky or irreversible work has an approval gate.

## Approval Gate

Stop after the plan is written. Do not implement until the user approves the plan or explicitly asks to continue.

## Execution Route

- Use `INLINE` for small, dependent, or tightly coupled work.
- Use `LAUNCH SWARM` when a batch has two or more independent tasks.
- After approval, execute batches in dependency order and run validation before completion.
