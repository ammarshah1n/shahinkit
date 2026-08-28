# pi efficiency overhaul + HUD running-subagent block

Date: 2026-08-28 · Controller: Claude Fable 5 (Claude Code) · Mirror: `~/shahinkit` commits `6eeba86`, `8d1b829`, `5f189d5`, `879d041` (pushed to `origin/main`)
Companion: `EFFICIENCY-PLAN-2026-08-28.md` (ranked next steps + rollback). Memory: `~/.claude/projects/-Users-integrale/memory/project_pi_efficiency_overhaul.md`; basic-memory `brain-meta/06-context/learnings/2026-08-28-pi-fan-out-was-slow…`.

---

## 1. Trigger

Cars session (`sessions/…Cars…/2026-08-28T02-24-28…jsonl`): model `gpt-5.6-sol`, 15 min, $1.30, 29 bash calls to build a small ranking site. Ammar: *"Why didn't sol just dispatch a team of luna subagents?"*

### Root causes (all verified from the transcript)

| # | Cause | Evidence |
|---|---|---|
| 1 | Luna fan-out doctrine was **Fable-only** | `extensions/fable-mode.ts:14` — `if (!/fable/i.test(model)) return`. Sol never saw "scout first / fan out by default". |
| 2 | First two turns went to **Codex Sites** | "build a website" matched `codex-sites` skill → 2× `mcp__codex_sites_codex` before "Forget sites". |
| 3 | Sol *did* dispatch 4 luna jobs — via **`pi-bg`**, not `subagent` | Parallel writes to one repo → AGENTS.md L62 mandates `pi-bg` worktrees. Correct per doctrine. |
| 4 | **`pi-bg` had no completion signal** | ~20 of 29 bash calls were `sleep 12–60; pi-bg ls`. AGENTS.md L61 still said "`subagent` blocks the turn" (stale since 27 Aug). |
| 5 | **`luna:max` is slow** for bounded work | One UI worker: 12.5 min / 128 tool calls / 11.7 MB jsonl. |
| 6 | `pi-bg` **local** children loaded **every extension + MCP** | No `--no-extensions` on the local path (remote path had it). Child saw ~70 tools incl. 50 `timed` schemas. |

Not the cause: `subagent` was registered and advertised `background: true`; auth was fine (0-byte `.err` on all jobs).

---

## 2. Changes — live config (`~/.pi/agent`, `~/bin`, `~/.claude`)

### 2.1 `extensions/pi-bg-notify.ts` (new)
- `tool_result` hook on bash: finds job ids printed by `pi-bg run` (regex `^[a-z][a-z-]*-\d{6}-\d+$`, must have a `.pid`), appends *"tracking X — do NOT sleep/poll `pi-bg ls`"* to that tool result.
- Polls each pid every 5 s (`process.kill(pid, 0)`, same test `pi-bg ls` uses). On exit: `pi.sendMessage({customType:"pi-bg-result", …}, {triggerTurn:true, deliverAs:"followUp"})` carrying `[pi-bg <id> done] <meta> <secs>` + the job's final reply (same parser as `pi-bg get`, 6 000-char cap, stderr tail if empty).
- Publishes HUD rows (see §2.7) while jobs run; clears when none.
- Test hook: `PI_BG_NOTIFY_LOG=<file>`. Verified with a real `luna:minimal` job and a fake-`pi` harness.

### 2.2 `extensions/fable-mode.ts` + `~/.claude/hooks/fable-mode.sh` — widened
`/fable/i` → `/fable|sol|opus/i` (Claude Code hook: `*fable*|*opus*`). `FABLE-MODE.md` retitled **"Controller mode — luna fan-out doctrine"**; new bullet: *scout first, write units ≤3 files / ≤5 min, never wait on a job — completion is pushed.*
Cost: +708 tokens/turn for sol/opus sessions (prompt-cached after turn 1).

### 2.3 `~/bin/pi-bg` — local children
`nohup pi --no-extensions -e ~/.pi/agent/extensions/fast-mode.ts …` (parity with `~/bin/luna` and the remote path). Child tool surface **70 → 7**, priority tier on, cold start **7.8 s → 5.9 s**. Also writes `~/.pi/bg/<id>.task` (task text for the HUD row); `pi-bg clean` removes it.

### 2.4 Default luna tier `max` → `high`
A/B on an identical 3-file drag-and-drop page (all three passed `node --check`, DnD + localStorage present):

| tier | wall time | tool calls |
|---|---|---|
| `luna:medium` | 64 s | 8 |
| `luna:high` | 89 s | 11 |
| `luna:max` | 142 s | 14 |

Applied to `agents/scout.md`, `~/bin/luna`, AGENTS.md "Worker tiering", `~/CLAUDE.md` tier table. `max` only when `high` demonstrably fails; `medium` for near-mechanical writes.

### 2.5 `rtk` wired in
- pi: `rtk init -g --agent pi` → `extensions/rtk.ts` (audited: delegates to `rtk rewrite`, fail-open, 2 s timeout). Verified: `rtk gain --history` shows `rtk git log` executed from a pi child.
- Claude Code: `~/.claude/settings.json` `PreToolUse` Bash → `rtk hook claude`. **There was no rtk hook before** despite `RTK.md` claiming one. Backup `settings.json.bak-rtk-20260828`.

