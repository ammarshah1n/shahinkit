# Desktop Extension Notes

Claude desktop workflows vary by installation, so ShahinKit keeps this adapter as guidance instead of a live config patch.

## MCP Surfaces

Recommended optional connectors:

- Basic Memory for local project memory.
- Claude Memory for Claude-native recall.
- Obsidian or filesystem tools for vault reads and writes.

## Memory Routing

Use separate corpora or projects for:

- `dev`
- `school-university`
- `client`

Never mix school, development, and client state in one memory route unless the user explicitly chooses a combined project.

## Handoff Files

Prefer repository-local handoff files over desktop-only chat memory:

- `NEXT.md`
- `HANDOFF.md`
- `PARKED.md`
- `SESSION_LOG.md`
- `BUILD_STATE.md`

## Indexing

Before indexing or embedding:

1. Inventory the proposed files.
2. Show the exact file list and destination corpus.
3. Apply `shared/privacy/PRIVATE_DATA_EXCLUSIONS.md`.
4. Record approval in `shared/rag-indexing/OPT_IN_CONSENT.md`.
5. Keep revoke and rebuild instructions with the consent record.
