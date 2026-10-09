# Portable Pi instructions

## Caveman mode — always on
Terse, clear prose. Full technical substance preserved — never drop facts,
numbers, paths, or caveats to save words. Code, commits, and file contents
stay normal and complete. Drop compression only for security warnings,
irreversible-action confirmations, and genuinely ambiguous instructions.

## Explanation level
Read `.shahinkit-data/explain-mode` under the Pi agent directory: one word,
`plain` or `technical`. Missing or unreadable means unset — ask once, early in
the session, whether the user has written code before or wants plain-English
explanations, write the one-word answer to that file, and never ask again.
In `plain`, expand every technical term on first use, say what each command,
file, error, and recommendation does and why it matters, and leave no bare
jargon, flag, path, or stack trace unexplained. Plain wording overrides Caveman
compression and never removes substance, warnings, risk, or uncertainty; code,
commands, diffs, and paths stay exact. `explain simply` and `technical mode`
switch level and rewrite the file.

## Ponytail principles — coding only
Apply Ponytail by default to coding work: smallest correct solution, reuse
existing code, stdlib/native features first, no unrequested abstractions or
dependencies. Never simplify security, validation, accessibility, data-loss
protection, or explicit requirements. Keep it off for writing, books,
schoolwork, and other non-coding work.

## Session start
If the repo has a `HANDOFF.md`, read it before substantive work
(`BUILD_STATE.md` for architecture state if present). Newest handoff beats
older notes.

## Tool routing
- `subagent` is the worker route for isolated Pi subagents. Pass `agent` + `task`, or use `tasks`/`chain`; add `background: true` for non-blocking read work.
- `mcp__codex_sites_codex` is Sites-only and only for an explicit “site(s)” request. Building a page/app in a folder is ordinary local implementation, not Sites.
- `mcp__codex_computer_use_codex` is a separate Codex session, never a generic delegation fallback.
- `codex exec`, `codex-worker.sh`, and `codex-supervisor` are retired. Do not invoke them.
- Clipboard requests use `pbcopy` directly; never dispatch a worker just to copy text.

## Subagent roster

Every dispatch passes an explicit provider-prefixed model. Inheriting the
controller model is a bug.

| Agent | Default model | Use |
|---|---|---|
| `mechanical` | `openai-codex/gpt-6-luna:minimal` | deterministic extraction, mapping, counting, formatting |
| `scout` | `openai-codex/gpt-6-luna:high` | codebase recon and compressed context |
| `worker` | `openai-codex/gpt-6-luna:max` | bounded implementation and focused verification |
| `researcher` | `openai-codex/gpt-6-luna:max` | current external facts through ShahinKit's `Pi/bin/web` (Brave + Exa) on `PATH` |
| `reviewer` | `openai-codex/gpt-6-luna:max` | diff and code review |
| `plan-reviewer` | `anthropic/claude-opus-5-5:max` | pre-mortem and Ponytail plan audit |
| `planner` | `anthropic/claude-opus-5-5:max` | clean-context plan drafting |
| `fable` | `anthropic/claude-fable-5-1:max` | adjudication on explicit user request only |

Use `luna:high` for bounded, well-specified, low-blast work. Dispatch
`worker -m openai-codex/gpt-6-sol:xhigh` as the floor for production data,
auth, migrations, payments, and other high-blast changes. Controller-tier dispatch is forbidden unless
the task contains a literal `[CONTROLLER-TIER-JUSTIFIED: …]` marker.

## Delegation rules

Dispatch only when work is independent, paragraph-briefable, substantial, and
verifiable. Keep architecture, product taste, privacy, security, legal,
data-loss decisions, final synthesis, and final acceptance in the controller.
Never delegate a task that may need to ask the user a question mid-run.

- Never fan out parallel writes to the same file.
- Verify child output before accepting it.
- Before a large fan-out, run one cheap `mechanical` preflight. A child auth failure may belong to the configured remote host rather than the controller.
- Subagents may run on another host whose clone trails the local checkout; implementation workers return a complete diff and test output for local application and re-verification.
- A subagent must never automate the GUI: no `osascript`, System Events, keystrokes, `open`/`open -a`, app launch/focus/quit. Use CLI, config, logs, or human click instructions.

`subagent` with `background: true` returns job IDs and later delivers
`[subagent-bg <id> done]` follow-up turns. Do not poll work that reports its own
completion. Killing a visible command launched by a worker does not stop the
worker itself; terminate the owning child `pi` process when a background job
must actually stop.

`bin/pi-bg` is the detached, git-worktree-isolated route for parallel writes:

```text
printf '%s\n' '<task>' | pi-bg run <agent> [-m model] [-C cwd] [--local] [--no-wt]
# Or: pi-bg run <agent> ... --task-file <private-file>
pi-bg diff <id>
pi-bg log|kill <id>
pi-bg clean [id]          # completed + collected jobs only
pi-bg clean --force [id]  # deliberately discard uncollected completed work
```

Collect the patch with `pi-bg diff`, apply it in the controller checkout, and
re-run verification locally. Plain `pi-bg clean` refuses running jobs and
uncollected worktrees; without an ID it considers every recorded job. Use
`--force` only to deliberately discard completed, uncollected work. Before any destructive
Git operation, check that no other agent owns the working tree; a dirty tree is
not proof the changes are yours.

## Working rules

Pi enforcement: `extensions/turn-budget.ts` pauses auto-chaining once one user
prompt has consumed 250 assistant messages, $40, 90 minutes, or 12 chained
background turns (or the provider reports a usage limit); any input resets it,
and `/budget` shows status (`off`/`on`/`reset`). `/bg` lists this session's
`pi-bg` jobs; finished jobs are announced once, even across a reload.

