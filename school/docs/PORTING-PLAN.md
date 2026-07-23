# ShahinKit Portable Porting Plan

## Goal anchor

Port sanitized, portable behavior from read-only `<DEV_SCOPE_SOURCE>`, `<HANDOVER_KIT_SOURCE>`, and live `<CLAUDE_HOME>`, `<OPENCODE_HOME>`, `<CODEX_HOME>` evidence into `<SHAHINKIT_REPO>`. Sources stay untouched. No secrets, private memory, transcripts, personal paths, symlinks, moving remote execution, or account-specific payload.

State-source labels resolve only in local execution environment. They never enter shipped files, receipts, backups, manifests, fixtures, generated copies, or logs.

## Locked precedence and boundaries

1. User-request decisions and this plan.
2. `<HANDOVER_KIT_SOURCE>/portable` policy wins every policy conflict.
3. `<SHAHINKIT_REPO>` target wins only compatibility and layout constraints.
4. Current official host/tool documentation controls supported syntax and capability claims.
5. Live `<CLAUDE_HOME>`, `<OPENCODE_HOME>`, and `<CODEX_HOME>` configurations are behavioral evidence only, never copied payload.
6. `<DEV_SCOPE_SOURCE>` is read-only optional-integration evidence only.

No source body enters port merely because present. Host permission/trust is security boundary. Hooks/plugins are advisory capability mechanisms, never claimed hard-policy enforcement.

## Supply chain and origin

- Natural-language installation names host explicitly: `--agent claude-code`, `--agent opencode`, or `--agent codex`; instructions never depend on auto-detection. Preview prints canonical GitHub owner/repository, checked-out `HEAD`, annotated release tag, immutable release-manifest SHA-256 tree digest, and immutable per-file SHA-256 digests before apply.
- Public acceptance requires canonical GitHub owner/repository equality, immutable release manifest matching checked-out tree and every tracked release file, and `git verify-tag <tag>` success for annotated tag signed by documented maintainer signing-key fingerprint. Any unavailable or failed check stops installer. Development checkout requires explicit `--allow-development-checkout`; provenance is development and never qualifies public acceptance.
- No remote install, `curl | shell`, moving branch, `npx -y`, package fetch, install/postinstall script, secret read, or arbitrary subprocess.
- Before public publication, release owner performs human release action: verify origin, signature/tag, commit, tree digest, licenses, static audit, and release notes; record approval in release metadata. This is not local implementation blocker.
- `school/third_party/ponytail/LOCK.json` and `school/third_party/caveman/LOCK.json` contain repository URL, tag, commit, tree digest, per-file digest, license text/digest, vendoring date, and static-audit result.
- Ponytail lock: MIT, `v4.8.4`, `bc9ee949d5f439e8b9f3bb92c6d6d3d1e6ebd324`. Caveman lock: MIT, `v1.9.1`, `0d95a81d35a9f2d123a5e9430d1cfc43d55f1bb0`.
- Vendored tests run only after static audit, from locked local files, inside isolated network-denied sandbox. If sandbox unavailable, tests skip with unavailable result and verification/public acceptance fails closed; never run unsandboxed fallback, installer/postinstall, or fetch behavior.

## Install mapping, detection, and fixtures

`--scope user|project` is required unless destination maps unambiguously. Natural-language commands always use `--agent claude-code`, `--agent opencode`, or `--agent codex`. `--agent auto` succeeds only when exactly one complete documented host-unique marker set below matches selected scope; zero or multiple matches fail closed with `--agent claude-code|opencode|codex` required. Auto-detection never selects by filename alone outside selected scope.

