# RAG Indexing

Indexing is deny-by-default.

Use RAG only for approved, redacted sources with a clear route:

- `dev`
- `school-university`
- `client`

Minimum gate:

- Source is explicitly opted in.
- Private data exclusions are applied.
- Redaction checklist is complete.
- Public export allowlist permits the file.
- Raw transcripts, secrets, and private local paths are excluded.
