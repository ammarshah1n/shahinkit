---
name: plans
description: Coordinate a batch of multiple plans or ideas with grouping, dependency routing, and plan-vet gate.
---

# Plans

Use this when the user gives multiple tasks, a spoken list, or asks for a batch of work.

## Phase A: Parse

- Normalize the user's list into task groups.
- Preserve explicit numbering.
- Merge only tightly coupled items.
- Split independent items.

## Phase B: Classify

For each group, classify:

- `IDEA`: use `idea`.
- `PLAN`: use `plan`.
- `MISSION`: use a shared foundation when outputs depend on one thesis or research spine.

## Phase C: Dependency Graph

- Identify independent groups.
- Identify strict dependencies.
- Default to parallel only where there is no dependency.
- Mark any real-world human action.

## Phase D: Plan Vet

Default behavior:

- planning is authorized by the first approval;
- building waits for a second approval after plans are visible.

Skip the second gate only when the user explicitly asked for full-auto execution.

## Phase E: Execution

When approved:

- run independent groups in parallel where tooling supports it;
- keep each group scoped;
- verify each group before merging results;
- produce one final report with shipped work, blocked work, and verification.