| Host | User scope mapping | Project scope mapping | Required signature | Fixture root |
|---|---|---|---|---|
| Claude Code | `<CLAUDE_HOME>/CLAUDE.md`, `<CLAUDE_HOME>/skills/`, `<CLAUDE_HOME>/commands/`, `<CLAUDE_HOME>/settings.json` managed blocks | `<DESTINATION>/CLAUDE.md`, `<DESTINATION>/.claude/skills/`, `<DESTINATION>/.claude/commands/`, `<DESTINATION>/.claude/settings.json` managed blocks | `CLAUDE_CODE_VERSION` semver satisfies B0-pinned Claude range; selected `settings.json` parses and validates B0-pinned official Claude settings schema ID/version | `school/tests/fixtures/hosts/claude-code/{user,project}` |
| OpenCode | `<OPENCODE_HOME>/AGENTS.md`, `<OPENCODE_HOME>/skills/`, `<OPENCODE_HOME>/commands/`, `<OPENCODE_HOME>/opencode.jsonc` managed blocks/plugins | `<DESTINATION>/AGENTS.md`, `<DESTINATION>/.opencode/skills/`, `<DESTINATION>/.opencode/commands/`, `<DESTINATION>/opencode.jsonc` managed blocks/plugins | `OPENCODE_VERSION` semver satisfies B0-pinned OpenCode range; selected `opencode.jsonc` parses and validates B0-pinned OpenCode schema ID/version | `school/tests/fixtures/hosts/opencode/{user,project}` |
| Codex | `<CODEX_HOME>/AGENTS.md`, `~/.agents/skills/`, `<CODEX_HOME>/config.toml` managed blocks | `<DESTINATION>/AGENTS.md`, `<DESTINATION>/.agents/skills/`, `<DESTINATION>/.codex/config.toml` managed blocks | `CODEX_VERSION` semver satisfies B0-pinned Codex range; selected real `config.toml` path parses and validates B0-pinned Draft-07 `ConfigToml` schema. Auto-detection uses executable, real config path, TOML parse, and documented contract; never schema URL or root `$schema`. | `school/tests/fixtures/hosts/codex/{user,project}` |

Claude Code and OpenCode auto marker sets require listed environment version plus validated config/schema marker; Codex requires executable version plus selected real config path, TOML parse, and documented contract. Codex schema metadata validates configuration only and never enters auto-detection. Partial sets do not match. Fixtures include zero-match, Claude-only, OpenCode-only, Codex-only, and every multi-match rejection case. `<DESTINATION>` is caller-supplied root. Fixture directories contain isolated config/signature templates, managed-block baselines, hostile symlink cases, and no real home/config data. B0 pins current official version ranges and schema IDs/versions; unsupported template capability stops adapter authoring, not silently substitutes behavior.

## Canonical ownership and roles

- `school/shared/` owns portable policy, skill bodies, memory templates, role schema, integration catalog, and render metadata.
- `claude-code/`, `opencode/`, and `codex/` own only verified host templates, commands, lifecycle assets, and generated renders. No symlinks.
- Handover portable policy supplies `CORE-RULES`, `TIER-POLICY`, `DELEGATION`, `ENFORCEMENT-SPECS`, and `EVAL-PROTOCOL`. Target layout may relocate them, never weaken them.
- `school/shared/models/roles.schema.json` drives actual Claude, OpenCode, and Codex templates. Defaults are exact: Claude controller=`opus`, research/implementation/review=`sonnet`, mechanical=`haiku`; OpenCode controller=`openai/gpt-5.6-sol`, research/implementation/review=`openai/gpt-5.6-terra`, mechanical=`openai/gpt-5.4-mini`; Codex controller=`gpt-5.6-sol`, research/implementation/review=`gpt-5.6-terra`, mechanical=`gpt-5.4-mini`. Fixtures assert exact rendered values in each host syntax.
- Every role default is user-overridable through documented per-role settings, but schema rejects missing resolved role values and any worker role inheritance from controller or another worker. Codex project template sets project role defaults only; never forces user-global model, approval, sandbox, network, trust, or credential configuration.

## Portable skills, lifecycle, and capability contract

Shared skills: `prime`, `memory`, `context-router`, `checkpoint`, `session-handoff`, `reflect`, `reflect-and-compound`, `wrap-up`, `miniwrap`, `correction-protocol`, `self-improve`, `delegation-routing`, `idea`, `plan`, `plans`, `mission`, `deep-idea`, `deep-plan`.

