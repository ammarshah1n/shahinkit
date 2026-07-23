# Memory render

Markdown is source of truth. ShahinKit manager renders five canonical templates
from `render-manifest.json`; it does not create a vault or write memory until a
user-directed skill needs a canonical file. Basic Memory is optional local
stdio retrieval. Use `config/mcp.basic-memory.example.json` only when the
`basic-memory` executable already exists and local placeholders are supplied.

Never export raw transcripts, course material, credentials, personal paths, or
memory automatically. Never sync or publish without explicit approval.
