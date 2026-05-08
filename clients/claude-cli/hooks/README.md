# Claude Code Hooks

Hook scripts live in `shared/hooks/`.

These scripts are inert until a user manually wires them into Claude Code settings.
Keep hook use opt-in because hooks can read project state or write handoff artifacts.

Recommended mapping:

| Claude Code Event | ShahinKit Script | Default Behavior |
|---|---|---|
| `SessionStart` | `shared/hooks/session-start.sh` | Read-only context check |
| `PreCompact` | `shared/hooks/precompact-snapshot.sh` | Dry-run unless enabled |
| `Stop` | `shared/hooks/post-session-export.sh` | Dry-run unless enabled |

Before enabling a write-capable hook, inspect the script and set the required `SHAHINKIT_*` environment variable explicitly.
