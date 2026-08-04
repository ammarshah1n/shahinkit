---
name: wrap-up
description: End a session with verification, durable state, handoff, and an optional explicit commit.
---

# Wrap-Up

Use when ending a meaningful session.

## Phase 1: Classify

- `SHIPPED`: requested work complete; required checks pass or are not applicable.
- `PARKED`: intentionally paused with a concrete restart action.
- `INTERRUPTED`: incomplete because a check fails or blocker remains.

## Phase 2: Verify

Run smallest project-appropriate checks for changed surface. Record commands and observed results. Do not claim checks were run when unavailable.

## Phase 3: Update Durable State

1. Update `PROJECT_STATE.md`: current status, files or deliverables, blockers, verification.
2. Update `NEXT.md`: exactly one concrete restart action.
3. Write or update `HANDOFF.md` for meaningful sessions: state, done, open decisions, blockers, checks, and restart action.
4. Run `reflect` for durable evidence-backed lessons only.

`PROJECT_STATE.md` remains current-state authority. `NEXT.md` remains restart-action authority. Handoff must not duplicate or compete with them.
Never store or copy raw transcripts, transcript exports, or raw tool output.

## Phase 4: Commit

Inspect status and preserve unrelated changes. Commit only when user explicitly requests it or project instructions explicitly require it, and only completed intended files. Never push automatically.

## Final Output

Report session state, files updated, checks and results, commit result or skip reason, blockers, and next action.