Fixture tests prove each skill's behavioral/capability contract, not only filename: memory/local source behavior; lifecycle ordering and bounded writes; idea/plan/plans/mission mode selection; controller/research/worker/reviewer/mechanical routing; excluded personal/domain/transcript/cloud behavior.

Generic prime, plan, dispatch, and verification safety-hook examples remain disabled. After preview, explicit `--apply`, and host trust confirmation, installer-managed Ponytail/Caveman lifecycle registrations are enabled by default. `--without-ponytail`, `--without-caveman`, and documented per-mode off states override defaults. Tests assert disabled generic examples and active managed registrations separately.

- Ponytail ports six approved portable skills, `full` default, override/off support.
- Caveman ports `caveman`, `caveman-commit`, `caveman-review`, and `caveman-help`; preserves Auto-Clarity and `full` default; excludes stats, compress, cavecrew, MCP shrink, and account-specific behavior.
- Third-party reconciliation occurs before shared rendering. Reconciliation records kept/dropped generic deltas from enhanced local evidence; shared and adapter renders consume only reconciled assets.
- Claude/OpenCode/Codex lifecycle capability claims are bound to B0 verified templates. Caveman static-context-only behavior is explicit where persistent lifecycle unsupported.
- Plugins/hooks use local state only when needed; no network, ambient secret reads, arbitrary subprocess, telemetry, transcript capture, or raw event persistence. Adapters scrub/minimize event payload before state use. Static audit and runtime negative fixtures prove prohibited network, environment-secret, subprocess, and payload-retention paths absent.

## Basic Memory and dev-scope contracts

Basic Memory is optional local-only: stdio transport; explicit local project/config placeholder; cloud endpoint/token absent; telemetry and auto-update disabled. Markdown remains source of truth. Network-denied fixture runs where harness supports it.

`school/integrations/dev-scope/` is optional, read-only stdio MCP using Node >=18, `@modelcontextprotocol/sdk ^1.29.0`, Zod `^3.25.0` or later, and `registerTool`.

- Roots are named, explicit, allowlisted locations. Inputs choose root ID and relative path only.
- Source walk allows only documented readable extensions and locations; applies query, depth, file-count, per-file byte, total-byte, match, output-byte, and time limits.
- Read/list/search redacts secret values and rejects secret names/sensitive stores. Literal bounded search only.
- Every path operation rejects empty, absolute, `.`/`..`, and malformed relative components; parent chain uses `lstat`/`realpath` containment; final component is opened no-follow; opened-object identity is rechecked against validated object. Source walks use `lstat`, no-follow, and containment.
- Residual hostile-root TOCTOU remains possible between checks absent OS isolation. Documentation requires OS sandbox or trusted root for hostile roots; code does not claim race-free protection.
- Git metadata uses resolved trusted git binary, sanitized environment, fixed read-only arguments, hooks disabled, pager disabled, external diff disabled, textconv disabled. No `.env`, `dotenv`, arbitrary command tool, `run_claude`, or root disclosure.

## Manager, manifest, receipt, backup, rollback

`school/scripts/manage.py` uses Python stdlib only. `.shahinkit-manifest.json` contains normalized relative owned paths, source/render digests, ownership, and adapter mappings only.

- Reject empty, absolute, `.`/`..`, non-normalized paths, and all symlink targets. Before every read/write/remove/backup operation, resolve destination containment and reject any symlinked destination ancestor; source walks use `lstat` no-follow plus containment.
- Install/update/uninstall/rollback use destination-local `.shahinkit-install-receipt.json`: relative owned paths/digests, selected features/modes, adapter/version, receipt ID, backup ID, origin/HEAD/tree digest, and scope. It contains no source labels, credentials, or absolute paths.
- Back up only managed files or delimited managed blocks, owner-only `0600`, keyed by receipt ID, with documented retention and restore behavior. Never back up sync-generated tracked repository copies; Git/canonical shared source is their rollback.
- `install` previews origin/provenance, host/scope, changed managed paths, active modes, trust requirement, fresh-session requirement, receipt/backup impact. `--apply` mutates only after trust confirmation.
- `update`, `uninstall`, and `rollback` require matching destination receipt, operate only on receipt+manifest ownership, prove idempotence, restore exact managed preimage, and never remove unowned content.

