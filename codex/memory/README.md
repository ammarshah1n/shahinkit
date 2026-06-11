# Memory Setup

Use Obsidian as the editor for the memory vault. It is the most compatible option because it stores notes as normal local Markdown files that agents, scripts, Git, and basic-memory can all read.

Download Obsidian: <https://obsidian.md/download>

## Create A Local Vault

```bash
mkdir -p "$HOME/Documents/Agent-Memory-Vault/Working-Context"
mkdir -p "$HOME/Documents/Agent-Memory-Vault/Handoffs"
mkdir -p "$HOME/Documents/Agent-Memory-Vault/Notes"
cp codex/memory/templates/PROJECT_STATE.md "$HOME/Documents/Agent-Memory-Vault/Working-Context/PROJECT_STATE.md"
cp codex/memory/templates/NEXT.md "$HOME/Documents/Agent-Memory-Vault/Working-Context/NEXT.md"
```

Open `~/Documents/Agent-Memory-Vault` in Obsidian.

## Register basic-memory

```bash
python3 -m pip install --user basic-memory
basic-memory project add agent-memory "$HOME/Documents/Agent-Memory-Vault" --default
basic-memory status --project agent-memory
```

Start the MCP server for Codex:

```bash
basic-memory mcp --transport streamable-http --host 127.0.0.1 --port 8000 --path /mcp --project agent-memory
```

Then merge `codex/config/config.patch.example.toml` into the local Codex config.

## Agent Rules

- Read memory at `prime`.
- Update `PROJECT_STATE.md` and `NEXT.md` at `wrap-up`.
- Write one handoff per meaningful session in `Handoffs/`.
- Store course-specific content in course folders or course RAG indexes, not in global memory unless the user asks.
- Do not publish or sync the vault unless the user explicitly asks.
