# ShahinKit

ShahinKit gives **Claude Code, Codex, and OpenCode** the same practical way to
start work, plan it, use specialist agents, remember decisions, and hand work to
the next session. It also includes a standalone **Pi** resource snapshot for
users who want the Pi setup.

You do not need to understand its files before using it.

## Install it

Copy this repository link:

```text
https://github.com/ammarshah1n/shahinkit
```

Paste it into Claude Code, Codex, or OpenCode with this request:

```text
Install ShahinKit from this repository and onboard me. Preview every change before applying it.
```

ShahinKit shows exactly what it intends to add. Nothing is installed until you
approve that preview. Public releases also verify repository, release tag, and
file integrity before changing your host configuration.

## Pi setup

Pi is intentionally not part of the receipt-backed host installer. Review and
copy the standalone resources in [`Pi/README.md`](Pi/README.md). It contains a
2026-09-03 audit of the portable live Pi resources, with credentials, sessions,
private infrastructure, GUI automation, and machine-specific runtime state excluded.

## What changes after installation

Your coding agent gains:

- **43 documented skills** for planning, research, study, review, memory, and
  session handoff;
- **five specialist agents**: controller, research, implementation, review, and
  mechanical, each on a model chosen by your budget;
- **`/onboard`**, which asks what you pay for and tunes model choice and
  delegation to match;
- **safe lifecycle hooks** that point the agent toward Prime and keep worker
  authority bounded;
- **Ponytail**, which prefers the smallest correct solution;
- **Caveman**, which keeps explanations short without deleting technical detail;
- optional **Basic Memory** setup for a local knowledge base; and
- visible Markdown state files instead of hidden transcript capture.

Open **[SKILLS.html](SKILLS.html)** for the searchable guide explaining every
skill and when to use it.

## Normal workflow

### 1. Start or resume with Prime

Ask for `/prime` at the beginning of meaningful work.

Prime reads the smallest useful set of project instructions, current state,
recent work, and optional local memory. It does not edit anything. Its job is to
stop the agent guessing.

### 2. Set your budget once with `/onboard`

`/onboard` asks which hosts you use and roughly what you pay for, then picks the
model and reasoning effort for each specialist agent and decides how eagerly work
is delegated. On an entry subscription the controller plans and hands the
building to cheaper workers. On a top subscription it delegates for parallelism
rather than thrift.

Run it again whenever your subscriptions change. It previews every change and
waits for your approval.

If the lifecycle prompts get in the way somewhere, list that folder in
`.shahinkit-data/opt-out` (one path per line) and ShahinKit stays silent under it.

### 3. Work normally

Describe what you need in ordinary language. ShahinKit can select a skill, or
you can name one directly:

- `/triage` when the request feels unclear or likely to sprawl;
- `/plan` for one non-trivial change;
- `/deep-plan` for broad, risky, or unfamiliar code;
- `/research` for current evidence with sources;
- `/study` for a user-approved Obsidian study structure; or
- `/watch` for a video you supplied and approved for analysis.

Specialist agents do bounded work. Controller keeps architecture, privacy,
security, data-loss decisions, synthesis, and final acceptance.

### 4. Finish with Miniwrap or Wrap Up

Use `/miniwrap` after a tiny task. Use `/wrap-up` after meaningful work.

Wrap Up verifies the changed surface, updates visible state, and writes a
handoff. It never commits or pushes unless you explicitly request that action.

## What is HANDOFF.md?

`HANDOFF.md` is a note from the previous session to the next one. It answers:

- What changed?
- What checks passed or failed?
- What remains blocked?
- What should happen next?

Wrap Up writes it. Prime reads it. `PROJECT_STATE.md` remains current truth;
`NEXT.md` keeps one concrete restart action. ShahinKit stores distilled state,
not raw conversations or tool dumps.

## What do hooks do?

Hooks are small host-native actions around agent events.

- **Claude Code and Codex:** SessionStart reminds the agent that Prime is
  available. SubagentStart reminds workers that their scope is bounded and that
  they do not own final decisions.
- **OpenCode:** native plugins provide the same Prime guidance, worker/mode
  boundaries, command timeout protection, and optional completion notices.

Hooks never run Prime or Wrap Up automatically. They only add brief guidance;
you remain in control of when those workflows run.

ShahinKit hooks do **not** record prompts, upload files, write hidden memory,
auto-commit, auto-push, or bypass permissions. Host configuration changes stay
behind preview, apply, and explicit trust approval.

## Ponytail and Caveman

Both modes are bundled and enabled by default after approved installation.

- **Ponytail:** fewer abstractions, fewer dependencies, existing code first.
- **Caveman:** shorter responses, same technical substance.

Say `stop ponytail`, `stop caveman`, or `normal mode` to turn them off for a
session. Installation can omit either mode with its documented option.

## Basic Memory

Basic Memory is optional and **off by default**. ShahinKit only provides a
local-mode template. It does not create a cloud workspace, copy your notes, or
send your files elsewhere. Enable it only after reviewing the local project and
paths shown in the installation preview.

Markdown remains source of truth even when Basic Memory is enabled.

## Why there are four folders

Repository has four user-facing roots:

```text
claude-code/
codex/
opencode/
Pi/
```

Claude Code owns canonical portable instructions, skills, hooks, policy, and
memory templates under `claude-code/core/`. Codex and OpenCode contain the
receipt-backed host adaptations. `Pi/` is a standalone Pi resource snapshot,
kept outside the three-host installer manifest. Automated tests stop drift in
the managed adapters.

## Safety and privacy

- Preview before every install, update, uninstall, or rollback.
- Existing personalized setups can use `--preserve-existing`; ShahinKit records
  collisions but never follows, replaces, or owns them.
- Explicit approval before any external or destructive action.
- No credentials, personal memory, course material, or machine-specific paths
  ship in this repository.
- No hidden telemetry or transcript capture.
- No automatic package installation, publication, commit, or push.
- Every file installed by the three-host managed installer is receipt-backed and
  rollbackable. Pi remains a separately reviewed manual copy.

## Advanced: run installer yourself

Read [INSTALL.md](INSTALL.md), then preview an explicit host and scope:

```sh
python3 claude-code/core/scripts/manage.py install --agent opencode --scope project --allow-development-checkout --preview
```

Review paths and copy the printed preview digest before applying. Restart the
selected host once after an approved install so it reloads configuration. This
is host activation—not a requirement to discard useful working context at every
milestone.
