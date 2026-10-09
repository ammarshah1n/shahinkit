# Replicate the full setup — web search, subagent rosters, dispatch doctrine

This is the end-to-end guide for rebuilding the setup ShahinKit was extracted
from: Brave + Exa web search for every agent, the subagent rosters on each
host, and the rules that decide when work is delegated. Everything here uses
files in this repository; nothing is installed for you.

Model names and prices are as of **2026-10**. Providers change both — check
their pages before relying on a number.

---

## 1. Web search: Brave + Exa through `web`

One small Python script (`Pi/bin/web`, standard library only) gives every agent
— Pi, Claude Code, Codex, OpenCode, and their subagents — the same three
commands:

| Command | Backend | Use it for | Rough cost |
|---|---|---|---|
| `web search "<q>" [n]` | Brave Search API | **Default.** Docs, errors, pricing, facts, links | ~$0.005/query; Brave has a free monthly allowance |
| `web research "<q>" [n]` | Exa neural search | **Real research only:** conceptual/landscape questions, "pages like this", or after two failed `search` rewordings | ~$0.007/query |
| `web get <url> [chars]` | plain HTTPS fetch | Read a page as text | free |

`search` falls back to Exa (with a note on stderr) when Brave has no key or
errors. Exit codes: `0` ok · `1` error · `3` blocked network · `4` no
results. **A non-zero exit never means "the answer is no".**

### 1.1 Get the keys

1. **Brave:** create an account at <https://brave.com/search/api/>, subscribe
   to a Search plan (the free tier is enough to start), and copy the API key
   from the API dashboard.
2. **Exa:** sign up at <https://exa.ai>, open the dashboard's API-keys page, and
   create a key.

You can run with only one of them: Brave-only works for `search`; Exa-only
makes `search` fall back to Exa every time (works, costs more).

### 1.2 Store the keys — pick ONE method per key

`web` looks in this order and uses the first hit:

1. **Environment variable** (any OS, also best for servers/CI):
   ```sh
   # ~/.zshrc or ~/.bashrc
   export BRAVE_API_KEY='...'
   export EXA_API_KEY='...'
   ```
2. **Key file** (any OS; good for remote/Linux worker boxes):
   ```sh
   mkdir -p ~/.config/brave ~/.config/exa
   printf '%s' '...' > ~/.config/brave/key
   printf '%s' '...' > ~/.config/exa/key
   chmod 600 ~/.config/brave/key ~/.config/exa/key
   ```
3. **macOS keychain** (Mac only; keeps keys out of shell history and dotfiles):
   ```sh
   security add-generic-password -a "$USER" -s brave-api-key -w
   security add-generic-password -a "$USER" -s exa-api-key -w
   # each prompts for the key
   ```

Never commit a key, paste it into an agent instruction file, or put it in a
Pi/Claude/Codex config that syncs.

### 1.3 Install the command

```sh
mkdir -p ~/bin
cp Pi/bin/web ~/bin/web
chmod +x ~/bin/web
# make sure ~/bin is on PATH (zsh/bash):
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc && exec $SHELL -l
```

Every host's agent can now run `web` through its normal shell tool — no MCP,
no per-host configuration.

### 1.4 Verify

```sh
web --help                          # usage, no network
web search "python urllib timeout" 3  # Brave: 3 results
web research "approaches to agent task budgeting" 3   # Exa: 3 results
web get https://example.com 500     # first 500 chars of the page
echo $?                             # 0 on success
```

| Symptom | Fix |
|---|---|
| exit 1, "no Brave API key" / "no Exa API key" | key not found by any of the three methods above |
| exit 3, "blocked" | a network filter (school/corporate) blocks the API. Set `WEB_PROXY` to an allowed proxy URL (e.g. `socks5h://127.0.0.1:1080` from an SSH tunnel); `web` retries through it only when the direct call is blocked |
| exit 4 | genuinely no results — reword, don't conclude "no" |
| 401/403 in the message | wrong or expired key |

### 1.5 Remote / subagent hosts

If subagents run on another machine (see `Pi/README.md` → Remote subagents),
that machine needs **its own** `~/bin/web` and keys (key file or env var).
Otherwise the research agent there runs with no web access at all, silently.
Smoke-test over ssh: `ssh <host> 'web search "test" 1; echo $?'`.

### 1.6 Teach the agents the routing

Already done in this repo: the **Web search** paragraph in
`claude-code/CLAUDE.md`, `codex/AGENTS.md`, `opencode/AGENTS.md`, and
`Pi/AGENTS.md`, plus `Pi/agents/researcher.md` and
`Pi/skills/delegation-routing/SKILL.md`. Copy those (section 3) and the agents
follow: `search` first, `research` only for real research, no speculative
fan-out of searches.

