# ShahinKit Pi adapter

This is the portable Pi-only slice of ShahinKit. It mirrors the reusable parts
of the active setup, not the full ShahinKit skill set and not a raw copy of
`~/.pi/agent`.

Last audited against the live setup: **2026-09-03**.

## Included

- `AGENTS.md` — portable Caveman, Ponytail, session-start, routing, worker safety, controller fan-out, HUD, and secret-handling rules.
- `agents/` — `mechanical`, `scout`, `worker`, `reviewer`, `plan-reviewer`, `researcher`, `planner`, and explicit-request-only `fable` profiles.
- `extensions/subagent/` — isolated single, parallel, chain, and background dispatch. Remote execution is opt-in and allowlist-only.
- `extensions/fable-mode.ts` — injects `FABLE-MODE.md` for controller-tier sessions.
- `extensions/pi-bg-notify.ts` plus `bin/pi-bg` — detached worktree-isolated write jobs with completion follow-ups.
- `extensions/hud.ts` — model/project state, context and subscription gauges, tool tally, elapsed time, and running-subagent rows; `/hud` toggles it.
- `extensions/image-guard.ts` — repairs or drops malformed image attachments before the request is sent, so one bad paste cannot wedge a session with `codec error: the image data you provided does not represent a valid image` on every turn.
- `extensions/fast-mode.ts`, `abliteration.ts`, and `double-escape-clear.ts` — optional provider speed mode, environment-keyed provider, and double-Escape clearing.
- `themes/` — `claude-mix`, `dark-hi`, `ember`, and `lagoon`.
- `tests/` — portable HUD, terminal-sanitization, image-guard, `pi-bg`, remote-map, and project-trust checks.
- `bin/luna` — one-shot Luna scout wrapper with private prompt-file handling.
- `packages.example.json` — pinned examples of four separately installed, compatible Pi packages; nothing is installed automatically.
- `prompts/` — `/implement`, `/implement-and-review`, and `/scout-and-plan`.
- `skills/` — the six portable Pi skills: `delegation-routing`, `plan`, `read`, `session-handoff`, `ship`, and `wrap-up`.
- `FABLE-MODE.md` — controller-tier read-fan-out doctrine.
- `AUDIT-2026-09-03.md` — exact inventory, exclusions, fixes, and verification evidence for this refresh.

Symlinked source skills are materialized as regular files.

## Deliberately excluded

The audit found additional live files that are not safe portable defaults:

- credentials, `auth.json`, sessions, caches, stores, logs, trust state, backups, sync conflicts, weather/runtime state, and personal memory;
- active `settings.json`, `models.json`, and `mcp.json` — they contain personal defaults, local paths, private endpoints, or OAuth configuration;
- `node_modules/` and local edits inside installed auth packages;
- institution-specific network proxying, local transcript/status relays, clipboard processing, and third-party conversation-compaction extensions;
- private-hardware/network model profiles, runtime snapshots, benchmark outputs, and machine-specific local-model documentation;
- the live deep-research profile/skill, which automates a GUI browser and violates the portable worker rule that subagents never control the screen;
- retired extensions, `.orig-*` files, generated evaluation results, and the
  generated RTK adapter (excluded until its redistribution provenance and a
  non-argv command-input contract are documented).

These exclusions preserve functionality that is portable without publishing
credentials, private infrastructure, user data, or host-specific automation.

## Install safely

Do not blindly overlay this adapter onto a personalized `~/.pi/agent`: that can
replace instructions, prompts, extensions, or skills. Keep credentials,
settings, sessions, and other user-owned state in place. The safest evaluation
is a separate Pi config directory:

```sh
mkdir -p ~/.pi/shahinkit-pi
cp -R Pi/. ~/.pi/shahinkit-pi/
PI_CODING_AGENT_DIR="$HOME/.pi/shahinkit-pi" pi
```

To merge resources into `~/.pi/agent`, back it up, review `diff -ru` first, and
copy only explicitly approved files. Restart Pi or run `/reload` after an
approved extension change.

### Add only the Abliteration.ai provider

Nothing here is installed for you, so a copy of this repository alone leaves
`/login` with no Abliteration.ai entry. Pi discovers providers from extensions
in its own config directory, so the file has to be placed there:

```sh
cp Pi/extensions/abliteration.ts ~/.pi/agent/extensions/abliteration.ts
```

Extensions load once at startup. Restart Pi, or run `/reload` in a running
session. `Abliteration.ai` then appears in `/login` as an API-key provider;
select it and paste the key, which Pi stores as a credential. Setting
`ABLITERATION_API_KEY` in the environment before launch works instead of
`/login`, and the extension's static model metadata keeps the provider listed
even when neither is present yet. Models are `abliteration-ai/abliterated-model`
and `abliteration-ai/abliterated-model-large`.

