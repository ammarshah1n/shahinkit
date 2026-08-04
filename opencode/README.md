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
| plugins | `<OPENCODE_HOME>/plugins/` | `<DESTINATION>/.opencode/plugins/` |

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

Optional `/course-rag` installs from Claude Code's canonical portable source and
builds only a local SQLite index from folders the user selects.

OpenCode automatically discovers local files in its standard user or project
plugin directory; config does not list them a second time. Files appear only in
applied trusted installations. Disable lifecycle modes at install with
`--without-ponytail` or `--without-caveman`; restart OpenCode once after
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

`shahinkit-guard.mjs` adds three fail-open runtime guards: a wall-clock clamp
on every bash call (10 min default, 30 min ceiling — one hung command cannot
eat hours), a session budget tripwire (past 25 worker dispatches or 4h it
forces a plain go/no-go checkpoint through the system prompt), and desktop
notifications (macOS only, best-effort) when a primary session stops, asks
for a decision, or trips its budget. It stores counters in process memory
only and spawns no subprocess except the macOS notifier.

It also adds Prime availability guidance once per session and clears that
in-memory marker when the session is deleted. It reads no prompt text and writes
no files.

## Reflection loop (optional)

`scripts/reflect.mjs` reads finished primary sessions from the local OpenCode
store, digests them (duration, dispatch counts, stalls, user frustration
signals), extracts failure candidates with a local `codex exec` pass, and
appends them to `~/.config/opencode/corrections/pending.md`. A failure class
recurring on two distinct days is proposed for promotion into `AGENTS.md` —
promotion is always a human decision; nothing self-installs. Schedule daily
with your scheduler of choice, or run manually; `--dry` prints digests only
and calls no model.
