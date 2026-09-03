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
- `research=fast` -> a separately configured `web` command on `PATH`: quick current facts, source discovery, and time-crunch lookup; cite source URLs directly. A non-zero exit is a tool failure, never a finding — exit 3 means the configured network route is unavailable.
- `research=deep` -> `researcher` subagent (`openai-codex/gpt-5.6-sol:xhigh`, web via that command): load-bearing decisions where provenance, pricing/limits, API behavior, compliance, architecture tradeoffs, or adversarial critique matter.
- `research=hybrid` -> `web` for breadth, then one `researcher` subagent for sourced synthesis.
- `research=none` is allowed only when all relevant facts are local, stable, and already loaded. It is invalid for integrity-critical assumptions about APIs, pricing, limits, legal/compliance, auth, sync, data loss, or architecture.
- Delegate safely: repo maps, unknown enumeration, source extraction, bounded implementation from an exact spec, deterministic plumbing, tests from explicit invariants, and adversarial review.
- Never delegate: open-ended creativity, product taste, architecture decisions, final synthesis, final acceptance, integrity-critical code/data-loss/privacy/legal/security decisions, or anything where a mistake cannot be caught by deterministic checks.
- Pi subagents are default for all bounded delegation and fan-out. Use host's `subagent` tool with appropriate Pi agent profile. Do not invoke Codex merely because work is delegated. Codex is opt-in only when user explicitly asks for Codex or task requires a Codex-only capability.
- New project enforcement: create or maintain a local `CLAUDE.md` and/or `AGENTS.md` block with this policy before non-trivial project work, unless the directory is intentionally one-off scratch.

---

## Tool Dispatch

**Hard separation:** a subagent is not a Codex session. Pi is default.

- “Send a subagent” means call the Pi `subagent` tool with `agent` + `task` (or `tasks`/`chain`). Select `scout`, `planner`, `worker`, or `reviewer` as appropriate.
- Do not translate generic delegation into Codex. `codex exec` is RETIRED — never call it. `mcp__codex_sites_codex` is Sites-only. Do not call `mcp__codex_computer_use_codex` unless user explicitly requests Codex or controller documents a Codex-only capability requirement.
- In OpenCode, use native `task`/`@` agents.
- Clipboard requests are direct shell work: use `pbcopy`; do not dispatch an agent or Codex session.

Default controller is the controller (strongest available model in the session). Delegation is a bounded execution tool, not a replacement for controller judgement.

1. **Research selector required for non-trivial planning:** `research=fast` uses the configured `web` command; `research=deep` uses the `researcher` subagent; `research=hybrid` uses `web` breadth then `researcher` synthesis; `research=none` requires a local/stable-facts justification.
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

## Fleet Dispatch — pi subagents

`codex exec`, `codex-supervisor`, `codex-worker.sh`, and `agentwatch` are **RETIRED (2026-08-13)**. Do not launch them. The fleet is the `subagent` tool.

- A fleet = ONE `subagent` call with a `tasks` array. Caps: **10 tasks per call, 6 concurrent** — the extension queues the rest. Progress streams into the tool result; there is nothing to health-check and nothing to restart.
- Every task carries an explicit provider-prefixed `model`. Inheriting is a bug.
- **Never fan out parallel writes to the same file** — children are separate processes sharing one cwd with no shared mutation queue. Disjoint files, or serialize.
- Sequential work with a clean artifact handoff = `chain` mode with `{previous}`, not a fleet.
- Roster and per-agent models: the active Pi config’s `AGENTS.md` § Subagent roster.

---

## Tool Arsenal

| Tool | Use for | NOT for |
|------|---------|---------|
| **Controller** | Creativity, architecture, routing, final synthesis, final acceptance, product taste, integrity-critical judgement | Blind fan-out without review |
| **Pi `subagent` tool** | **The worker route.** Bounded implementation, deterministic plumbing, tests, repo maps, extraction, research, and review | Architecture, final synthesis, final acceptance, product taste |
| **Codex Sites (`mcp__codex_sites_codex`)** | Sites work only — sites, landing pages, dashboards, private deploys | Everything else. `codex exec` is retired; "use Codex" now means the Codex-provider models the pi roster already runs on |
| **`web` on `PATH`** (separate, configured Exa client) | Quick web-grounded facts, official docs, API refs. Read result snippets before spending a page fetch | Deep multi-source synthesis or speculative fan-out |
| **`researcher` subagent** | Cited research synthesis through the configured web client | Browser automation or external actions |
| **ChatGPT o3** | Long-chain reasoning, brainstorming, strategic planning | Code execution |
| **Supabase Edge Functions** | Serverless automation, cron jobs, webhooks | Frontend logic |
