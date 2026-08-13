# ShahinKit Pi adapter

This is the Pi-only slice of ShahinKit. It copies the resources currently
loaded by the Pi setup; it does **not** mirror the full ShahinKit skill set.
Missing skills are intentional.

## Included

- `AGENTS.md` — portable Caveman, Ponytail, session-start, and tool-routing rules.
- `agents/` — `planner`, `reviewer`, `scout`, and `worker` profiles.
- `extensions/` — Abliteration provider, Codex Fast mode, and the subagent tool.
- `prompts/` — `/implement`, `/implement-and-review`, and `/scout-and-plan`.
- `skills/` — only the six skills present in the Pi setup:
  `delegation-routing`, `plan`, `read`, `session-handoff`, `ship`, and `wrap-up`.

Symlinked source skills were materialized as regular files. This folder contains
no credentials, auth files, sessions, caches, package installs, or personal
memory.

## Install safely

Do not blindly overlay this adapter onto an existing personalized
`~/.pi/agent`: that can replace your instructions, prompts, extensions, or
skills. Keep credentials, settings, sessions, and other user-owned state in
place. The safest install is a separate Pi config directory:

```sh
mkdir -p ~/.pi/shahinkit-pi
cp -R Pi/. ~/.pi/shahinkit-pi/
PI_CODING_AGENT_DIR="$HOME/.pi/shahinkit-pi" pi
```

To merge resources into `~/.pi/agent`, back it up, review `diff -ru` first, and
copy only the files you explicitly approve. Restart Pi or run `/reload` after
an approved change.

## Install for one project

Copy the resources into the project's `.pi/` directories and merge the
instructions into the project-root `AGENTS.md`:

```sh
mkdir -p .pi/{agents,extensions,prompts,skills}
# Review and merge Pi/AGENTS.md into ./AGENTS.md; Pi does not load .pi/AGENTS.md as context.
cp -R Pi/agents/. .pi/agents/
cp -R Pi/extensions/. .pi/extensions/
cp -R Pi/prompts/. .pi/prompts/
cp -R Pi/skills/. .pi/skills/
```

Project-local resources require Pi project trust. Review them before approving
trust; extensions execute with the permissions of the Pi process.

## Notes

- `extensions/fast-mode.ts` adds `/fast`; it stores its toggle in Pi's normal
  local runtime state, not in this repository.
- `extensions/abliteration.ts` is optional and uses `ABLITERATION_API_KEY`.
- `extensions/subagent/` requires the `pi` executable and the profiles in
  `agents/`.
- Provider credentials, model defaults, package settings, and keybindings stay
  user-owned and are intentionally not included here.
