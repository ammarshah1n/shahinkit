# MCP Templates

Templates are reviewable source files, not active host configuration. Replace
only angle-bracket placeholders in a local copy. Never commit replacement
values, secret files, local paths, or generated host configuration.

## Basic Memory v0.22.1

`basic-memory/` defines only local stdio launchers for a preinstalled,
verified Basic Memory `0.22.1` executable. Before copying a launcher, run
`basic-memory --version` and require exact `0.22.1`; do not use `uvx`, package
bootstrap, or a shell wrapper. Each launcher invokes `basic-memory mcp
--transport stdio --project <LOCAL_PROJECT_NAME>`.

Copy `local-config.example.json` to
`<LOCAL_BASIC_MEMORY_CONFIG_DIR>/config.json` after replacing placeholders.
The supported `BASIC_MEMORY_CONFIG_DIR` isolates that configuration. The
config registers exactly one local project, selects it as default, constrains
projects to `<LOCAL_PROJECT_ROOT>`, disables automatic updates, disables
Logfire instrumentation and export, and opts out of cloud promotions. Launcher
environment binds the same config directory, project, project root, and
off-settings. No cloud host, cloud API key, cloud token, endpoint, or remote
transport is supplied.

Copy one host fragment into that host's documented MCP configuration, then
restart host and confirm Basic Memory tools appear. The fragments are:

- `basic-memory/claude-code.mcp.json`
- `basic-memory/opencode.mcp.json`
- `basic-memory/codex.mcp.toml`

## Optional examples

`optional/` contains Context7, Timed, research, and development-scope examples.
All are disabled. They demonstrate environment-variable and secret-file
references only; no credential, endpoint, or filesystem location is shipped.
Keep optional examples disabled until user explicitly reviews, configures, and
enables one in host-supported syntax.

`dev-scope` remains local stdio only. It is read-only and must use an explicit
operator-owned configuration file. It never receives a root path through tool
input. See `claude-code/core/integrations/dev-scope/README.md` for bounds and hostile-root
limits.

No template fetches packages, runs `uvx`, runs `npx -y`, invokes a shell, or
enables remote installation. A host restart is required after any host
configuration change.
