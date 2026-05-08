# Memory Context

## Prior Decisions

- ShahinKit should package a complete Claude/Codex operating system, not only prompt snippets.
- The handoff/resume system is the core product surface: `NEXT.md`, `HANDOFF.md`, session logs, current-state files, and wrap-up flows must be first-class.
- `deep-idea` should be the full idea workflow, with `new-idea` as a shorter public alias.
- The planning workflow based on `deep-plan` is a core differentiator because it forces memory retrieval, codebase mapping, dependency graphs, parallel batches, and human review before implementation.
- `skill-builder` should be included as a generic way to create reusable domain skills from transcripts or rough descriptions.
- School/university and development workflows need separate vault templates and separate memory corpora to avoid context contamination.

## Relevant Patterns

- Agent instructions should be layered:
  - shared neutral guidance as the source of truth;
  - Claude Code adapters through `CLAUDE.md`, `.claude/settings.json`, `.claude/skills/`, and `.claude/hooks/`;
  - Codex adapters through `AGENTS.md`, `.codex/config.toml`, `.codex/hooks.json`, skills, and plugins.
- Startup should prime only the smallest useful context:
  - current state;
  - parked work;
  - recent handoff;
  - relevant memory routing;
  - project-specific rules.
- Wrap-up should write durable state before the session ends:
  - `NEXT.md` for immediate resume;
  - `HANDOFF.md` for narrative context;
  - `PARKED.md` or per-track handoff files for multiple active streams;
  - append-only session logs for audit and history;
  - memory writes where configured.
- Vaults should have a front-door index:
  - `VAULT-INDEX.md`;
  - `Working-Context/<project-or-school>-state.md`;
  - rules, walkthroughs, prompts, specs, context, templates, archive.
- Bulk imports should create `_INDEX.md` files with source metadata, summary, tags, and links.
- RAG/indexing must be opt-in, with a preview of files to be indexed and private-data exclusions.

## Related Past Work

- `deep-idea` defines the greenfield flow: memory context, idea brief, interview, research lanes, PRD, build context, and a deep-plan graduation gate.
- `deep-plan` defines mature-repo planning: memory retrieval, codebase mapping, plan writing, validation checklist, and execution-mode selection.
- `skill-builder` defines a reusable flow for building new domain skills.
- `wrap-up`, `miniwrap`, `checkpoint`, and `prime` define reusable lifecycle pieces.
- Existing vault workflows show the current-state and vault-index pattern.
- School workflow artifacts show subject, assignment, reading, source, and note structures that can become placeholders without copying private content.

## Known Constraints

- Do not copy private identity, project paths, private vault content, school details, client details, private rules, secrets, or raw transcripts into the public kit.
- Do not ship local config wholesale; render templates with placeholders and patch snippets instead.
- Do not enable embedding, indexing, transcript export, public export, or git-pull hooks by default.
- Claude Code and Codex support overlapping but different surfaces, so ShahinKit needs shared source files plus thin client adapters.
- Claude Desktop extension support should be treated separately from Claude Code CLI/IDE support unless official docs verify feature parity.
- Public templates should default to deny-all export and explicit allowlists for any public or shared output.

## Phase M Refresh For Plug-And-Play Build

- Prior ShahinKit notes support the initial PRD, planning pillar, and discovery work.
- Memory retrieval can be unavailable, so generated plans should state unavailable sources instead of inventing context.
- Reusable pattern: repo rules are the source of truth, vault state mirrors project state, and startup reads should be ordered and bounded.
- Large work should carry the planning prelude, parallel execution model, and split criteria without requiring the user to re-prompt.
- Architecture rule: separate entrypoints/adapters from shared workflow logic.
