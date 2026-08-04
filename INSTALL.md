# Install ShahinKit

`claude-code/core/scripts/manage.py` is Python-stdlib-only. Mutating commands are preview by
default and require `--apply --preview-digest <SHA256>` from exact prior preview;
install and update also require `--trust-host`.
Trust remains host-controlled: manager never grants it.

## Canonical source and natural-language request

Canonical repository URL:

```text
https://github.com/ammarshah1n/shahinkit.git
```

Paste that exact URL into an install request. Example:

> Install ShahinKit from `https://github.com/ammarshah1n/shahinkit.git` for
> Claude Code in user scope. Preview only. Keep Ponytail and Caveman defaults.

Name host explicitly. Do not ask installer to infer host from a URL, filename,
or current branch. `--agent auto` is reserved for a future strict detector: it
will succeed only when exactly one complete documented host marker set exists
in selected scope; zero or multiple matches fail closed.

## Command contract

Choose immutable `<RELEASE_TAG>` and clone detached from that tag, never a
moving branch:

```sh
git clone https://github.com/ammarshah1n/shahinkit.git shahinkit
cd shahinkit
git checkout --detach <RELEASE_TAG>
git verify-tag <RELEASE_TAG>
```

Preview first. Host is explicit; scope is explicit:

```sh
python3 claude-code/core/scripts/manage.py install --agent claude-code --scope user --preview
python3 claude-code/core/scripts/manage.py install --agent opencode --scope project --destination <DESTINATION> --preview
python3 claude-code/core/scripts/manage.py install --agent codex --scope user --preview
```

For this unreleased development checkout, append
`--allow-development-checkout`; it is explicitly non-public and does not
replace release provenance verification.

Only after preview shows expected provenance, paths, modes, backup impact, and
trust requirement, copy its `preview-digest` and repeat same command with
`--apply --preview-digest` plus explicit host trust:

```sh
python3 claude-code/core/scripts/manage.py install --agent claude-code --scope user --apply --preview-digest <SHA256> --trust-host
```

Ponytail and Caveman default to `full` after preview, `--apply`, and explicit
host trust. Disable either during installation only when requested:

```sh
python3 claude-code/core/scripts/manage.py install --agent claude-code --scope user --preview --without-ponytail
python3 claude-code/core/scripts/manage.py install --agent claude-code --scope user --preview --without-caveman
```

Use `--preserve-existing` when installing beside an established host setup. It
leaves every unowned file, symlink, and conflicting config value untouched,
records those destinations as preserved rather than owned, and adds only
missing safe config tables/list entries. Preview labels each preserved path.

```sh
python3 claude-code/core/scripts/manage.py install --agent claude-code --scope user --preview --preserve-existing
```

Per-session opt-out remains `stop ponytail`, `stop caveman`, or `normal mode`.
The installer never auto-applies, invokes a shell pipe, fetches packages, or
selects a host implicitly.

## Scope mappings

| Host | User scope | Project scope |
|---|---|---|
| Claude Code | `<CLAUDE_HOME>/CLAUDE.md`, `skills/`, `settings.json` managed blocks; Course RAG `{{SHAHINKIT_DATA_DIR}}/course-rag` | `<DESTINATION>/CLAUDE.md`, `.claude/skills/`, `.claude/settings.json` managed blocks; Course RAG `{{SHAHINKIT_DATA_DIR}}/course-rag` |
| OpenCode | `<OPENCODE_HOME>/AGENTS.md`, `skills/`, `commands/`, `opencode.user.jsonc.example` managed merge, `plugins/portable-gates.features.mjs` | `<DESTINATION>/AGENTS.md`, `.opencode/skills/`, `.opencode/commands/`, `opencode.jsonc.example` managed merge, `.opencode/plugins/portable-gates.features.mjs` |
| Codex | `<CODEX_HOME>/AGENTS.md`, `$HOME/.agents/skills/`, `config.toml` managed blocks; Course RAG `{{SHAHINKIT_DATA_DIR}}/course-rag` | `<DESTINATION>/AGENTS.md`, `.agents/skills/`, `.codex/config.toml` managed blocks; Course RAG `{{SHAHINKIT_DATA_DIR}}/course-rag` |

`--scope user|project` is required. User roots are `~/.claude`,
`~/.config/opencode`, and `~/.codex`; project root is current directory.
`--destination <DESTINATION>` is intended for isolated testing and maps all
managed roots, including Codex `$HOME` assets, below that directory. Manager must reject
absolute or escaping manifest paths, symlinked ancestors, and unsupported host
configuration before mutation. Explicit `--preserve-existing` may skip a
symlinked destination without following or changing it; default behavior still
fails closed.

