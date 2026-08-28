# pi efficiency plan — 2026-08-28

Trigger: Cars session (gpt-5.6-sol, 15 min, $1.30, 29 bash calls). Sol built a
website via Codex Sites twice, then dispatched 4 luna jobs via `pi-bg` and
sleep-polled `pi-bg ls` ~20 times while a single `luna:max` UI worker ran 12.5 min.

## Done today (all verified live)

| # | Change | Where | Measured effect |
|---|---|---|---|
| 1 | `pi-bg-notify.ts` — pushes `[pi-bg <id> done]` + final reply as a follow-up turn; stamps "do NOT poll" on the dispatch result | `~/.pi/agent/extensions/pi-bg-notify.ts` | 20 poll calls → 0 |
| 2 | `pi-bg` local children run `--no-extensions -e fast-mode.ts` (parity with `~/bin/luna`) | `~/bin/pi-bg` | child tool surface 70 → 7, priority tier on, cold start 7.8s → 5.9s |
| 3 | Luna doctrine widened Fable-only → Fable/sol/Opus | `extensions/fable-mode.ts`, `~/.claude/hooks/fable-mode.sh`, `FABLE-MODE.md` | sol now scouts-first / fans out without being told |
| 4 | Default luna tier `max` → `high` (A/B 3-file DnD page, identical output: medium 64s · high 89s · max 142s) | `agents/scout.md`, `~/bin/luna`, AGENTS.md tiering, CLAUDE.md | ~1.6× faster bounded work |
| 5 | `rtk` wired into pi (`rtk init -g --agent pi` → `extensions/rtk.ts`, delegates to `rtk rewrite`, fail-open) and into Claude Code (`PreToolUse` Bash → `rtk hook claude`) | `extensions/rtk.ts`, `~/.claude/settings.json` | 60–90% fewer tokens on git/ls/grep/test/npm output (rtk's own numbers; first pi hit −25%) |
| 6 | `timed` MCP direct tools 50 → 7 (allowlist from real usage: get_context_for, list_tasks, memory_ingest, write_note, add_observation, update_task, search_memory); rest via `mcp({search})` | `~/.pi/agent/mcp.json` | ~43 tool schemas removed from every controller turn |
| 7 | Doctrine: scout first, write units ≤3 files / ≤5 min, never wait on a job; Sites only on explicit "site(s)"; stale "subagent blocks the turn" fixed | `FABLE-MODE.md`, AGENTS.md | prevents the three behaviours that cost the Cars session |

Restart pi (extensions load at startup; `/reload` for mcp.json) and Claude Code.

## Parity with Claude Code — where pi now stands

| Claude Code capability | pi equivalent | Status |
|---|---|---|
| Background Agent + completion notification | `subagent background:true` (27 Aug) + `pi-bg-notify` (today) | ✅ |
| Deferred tool schemas (ToolSearch) | mcp-adapter proxy + `directTools` allowlist | ✅ after #6 |
| Hooks (SessionStart / PreToolUse) | extensions (`before_agent_start`, `tool_call`, `tool_result`) | ✅ |
| rtk token filter | `rtk.ts` | ✅ pi ahead — Claude Code had no hook until today |
| Auto-compaction | built-in (reserve 16k, keep 20k) | ✅ |
| Tool output truncation | 2000 lines / 50 KB | ✅ |
| Large tool output persisted to file + preview | none — output is cut, not saved | ❌ (item A) |
| Backgrounded Bash with wake-up | none (only subagents) | ❌ (item B) |
| Model tiers for subagents | luna:minimal / high / terra / sol | ✅ |

## Next, ranked by gain per line of code

**A. Persisted tool output (extension, ~40 lines).** `tool_result` hook on bash/read:
if content > ~8 KB, write it to `~/.pi/agent/tool-out/<id>.txt`, replace with first
40 lines + path. Same as Claude Code's persisted-output. Saves the 50 KB bash dumps
that currently land in context whole.

**B. `bash_bg` tool (~60 lines).** `pi.registerTool` that spawns a command detached,
returns a job id, and reuses the `pi-bg-notify` pid-watch to push stdout tail when it
exits. Removes the last reason to `sleep N; check`.

**C. Remote dispatch default.** `subagent`/`pi-bg` send mapped cwds (`~/Documents`,
`time-manager-desktop`, `facilitated`) to fedora by default. Cost: ssh hop, fedora
clone trails local commits, fedora lacks `~/bin` tools unless installed. Decision for
Ammar: flip to local-by-default with `remote: true` opt-in. Not done — behaviour change
he should choose.

**D. Worktrees inside `subagent background`.** Would let one tool do reads and writes
and retire `pi-bg`. Skipped: after #1, `pi-bg` already gives the same UX for writes.
Only worth it if two routes keep causing wrong-route picks.

**E. Weekly check.** `rtk gain` + `grep -c '"sleep' ~/.pi/agent/sessions/**/*.jsonl`
(should trend to zero) + HUD `$cost` per session. If a controller session exceeds
~$1 with <5 subagent dispatches, the doctrine isn't being followed — read that
session's tool calls, not the doctrine.

## Rollback

- `~/.pi/agent/mcp.json.bak-directtools-20260828`
- `~/.claude/settings.json.bak-rtk-20260828`
- Delete `extensions/pi-bg-notify.ts` / `extensions/rtk.ts` to remove either.
- `fable-mode.ts:15` regex back to `/fable/i` to re-narrow the doctrine.
