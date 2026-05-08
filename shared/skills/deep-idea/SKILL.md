---
name: deep-idea
description: Turn an early idea into research, interview notes, PRD, build context, and a deep-plan-ready project package before code starts.
---

# Deep Idea

Use this for greenfield products, apps, workflows, school systems, personal systems, and immature repos that need discovery before implementation planning.

`new-idea` is the short public alias. `deep-idea` is the full discovery workflow name.

## Workflow

1. Capture the idea, target users, desired outcome, constraints, and assumptions.
2. Write `docs/research/IDEA_BRIEF.md`.
3. Ask concise interview questions only for unknowns that research or local files cannot answer.
4. Write `docs/research/INTERVIEW.md`.
5. Run research lanes relevant to the idea:
   - user needs;
   - existing alternatives;
   - technical options;
   - data and privacy constraints;
   - risks;
   - implementation shape.
6. Write `docs/research/RESEARCH_BRIEF.md`.
7. Write `docs/PRD.md`.
8. Write or update `docs/BUILD_CONTEXT.md`.
9. Stop for review before implementation planning.

## Rules

- Do not write implementation source files inside `deep-idea`.
- Mark unresolved decisions instead of guessing.
- Keep the research practical and source-grounded.
- Graduate to `deep-plan` only after the PRD and build context have been reviewed.
