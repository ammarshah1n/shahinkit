---
name: read
description: Session-start context load — read the project handoff and resume the next queued task. Use at the start of a session, or when asked to "read the handoff", "resume", or "what's next".
---

# read — handoff load + resume

1. Read `HANDOFF.md` in the repo root. If it does not exist, say so and stop.
2. If they exist, also read `BUILD_STATE.md` (architecture state) and the last
   entry of `SESSION_LOG.md`. Do not read older log entries.
3. Brief the user in a few lines: current state, what the last session finished,
   and the single next queued task with its resume instruction.
4. Then start that next task. If the handoff marks it blocked or ambiguous,
   ask one bundled question instead of guessing.

Rules: newest handoff beats older notes; never re-do work the handoff marks
done; keep the briefing short — this is a launchpad, not a report.