## Proposed tree

```text
shahinkit/
├── .shahinkit-manifest.json
├── .shahinkit-plan-state.md
├── INSTALL.md
├── school/docs/{PORTING-PLAN.md,integration-catalog.md}
├── school/scripts/manage.py
├── school/third_party/{ponytail,caveman}/{LICENSE,PROVENANCE.md,LOCK.json,skills/,school/tests/}
├── school/shared/{policies/,models/{roles.schema.json,README.md},context/,skills/,memory/,mcp/}
├── claude-code/{CLAUDE.md,commands/,config/,hooks/,plugins/,memory/,skills/}
├── opencode/{AGENTS.md,commands/,config/,hooks/,plugins/,memory/,skills/}
├── codex/{AGENTS.md,config/,hooks/,memory/,skills/}
├── school/integrations/dev-scope/{README.md,package.json,package-lock.json,config.example.json,index.js,test/}
└── school/tests/{test_manage.py,fixtures/hosts/{claude-code,opencode,codex}/{user,project}/}
```

`INSTALL.md` owns exact natural-language flow: canonical origin only; `--agent claude-code|opencode|codex`; preview; canonical GitHub owner/repository, release manifest, tag-signature, and maintainer-fingerprint verification; trust confirmation; `--apply`; host activation/fresh-session check; receipt location; update/uninstall/rollback commands; public-release versus development-checkout rule; failure/restore acceptance. `--agent auto` is documented only with strict marker-set rules. No URL interception or implied remote execution.

## Dependency graph and batches

```text
B0 evidence/syntax/static-audit ─> B1 policy/roles/manifest ─> B2P vendor reconcile ─> B2 shared render ─> B3 adapters
B0 ─> B4 hardened dev-scope ────────────────────────────────────────────────────────────────────────────────┤
B2+B3+B4 ─> B5 manager/receipt/backups ─> B6 isolated verification/review
```

| Batch | Lane | Work | Acceptance |
|---|---|---|---|
| B0 | LAUNCH SWARM | Sanitized inventory; official host syntax/capabilities; canonical GitHub owner/repository, maintainer fingerprint, version/schema-marker evidence; vendor static audit. | Evidence has no payload/private paths; unsupported capability documented; canonical release verification inputs and auto marker sets pinned; static audit precedes tests. |
| B1 | INLINE | Portable policy, role schema, immutable release manifest, normalized manifest, exact mapping fixtures. | Handover policy wins conflicts; target affects layout only; exact rendered role defaults, no inheritance, and zero/one/multiple auto fixtures pass. |
| B2P | LAUNCH SWARM | Vendor locked snapshots and Ponytail/Caveman reconciliation. | Repo/tag/commit/tree/file/license digests present; network-denied isolated tests or fail-closed unavailable result; reconciliation closed before render. |
| B2 | LAUNCH SWARM | Shared skills, memory, Basic Memory contract, catalog, `INSTALL.md`. | Capability fixtures cover complete skill set; JSON files each validate independently. |
| B3 | LAUNCH SWARM | Claude/OpenCode/Codex renders and lifecycle assets. | Generic examples disabled; managed Ponytail/Caveman registrations active after trust/apply; payload/security negative tests pass. |
| B4 | INLINE | Hardened dev-scope. | Allowlist, redaction, bounds, no-follow/identity checks, trusted-git controls, hostile-root residual documented. |
| B5 | INLINE | Manager, receipt, backups, install/update/uninstall/rollback. | Per-host/per-scope isolated smoke proves ownership, idempotence, restoration, containment, and no unowned writes. |
| B6 | LAUNCH SWARM | Full scans, drift, parse, vendor, host, network-denied, and independent review. | Every concrete finding adjudicated; observed checks green; no open fork. |

## Verification matrix

