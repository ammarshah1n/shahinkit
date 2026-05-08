---
name: wrap-up
description: End-of-session closeout for portable projects: inspect state, record handoff files, verify, update configured memory, and commit when required.
---

# wrap-up

Use when a work session is ending and the project needs a durable handoff.

## Adapter Knobs

Enable only adapters that the host project explicitly configures:

- `local-only`: write repository handoff files only.
- `git`: inspect status, diff, and commit when project rules require it.
- `basic-memory`: write concise memory notes to the configured project.
- `claude-memory`: write concise memory notes to the configured memory surface.
- `obsidian`: write or update configured vault notes.

Never include private local paths, personal names, secrets, raw transcript text, or unrelated environment details.

## Phases

1. Inspect state.
   - Read project instructions first.
   - Check repository status when Git is present.
   - Identify changed files, open work, verification commands, and configured adapters.
   - Read existing `NEXT.md`, `HANDOFF.md`, `SESSION_LOG.md`, and `BUILD_STATE.md` before editing them.

2. Summarize shipped work.
   - State only completed work that is visible in files or verified behavior.
   - Separate incomplete work, blockers, and assumptions.
   - Keep the summary brief and factual.

3. Update `NEXT.md`.
   - Record the next concrete action.
   - Include the exact command to resume when useful.
   - Remove stale next steps that are now complete.

4. Update `HANDOFF.md`.
   - Record current state, files touched, decisions made, blockers, and verification status.
   - Include restart instructions that do not depend on local machine paths.

5. Append `SESSION_LOG.md`.
   - Add a dated entry.
   - Include completed work, verification run, and follow-up state.
   - Do not paste chat logs or sensitive content.

6. Update `BUILD_STATE.md` when present.
   - Record the latest build, test, lint, or manual verification result.
   - Note failures with the exact failing command and short cause.

7. Write memory notes only when configured.
   - Use the enabled adapter.
   - Store durable facts, decisions, and next actions only.
   - Do not write secrets, private paths, or transcript excerpts.

8. Run verification selected by project type.
   - JavaScript or TypeScript: prefer configured `test`, `lint`, `typecheck`, and `build` scripts.
   - Python: prefer configured test and lint commands.
   - Swift or Xcode: prefer configured build and test commands.
   - Static content: validate generated files and links where practical.
   - If commands are unavailable, record that verification was not run and why.

9. Commit only when required.
   - If the host project requires commits and Git is enabled, commit the completed change using the project format.
   - Do not commit unrelated changes.
   - If commits are not required, leave the working tree unchanged except for requested handoff files.

## Output

Report:

- Files updated.
- Verification commands and results.
- Commit hash, if a commit was required and created.
- Remaining blocker or next action, if any.
