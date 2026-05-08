# Research Brief

## Research Summary

ShahinKit should be structured as a portable workflow kit with one shared source of truth and thin adapters for Claude Code, Codex, and desktop/IDE surfaces. The strongest value proposition is not "a folder of prompts"; it is a complete agent operating system for starting work, planning correctly, using memory, indexing knowledge with consent, and ending sessions with durable handoff.

## Lanes Activated And Why

- Agent workflow and handoff mechanics: activated because handoff/resume is the core product surface.
- Vault and template structure: activated because the kit needs development and school/university vault templates.
- Client compatibility: activated because the kit must support Claude CLI, Codex App, and Claude Code Desktop/IDE surfaces.
- Official documentation check: activated because local configs can drift from current public client behavior.

## Key Findings Per Lane

### Agent Workflow And Handoff Mechanics

- Package a layered instruction contract:
  - shared rules;
  - Claude adapter;
  - Codex adapter;
  - project-specific overrides.
- Ship a read-only `prime` flow for session start.
- Ship a memory-first retrieval gate before planning, architecture claims, or research.
- Treat `wrap-up` as a full lifecycle, not a closing note:
  - state detection;
  - handoff generation;
  - memory writes;
  - current-state propagation;
  - verification.
- Support lighter close paths with `miniwrap` and `checkpoint`.
- Add per-track handoffs for concurrent projects, subjects, clients, or feature streams.
- Add compaction and transcript survival hooks so context does not disappear when a session is compacted or closed.

### Vault And Template Structure

- Development vaults should include:
  - `VAULT-INDEX.md`;
  - `Working-Context/project-state.md`;
  - `HANDOFF.md`;
  - `NEXT.md`;
  - rules, walkthroughs, prompts, specs, errors, dev logs, context, templates, and archive folders.
- School/university vaults should include:
  - `VAULT-INDEX.md`;
  - `Working-Context/school-state.md`;
  - current term;
  - subjects;
  - lessons;
  - readings;
  - notes;
  - sources;
  - assessments;
  - assignments with brief, rubric, sources, drafts, feedback, and handoff;
  - milestones;
  - evidence;
  - import holding folders.
- Bulk imports should create `_INDEX.md` files with source metadata, summary, tags, and links.
- RAG/indexing must be explicit opt-in with redaction and public-export allowlists.

### Client Compatibility

- Shared `skills/<name>/SKILL.md` is the best portable workflow format.
- Claude Code supports project and personal `CLAUDE.md`, skills, commands, hooks, MCP, and settings.
- Codex supports `AGENTS.md`, skills, MCP, hooks behind a feature flag, app slash commands, and `$` skill invocation.
- Claude Desktop should be treated primarily as a desktop extension/MCP surface until exact Claude Code Desktop parity is verified.
- Client folders should contain only adapter templates and patch snippets. Do not copy local user config.

### Official Documentation Check

- Codex reads `AGENTS.md` guidance globally and per project.
- Codex skills use `SKILL.md` directories and are available in CLI, IDE extension, and Codex app.
- Codex MCP configuration is in `config.toml`, globally or project-scoped.
- Codex hooks are supported behind a `codex_hooks` feature flag and can live in `hooks.json` or `config.toml`.
- Codex App supports slash commands and `$` skill invocation.
- Claude Code reads `CLAUDE.md` memory/instruction files from user and project scopes.
- Claude Code skills supersede command-only workflows but `.claude/commands/` remains compatible.
- Claude Code settings support hooks, MCP, permissions, environment variables, and project/user hierarchy.
- Claude Desktop supports installing local MCP servers through desktop extensions.

## Proposed Repo Shape

```text
shahinkit/
  docs/
  shared/
    instructions/
    skills/
    hooks/
    handoff/
    memory/
    rag-indexing/
    privacy/
  clients/
    claude-cli/
    codex-app/
    claude-code-desktop/
  templates/
    dev-vault/
    school-university-vault/
    repo-adapter/
  scripts/
    doctor.sh
    render-client-config.sh
    install.sh
  bin/
    shahinkit
```

## Highest-Value Product Additions

- `new-idea`: public name for the greenfield `deep-idea` workflow.
- `deep-plan`: mature-repo planning workflow that makes Codex produce grounded dependency-aware plans.
- `wrap-up`: comprehensive handoff writer.
- `prime`: start-of-session orientation.
- `memory-routing`: separate dev, school, and optional client memory projects.
- `ingest-large-folder`: prompt/template flow for OneDrive, zip, course exports, and project archives.
- `rag-consent`: explicit indexing approval and redaction gate.
- `doctor`: verifies client config, required tools, memory servers, and hook install status.

## Open-Source Candidates And Decisions

Not researched yet. This pass focused on Ammar's local workflow and official client compatibility. RAG/indexing stack and installer tooling still need a dedicated open-source evaluation lane.

## Contradictions Or Conflicts

- Codex App supports slash commands, but local Codex instructions warn not to use user-defined slash aliases as the primary skill invocation path. ShahinKit should expose skills through `$skill-name` and adapter docs, not rely on custom slash commands for Codex.
- Claude Code commands now overlap with skills. ShahinKit should author skills first and only render commands as compatibility adapters.
- Claude Desktop MCP support is clear, but full Claude Code Desktop workflow parity still needs verification before promising identical support.

## Confidence Assessment

- High confidence: shared source plus thin client adapters.
- High confidence: handoff/resume is the highest-value differentiator.
- High confidence: `new-idea`, `deep-plan`, `prime`, and `wrap-up` should be core modules.
- Medium confidence: default repo layout.
- Low confidence: final RAG/indexing stack until open-source research is complete.

## Implications For PRD

- Add "shared source plus adapters" as an architectural constraint.
- Treat `new-idea` and `deep-plan` as core MVP features.
- Add a `doctor`/installer workflow to make the kit usable by non-experts.
- Add explicit privacy/export/indexing constraints.
- Separate Claude Desktop promises from Claude Code CLI/IDE promises until verified.

## Sources

- OpenAI Codex overview: https://developers.openai.com/codex
- OpenAI Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md
- OpenAI Codex skills: https://developers.openai.com/codex/skills
- OpenAI Codex hooks: https://developers.openai.com/codex/hooks
- OpenAI Codex MCP: https://developers.openai.com/codex/mcp
- OpenAI Codex app commands: https://developers.openai.com/codex/app/commands
- Anthropic Claude Code memory: https://code.claude.com/docs/en/memory
- Anthropic Claude Code skills/commands: https://code.claude.com/docs/en/slash-commands
- Anthropic Claude Code settings: https://docs.anthropic.com/en/docs/claude-code/settings
- Anthropic Claude Code hooks: https://code.claude.com/docs/en/hooks
- Anthropic Claude Code MCP: https://code.claude.com/docs/en/mcp
- Claude Desktop local MCP servers: https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop
