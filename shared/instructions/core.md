# Core Operating Contract

This file is the shared source of truth for ShahinKit client adapters.

Client-specific files such as `CLAUDE.md`, `AGENTS.md`, Codex config snippets, Claude settings snippets, and desktop notes should adapt this contract without changing its behavior.

## Rules

- Read the target file before editing it.
- Edit minimally. Change only what the task requires.
- Ask before destructive operations such as delete, move, overwrite, force push, reset, public export, or bulk import.
- Keep client-specific behavior in `clients/`.
- Keep reusable workflow logic in `shared/`.
- Keep templates free of personal paths, secrets, private transcripts, private school data, and private client data.
- Use explicit consent gates for indexing, embedding, transcript export, and public export.

## Workflow Order

Use this order unless the user explicitly asks for a narrower task:

1. `prime`: read the smallest useful context.
2. `deep-idea` or `new-idea`: use for greenfield projects, product ideas, school systems, or immature repos.
3. `deep-plan`: use for non-trivial work in a mature repo.
4. `skill-builder`: use when the user wants a reusable assistant skill for a recurring domain.
5. Implementation: follow the approved plan.
6. `wrap-up`: write resumable state before ending the session.

## Adapter Boundary

The adapter's job is syntax and installation shape:

- Claude Code: `CLAUDE.md`, `.claude/skills/`, `.claude/commands/`, `.claude/settings.json`, hooks.
- Codex: `AGENTS.md`, skills, `config.toml`, hook snippets, `$skill` invocation guidance.
- Claude Desktop: desktop extension and MCP notes.

Adapters should point to shared concepts rather than duplicating the full workflow.