Optional: add `"abliteration-ai/*"` to `enabledModels` in `settings.json` to put
these models in the Ctrl+P cycle. That setting only affects cycling, not
availability.

The user-level `luna` and `pi-bg` helpers target POSIX hosts and require Bash,
Python 3, and the `pi` executable; `pi-bg` also uses Git and `jq`, with OpenSSH
required only for configured remote execution.

`packages.example.json` is a settings fragment, not an installer. Review each
entry and use Pi’s normal `pi install npm:<package>@<version>` flow only for
packages you choose; Pi then records them in the active `settings.json`.
Capabilities matter: `pi-mcp-adapter` executes configured MCP tools and may open
OAuth browser flows; `pi-claude-auth` reads Claude Code OAuth credentials and
writes Pi auth state; the two theme packages change presentation. The active
`pi-agent-goal` version is intentionally omitted because its declared Pi peer
range ends before the audited Pi version.

## Install for one project

Copy resources into project-local `.pi/` directories and merge the portable
instructions into the project-root `AGENTS.md`:

```sh
mkdir -p .pi/{agents,extensions,prompts,skills,themes}
# Review and merge Pi/AGENTS.md into ./AGENTS.md; Pi does not load .pi/AGENTS.md.
cp -R Pi/agents/. .pi/agents/
cp -R Pi/extensions/. .pi/extensions/
cp -R Pi/prompts/. .pi/prompts/
cp -R Pi/skills/. .pi/skills/
cp -R Pi/themes/. .pi/themes/
cp Pi/FABLE-MODE.md .pi/FABLE-MODE.md
```

Project-local profiles are intentionally not in the subagent tool’s default
user scope. Calls must set `agentScope: "project"` (or `"both"`); the bundled
workflow prompts remind the controller. Fast Mode is added to child processes
only when it exists in the active user config, so a project-only install still
runs without it. `bin/luna` and `bin/pi-bg` are user-level helpers and are not
installed by this project-local recipe.

Project-local resources require Pi project trust. Extensions execute with the
permissions of the Pi process; review them before approving trust.

## Remote subagents

Remote routing is disabled until all three variables are set:

```sh
export PI_REMOTE_SUBAGENT_HOST='build-host'
export PI_REMOTE_SUBAGENT_HOME='/home/worker'
export PI_REMOTE_SUBAGENT_MAP="$HOME/project=/home/worker/project;$HOME/other=/home/worker/other"
```

The remote host must have the corresponding Pi config path and
`extensions/fast-mode.ts`; preflight rejects a route missing either the mapped
working directory or extension. Only listed roots map remotely. The `subagent`
extension falls back locally and writes a private, 1 MiB-rotated receipt under
the active config’s `logs/remote-subagent-build.log` when configured routing is
disabled, unmapped, or unreachable. Default unconfigured local operation is not
logged. `pi-bg` stays local
when remote routing is unconfigured, but fails loudly for an unmapped or
unreachable configured route; use `--local` deliberately. Set
`PI_REMOTE_SUBAGENTS=0` or create `remote-subagents-off` in the active config for
the kill switch.

## Verification

Run from the repository root:

```sh
node Pi/tests/hud-layout.test.mjs
node Pi/tests/hud-quota.test.mjs
node Pi/tests/sanitize.test.mjs
Pi/tests/luna-smoke.sh
Pi/tests/pi-bg-smoke.sh
node Pi/tests/subagent-remote.test.mjs
node Pi/tests/subagent-trust.test.mjs
python3 claude-code/core/scripts/build_catalog.py --check
python3 claude-code/core/scripts/build_manifest.py --check
python3 -m pytest -q claude-code/core/tests
```

Set `PI_PACKAGE_ROOT` only when Pi is not installed under the global npm root.

## Notes

- `extensions/fast-mode.ts` stores its toggle in Pi runtime state, defaults off,
  and enables higher-usage priority requests only after `/fast on`.
- HUD weather egress is off by default. Set `PI_HUD_WEATHER=1` to permit a
  once-per-session refresh from `wttr.in`; cached text remains local.
- `pi-bg` applies private permissions locally and remotely, but retains task
  text, prompts, stderr, and message/tool JSONL until cleanup. Plain
  `pi-bg clean [id]` refuses running jobs and uncollected worktrees;
  `--force` deliberately discards completed uncollected work. Task and system
  prompts are read from stdin or `--task-file` and passed through private files,
  never task-bearing process arguments; job status validates process identity,
  and `kill` terminates the local process tree.
- `extensions/abliteration.ts` requires `ABLITERATION_API_KEY`.
- `researcher` expects a separately installed `web` command on `PATH` with the
  documented `search`/`get` interface and credentials managed outside the repository.
- Fable is never automatic; its profile requires explicit user request and provider availability.
- Provider credentials, model defaults, keybindings, private MCP servers, and machine-specific network policy remain user-owned.