Receipts and backups address outputs as `root:<relative-path>` or
`home:<relative-path>`, never absolute paths. In isolated destinations, `root`
is `<DESTINATION>` and `home` is `<DESTINATION>/home`.

## Study vaults

`/study` works only inside user-selected existing Obsidian vault with real
`.obsidian` directory. It interviews user, previews direct subject folders plus
canonical `Study.md`, then requires explicit confirmation before writing. Kit
ships no course content, never copies content automatically, and does not
require Course-RAG.

Course-RAG runtime references are resolved under selected scope root, never an
arbitrary current working directory. Render all Basic Memory local values before
an enabled MCP configuration is installed:
config directory, project name, project path, and project root. OpenCode's
adjacent feature file defaults Ponytail and Caveman to `true`; render either to
`false` only when its matching install opt-out is selected.

Basic Memory is disabled in every generated host configuration by default, so
the host never starts an unreviewed MCP. Add `--with-basic-memory` only after
local Basic Memory is installed and reviewed; it renders local config directory,
project name, project path, and project root. Cloud mode is unsupported.

## Provenance and signature gate

Public-release install must stop unless all checks pass before `--apply`:

1. Canonical GitHub owner/repository equals `ammarshah1n/shahinkit`.
2. Checked-out `HEAD` matches immutable release manifest tree and per-file
   SHA-256 digests.
3. `<RELEASE_TAG>` is annotated and `git verify-tag <RELEASE_TAG>` succeeds.
4. Signing key fingerprint equals documented release maintainer fingerprint.
5. Preview identifies adapter, scope, changed managed paths, active modes,
   host-reload requirement, receipt, and backup effect.

Any unavailable or failed gate stops installation. A development checkout will
require explicit `--allow-development-checkout`; its provenance is
development-only and never qualifies as public-release acceptance.

## Apply, trust, and host activation

`--apply` may change only manifest-owned files or delimited managed blocks.
Preserved destinations are never claimed, replaced, removed, or followed.
Before mutation it must create an owner-only backup of only changed managed
content and write destination-local receipt
`<DESTINATION>/.shahinkit-install-receipt.json`. Receipt contains relative
owned paths and digests, selected host/scope/features/modes, adapter version,
preserved relative paths, receipt and backup IDs, and provenance digests. It contains no credentials,
source labels, or absolute paths.

After apply:

1. Restart selected host once so it reloads installed instructions, agents, and hooks.
2. Confirm installed host recognizes managed instructions and selected
   Ponytail/Caveman defaults.
3. Confirm Basic Memory remains optional; enable only reviewed local stdio
   template with a named project, `mode: local`, `workspace_id: null`,
   `BASIC_MEMORY_FORCE_LOCAL=true`, and `BASIC_MEMORY_EXPLICIT_ROUTING=true`.
4. Continue existing work normally after activation; milestones do not force
   session resets. Record failed activation as failed; do not claim install complete. Use
   receipt-backed rollback before retrying.

## Update, uninstall, and rollback

All operations require matching destination receipt and operate only on
receipt-plus-manifest ownership. Preview is mandatory before `--apply`; copy
the printed digest into each matching mutation:

```sh
python3 claude-code/core/scripts/manage.py update --agent claude-code --scope user --preview
python3 claude-code/core/scripts/manage.py update --agent claude-code --scope user --apply --preview-digest <SHA256> --trust-host
python3 claude-code/core/scripts/manage.py uninstall --agent claude-code --scope user --apply --preview-digest <SHA256>
python3 claude-code/core/scripts/manage.py rollback --receipt <RECEIPT_ID> --preview
python3 claude-code/core/scripts/manage.py rollback --receipt <RECEIPT_ID> --apply --preview-digest <SHA256>
```

After review, add `--apply` and `--trust-host` to update. Before
an update applies, rerun every fail-closed public-release gate: canonical
origin, release-manifest tree and file digests, annotated signed tag via `git
verify-tag <RELEASE_TAG>`, and documented signer fingerprint. Any unavailable
or failed gate stops the update. Rollback uses only receipt-owned backup data,
restores exact managed preimage, and never removes unowned content. Retention
expiry removes only backup data associated with receipt, never destination
files. If receipt or backup is missing, stop and restore manually from trusted
version control or documented backup; never guess ownership.

## Non-goals and safety

No remote install, URL interception, moving main branch, package fetch,
postinstall, cloud-memory setup, telemetry configuration, secret extraction,
or arbitrary subprocess is part of this contract. Optional Context7, Timed,
research, and dev-scope MCP examples stay disabled until user explicitly
enables reviewed host configuration.
