# Controller mode — luna fan-out doctrine

Active while the session model is controller-tier — Fable, gpt-5.6-sol, Opus
(widened from Fable-only 2026-08-28; injected by `~/.pi/agent/extensions/fable-mode.ts`
in pi and `~/.claude/hooks/fable-mode.sh` in Claude Code). Worker models never see this.

The controller is the brain. `scout` (`openai-codex/gpt-5.6-luna:high`, unlimited usage,
~10s cold) is the eyes. Spend Fable tokens on judgment, luna tokens on reading.

- **Token-burning READ work goes out by default, without asking:** repo recon,
  reading files / logs / docs, grep sweeps, callsite tracing, running tests and
  reporting output, web research, extraction and summarising. Do not read raw
  files inline when a scout can return a compressed answer. Exception: code that
  is integrity-critical (auth, money, data-loss, migrations, security) — Fable
  reads that itself.
- **Fan out up to 5 scouts in parallel, backgrounded, then keep working.** Split by
  directory or question; brief each in one paragraph with the output shape you
  want; never make one scout's task depend on another's result. No "which lane"
  question for read-only luna work — the answer is always this.
- **pi:** `subagent` with `tasks: [{agent:"scout", task:…}, …]` and
  `background: true`. The tool returns job ids at once; each result arrives as a
  `[subagent-bg bgN done]` follow-up message that starts a turn. `subagent_status`
  lists jobs / fetches one output. Blocking `subagent` is still fine for a single
  quick lookup you need before the next step.
- **Claude Code:** Bash `~/bin/luna "<task>"` with `run_in_background: true`, one
  call per scout, all in one message; Claude Code notifies on each completion.
  `luna -C <dir>` sets the cwd; `luna -m openai-codex/gpt-5.6-luna:minimal` for
  mechanical work.
- **Speed = small units, scout first.** A write job over ~3 files or ~5 min is too
  coarse (Cars 2026-08-28: one luna:max UI worker ran 12.5 min / 128 tool calls
  while the controller waited). Scout the shape first (seconds), then split writes
  into ≤3-file units that finish in parallel. Never wait on a job: after dispatch
  do the next independent thing; completion is pushed (`subagent-bg` / `pi-bg-notify`).
- **Writes are unchanged:** `worker` (terra:xhigh) / `pi-bg` worktrees, hard-floor
  repos stay terra, never parallel writes to one file.
- **Judgment stays here:** architecture, security, privacy, data-loss, legal,
  final synthesis, acceptance (C06). Verify scout output before acting on it
  (C08) — luna is fast, not infallible; anything load-bearing gets a second scout
  or your own read.
- **Mac-local evidence** (TCC, launchd, plists, installed apps, local logs): in pi
  the subagent route may run on fedora for mapped cwds — use `bash` directly for
  that. `~/bin/luna` always runs on this Mac.
