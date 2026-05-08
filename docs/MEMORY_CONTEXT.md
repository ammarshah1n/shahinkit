# Memory Context

## Prior Decisions

- ShahinKit should package a complete Claude/Codex operating system, not only prompt snippets.
- The handoff/resume system is the core product surface: `NEXT.md`, `HANDOFF.md`, session logs, current-state files, and wrap-up flows must be first-class.
- `new-idea` should be the public-facing idea workflow, based on Ammar's current `deep-idea` skill.
- The planning workflow based on `deep-plan` is a core differentiator because it forces memory retrieval, codebase mapping, dependency graphs, parallel batches, and human review before implementation.
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

- Local `deep-idea` defines the greenfield flow: memory context, idea brief, interview, research lanes, PRD, build context, and a deep-plan graduation gate.
- Local `deep-plan` defines mature-repo planning: memory retrieval, codebase mapping, plan writing, validation checklist, and execution-mode selection.
- Local `wrap-up`, `miniwrap`, `checkpoint`, and `prime` skills define reusable lifecycle pieces.
- Timed and PFF vaults show the current-state and vault-index pattern.
- School workflow artifacts show assignment, milestone, evidence, and reflection structures that can become placeholders without copying private content.

## Known Constraints

- Do not copy Ammar-specific identity, project paths, private vault content, school details, client details, TickTick/AIF private rules, secrets, or raw transcripts into the public kit.
- Do not ship local config wholesale; render templates with placeholders and patch snippets instead.
- Do not enable embedding, indexing, transcript export, public export, or git-pull hooks by default.
- Claude Code and Codex support overlapping but different surfaces, so ShahinKit needs shared source files plus thin client adapters.
- Claude Desktop extension support should be treated separately from Claude Code CLI/IDE support unless official docs verify feature parity.
- Public templates should default to deny-all export and explicit allowlists for any public or shared output.
