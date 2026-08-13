---
name: session-handoff
description: Read durable state at session start and write a structured handoff at meaningful session close.
---

# Session Handoff

## Start

1. Read project instructions.
2. Read `PROJECT_STATE.md`, then `NEXT.md`, then latest relevant `HANDOFF.md` when present.
3. Use optional Basic Memory only for focused retrieval after Markdown context.
4. Report current state, blockers, and restart action before work.

## Close

For meaningful sessions, write or update `HANDOFF.md` using the shared template. Include only:

- session state: `SHIPPED`, `PARKED`, or `INTERRUPTED`;
- concrete completed work;
- verification actually run and results;
- blockers and open decisions as questions;
- one exact restart action.

Then update canonical authorities: `PROJECT_STATE.md` for current status and `NEXT.md` for restart action.

## Boundaries

- Handoff explains state; it does not become a second current-state authority.
- Preserve prior handoff history when project convention keeps it. Otherwise replace only stale current handoff after preserving essential context.
- Never store or copy raw transcripts, transcript exports, or raw tool output.
