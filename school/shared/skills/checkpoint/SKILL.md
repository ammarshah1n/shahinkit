---
name: checkpoint
description: Save bounded session progress without ending or committing work.
---

# Checkpoint

Use when user asks to save progress, create a handoff, or preserve a resumable point during ongoing work.

## Procedure

1. Inspect work completed in current session and unresolved blockers.
2. Update `PROJECT_STATE.md` when present or explicitly configured: completed work, active work, blockers, and checks run.
3. Update `NEXT.md` with one concrete restart action.
4. Create or update `HANDOFF.md` only for meaningful context that cannot fit in current state and next action.
5. Report files updated and exact restart action.

## Boundaries

- Do not create duplicate authorities: state stays in `PROJECT_STATE.md`; next action stays in `NEXT.md`.
- Do not commit, push, sync, or publish as part of checkpoint.
- Record distilled facts only. Never store or copy raw transcripts, transcript exports, or raw tool output.
