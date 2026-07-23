---
name: plans
description: Coordinate multiple independent plans or ideas as one dependency-aware slate. Detects coupled work and routes it to mission mode; requires explicit approval before implementation.
---

# Plans

Use for several independent asks. For one request use `plan` or `idea`. For coupled deliverables sharing one thesis, use `mission`.

## Slate

1. Retrieve shared memory first. Normalize every ask; preserve user grouping where supplied.
2. Detect coupling before final grouping. Shared thesis, shared research foundation, or output-to-output strategy dependency means `MISSION`, not a slate.
3. Classify each independent group provisionally as `IDEA` or `CHANGE`; its `plan` run makes final classification.
4. Assign research mode per group. Run shared deep research once only when an unknown changes multiple groups.
5. Build slate dependency graph and parallel-batch schedule. Independent groups run in parallel; real dependencies serialize.
6. Present slate: group, classification, anchor, research mode, dependencies, batch, and named human blockers.

## Gates and execution

One explicit slate `GO` authorizes research and plan production only. Each group follows `plan` or `idea` fully: memory-first, research decision, dependency graph, parallel batches, spec-drift, delete/merge, adversarial review, correctness gates.

After reviewed plans exist, present a consolidated plan-vet packet. A second explicit `GO` always authorizes implementation; prior authorization cannot waive this gate. No implementation starts before that second explicit `GO`. Track each group as `PLANNED`, `VETTED`, `BUILDING`, `GREEN`, `MERGED`, or `BLOCKED` in durable project state.

Execute independent approved groups in isolated workspaces where host supports isolation. Controller accepts no group until its stated invariants, verification, and anchor outcome have observed evidence. A blocked group does not stop independent groups. Run cross-group adversarial review before final completion; resolve verified findings or report named blockers.

## Adapter capability contract

Host adapters may provide isolated workspaces, parallel workers, durable plan-state storage, and merge support. If unavailable, preserve dependency ordering and record constrained execution; do not claim isolation or parallelism that did not occur.
