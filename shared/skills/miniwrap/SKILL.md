---
name: miniwrap
description: Lightweight closeout for tiny tasks, one-off edits, and quick checks with minimal state recording and optional commit when required.
---

# miniwrap

Use for a tiny task with one clear outcome, such as a one-file edit, a quick check, or a small data update.

Escalate to `wrap-up` when:

- More than one workstream is active.
- An open decision remains.
- Multiple handoff files need updates.
- Verification is complex or failing.

## Steps

1. Inspect the task state.
   - Read relevant project instructions.
   - Check Git status when Git is present.
   - Identify exactly what changed.

2. Verify only what is proportional.
   - Run the smallest relevant command or manual check.
   - If no verification is needed, say so briefly.

3. Commit only when required.
   - If files changed and repository rules require a commit, create one using the required format.
   - Do not commit unrelated changes.
   - Do not commit when project rules or user instructions forbid it.

4. Report briefly.
   - State the result.
   - List changed files if any.
   - Give the next action only when one is needed.

## Privacy

Do not include private local paths, personal names, secrets, transcript content, or unrelated environment details.
