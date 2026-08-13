---
name: delegation-routing
description: Use for delegation, subagents, Codex workers, codex fleet dispatch, research routing, bounded implementation fan-out, or worker acceptance decisions.
---

# Delegation Routing

## Controller-Controlled Workflow Default

This is the default for every new project and every active project unless a local `CLAUDE.md`/`AGENTS.md` explicitly narrows it.

- Subagent dispatch defaults DOWN. Mechanical/extraction/mapping/formatting work → haiku / gpt-5.6-luna worker (gpt-5.4-mini retired 2026-08-31). Research/reading → sonnet. A controller-tier subagent (opus or the session's own model) is FORBIDDEN unless the Agent prompt contains the literal marker [CONTROLLER-TIER-JUSTIFIED: <one-line reason>]. No marker → don't dispatch it.
- **Controller invariant:** the controller (strongest available model in the session) owns creative brainstorming, architecture calls, routing, final synthesis, and final quality/taste review. Delegation is allowed only when the result is bounded and can be independently checked before use.
- Every `/plan`, `/idea`, `/plans`, `/mission`, significant refactor, or multi-file feature plan includes `**Research:** none|fast|deep|hybrid` near the top.
- Defaults: `/plan=fast`, `/idea=hybrid`, `/plans=per-group fast with one shared deep report only for cross-cutting unknowns`, `/mission=hybrid`.
- `research=fast` -> Comet: quick current facts, source discovery, browser/file research, and time-crunch lookup.
- `research=deep` -> `hyperresearch-codex`: load-bearing decisions where provenance, pricing/limits, API behavior, compliance, architecture tradeoffs, or adversarial critique matter.
- `research=hybrid` -> Comet for breadth first, then HyperResearch to audit and synthesize the decision-grade report.
- `research=none` is allowed only when all relevant facts are local, stable, and already loaded. It is invalid for integrity-critical assumptions about APIs, pricing, limits, legal/compliance, auth, sync, data loss, or architecture.
- Delegate safely: repo maps, unknown enumeration, source extraction, bounded implementation from an exact spec, deterministic plumbing, tests from explicit invariants, and adversarial review.
- Never delegate: open-ended creativity, product taste, architecture decisions, final synthesis, final acceptance, integrity-critical code/data-loss/privacy/legal/security decisions, or anything where a mistake cannot be caught by deterministic checks.
- Pi subagents are default for all bounded delegation and fan-out. Use host's `subagent` tool with appropriate Pi agent profile. Do not invoke Codex merely because work is delegated. Codex is opt-in only when user explicitly asks for Codex or task requires a Codex-only capability.
- New project enforcement: create or maintain a local `CLAUDE.md` and/or `AGENTS.md` block with this policy before non-trivial project work, unless the directory is intentionally one-off scratch.

---

## Tool Dispatch

**Hard separation:** a subagent is not a Codex session. Pi is default.

- “Send a subagent” means call the Pi `subagent` tool with `agent` + `task` (or `tasks`/`chain`). Select `scout`, `planner`, `worker`, or `reviewer` as appropriate.
- Do not translate generic delegation into Codex. Do not call `mcp__codex_computer_use_codex`, `mcp__codex_sites_codex`, or `codex exec` unless user explicitly requests Codex or controller documents a Codex-only capability requirement.
- In OpenCode, use native `task`/`@` agents.
- Clipboard requests are direct shell work: use `pbcopy`; do not dispatch an agent or Codex session.

Default controller is the controller (strongest available model in the session). Delegation is a bounded execution tool, not a replacement for controller judgement.

1. **Research selector required for non-trivial planning:** `research=fast` uses Comet; `research=deep` uses `hyperresearch-codex`; `research=hybrid` uses Comet breadth then HyperResearch synthesis; `research=none` requires a local/stable-facts justification.
2. **Independent bounded subtasks:** route **codebase discovery, file mapping, import/callsite tracing, source extraction, bounded implementation/plumbing/tests, and review** to Pi `subagent` by default. The controller writes the spec and adjudicates the result.
3. **Review or diagnosis of completed work:** use a Pi review subagent when independent critique improves defect catch-rate. The controller still decides what lands.
4. Everything else with open-ended creativity, architecture, final synthesis, product voice, or integrity-critical risk: **self-execute in the controller**.

### Runtime scoping

- Pi: route bounded implementation, codebase discovery, file mapping, import/callsite tracing, source extraction, plumbing, tests, and review through Pi `subagent`.
- Claude Code: use its approved Agent route outside Pi. OpenCode: use native `@`/`task` subagents.
- Never switch to Codex merely because task is bounded.

### Codex scope

Use Codex only when explicitly requested or when controller documents a Codex-only capability requirement. Otherwise use Pi `subagent`.

Never use Codex for generic delegation, creative brainstorming, architecture calls, final synthesis, final acceptance, product taste, or privacy/legal/security decisions that the controller cannot deterministically verify. Do not route through aliases named "Codex".

---

## Codex Fleet Dispatch

- NEVER launch `codex exec` workers detached (`nohup … &`) — deaths become invisible. One worker = its own `run_in_background:true` Bash call. A fleet = ONE background Bash call running `~/bin/codex-supervisor --jobs-file jobs.tsv --out-dir DIR --worker <codex-worker.sh>` (jobs.tsv rows: `name\tbrief\tscope\tcwd`; auto-restarts dead workers, kills hung ones, one notification when all terminal).
- Generic worker wrapper if the repo has none: `--worker ./scripts/codex-worker.sh`.
- Health check = `cat DIR/*.status` (never `ps aux | grep codex`). Live view: run `agentwatch` in any terminal; `agentwatch 0` is a one-shot snapshot.

---

## Tool Arsenal

| Tool | Use for | NOT for |
|------|---------|---------|
| **Me (Claude Code / controller)** | Creativity, architecture, routing, final synthesis, final acceptance, product taste, integrity-critical judgement | Blind fan-out without review |
| **Pi `subagent` tool** | Bounded implementation, deterministic plumbing, tests, repo maps, extraction, and review | Architecture, final synthesis, final acceptance, product taste |
| **Codex (`codex exec` or MCP session)** | Explicit user-requested Codex work or documented Codex-only capability | Generic delegation, pretending to be a Pi subagent, or making final decisions |
| **Perplexity Pro Search** | Quick web-grounded answers, docs, API refs | Deep multi-source research |
| **Perplexity Deep Research** (`/comet`) | Competitive analysis, grant landscape, technical deep dives — fastest, curated, burns Pro budget | Privacy-sensitive research; batch / automated runs |
| **self-hosted research runner** | Same category as a deep research service, using the host's approved private search setup. | One-shot lookups use the fast search route instead. |
| **Comet** | Web interaction — fills, scraping, browser automation | Code generation |
| **ChatGPT o3** | Long-chain reasoning, brainstorming, strategic planning | Code execution |
| **Supabase Edge Functions** | Serverless automation, cron jobs, webhooks | Frontend logic |
