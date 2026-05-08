# ShahinKit

ShahinKit is a plug-and-play Claude Code and Codex workflow kit for development, school, university, and knowledge-heavy project work.

## What This Is

ShahinKit packages the operating system around an agent: instructions, skills, handoff files, memory routing, Obsidian vault templates, client adapters, and opt-in indexing workflows.

It is not a hosted app. It is a template-first repository that gives a person a working structure for:

- starting an agent session with the right context;
- turning rough ideas into PRDs and build context;
- producing better code plans before implementation;
- using Basic Memory and Claude Memory without mixing contexts;
- ingesting large folders or exports into a vault;
- ending sessions with durable handoff files.

## Who It Is For

- Developers using Claude Code, Codex, or both.
- Students using Obsidian with Claude/Codex for school or university.
- People who move large course, project, OneDrive, or zip exports into a structured vault.
- Anyone who needs `NEXT.md`, `HANDOFF.md`, session logs, and memory to make agent work resumable.

## Repository Layout

```text
shared/                       Client-neutral source of truth
  instructions/               Operating contract, safety, memory, handoff
  skills/                     Portable agent skills
  hooks/                      Optional hook scripts
  handoff/                    Handoff file templates
  memory/                     Basic Memory and Claude Memory templates
  rag-indexing/               Opt-in indexing consent and redaction docs
  privacy/                    Private-data and export checklists
clients/                      Thin client adapters
  claude-cli/
  codex-app/
  claude-code-desktop/
templates/                    Vault and repo starter templates
  dev-vault/
  school-university-vault/
  repo-adapter/
scripts/                      Doctor, render, and install helpers
bin/                          ShahinKit launcher
docs/                         PRD, build context, maps, plans, research
```

## Install Model

ShahinKit defaults to preview-first operation.

- Templates are inert until copied.
- Hooks are opt-in.
- Indexing and embedding require explicit consent.
- Install scripts print planned writes before touching a target.
- Live Claude, Codex, or desktop config is not edited directly by default.

## Core Workflows

- `prime`: read the smallest useful project context at session start.
- `new-idea`: turn a rough idea into research, PRD, build context, and a deep-plan-ready package before implementation starts.
- `deep-plan`: upgrade mature repo planning through memory retrieval, codebase mapping, dependency graph, parallel batches, and review gate.
- `wrap-up`: write durable end-of-session state across `NEXT.md`, `HANDOFF.md`, logs, build state, and memory.
- `ingest-large-folder`: inventory and route OneDrive, zip, course, or project exports.
- `rag-consent`: require approval before embedding or indexing vault contents.

## Planning Upgrade

`new-idea` and `deep-plan` are the core planning advantage in ShahinKit. They are built from observed Claude Code and Codex usage where Codex can be weaker at planning out of the box, especially on greenfield ideas, multi-file changes, and repo-scale execution.

The goal is to make Codex plan with more structure than a normal prompt: memory first, real codebase map second, dependency graph third, parallel execution plan fourth. In practice, this can turn Codex from a weaker planner than Claude Code into a stronger one for implementation planning, because the workflow forces it to ground every plan in files, constraints, handoff state, and verification gates.

## Safety Model

ShahinKit is deny-by-default for destructive work.

- Ask before deleting, moving, overwriting, force-pushing, or exporting.
- Keep personal data, credentials, private transcripts, school data, and client data out of reusable templates.
- Keep development, school/university, and client memory projects separate.
- Do not index or embed user files until the proposed file list has been shown and approved.

## Quick Start

Run the doctor first:

```bash
scripts/doctor.sh
```

Render a Codex adapter:

```bash
scripts/render-client-config.sh --client codex-app --output ./dist/codex-app
```

Render a Claude Code adapter:

```bash
scripts/render-client-config.sh --client claude-cli --output ./dist/claude-cli
```

Inspect the rendered files before installing. When ready, use `scripts/install.sh` with `--dry-run` first.