### 2.6 `mcp.json` — `timed` direct tools 50 → 7
pi-mcp-adapter 2.15 exposes **all** server tools as direct tools unless `directTools` is set. Allowlist from actual usage across all sessions: `get_context_for, list_tasks, memory_ingest, write_note, add_observation, update_task, search_memory`. Rest via `mcp({search})`. **−5 152 tokens per controller turn.** Backup `mcp.json.bak-directtools-20260828`. Needs `/reload`.

### 2.7 HUD — vertical running-subagent block
Ammar: *"no way of knowing there are subagents running… a vertical list of the subagents and what they are doing."*

- `extensions/hud.ts`: any extension status whose text contains **tab-separated fields** is a block — rows split on `\n`, fields `agent\telapsed\ttask` — rendered under the tool tally (line 3), only while non-empty. Single-line statuses still go on line 5.
- Publishers: `subagent/index.ts` (`publishStatus()` — bg jobs from `bgJobs`, blocking calls via `tool_call`/`tool_result` hooks on `subagent`; 5 s refresh timer while running) and `pi-bg-notify.ts` (`publish()` — reads `<id>.task`). Status key cleared (`setStatus(key, undefined)`) when nothing runs, so the idle footer is unchanged.
- Rendered (width 120, from `tests/hud-layout.test.mjs`):
  ```
  ✓ bash ×19 · ✓ read ×4 · ✗ edit ×1
    ◐ mechanical ⇢     7s  copy 22 candidate photos into assets/
    ◐ scout bg1     42s  map repo layout for cars.js and the ranking UI so the worker brief is exact
    ◐ worker bg2  1m12s  implement data/cars.js + validator
  Tokens 38M (in 27k · out 123k · cache 37M)                                        0s
  ```
  `⇢` = `pi-bg` job, `bgN` = `subagent background`, bare agent = blocking call.
- Test scenario added to `tests/hud-layout.test.mjs` (PASS at widths 120/80/50/30/20). `tests/hud-quota.test.mjs` has **1 pre-existing failure** ("anthropic → shows a reset countdown"; hud.ts and the test both untouched since 25 Aug — captured reset epoch has aged past now). Not addressed.
- Backups: `hud.ts.orig-20260828`, `subagent/index.ts.orig-20260828`.

### 2.8 Doctrine text (AGENTS.md, FABLE-MODE.md)
- L61 rewritten: `pi-bg` = detached worktree-isolated route for parallel writes; `subagent background:true` for reads; **never sleep/poll**.
- Sites rule: `mcp__codex_sites_codex` only on an explicit "site(s)" request.
- Roster line: scout = `luna:high`; widened-doctrine note.

---

## 3. Token accounting (controller session, per turn)

| Item | Δ tokens |
|---|---|
| `timed` schemas 50 → 7 | −5 152 |
| Doctrine (sol/opus only) | +708 |
| AGENTS.md edits | +350 |
| pi-bg-notify stamp | +45 per dispatch |
| **Net** | **≈ −4 100 every turn**, plus rtk's 60–90 % on tool output |

Child (pi-bg local): ~8 000 tokens of dead schema removed per turn.

---

## 4. Verification log

| What | How | Result |
|---|---|---|
| pi-bg-notify tracking note | `pi -p -e pi-bg-notify.ts` + real `pi-bg run` | note appended |
| pi-bg-notify completion + HUD status | node harness, fake `pi`/`ctx.ui`, real job | follow-up sent with `PONG`; status set → `null` |
| fable-mode widening | `echo '{"model":"gpt-5.6-sol"}' \| fable-mode.sh` | context emitted |
| pi-bg child tool surface | `pi-bg run mechanical … "list your tools"` | 7 tools |
| luna tiers | 3 parallel `pi-bg` workers, same task | table in §2.4 |
| rtk in pi | `pi -p -e rtk.ts` + `rtk gain --history` | `rtk git log` recorded |
| all extensions load | `pi -p --no-session … "Reply OK"` | `OK`, 0 load errors |
| HUD layout | `node tests/hud-layout.test.mjs` | PASS |

---

## 5. Operating notes

- **Restart pi** after any of this (extensions load at startup; `/reload` + `/hud` ×2 also works; `/reload` for `mcp.json`).
- A running session from before the change sees none of it.
- Never `pi-bg clean` while another session's jobs are running — it wipes every job dir.
- Open items (Ammar's call): **A** persisted big tool output to file + preview; **B** `bash_bg` tool on the same pid watcher; **C** remote-to-fedora dispatch → local-by-default. Details in `EFFICIENCY-PLAN-2026-08-28.md`.

## 6. Rollback

- `mcp.json.bak-directtools-20260828`, `~/.claude/settings.json.bak-rtk-20260828`
- `extensions/hud.ts.orig-20260828`, `extensions/subagent/index.ts.orig-20260828`
- Delete `extensions/pi-bg-notify.ts` / `extensions/rtk.ts` to remove either
- `fable-mode.ts:15` regex back to `/fable/i`
- `~/bin/pi-bg`: drop `--no-extensions -e …fast-mode.ts` on the local `nohup pi` line
