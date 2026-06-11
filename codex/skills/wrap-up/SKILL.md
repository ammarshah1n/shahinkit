---
name: wrap-up
description: End a session by classifying state, updating handoff files, recording verification, and committing only when required.
---

# Wrap-Up

Use this when the session is ending or the user asks to wrap up.

## Phase 0: Classify State

Run one status check and classify:

- `SHIPPED`: all requested work is complete and verification passed or was not applicable.
- `PARKED`: work is intentionally paused with a clear next action.
- `INTERRUPTED`: work is incomplete because of a failing check or blocker.

## Phase 1: Inspect Changes

- Read project instructions before deciding what to write.
- Run `git status --short` when in a git repo.
- Identify files changed this session.
- Do not commit unrelated changes.

## Phase 2: Update Handoff Files

If the project has these files, update them:

- `BUILD_STATE.md`: verification status and known failures.
- `HANDOFF.md`: current state, files touched, decisions, blockers, restart point.
- `NEXT.md`: one concrete next action.
- `PARKED.md`: only when multiple tracks are active.
- `SESSION_LOG.md`: append a short dated entry when present.

Do not create handoff files unless the project already uses them or the user asks.

## Phase 3: Memory

Write memory only when the project has an explicit memory target. Store durable facts only:

- decision made;
- bug fixed;
- architecture constraint;
- verification result;
- exact next action.

## Phase 4: Verify

Run project-appropriate checks when available:

- JavaScript or TypeScript: package scripts for test, lint, typecheck, build.
- Python: tests, import checks, or script compilation.
- Shell: `bash -n`.
- Documentation-only: link/path sanity and privacy scan.

If a command is unavailable, say so.

## Phase 5: Commit

Commit only if the host project requires commits or the user asked for commits.

- Use a conventional commit subject.
- Keep the commit scoped to completed work.
- Do not push unless explicitly asked.

## Final Output

Report:

- session state;
- files updated;
- verification commands and results;
- commit hash if created;
- remaining blocker or next action.
