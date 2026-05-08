# Claude Code Desktop Adapter

This folder documents how to use ShahinKit with desktop Claude workflows and MCP-backed memory tools.

Use this adapter when the user works from a desktop app but wants the same project shape as Claude Code or Codex:

- shared instructions;
- portable skills;
- opt-in hooks;
- Basic Memory or Claude Memory routing;
- Obsidian vault templates;
- durable handoff files.

## Setup Model

1. Render this adapter with `scripts/render-client-config.sh`.
2. Inspect the generated files.
3. Copy only the approved instructions, skills, and MCP notes into the desktop workflow.
4. Configure memory connectors manually.
5. Run `rag-consent` before embedding or indexing local files.

Do not paste private transcripts, credentials, or unredacted local paths into desktop memory.
