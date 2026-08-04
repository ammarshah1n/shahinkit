# B0 Provenance and Host Contract Baseline

Verified 2026-07-14. This record contains public release metadata and
fixture contracts only. It contains no source payload, local path, account
state, credential, transcript, or secret.

## ShahinKit release provenance

| Field | Locked value |
|---|---|
| Canonical GitHub owner/repository | `ammarshah1n/shahinkit` |
| Canonical Git URL | `https://github.com/ammarshah1n/shahinkit.git` |
| Public release requirement | Annotated signed tag; immutable release manifest tree and per-file SHA-256 digests; canonical origin equality |
| Maintainer signing-key fingerprint | `UNSET` |
| Public-release status | Blocked until release owner documents fingerprint and creates verifiable annotated tag |
| Development checkout | Requires explicit `--allow-development-checkout`; never qualifies public acceptance |

No tag or signing fingerprint was available in target history at this check.
Future installer code must fail closed for public acceptance while this value
is unset.

## B0 host compatibility pins

Version markers are ShahinKit installer inputs. They are not claimed to be
host-provided environment variables. The installer obtains a host version from
the documented `--version` command, then supplies the normalized value to its
marker evaluation.

| Host | Official release observed | B0 accepted range | Required marker | Release URL | Config-contract URL |
|---|---:|---|---|---|---|
| Claude Code | `2.1.209` | `>=2.1.209 <2.2.0` | `CLAUDE_CODE_VERSION` | `https://github.com/anthropics/claude-code/releases/tag/v2.1.209` | `https://code.claude.com/docs/en/settings` |
| OpenCode | `1.18.0` | `>=1.18.0 <1.19.0` | `OPENCODE_VERSION` | `https://github.com/anomalyco/opencode/releases/tag/v1.18.0` | `https://opencode.ai/docs/config/` and `https://opencode.ai/config.json` |
| Codex | `0.145.0` | `>=0.145.0 <0.146.0` | `CODEX_VERSION` | `https://github.com/openai/codex/releases/tag/rust-v0.145.0` | `https://developers.openai.com/codex/config-schema.json`, `https://github.com/openai/codex/blob/main/codex-rs/core/src/config/schema.md`, and `https://github.com/openai/codex/blob/main/codex-rs/core/config.schema.json` |

Claude Code and OpenCode publish schema identifiers but no independent schema
version, so their fixtures use `none-published` plus host parsing. Codex
publishes a Draft-07 JSON Schema titled `ConfigToml`; the pinned source artifact
is the validation evidence. Codex auto-detection uses executable version,
selected real config path, TOML parse, and documented contract only. It never
uses schema metadata or a root `$schema` key, which the Codex schema rejects.
A host template needing an unavailable capability stops adapter authoring.

## Verified official contracts

| Host | Verified contract used by later batches | Evidence URL |
|---|---|---|
| Claude Code | User and project settings use `settings.json`; project config is trust-gated; hooks and plugins are host capabilities, not hard-policy enforcement. | `https://code.claude.com/docs/en/settings` |
| OpenCode | `opencode.json` and `opencode.jsonc` are documented config names; `https://opencode.ai/config.json` is the documented runtime schema; commands, skills, and plugins are supported configuration surfaces. | `https://opencode.ai/docs/config/` and `https://opencode.ai/config.json` |
| Codex | User config is `config.toml`; trusted projects can load `.codex/config.toml`; canonical skills are `~/.agents/skills` for user scope and `.agents/skills` for project scope; `.codex/skills` is deprecated compatibility only. Native hooks load from user or project `hooks.json`. Config validates against Draft-07 `ConfigToml`; project config must not set user-global provider, approval, sandbox, network, trust, credential, notification, or telemetry controls. | `https://github.com/openai/codex/blob/main/codex-rs/core-skills/src/loader.rs`, `https://github.com/openai/codex/blob/main/codex-rs/hooks/src/engine/discovery.rs`, `https://developers.openai.com/codex/config-file/config-reference/`, and `https://developers.openai.com/codex/config-schema.json` |

## Sources and verification method

- Claude Code: `https://github.com/anthropics/claude-code/releases/tag/v2.1.209` and `https://code.claude.com/docs/en/settings`.
- OpenCode: `https://github.com/anomalyco/opencode/releases/tag/v1.18.0`, `https://opencode.ai/docs/config/`, and `https://opencode.ai/config.json`.
- Codex: `https://github.com/openai/codex/releases/tag/rust-v0.145.0`, `https://github.com/openai/codex/blob/main/codex-rs/core-skills/src/loader.rs`, `https://github.com/openai/codex/blob/main/codex-rs/hooks/src/engine/discovery.rs`, `https://developers.openai.com/codex/config-file/config-reference/`, and `https://developers.openai.com/codex/config-schema.json`.
- Canonical target remote checked with `git ls-remote --get-url origin`.

Official source URLs are evidence references, not installation inputs. No
installer may fetch from them at runtime.
