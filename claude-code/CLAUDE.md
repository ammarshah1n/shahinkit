# CLAUDE.md

Use this file as the project or global instruction layer for Claude Code.

## Operating Contract

- Read the target file before editing it.
- Check `git status` before writing.
- Edit minimally. Do not improve unrelated code.
- Ask before destructive operations such as delete, move, reset, force push, branch deletion, database drops, bulk import, indexing, upload, or public export.
- Do not store credentials, private transcripts, personal paths, or course material in reusable kit files.
- Commit completed changes with conventional commit messages when the host project requires commits.

## Session Flow

1. Use `prime` at the start of non-trivial work.
2. Use `idea` for a new product, workflow, or feature concept.
3. Use `plan` for one non-trivial change.
4. Use `plans` for a batch of independent changes or ideas.
5. Use `deep-plan` when codebase mapping is the main risk.
6. Use `deep-idea` when the repo does not exist or is too immature for codebase mapping.
7. Use `wrap-up` before ending meaningful work.

## Planning Rules

- Ground plans in real files and current project state.
- Plans must include a dependency graph and a parallel batch schedule.
- Use parallel execution only when tasks are not dependency-blocked.
- Do not include time estimates.
- Do not leave vague deferrals. Convert blockers into named human actions or implementation steps.
- Stop for approval before implementation unless the user explicitly asked to execute an approved plan.

## Cost-Aware Routing

The lead agent is responsible for model and subagent cost discipline.

- Inline small work: single-file edits, typo fixes, short README changes, simple shell output, targeted searches, and obvious mechanical changes.
- Use cheaper or lower-effort workers for deterministic extraction, file inventory, formatting, bulk renames that have already been approved, and scripted checks.
- Use stronger reasoning for architecture choices, high-blast-radius changes, security, migrations, auth, money, data loss risk, correctness guarantees, and final plan review.
- Do not dispatch expensive high-effort subagents just because a task can be parallelized.
- If a subagent is used, give it a narrow prompt, exact files or directories, expected output, and a verification command.

## Course RAG

When the user provides a course folder, use `course-rag` to build a local SQLite search index. Never edit the source folder. Search the index before answering course-content questions and cite the source path shown by the search result.
