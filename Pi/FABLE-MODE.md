# Controller mode — Luna fan-out doctrine

Active while the Pi session model is controller-tier: Fable, GPT Sol, Opus,
or Astra. `extensions/fable-mode.ts` injects this file from the active Pi config.
Worker models never receive it.

The controller is the brain. `scout`
(`openai-codex/gpt-6-luna:high`) is the eyes. Spend controller tokens on
judgment and Luna tokens on reading.

- **Questions are not work.** Advice, a briefing, "what do I say", or anything
  the user needs in the next few minutes: answer now from context, ≤10 lines,
  zero subagents. Offer a deeper dig separately. Fan-out is for repository or
  research work the user asked for.
- **Handoff mode beats everything here.** When the user explicitly says "give it
  to a subagent" / "hand this off": zero recon, rewrite the brief, dispatch in
  the background, reply in one line (see `AGENTS.md` → Working rules).

- **Token-heavy read work goes out by default:** repository recon, file/log/doc
  reading, grep and callsite tracing, tests and output reporting, research,
  extraction, and summarization. Integrity-critical auth, money, migration,
  security, privacy, and data-loss code stays in the controller.
- **Fan out up to five independent background scouts, then keep working.** Split
  by directory or question; brief each in one paragraph with the required output
  shape. Never make one scout depend on another scout’s result.
- Use `subagent` with `tasks: [{agent:"scout", task:…}, …]` and
  `background: true`. It returns job IDs immediately and later delivers
  `[subagent-bg <id> done]` follow-up turns. A blocking single scout is fine only
  when its answer gates the next action.
- **Scout first; keep write units small.** Split independent writes into small,
  disjoint units. Never fan out parallel writes to one file. Do not wait on a
  job while independent work remains.
- **Speed = small units.** A write job over ~3 files or ~5 minutes is too coarse:
  scout the shape first, then split writes into ≤3-file units that finish in
  parallel. Completion is pushed (`subagent-bg` / `pi-bg-notify`); never sleep
  or poll.
- Write jobs use `worker` (`luna:max`) or worktree-isolated `pi-bg`; high-blast
  repositories stay on `gpt-6-sol:xhigh`.
- **Fan-out is budgeted.** `turn-budget.ts` pauses auto-chaining at its limits
  and steers once at 75%: leave the tree clean and reply DONE / NOT DONE. More
  than 20 direct file mutations in a turn (including shell writes) means you are
  the worker now — stop and dispatch. ≥6 independent items in one message is the
  Batch rule: triage inline, fan out by disjoint file group, verify once.
- Architecture, security, privacy, data-loss, legal judgment, final synthesis,
  and final acceptance stay in the controller. Verify scout output before using
  it; load-bearing claims get a second source or direct controller check.
- Evidence tied to the controller host—installed apps, local permissions,
  launch services, machine logs, and host configuration—must be read locally.
  A remote subagent may not see the same machine.
- Subagents never automate the GUI. Use CLI/config/logs or tell the human what to
  click.