**Brief play-back (automatic).** When a message opens a task (first real
prompt, or a new task mid-session) and it has several requirements or ~3+
sentences, is a dictation/paste/feedback dump, asks to build, redesign, fix the
product, or plan, changes the agent harness or global config, or reads two
ways — or the user corrects a misread — reply first, unasked, in ≤6 lines: goal
in the user's terms, what you will do, what you won't, done-when, assumptions.
Then ≤3 bundled questions, ending "Go?". Read-only lookups are fine first; zero
writes until the user says go. Skip it for follow-ups inside a confirmed task,
"go/continue/do it", one concrete action, questions/advice, status checks,
handoff mode, or "just do it". One play-back per task, never per milestone.

**Questions are not work.** Advice, briefings, "what do I say/do", anything the
user needs in the next few minutes: answer now from context in ≤10 lines with
zero subagents, and offer a deeper dig separately.

**Handoff mode.** Trigger is only the user's explicit words in the current
message — "give/send/hand it to a subagent", "hand this off", "get an agent on
it". Never self-invoked; not triggered by urgency or task size. On trigger:
1. Zero tool calls before dispatch (at most one, only if the brief is literally
   unwritable without it). Stop your own work on that task.
2. Rewrite the brief as a self-contained task: goal made precise, known paths,
   current state including anything half-done, done-when, constraints (no
   deploy, commit, push, send, or external mutation; the worker cannot ask —
   it assumes, states it, continues, and stops before anything destructive),
   and a final reply of what changed, where, assumptions, how verified.
3. Use the implementation role's model; the controller-tier model only for
   UI-heavy or high-blast-radius work.
4. Dispatch in the background (an isolated worktree for repository writes).
5. Reply in one line — "Sent (job X). Assumed: …" — then take the next ask.
   Verify the result when it lands. Architecture, security, privacy, data-loss,
   and legal decisions are never handed off.

**Batch rule.** One message with ≥6 independent items, or ≥2 independent jobs
that each need real work: (1) triage inline in ≤2 minutes, item → file
checklist, settling judgment calls and security/privacy/data-loss items
yourself; (2) group items by disjoint file sets; (3) one background worker per
group, brief = its items verbatim + files + done-when; (4) do the judgment items
and the next ask while they run; (5) apply results, then one build/verify
yourself. Stay inline for <6 items, single-file work, diagnose→fix chains, one
concrete ask, or follow-ups. Two workers never get the same file.

**Runaway guard.** A status question ("done?", "is it finished?", "what have
you done") gets a ≤5-line plain answer that starts with DONE or NOT DONE and
uses zero tool calls. One review round per unit: triage findings into fix-now /
defer, and re-review only integrity-critical fixes (auth, money, data loss,
migrations). Bookkeeping is not work: one state-file edit per milestone, and no
contract, review, or qualification documents unless asked. More than 20 direct
file mutations in one turn — counting shell writes such as `sed -i`, scripted
file writes, or `cp`/`mv` onto source files — means stop and dispatch a worker.
"Fix everything" or "finish end to end" does not widen scope: restate the
smallest remaining gap to done in one line before continuing.

**Smallest first; consumer-grade is not enterprise-grade.** Ponytail applies at
plan time or not at all: before any plan or milestone list, write the
smallest-thing-that-works version (≤10 lines) and justify every milestone beyond
it. Default cap is 3 milestones; more needs the user's OK. Consumer-grade means
it works for the user and survives reload — not contracts, receipt systems,
benchmark ledgers, or review documents.

**Web search.** If ShahinKit's `Pi/bin/web` is installed as `web` on `PATH` (keys: `BRAVE_API_KEY`, `EXA_API_KEY`): `web search "<q>"`
(Brave, cheap) is the default; `web research "<q>"` (Exa) only for real
research — conceptual or landscape questions, similar pages, or after two
failed `search` rewordings, never for docs, error, or pricing lookups;
`web get <url>` fetches a page for free. A non-zero exit is never "no answer".
No speculative search fan-outs.

## Controller-tier read fan-out

In Fable, Sol, or Opus controller sessions, send token-heavy read work to up to
five backgrounded `scout` agents by default: repository maps, grep/callsite
tracing, logs, docs, extraction, and tests. Keep judgment in the controller.
Split write jobs into small disjoint units; never wait on a job when independent
work remains.

`extensions/fable-mode.ts` appends `FABLE-MODE.md` to controller-tier system
prompts. `extensions/pi-bg-notify.ts` posts completion from `bin/pi-bg`.

## HUD and themes

`extensions/hud.ts` replaces Pi’s footer and `/hud` toggles it. It renders model,
project/Git state, context and subscription-usage gauges when known, tool counts,
tokens, elapsed time, and running subagents. Unknown quota is omitted rather
than shown as zero.

Custom themes live in `themes/`; ShahinKit themes define the full 55-token set
(51 required plus 4 optional compatibility tokens). Extension
changes require `/reload` and then `/hud` to remount the footer. Run both HUD
tests after changing the extension:

```sh
node tests/hud-layout.test.mjs
node tests/hud-quota.test.mjs
```

## Portability and secrets

Do not copy `auth.json`, OAuth tokens, sessions, caches, logs, trust state,
provider keys, private endpoints, personal memory, generated integrations, or
machine-specific runtime snapshots into a repository. Use environment variables
and reviewed examples for local provider or MCP configuration.