- Validate tracked JSON independently, NUL-safe, without output overwrite: `while IFS= read -r -d '' f; do python3 -m json.tool "$f" >/dev/null || exit 1; done < <(git ls-files -z -- '*.json')`.
- Scan all tracked content, not selected filenames, for personal-path patterns, secret patterns, transcripts, private memory, caches, and prohibited execution. Reviewed false-positive allowlist is explicit, minimal, path+reason bound, and itself reviewed.
- `sync --check` verifies generated drift. Static vendor audit precedes local vendor school/tests/rule-copy checks.
- Host fixture matrix runs `install`, `update`, `uninstall`, and `rollback` independently for every `{claude-code,opencode,codex} × {user,project}` fixture; asserts receipt ownership, default modes, opt-outs, idempotence, exact managed restoration, no unowned mutation, and no symlinked ancestor/target access. Auto fixtures assert zero marker sets reject, each single complete marker set selects only its host, and every multiple complete marker-set combination rejects.
- Parse current host templates; test exact role renders and no worker inheritance; assert generic examples disabled and installer-managed active registrations after preview/apply/trust; assert documented fresh-session behavior.
- Verify public release canonical GitHub owner/repository, immutable release-manifest tree/file SHA-256 digests, annotated `git verify-tag` result, and documented maintainer signing-key fingerprint. Any unavailable/failed verification stops installer and blocks public acceptance; development override is tested as non-qualifying.
- Basic Memory runs network-denied where supported. Vendored tests require network-denied sandbox; unavailable sandbox produces fail-closed verification, never unsandboxed execution. Dev-scope tests cover extension/location allowlists, secret redaction, limits, traversal, symlink, final-object identity, and hostile-root warning.
- `git diff --check`, tracked-content scan, `INSTALL.md` presence, receipt assertions, symlink containment, uninstall, rollback, Ponytail `4.8.4`, and Caveman `1.9.1` are mandatory final observations.

## Delete / merge and rollback

| Component | Action | Destination/reason |
|---|---|---|
| Duplicated generic skills and memory | Merge | `school/shared/`; adapters only render host mechanics. |
| Handover bindings/live configs | Do not copy | Placeholder policy and behavioral evidence only. |
| Generic safety hooks | Keep disabled examples | Advisory safety templates. |
| Managed Ponytail/Caveman lifecycle | Install default-on after trust/apply | Host adapter registration, receipt-owned. |
| Vendor portable assets | Pin/reconcile before render | `school/third_party/` then school/shared/adapter output. |
| Fable/domain/personal/transcript/cloud assets | Exclude | Privacy and scope boundary. |
| `.env`, `dotenv`, `node_modules`, `run_claude` | Exclude | Secret, portability, execution boundary. |
| `course-rag/` | Untouched | Out of scope. |

Rollback restores only receipt-owned managed blocks/files from owner-only backup. Sync-generated repository copies roll back through Git/canonical shared source, never destination backup. Retention expiry removes only backup data associated with receipt and never destination content.

## Spec-drift and acceptance

| Requirement | Resolution |
|---|---|
| Personal/source paths | Neutral labels only; source labels local-resolution-only. |
| Policy precedence | Handover policy wins policy; target only compatibility/layout; live configs evidence only. |
| Auto install | Natural-language explicit host flag; `auto` only one complete version+schema marker set, zero/multiple fail closed. |
| Supply chain | Canonical GitHub owner/repository, immutable SHA-256 release manifest, annotated-tag fingerprint verification, explicit non-qualifying development override. |
| Roles/lifecycle | Exact role defaults/renders, per-role overrides, no worker inheritance, capability fixtures. |
| Safety hooks/default modes | Generic examples disabled; managed modes enabled after trust/apply. |
| Vendor order | Reconcile before shared rendering. |
| Manager safety | Relative-only manifest, no-follow containment, destination receipt, owned backup/restore. |
| Dev scope/MCP | Local-only Basic Memory; bounded/redacted no-follow dev-scope; no hard-policy hook claim. |

Implementation accepted only after B6 independently observes all matrix checks green, all findings adjudicated, no open fork, no source/active-host mutation, and mandatory public-release verification satisfied when publishing. GO received 2026-07-14; implementation authorized under reviewed plan; no push/tag/release or destructive source changes authorized.
