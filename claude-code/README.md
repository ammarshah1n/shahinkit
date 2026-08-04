# ShahinKit Claude Code adapter

Claude Code contract: `>=2.1.209 <2.2.0`. Templates use Claude Code's current
`settings.json`, `.mcp.json`, `SKILL.md`, agent-frontmatter, and hook syntax.

## Destination map

| Scope | Instructions | Skills | Commands | Agents | Settings | MCP |
|---|---|---|---|---|---|---|
| User | `~/.claude/CLAUDE.md` | `~/.claude/skills/` | `~/.claude/commands/` | `~/.claude/agents/` | `~/.claude/settings.json` | `~/.claude.json` |
| Project | `CLAUDE.md` | `.claude/skills/` | `.claude/commands/` | `.claude/agents/` | `.claude/settings.json` | `.mcp.json` |

Project settings, skills, agents, and MCP setup require Claude Code workspace
trust. Apply only through ShahinKit manager preview, explicit `--apply`, and
`--trust-host`; restart Claude Code once after first installation so it reloads
the approved configuration. No symlinks.

## Adapter assets

- `render-manifest.json`: canonical shared and pinned-vendor render map.
- `config/settings.patch.example.json`: valid settings patch examples; merge
  only needed fields into selected scope.
- `hooks/user.hooks.example.json` and `hooks/project.hooks.example.json`:
  host-native `SessionStart` and `SubagentStart` registrations. Manager composes
  selected hook config with base settings patch.
- `core/hooks/shahinkit_hook.py`: fail-open guidance runner. It retains no
  prompts, writes no files, and performs no network calls.
- `config/roles.resolved.example.json`: ShahinKit render input for per-role
  overrides. It is not a Claude Code settings file; renderer writes explicit
  `model` frontmatter into each agent definition.
- `config/mcp.basic-memory.example.json`: optional local stdio Basic Memory
  template. Render `config/basic-memory.local-config.example.json` with project
  `mode: local` and `workspace_id: null`; `basic-memory` must already be
  installed. `BASIC_MEMORY_FORCE_LOCAL=true` and
  `BASIC_MEMORY_EXPLICIT_ROUTING=true` are required. No cloud credentials,
  updater, or remote fetch.
- `hooks/generic.disabled.example.json`: retired pointer, not hook config.
- `hooks/managed-lifecycle.after-trust.json`: manager metadata for default
  Ponytail/Caveman activation plus lifecycle safety metadata after trust.
- `agents/`: explicit independent-role definitions. No permission bypass.
- `SKILL.md` directories are canonical slash-command definitions. No legacy
  command shim is rendered for a name implemented by a skill.

`study` renders as shared `/study` skill. It requires an existing Obsidian vault,
bundles no course content, copies nothing automatically, and has no Course-RAG
requirement.

Ponytail uses static rendered context and its approved skill set. Caveman uses
static context plus explicit command shims. Lifecycle hooks only advertise
Prime and bound worker authority; no prompt inspection, state file, event
retention, or hidden write occurs. `course-rag/` remains local and opt-in.
