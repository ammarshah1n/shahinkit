# Memory Routing

Route memory by context. If the route is unclear, do not write.

| Route | Use For | Exclude |
|---|---|---|
| `dev` | Code decisions, build state, project handoffs | School work, client-private details, raw transcripts |
| `school-university` | Coursework planning, study notes, assessment state | Client work, secrets, private conversations |
| `client` | Client deliverables, public decisions, approved project facts | Personal data, school work, internal transcripts |

Rules:

- Deny writes by default.
- Store only the minimum useful summary.
- Use relative paths, public project names, and stable identifiers.
- Do not store secrets, private local paths, raw transcripts, or personal identifiers.
