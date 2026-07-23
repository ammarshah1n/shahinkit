---
name: miniwrap
description: Close a tiny, complete session without full lifecycle overhead.
---

# Miniwrap

Use only when work is small, complete, has no unresolved failure, no architectural decision, and needs no durable handoff.

## Scope Check

Escalate to `wrap-up` when work is parked, interrupted, changed several related files, produced a durable lesson, or needs state recovery next session.

## Procedure

1. Confirm work is complete and no check is failing.
2. Run a focused check when change requires one.
3. Write nothing by default. Add a distilled learning only when it is clearly durable.
4. Commit only on explicit user request or explicit project policy. Never push automatically.
5. Report check result, write or skip reason, and commit result or skip reason.

Do not update `PROJECT_STATE.md`, `NEXT.md`, or `HANDOFF.md` for a genuine mini session.
