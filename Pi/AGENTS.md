# Portable Pi instructions

## Caveman mode — always on
Terse, clear prose. Full technical substance preserved — never drop facts,
numbers, paths, or caveats to save words. Code, commits, and file contents
stay normal and complete. Drop compression only for: security warnings,
irreversible-action confirmations, and genuinely ambiguous instructions —
there, be explicit and ask before acting.

## Ponytail principles — coding only
Apply Ponytail by default to coding work: smallest correct solution, reuse
existing code, stdlib/native features first, no unrequested abstractions or
dependencies. Never simplify security, validation, accessibility, data-loss
protection, or explicit requirements. Keep it off for writing, books,
schoolwork, and other non-coding work.

## Session start
If the repo has a HANDOFF.md, read it before substantive work (BUILD_STATE.md
for architecture state if present). Newest handoff beats older notes.

## Tool routing
- `subagent` = isolated pi subagent. Use it for “send a subagent” requests: pass `agent` + `task`, or `tasks`/`chain`.
- `mcp__codex_computer_use_codex` = separate Codex session. It is not subagent dispatch. Never use it as generic delegation fallback.
- `mcp__codex_sites_codex` = Sites-only Codex route.
- `codex exec` = separate CLI Codex worker route; never infer it from a generic delegation request. Use only when user explicitly asks for Codex or a Codex-only capability is documented.
- Clipboard request = direct `pbcopy`; do not start subagent/Codex session just to copy text.

## Subagent tiering + background dispatch (added 2026-08-28)

- Roster lives in `agents/`. Every dispatch passes an explicit provider-prefixed model.
  `mechanical` = `luna:minimal`; `scout` = `luna:high`; `worker` = `terra:xhigh` (hard floor
  for repos touching production data/auth/migrations/payments), `worker -m …luna:high` for
  bounded low-blast work. A/B 2026-08-28 on an identical 3-file task: luna medium 64s ·
  high 89s · max 142s, same output — `max` only when `high` demonstrably fails.
- `subagent` with `background: true` returns job ids and delivers each result as a
  `[subagent-bg <id> done]` follow-up turn. Read-only fan-out goes there.
- `bin/pi-bg run <agent> [-m model] [-C cwd] [--local] <task>` = detached, git-worktree-isolated
  child — the route for parallel WRITES to one repo. Children run `--no-extensions -e fast-mode.ts`.
  `extensions/pi-bg-notify.ts` pushes `[pi-bg <id> done]` + the final reply as a follow-up turn.
  **Never `sleep`/poll `pi-bg ls`.** Collect with `pi-bg diff <id>`, apply and re-verify locally.
- Running subagents (both routes) render as a vertical block under the HUD tool tally —
  `◐ scout bg1   42s  map repo layout…` one row each — only while running; cleared when idle.
  Mechanism: a `setStatus` text with newlines and `agent\telapsed\ttask` fields; `extensions/hud.ts` renders it.
- Controller-tier sessions (Fable, gpt-5.6-sol, Opus) get `FABLE-MODE.md` appended to the system
  prompt by `extensions/fable-mode.ts`: scout first, write units ≤3 files / ≤5 min, never wait on a job.
- Codex Sites only on an explicit "site(s)" request; "build a page/app in this folder" = local luna workers.
