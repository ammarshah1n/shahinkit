---
name: memory
description: Maintain portable, Markdown-first durable memory with optional Basic Memory retrieval.
---

# Memory

Use when setting up, reading, or writing durable project memory.

## Source of Truth

- Markdown files are human-readable source of truth.
- Basic Memory is optional local retrieval over those files, never competing state storage.
- If Basic Memory is unavailable, read and write Markdown directly.
- Store distilled facts, decisions, constraints, verification results, and restart instructions. Never store or copy raw transcripts, transcript exports, or raw tool output.

## Canonical Files

| File | Authority |
|---|---|
| `PROJECT_STATE.md` | Current project status, active work, blockers, verification |
| `NEXT.md` | Single current restart action |
| `HANDOFF.md` | Meaningful session record and resume context |
| `LEARNINGS.md` | Durable reusable lessons |
| `CORRECTIONS.md` | Durable corrections and prevention rules |

Do not duplicate current state across files. `PROJECT_STATE.md` owns status; `NEXT.md` owns restart action; handoffs link or summarize, not replace either authority.

## Write Rules

1. Read existing target before editing.
2. Update existing entry when same fact already exists; do not create near-duplicates.
3. Use dated, concise entries with evidence or source reference when available.
4. Keep sensitive or private content local unless user explicitly authorizes another destination.
5. Use templates from `school/shared/memory/` when creating canonical files.

## Basic Memory

When configured, search before fresh research or claims about prior work. Write only distilled notes worth future retrieval. Do not use it to capture sessions, persist raw tool output, or replace canonical Markdown.
