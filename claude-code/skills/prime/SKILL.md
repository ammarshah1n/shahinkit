---
name: prime
description: Prime a project by reading the smallest useful context at session start. Read-only.
---

# Prime

Use this when starting work in a project or when the user asks to load context.

## Rules

- Read-only. Do not create, edit, move, delete, install, or index anything.
- Prefer targeted reads over broad scans.
- Stop once the next safe action is clear.

## Read Order

1. Current directory and git root.
2. Project instructions: `CLAUDE.md`, `AGENTS.md`, or local equivalent.
3. README and package manifests.
4. Handoff files: `NEXT.md`, `HANDOFF.md`, `BUILD_STATE.md`, `PARKED.md`.
5. Memory context files when present, especially Obsidian vault files under `Working-Context/`.
6. basic-memory MCP results for the current project or task when the server is available.
7. Recent commits and `git status`.

## Output

Report in this shape:

```text
PROJECT: <name> @ <branch or no git>
PATH: <absolute path>
STACK: <detected stack or unknown>
STATE: <clean or changed files>
CONTEXT: <instruction and handoff summary>
ENTRY POINTS: <scripts, commands, apps, or unknown>
RECENT WORK: <last few commits or none>
NEXT: <recommended next action>
```
