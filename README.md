# ShahinKit

ShahinKit is a portable operating kit for Claude Code and OpenAI Codex. It gives a fresh agent the rules, skills, planning workflows, handoff habits, and local course-search workflow it needs without copying private machine state.

The repository intentionally has only three user-facing root entries:

- `README.md` - this overview.
- `claude-code/` - everything needed for Claude Code.
- `codex/` - everything needed for Codex.

No private course material, personal vaults, credentials, or local machine paths are included.

## Quick Start

1. Download Obsidian from <https://obsidian.md/download>. Use it as the document editor for notes, handoffs, and memory files.
2. Pick the agent you use: `claude-code/` or `codex/`.
3. Read that folder's README.
4. Copy the matching instruction file, skills, config fragments, and memory templates into your own project or agent config.
5. Optional but recommended: install `basic-memory` and register a local Obsidian vault as the agent memory project.

## What Is Included

- Agent instruction files.
- Planning skills: `plan`, `plans`, `idea`, `deep-plan`, and `deep-idea`.
- Session lifecycle skills: `prime` and `wrap-up`.
- Memory workflow: Obsidian vault templates, basic-memory MCP setup notes, and local handoff/state conventions.
- Local course RAG: point the kit at a course folder, build a SQLite search index, and search it before answering course-content questions.
- Config and hook examples that are opt-in and safe to inspect before use.

## Safety Model

- Read before writing.
- Edit only what the task requires.
- Ask before destructive operations.
- Do not index, embed, upload, or export private files without explicit approval.
- Keep generated indexes local.
- Keep agent routing cost-aware: expensive models and subagents are for hard reasoning, high-risk changes, and review, not small mechanical edits.

## Memory Model

The portable memory system has three layers:

1. Obsidian vault: the human-readable source of truth for notes, project state, and handoffs.
2. basic-memory MCP: optional local retrieval over the vault, exposed to the agent when installed.
3. Plain markdown fallback: the agent can still read `PROJECT_STATE.md`, `NEXT.md`, and handoff files directly if MCP is unavailable.

The kit does not ship a memory database or private notes. It ships templates and setup instructions so each user can create their own local vault.
