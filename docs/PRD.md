# ShahinKit PRD

## Problem Statement

Claude Code, Codex, and related desktop/CLI workflows become powerful only after a user has agent instructions, skills, memory, vault structure, handoff files, and repeatable wrap-up habits. Most users have to discover and wire those pieces manually.

ShahinKit is an all-in-one kit for setting up those workflows for development and school/university work.

## Target Users And Jobs-To-Be-Done

- Developers who want a ready-to-use Claude Code and Codex workflow with skills, memory, handoffs, and project structure.
- School or university students who want an Obsidian vault structure compatible with Claude Code and Codex.
- Power users who ingest large course, project, OneDrive, or zip archives and want the material indexed into a useful vault.
- Users who need agents to resume work reliably through `next.md`, `handoff.md`, session logs, and wrap-up routines.

## Core Features (MVP)

- Claude CLI compatibility folder.
- Codex App compatibility folder.
- Claude Code Desktop App compatibility folder.
- School/university Obsidian vault template compatible with Claude Code and Codex.
- Built-in opt-in RAG/indexing flow that asks the user before embedding vault contents.
- Prompt/template workflow for ingesting OneDrive exports, large zip files, and other bulk folders into the vault.
- Development vault template matching Ammar's current workflow style, including indexing.
- Basic Memory and Claude Memory setup for Claude workflows.
- Basic Memory and Claude Memory setup for school/university vault workflows.
- Comprehensive handoff system:
  - start-of-session hooks/context so Codex and Claude Code know the current project state;
  - `/wrap-up` or equivalent wrap-up flow;
  - `next.md`;
  - `handoff.md`;
  - session logs;
  - current-state files;
  - commit/push guidance where appropriate.
- Repository sections for at least:
  - `dev/`
  - `school-university/`
  - client-specific folders for Claude CLI, Codex App, and Claude Code Desktop App.

## Out Of Scope (MVP)

- A full hosted SaaS product.
- A custom vector database service unless local RAG requires one.
- Replacing Claude Code, Codex, Obsidian, Basic Memory, or Claude Memory.
- Automated destructive file moves or imports without explicit user confirmation.

## Success Metrics

- A new user can install or copy the kit and get a working agent-compatible vault.
- A project can be stopped and resumed from handoff files without the agent losing context.
- Large folders or zip exports can be ingested through a documented, repeatable flow.
- The kit works across Claude CLI, Codex App, and Claude Code Desktop App.
- The highest-value workflows from Ammar's personal setup are captured as reusable templates instead of remaining implicit.

## Technical Constraints

- Must support Claude CLI.
- Must support Codex App.
- Must support Claude Code Desktop App.
- Must keep destructive operations opt-in.
- Must ask before embedding or indexing user vault contents.
- Must be template-oriented enough that users can adapt it without adopting Ammar's entire private setup.
- Must keep school/university and development workflows separate enough to avoid mixed context.

## Business Model

Open question. Candidate directions:

- Free/open-source core kit with paid implementation help.
- Personal brand asset for Facilitated.
- Paid advanced templates for school/university and professional agent workflows.

## Competitive Differentiation

- Focuses on complete agent operating systems, not just prompt snippets.
- Covers both development and school/university workflows.
- Treats handoff/resume as the main product surface.
- Bridges Obsidian, RAG/indexing, Basic Memory, Claude Memory, Claude Code, and Codex.
- Comes from a real working setup rather than a theoretical template.

## Open Questions

- Final public name: `shahinkit`, `ShahinKit`, or another brand.
- Whether folder naming should be `school-university/`, `learning/`, or separate `school/` and `university/`.
- Which RAG/indexing stack should be the default.
- Whether the repo ships scripts, docs-only templates, or both.
- How much of Ammar's current personal workflow should be generalized versus copied directly.
- Whether `wrap-up` should be implemented as a portable skill, shell script, prompt pack, or client-specific adapter.
- What the first install path should be for non-technical users.

## Memory Context Used

Not yet retrieved. Discovery will inspect Ammar's current workflow artifacts and memory systems before the PRD is finalized.
