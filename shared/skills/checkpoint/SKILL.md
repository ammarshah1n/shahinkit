---
name: checkpoint
description: Mid-session handoff that records current progress, exact restart state, blockers, touched files, and verification without claiming completion.
---

# checkpoint

Use when pausing active work before final completion.

Do not present the task as finished unless it is actually complete and verified.

## Steps

1. Inspect current state.
   - Read project instructions.
   - Check Git status when Git is present.
   - Identify files touched, pending edits, and active branch or workspace label.

2. Write current state.
   - Record what is complete.
   - Record what is in progress.
   - Record what is intentionally not started.

3. Record the exact next command.
   - Include the command that should be run next.
   - Keep commands portable; avoid private local paths.

4. Record open blockers.
   - Note missing decisions, failing commands, unavailable services, or blocked approvals.
   - Include the smallest next unblock step.

5. Record files touched.
   - List only relevant files.
   - Mark files with uncommitted changes when Git is available.

6. Record verification status.
   - List commands run and their result.
   - If verification was skipped, state why.

## Output

Return a concise checkpoint with:

- Current state.
- Exact next command.
- Open blockers.
- Files touched.
- Verification status.

Do not include private local paths, personal names, secrets, raw transcript text, or unrelated environment details.
