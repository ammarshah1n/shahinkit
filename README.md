# ShahinKit

ShahinKit is a portable operating kit for Claude Code and OpenAI Codex. It gives a fresh agent the rules, skills, planning workflows, handoff habits, and local course-search workflow it needs without copying private machine state.

The repository intentionally has only three user-facing root entries:

- `README.md` - this overview.
- `claude-code/` - everything needed for Claude Code.
- `codex/` - everything needed for Codex.

No private course material, personal vaults, credentials, or local machine paths are included.

## Quick Start

1. Pick the agent you use.
2. Open either `claude-code/` or `codex/`.
3. Read that folder's README.
4. Copy the matching instruction file and skills into your own project or agent config.

## What Is Included

- Agent instruction files.
- Planning skills: `plan`, `plans`, `idea`, `deep-plan`, and `deep-idea`.
- Session lifecycle skills: `prime` and `wrap-up`.
- Local course RAG: point the kit at a course folder, build a SQLite search index, and search it before answering course-content questions.
- Config and hook examples that are opt-in and safe to inspect before use.

## Safety Model

- Read before writing.
- Edit only what the task requires.
- Ask before destructive operations.
- Do not index, embed, upload, or export private files without explicit approval.
- Keep generated indexes local.
- Keep agent routing cost-aware: expensive models and subagents are for hard reasoning, high-risk changes, and review, not small mechanical edits.
