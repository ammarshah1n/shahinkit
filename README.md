# ShahinKit

ShahinKit is portable working habits for Claude Code, OpenCode, and Codex. It
helps a new AI session pick up safely without copying private machine state.

## Why it exists

AI sessions are temporary. A new session does not automatically know what a
previous session changed, decided, verified, blocked, or should do next. Without
a deliberate handoff, beginners repeat explanations, lose decisions, or let an
agent guess from stale files.

ShahinKit provides visible start/stop workflows and Markdown templates. It is
not private memory, an automatic transcript recorder, or a promise that every
host has lifecycle hooks.

## First session, end session, next session

1. **First session:** install from `INSTALL.md`, then start work with `/prime`.
   `/prime` is read-only: it reads project instructions, README or manifest,
   `PROJECT_STATE.md`, `NEXT.md`, latest relevant `HANDOFF.md`, optional local
   Basic Memory, and recent commits/status. It reports one safe next action.
2. **End session:** use `/wrap-up` for meaningful work. It classifies work as
   `SHIPPED`, `PARKED`, or `INTERRUPTED`; runs smallest relevant checks; updates
   `PROJECT_STATE.md`, `NEXT.md`, and `HANDOFF.md`; and records only distilled
   lessons. It never stores raw transcripts or tool dumps. It commits only when
   explicitly requested and never pushes automatically.
3. **Next session:** run `/prime` again. It reads those visible files instead of
   guessing what happened before.

These commands are intentional: inspectable, portable between hosts, and free
from hidden transcript capture or surprise writes. Current kit renders no
lifecycle hook for Codex and no safe persistent Claude lifecycle adapter.
Ponytail/Caveman static context or managed modes activate only after documented
preview, apply, and trust. Generic safety hooks stay disabled or advisory.
`/prime` and `/wrap-up` are not automatic lifecycle hooks; run them explicitly.

## Study flow

Open an existing Obsidian vault, then use `/study`. On first use it asks for
subject names, whether direct-child subject folders already exist, and the
status/location of user-owned course content. It previews exact folder and
`Study.md` changes, then writes only after `CONFIRM STUDY SETUP`. `/study setup`
safely reconfigures a valid mapping. ShahinKit ships no course content, creates
no vault, copies nothing automatically, and does not require Course-RAG.

## What is included

- Host adapters: `claude-code/`, `opencode/`, and `codex/`.
- Canonical portable core and school layer: `school/`.
- Planning, handoff, study skills, memory templates, installer tooling, tests,
  optional local Basic Memory guidance, and optional local Course-RAG tools.
- Opt-in configuration and hook examples.

No private course material, personal vaults, credentials, or local machine
paths are included.

## Install safely

Read `INSTALL.md`. Preview explicit host and scope first, for example:

```sh
python3 school/scripts/manage.py install --agent opencode --scope project --allow-development-checkout --preview
```

Review paths, managed blocks, conflicts, provenance, and trust requirement.
Copy printed `preview-digest`, then apply same reviewed plan with
`--apply --preview-digest <SHA256> --trust-host`. Every mutation requires that
exact digest. Basic Memory is disabled by default; add `--with-basic-memory`
only after reviewed local setup.

## Safety model

- Read before writing. Edit only task-required files.
- Ask before destructive operations.
- Do not index, embed, upload, or export private files without explicit approval.
- Keep generated indexes local.
- Use expensive models and subagents for hard reasoning, high-risk changes, and
  review—not small mechanical edits.
