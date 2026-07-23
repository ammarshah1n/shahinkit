# Codex CLI Adapter

Target: Codex CLI `0.144.5`. Copy files; never symlink. Review every fragment
before merging. This adapter does not set model, approval, sandbox, network,
provider, credential, telemetry, or project-trust settings.

## Install mapping

| Asset | User destination | Project destination |
|---|---|---|
| `AGENTS.md` | `<CODEX_HOME>/AGENTS.md` | `<DESTINATION>/AGENTS.md` |
| rendered skills | `$HOME/.agents/skills/<name>/SKILL.md` | `<DESTINATION>/.agents/skills/<name>/SKILL.md` |
| `config/config.patch.example.toml` | `<CODEX_HOME>/config.toml` managed merge | `<DESTINATION>/.codex/config.toml` managed merge |
| `config/agents/<role>.toml` | `<CODEX_HOME>/agents/<role>.toml` | `<DESTINATION>/.codex/agents/<role>.toml` |

Course RAG script, README, and index files render under
`{{SHAHINKIT_DATA_DIR}}/course-rag` for either scope. Its rendered skill invokes
that data destination, never this checkout.

`render-manifest.json` is source-of-truth for copied assets and destinations.
Skill destinations follow Codex's official loader:
`https://github.com/openai/codex/blob/rust-v0.144.5/codex-rs/core-skills/src/loader.rs`.
The config examples use current separate agent files. They intentionally do not
use legacy `profiles.*` tables. Configure each role explicitly; workers never
inherit controller model or authority.

## Skills

Rendered shared skills: `checkpoint`, `context-router`, `corrections`,
`deep-idea`, `deep-plan`, `delegation-routing`, `idea`, `memory`, `miniwrap`,
`mission`, `plan`, `plans`, `prime`, `reflect`, `self-improve`,
`session-handoff`, and `wrap-up`, plus pinned Ponytail and Caveman skills.
`course-rag` remains adapter-local because it invokes this adapter's local
index scripts.

`study` is rendered shared skill: `/study` safely maps direct subject folders in
an existing Obsidian vault. It bundles no course content, copies nothing
automatically, and does not require Course-RAG.

## Hooks and MCP

Generic gate examples are disabled advisory material, not enforcement. Codex
receives no lifecycle hook: Ponytail and Caveman static instructions and skills
become active only after preview, `--apply`, and host-trust confirmation.

Basic Memory template launches preinstalled `basic-memory` through stdio with
placeholder environment references and local-only policy. Render its local
project config with `mode: local` and `workspace_id: null`; require
`BASIC_MEMORY_FORCE_LOCAL=true` and `BASIC_MEMORY_EXPLICIT_ROUTING=true`.
Optional MCP entries are disabled and reference environment variable names only.
No template embeds credentials or enables remote access.

## Retained local assets

`memory/` holds Markdown templates. `course-rag/` builds local SQLite indexes
without editing or uploading source material.
