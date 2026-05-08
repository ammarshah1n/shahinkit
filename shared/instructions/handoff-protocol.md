# Handoff Protocol

ShahinKit treats resumability as a product feature. Every serious session should leave enough state for a fresh agent to continue without guessing.

## Files

- `NEXT.md`: the immediate next action and resume command.
- `HANDOFF.md`: narrative state, changed files, verification, risks, and exact resume point.
- `PARKED.md`: multiple parked tracks when more than one stream is active.
- `SESSION_LOG.md`: append-only session history.
- `BUILD_STATE.md`: what works, what is blocked, and verification matrix.

## Start-Of-Session Read Order

1. Project instruction file: `AGENTS.md`, `CLAUDE.md`, or equivalent.
2. `NEXT.md`.
3. `HANDOFF.md`.
4. `BUILD_STATE.md`.
5. `docs/MEMORY_CONTEXT.md`.
6. `VAULT-INDEX.md`, when the workspace is an Obsidian vault.
7. Project-specific rules referenced by those files.

Read only what is needed for the task. Avoid archive and session-log noise unless the task asks for history.

## End-Of-Session Write Order

1. Update verification status.
2. Update `BUILD_STATE.md` when the project state changed.
3. Write or update `HANDOFF.md`.
4. Write or update `NEXT.md`.
5. Append `SESSION_LOG.md`.
6. Update `PARKED.md` for parallel tracks.
7. Write memory notes only when configured.

## Per-Track Handoffs

Use this naming pattern for concurrent tracks:

```text
handoffs/YYYY-MM-DDTHH-MM-SSZ-<track>-<slug>.md
```

Each handoff should include:

- current track;
- status;
- changed files;
- verification;
- blocker or next action;
- exact resume command.