### 1.7 CLI vs the Exa MCP connector

| | `web` CLI (this) | Exa MCP connector |
|---|---|---|
| Works in | any host with a shell, including headless subagents | only sessions with that MCP configured |
| Context cost | zero until called; compact output | tool schemas sit in context every turn; fuller results |
| Routing | Brave-first, Exa for research only | Exa only; the model decides when |
| Network | runs on your machine (proxy via `WEB_PROXY`) | hosted connectors run provider-side |
| Extras | search, highlights, fetch | crawl, deep-research, code search (connector-dependent) |

Recommended: CLI as the default everywhere; add the connector only for
chat-only surfaces (web/mobile apps) where there is no shell.

---

## 2. Subagent rosters

Rule that applies everywhere: **every dispatch names its model explicitly.**
Inheriting the session model is a bug. Tier by blast radius, not repo size.

### 2.1 Pi (`Pi/agents/`, the reference roster)

| Agent | Model | Use for |
|---|---|---|
| `scout` | `openai-codex/gpt-6-luna:high` | codebase recon → compressed context for another agent |
| `mechanical` | `openai-codex/gpt-6-luna:minimal` | deterministic extraction, mapping, counting, formatting |
| `worker` | `openai-codex/gpt-6-luna:max` | bounded implementation + focused verification |
| `researcher` | `openai-codex/gpt-6-luna:max` | current external facts via `web`; returns sources + uncertainty |
| `reviewer` | `openai-codex/gpt-6-luna:max` | diff/code review; fan out 3 for a multi-lens sweep |
| `planner` | `anthropic/claude-opus-5-5:max` | drafts a plan in a clean context from a brief |
| `plan-reviewer` | `anthropic/claude-opus-5-5:max` | pre-mortem + Ponytail audit of a plan before GO |
| `fable` | `anthropic/claude-fable-5-1:max` | adjudication — only when the user explicitly asks |

Worker tiering:

- `luna:high` — the standard workhorse for bounded, well-specified, low-blast
  work (`worker -m openai-codex/gpt-6-luna:high`).
- `luna:max` — the `worker` default.
- `gpt-6-sol:xhigh` — the hard floor for anything touching production data,
  auth, migrations, or payments.
- `mechanical` — when the output is known in advance.
- Controller-tier models (Opus, Fable, Sol, Astra) are never dispatched as
  workers unless the brief carries a literal
  `[CONTROLLER-TIER-JUSTIFIED: <reason>]` marker.

### 2.2 Claude Code (`claude-code/agents/`)

The Agent tool only accepts `haiku` | `sonnet` | `opus` (| `fable`), so the same
tiers map onto five roles. `/onboard` picks the model per role from your budget;
the full-budget mapping is:

| Role | Model | Pi equivalent |
|---|---|---|
| `controller` | `opus` | the session itself / `planner`, `plan-reviewer` |
| `research` | `sonnet` | `scout`, `researcher` |
| `implementation` | `sonnet` | `worker` |
| `review` | `sonnet` | `reviewer` |
| `mechanical` | `haiku` | `mechanical` |

### 2.3 Codex (rendered by the installer into `~/.codex/agents/*.toml`)

| Role | Model / effort |
|---|---|
| `controller`, `implementation`, `review`, `research` | `gpt-6-sol` / high |
| `explorer` | `gpt-6-sol` / medium |
| `mechanical` | `gpt-6-luna` / low |

### 2.4 OpenCode (`opencode/.opencode/`)

Same five roles; `/onboard` resolves models from the providers you have.

### 2.5 Extra lanes worth copying (patterns, not shipped)

These exist in the original setup but are private to it. Rebuild them for your
own needs:

- **Confidential-data lane** — a parallel `*-scout` / `*-worker` /
  `*-mechanical` / `*-heavy` set pinned to models hosted in the required
  jurisdiction (e.g. EU-only), forced to run locally, used *only* for
  confidential folders. Normal work keeps the normal roster.
- **Local-model lane** — `qwen-scout` / `qwen-worker` style profiles pointing at
  a self-hosted model on your own hardware for zero-marginal-cost read work.
- **Deep-research lane** — an agent that drives a hosted deep-research product
  for multi-minute cited reports. Excluded here because it automates a GUI
  browser, which breaks the "subagents never touch the screen" rule.
