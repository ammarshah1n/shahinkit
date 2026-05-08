# Claude Mem Template

## Corpora

| Corpus | Path Template | Purpose |
|---|---|---|
| `dev` | `{{DEV_VAULT_PATH}}` | Development decisions, implementation notes, handoffs |
| `school-university` | `{{SCHOOL_VAULT_PATH}}` | Coursework notes, study planning, assessment state |
| `client` | `<client-approved-path>` | Approved client facts and deliverable state |

## Separation Rules

- Keep dev, school-university, and client corpora separate.
- Deny indexing by default; opt in specific files or folders only.
- Do not index raw transcripts, secrets, private local paths, or personal identifiers.
- Redact before indexing or exporting.
- Public exports must use an allowlist, not broad folder sync.
