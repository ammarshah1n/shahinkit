# ShahinKit OpenCode adapter

Portable OpenCode v1.17.20 template. Render `opencode.jsonc.example` only for
project scope; render `opencode.user.jsonc.example` only for user scope. Copy
`AGENTS.md` and `.opencode/` into selected scope only through ShahinKit installer
after preview, `--apply`, and host trust confirmation. No symlinks.

## Destination map

| Asset | User destination | Project destination |
|---|---|---|
| `AGENTS.md` | `<OPENCODE_HOME>/AGENTS.md` | `<DESTINATION>/AGENTS.md` |
| `opencode.user.jsonc.example` | `<OPENCODE_HOME>/opencode.jsonc` managed merge | — |
| `opencode.jsonc.example` | — | `<DESTINATION>/opencode.jsonc` managed merge |
| agents | `<OPENCODE_HOME>/agents/` | `<DESTINATION>/.opencode/agents/` |
| commands | `<OPENCODE_HOME>/commands/` | `<DESTINATION>/.opencode/commands/` |
| rendered skills | `<OPENCODE_HOME>/skills/` | `<DESTINATION>/.opencode/skills/` |
| plugin | `<OPENCODE_HOME>/plugins/portable-gates.mjs` | `<DESTINATION>/.opencode/plugins/portable-gates.mjs` |

`render-manifest.json` is source-of-truth for copied assets and destinations.

## Layout

- `.opencode/agents/`: explicit independent roles.
- `.opencode/commands/`: thin prompt wrappers.
- `.opencode/plugins/`: local, in-memory Ponytail/Caveman lifecycle gate.
- `.opencode/skills/`: render destination for portable skills.
- `memory/`: render destination for Markdown templates.

`/study` uses rendered shared `study` skill through a thin command wrapper. It
requires an existing Obsidian vault, bundles no course content, copies nothing
automatically, and does not require Course-RAG.

`plugin` registration is installer-managed and active only in applied trusted
installations. Preview has no runtime registration. Disable lifecycle modes at
install with `--without-ponytail` or `--without-caveman`; restart OpenCode for
configuration changes.

## Role overrides

Each role model lives directly in its own `.opencode/agents/<role>.md`
frontmatter. Override only that file's `model` value. Do not use model
inheritance or copy controller model into workers.

## Local MCP examples

Basic Memory runs only as local stdio with explicit local placeholders. Render
its local project config with `mode: local` and `workspace_id: null`; require
`BASIC_MEMORY_FORCE_LOCAL=true` and `BASIC_MEMORY_EXPLICIT_ROUTING=true`. It
has no cloud endpoint, token, telemetry, or updater configuration. `dev-scope`
is disabled local-only placeholder. Supply no credentials in this template.

## Plugin boundaries

`portable-gates.mjs` retains only whitelisted mode per session in process
memory. It never reads environment variables, files, secrets, network, or
subprocesses; never persists event payloads or transcript text; and logs a
static warning when hook input is invalid.