- **Multi-agent pipelines** — the original Claude Code setup also runs
  *deep-plan* (haiku mapper → sonnet explorer → opus planner → sonnet reviewer)
  and *hyperresearch* (fetcher, source/loci analysts, depth investigator,
  width/depth/dialectic/instruction critics, synthesizer, patcher, polish
  auditor — sonnet for gathering, opus for judgment). Same principle: cheap
  models gather, the strong model judges.
- **Bulk fan-out** — for hundreds of independent rows (screening, extraction),
  a script that shards the list across many cheap headless workers on a spare
  machine, outside the 6-wide subagent tool.

---

## 3. Dispatch doctrine (the rules that make the roster work)

All in the host instruction files under **Working rules** (Claude Code
`claude-code/CLAUDE.md`, Codex `codex/AGENTS.md`, OpenCode `opencode/AGENTS.md`,
Pi `Pi/AGENTS.md`). Summary:

- **Brief play-back** — on any task-opening prompt that is big, a dump, a
  build/plan, a harness change, or ambiguous, the agent restates the brief
  unasked (≤6 lines: goal, will do, won't do, done-when, assumptions; ≤3
  questions; "Go?") and writes nothing until you say go.
- **Questions are not work** — advice gets answered now, ≤10 lines, no
  subagents.
- **Handoff mode** — "give it to a subagent": zero recon, rewrite the brief,
  background dispatch, one-line reply.
- **Batch rule** — ≥6 independent items or ≥2 real jobs: triage, group by
  disjoint files, one worker per group, verify once.
- **Runaway guard** — "done?" gets DONE / NOT DONE in ≤5 lines with no tools;
  one review round; bookkeeping is not work; >20 file mutations in a turn
  (incl. shell writes) → dispatch a worker.
- **Smallest first** — 10-line smallest version before any plan; ≤3 milestones
  by default; consumer-grade ≠ enterprise-grade.
- **Controller fan-out** (Pi `FABLE-MODE.md`, injected for controller-tier
  sessions) — read-heavy work goes to up to 5 background scouts; writes go to
  small worktree-isolated jobs; judgment stays with the controller.
- **Never delegated** — architecture, security, privacy, data-loss, legal
  decisions, final acceptance.

---

## 4. 1:1 replication checklist

### Pi

```sh
# 0. back up what you have
cp -R ~/.pi/agent ~/.pi/agent.bak-$(date +%Y%m%d)

# 1. resources (review `diff -ru Pi ~/.pi/agent` first if you already customised)
cp -R Pi/agents Pi/extensions Pi/prompts Pi/skills Pi/themes ~/.pi/agent/
cp Pi/AGENTS.md Pi/FABLE-MODE.md ~/.pi/agent/

# 2. user-level helpers
mkdir -p ~/bin && cp Pi/bin/{web,pi-bg,luna} ~/bin/ && chmod +x ~/bin/{web,pi-bg,luna}

# 3. optional packages — review Pi/packages.example.json, then e.g.
#    pi install npm:pi-mcp-adapter@<version>

# 4. log in to the providers your roster uses (OpenAI Codex, Anthropic)
pi   # then /login

# 5. restart pi (or /reload) and verify
node --test Pi/tests/*.test.mjs
bash Pi/tests/pi-bg-smoke.sh && bash Pi/tests/luna-smoke.sh
```

Knobs (all optional):

| Setting | Effect |
|---|---|
| `~/.pi/agent/turn-budget.json` | override the 250 msg / $40 / 90 min / 12 bg-turn limits; `/budget off\|on\|reset` |
| `PI_SUBAGENT_TIMEOUT_MIN` | blocking-subagent kill timer (default 10) |
| `PI_AUTO_TITLE=0` / `PI_AUTO_TITLE_MODEL=provider/model` | disable / LLM-refine session titles (prompt text goes to that provider) |
| `PI_REMOTE_SUBAGENT_HOST`, `_HOME`, `_MAP` | allowlisted remote execution (see `Pi/README.md`) |
| `WEB_PROXY` | proxy retry for `web` on filtered networks |
| `enabledModels` in `settings.json` | which models Ctrl+P cycles through |

### Claude Code, Codex, OpenCode

Use the receipt-backed installer (`INSTALL.md`): paste the repo link into the
host and ask it to install and onboard you; it previews every change first.
Then do section 1 (web) — the installer does not put `web` on `PATH`.

### Done when

- `web search "test" 1` and `web research "test" 1` both exit 0.
- A subagent asked to "find the current price of X" runs `web search`, not
  `web research`.
- A multi-requirement prompt gets a brief play-back before any edit.
- `/budget` (Pi) prints the limits; `/bg` lists background jobs.
