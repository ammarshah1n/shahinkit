# Local Memory

Use local Markdown as source of truth. Choose a local vault root, create its
working-context and handoff directories, then copy supplied templates into that
vault. Open chosen vault with any Markdown editor.

Basic Memory is optional local retrieval. Install it separately, register a
local project with chosen project name and vault root, then merge reviewed
`config/config.patch.example.toml`. Its Codex template launches preinstalled
`basic-memory` using stdio; it does not configure cloud endpoints or keys.

## Rules

- Read relevant Markdown memory during `prime`.
- Update `PROJECT_STATE.md` and `NEXT.md` during meaningful `wrap-up`.
- Store course material in course folders or local course-RAG indexes unless user requests otherwise.
- Never sync, publish, upload, or capture raw transcripts without explicit user approval.
