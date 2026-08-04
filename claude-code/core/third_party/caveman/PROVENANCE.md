# Caveman provenance and reconciliation

## Locked upstream

- Repository: `https://github.com/JuliusBrussee/caveman.git`
- Tag: `v1.9.1`
- Commit: `0d95a81d35a9f2d123a5e9430d1cfc43d55f1bb0`
- Tree: `867418a8efea2c92b3885b8efd99d73d7c58af11`
- License: MIT; exact text in `LICENSE`

Upstream was statically audited before any test. No upstream executable,
installer, package lifecycle, network client, environment/config reader,
subprocess launcher, event persistence, cache, or state file is vendored.

## Selected portable scope

Selected upstream skill sources are `skills/caveman/SKILL.md`,
`skills/caveman-commit/SKILL.md`, `skills/caveman-review/SKILL.md`, and
`skills/caveman-help/SKILL.md`. Claude command/static-context assets, OpenCode
plugin/config resolver, and Codex static context are sanitized derived assets.
They use no network, subprocess, environment, filesystem, secret, or
event-persistence API. OpenCode retains only selected mode in memory until the
plugin process ends; it never persists message text or mode state.

`LOCK.json` records upstream and shipped-file SHA-256 values. It excludes its
own digest because a self-hash cannot be stable; every other shipped file is
locked and verified by `claude-code/core/tests/test_vendor.py`.

## Read-only OpenCode fork reconciliation

Evidence reviewed: local enhanced OpenCode plugin and `caveman` skill.

| Evidence | Decision | Reason |
|---|---|---|
| `skills/caveman/SKILL.md` rules for full default, Auto-Clarity, no tool narration, no invented abbreviations/arrows, language preservation | Retained through upstream v1.9.1 skill unchanged | Same generic-safe wording already exists in locked v1.9.1. No local-only delta. |
| Local README’s older abbreviation/arrow examples | Dropped | Contradicts locked v1.9.1 skill’s clarity rule. |
| Plugin quote unwrapping, event dispatch, per-turn transform behavior | Retained only as clean-room selected-mode handling | Required for next-turn reminders; stores only whitelisted mode in memory, never text or persistent state. |
| Plugin config lookup, flag read/write, XDG/home resolution, debug environment reads | Dropped | Environment, private config, filesystem state, and secret-adjacent ambient reads are excluded. |
| Static default-full prompt transform | Retained as clean-room `opencode/plugin.js` | Generic, host-native, no ambient reads or persistence. |

No generic-safe improvement unique to local fork remained after comparison.

## Derived changes

1. Core `caveman`, `caveman-commit`, and `caveman-review` skill text is copied
   from v1.9.1; target files normalize missing terminal newlines only.
2. `skills/caveman-help/SKILL.md` removes stats, compress, environment-variable,
   and user-config instructions; only four approved skills remain.
3. Claude lifecycle is static context plus command templates. No hook command or
   persistent mode tracker is shipped.
4. OpenCode uses a pure explicit-mode resolver and next-turn system transform.
   It keeps only selected mode in memory; no persistent runtime state exists.
5. Codex uses static `AGENTS.md` plus copied skill assets; upstream hook command
   execution is excluded.

## Static-audit result

Pass. Selected payload is declarative Markdown/JSON or pure ESM. Audit rejects
network primitives, package fetch/install lifecycle, environment/private-config
access, subprocess APIs, telemetry, raw-event retention, and persistent state.
