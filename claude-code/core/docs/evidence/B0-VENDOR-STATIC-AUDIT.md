# B0 Vendor Static-Audit Baseline

Verified 2026-07-14 against temporary, detached, public upstream checkouts.
No upstream file was copied into ShahinKit. No vendor tests were run.

## Locked snapshot identity

| Vendor | Repository | Tag | Commit | Tree | License SHA-256 |
|---|---|---|---|---|---|
| Ponytail | `https://github.com/DietrichGebert/ponytail.git` | `v4.8.4` | `bc9ee949d5f439e8b9f3bb92c6d6d3d1e6ebd324` | `2b3486c779084a0442ac530affd85fb864499827` | `fb1bc6909ac3ef82d5c22106e32ef682b0cff66788fa915fb9b53b15c9d2f3ab` |
| Caveman | `https://github.com/JuliusBrussee/caveman.git` | `v1.9.1` | `0d95a81d35a9f2d123a5e9430d1cfc43d55f1bb0` | `867418a8efea2c92b3885b8efd99d73d7c58af11` | `5eb826cd03151bcc7cce3f80d40e87733237fedfc6c36d6908aca5fd650a0bdb` |

Both pinned commits resolve from their declared tags. License texts identify
MIT. Per-file digests and complete lock files remain B2P work; no vendor
payload is present in this batch.

## Static-audit rules and findings

Audit ran before any vendor test. Rules apply to tracked source; root-level
documentation matches are recorded separately and never treated as executable
approval.

| Rule | Matched construct | Result |
|---|---|---|
| `A1` | `curl` or `wget` bootstrap piped to a shell | Reject selected asset |
| `A2` | `npx -y` or other package-fetch execution | Reject selected asset |
| `A3` | installer or package lifecycle behavior | Reject selected asset |
| `A4` | ambient environment read | Reject selected asset unless B2P proves a narrow, non-secret replacement |
| `A5` | arbitrary process spawn or shell execution | Reject selected asset |
| `A6` | direct network primitive | Reject selected asset |
| `D1` | documentation mentions an `A1`–`A6` construct | Do not execute; keep only after B2P wording review |

| Vendor | Pinned-tree relative path(s) | Matched rule(s) | Result |
|---|---|---|---|
| Ponytail | `.opencode/plugins/ponytail.mjs`, `hooks/ponytail-config.js`, `hooks/ponytail-runtime.js` | `A4` | Not eligible for wholesale vendoring. |
| Ponytail | `scripts/publish-openclaw-skills.js` | `A5` | Not eligible for wholesale vendoring. |
| Caveman | `install.sh`, `install.ps1` | `A2`, `A3` | Not eligible for wholesale vendoring. |
| Caveman | `bin/install.js` | `A1`, `A2`, `A3`, `A4`, `A5`, `A6` | Not eligible for wholesale vendoring. |
| Caveman | `bin/lib/openclaw.js`, `bin/lib/settings.js`, `src/hooks/cavecrew-model-overrides.js`, `src/hooks/caveman-activate.js`, `src/hooks/caveman-config.js`, `src/hooks/caveman-stats.js`, `src/hooks/install.ps1`, `src/hooks/install.sh`, `src/hooks/uninstall.ps1`, `src/hooks/uninstall.sh`, `src/plugins/opencode/plugin.js`, `src/tools/caveman-init.js` | `A4` | Not eligible for wholesale vendoring. |
| Caveman | `src/hooks/caveman-mode-tracker.js`, `src/mcp-servers/caveman-shrink/index.js`, `src/mcp-servers/caveman-shrink/spawn-options.js` | `A4`, `A5` | Not eligible for wholesale vendoring. |
| Caveman | `CLAUDE.md`, `INSTALL.md`, `SECURITY.md`, `src/hooks/README.md` | `D1` | Review wording only; no executable artifact may be selected. |

This is an expected rejection of full upstream payload, not permission to
weaken safeguards. B2P may select only reconciled, audited portable skill
assets. It must rerun static audit on selected files, record every retained
file digest in `LOCK.json`, and run tests only from that locked local selection
inside a network-denied sandbox. Sandbox absence or audit failure blocks tests
and public acceptance; no unsandboxed fallback is permitted.

## B2P audit gate

Reject selected assets containing any of:

- remote installation or package fetch;
- `curl | shell`, `wget | shell`, or `npx -y` execution;
- install/postinstall behavior;
- ambient secret or broad environment reads;
- arbitrary subprocess launch;
- telemetry, transcript capture, raw event retention, or network calls.

Documented examples and tests may describe prohibited paths but never make
them executable. Later audit records must distinguish documentation text from
executable code and retain reviewed findings.
