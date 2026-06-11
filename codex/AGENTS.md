# AGENTS.md

Use this file as the project or global instruction layer for OpenAI Codex.

## Operating Contract

- Read the target file before editing it.
- Check `git status` before writing in a git repo.
- Edit minimally. Change only what the task requires.
- Ask before destructive operations such as delete, move, reset, force push, branch deletion, database drops, bulk import, indexing, upload, or public export.
- Do not store credentials, private transcripts, personal paths, or course material in reusable kit files.
- Prefer `rg` for file and text search.
- Commit completed changes with conventional commit messages when the host project requires commits.

## Skill Invocation

Codex skills are invoked by name in plain text, not with leading slash commands.

Use:

- `prime`
- `idea`
- `plan`
- `plans`
- `deep-idea`
- `deep-plan`
- `course-rag`
- `wrap-up`

## Session Flow

1. Use `prime` at the start of non-trivial work.
2. Use `idea` for a new product, workflow, or feature concept.
3. Use `plan` for one non-trivial change.
4. Use `plans` for a batch of independent changes or ideas.
5. Use `deep-plan` when codebase mapping is the main risk.
6. Use `deep-idea` when the repo does not exist or is too immature for codebase mapping.
7. Use `course-rag` when the user gives a course folder and wants local course search.
8. Use `wrap-up` before ending meaningful work.

## Planning Rules

- Ground plans in real files and current project state.
- Plans must include a dependency graph and a parallel batch schedule.
- Use parallel execution only when tasks are not dependency-blocked.
- Do not include time estimates.
- Do not leave vague deferrals. Convert blockers into named human actions or implementation steps.
- Stop for approval before implementation unless the user explicitly pasted an approved plan and asked for implementation.

## Cost-Aware Routing

The lead agent owns cost discipline. Do not reflexively dispatch high-effort subagents.

### Inline By Default

Do directly in the lead session:

- single-file edits;
- typo or wording fixes;
- small README/config updates;
- targeted `rg`, `sed`, `git status`, `git diff`, `git show`, and manifest reads;
- simple command output requests;
- mechanical changes where the target files are already known.

### Cheap Worker

Use a lower-cost worker only when it saves meaningful lead-agent context:

- file inventory;
- literal search summaries;
- table extraction;
- deterministic bulk checks;
- generated fixtures from an exact spec.

### Strong Worker

Use stronger model effort only when correctness depends on real reasoning:

- architecture decisions;
- cross-module refactors;
- auth, payment, migration, privacy, or data-loss risk;
- ambiguous requirements;
- plan review;
- adversarial review of high-impact diffs.

### Subagent Rules

- Subagents are discretionary, not automatic.
- Do not use strong high-effort workers for small mechanical tasks.
- Give each subagent exact scope, expected output, files or directories, and verification.
- The lead agent must review worker output before treating it as done.

## Course RAG

When the user provides a course folder, use `course-rag` to build a local SQLite search index. Never edit the source folder. Search the index before answering course-content questions and cite the source path shown by the search result.
