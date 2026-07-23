---
name: prime
description: Read smallest useful project and memory context at session start. Read-only.
---

# Prime

Use when starting work, resuming work, or asked to load context.

## Rules

- Read-only: do not create, edit, move, delete, install, index, sync, commit, or run state-changing commands.
- Prefer direct, bounded reads. Skip absent files without error.
- Stop when current state and next safe action are clear.

## Read Order

1. Identify current directory, repository root when present, and active branch.
2. Read project instructions: `AGENTS.md`, `CLAUDE.md`, or documented equivalent.
3. Read `README.md` and relevant manifest or package file.
4. Read configured Markdown memory in this order when present: `PROJECT_STATE.md`, `NEXT.md`, latest relevant `HANDOFF.md`.
5. Query optional Basic Memory only for current project, task, or subject. Treat results as retrieval aids; Markdown remains authoritative.
6. Read recent commits and working-tree status.

## Output

```text
PROJECT: <name> @ <branch or no git>
PATH: <working directory>
STACK: <detected stack or unknown>
STATE: <clean, changed, or no git>
CONTEXT: <instructions and current-state summary>
MEMORY: <Markdown files read; Basic Memory result or unavailable>
RECENT WORK: <recent commits or none>
NEXT: <one concrete safe action>
```
