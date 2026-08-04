# Integration Catalog

Catalog describes portable contract only. `core` means required architecture; `optional` means disabled or unavailable until user enables it; `excluded` means never ported. No entry claims an unbuilt adapter asset exists.

| Type | Item | Class | Contract |
|---|---|---|---|
| Integration | Claude Code adapter | core | Host render target; later adapter work binds shared policies and resolved role models. |
| Integration | OpenCode adapter | core | Host render target; later adapter work binds shared policies and resolved role models. |
| Integration | Codex adapter | core | Host render target; later adapter work binds shared policies and resolved role models. |
| Integration | Local markdown memory | core | User-owned markdown remains source of truth; no cloud endpoint or account payload. |
| MCP | Basic Memory | optional | Local-only stdio configuration placeholder; user supplies local project/config. Cloud endpoint, token, telemetry, and auto-update excluded. |
| MCP | Development-scope MCP | optional | Future read-only local stdio integration with explicit roots, bounded reads, and redaction. |
| Hooks | Generic prime, plan, dispatch, verification examples | optional | Disabled advisory examples only; hooks never claim hard-policy enforcement. |
| Hooks | Managed Ponytail/Caveman lifecycle registrations | optional | Enabled only after preview, explicit apply, and host trust confirmation; no network, secret reads, telemetry, transcript capture, or arbitrary subprocess. |
| Integration | Remote installation, moving branches, package fetch, install hooks | excluded | No remote execution, `curl | shell`, `npx -y`, postinstall, or arbitrary subprocess. |
| Integration | Cloud memory, personal/domain data, transcripts, private paths | excluded | No account-specific payload, credentials, private memory, or personal paths. |
| Integration | Email, calendar, booking, payment, scheduling action | excluded | Kit observes and recommends; it does not act on external systems. |
