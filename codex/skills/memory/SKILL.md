---
name: memory
description: Set up and use a local Obsidian plus basic-memory project for durable agent memory.
---

# Memory

Use this when the user wants persistent local memory, basic-memory MCP setup, or Obsidian-backed notes.

## Rules

- Use Obsidian as the human editor for memory files.
- Keep memory local unless the user explicitly asks to sync, publish, or upload it.
- Store durable facts, not raw transcripts.
- Do not write private course content into global memory unless the user asks.
- If basic-memory MCP is unavailable, fall back to reading and writing markdown files.

## Setup

Read `codex/memory/README.md`.

Default local vault:

```text
~/Documents/Agent-Memory-Vault
```

Default basic-memory project:

```text
agent-memory
```

## Prime

- Read project instructions.
- Read `Working-Context/PROJECT_STATE.md`.
- Read `Working-Context/NEXT.md`.
- Query basic-memory for the current project, task, or subject when available.

## Wrap-Up

- Update `PROJECT_STATE.md`.
- Update `NEXT.md` with one restart action.
- Write a handoff in `Handoffs/` for meaningful sessions.
- Add durable facts through basic-memory when the MCP tool is available.
