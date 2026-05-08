# Memory Protocol

ShahinKit separates memory by domain so development, school/university, and client work do not contaminate each other.

## Memory Routes

- `dev`: project architecture, coding decisions, bugs, verification, release notes.
- `school-university`: subjects, assignment briefs, rubrics, feedback, evidence, learning reflections.
- `client`: client-specific decisions, context, handoffs, and deliverables.

Use separate Basic Memory projects, Claude Memory corpora, or vault folders for these routes.

## Retrieval Rule

Before making architecture claims, writing implementation plans, or summarizing project state, retrieve relevant local memory where configured.

If memory tooling is unavailable, write that explicitly in the planning or handoff artifact. Do not invent retrieved context.

## Write Rule

Write memory only when the user or project has configured a memory target. Prefer concise decision notes:

- what changed;
- why it changed;
- what constraint matters next;
- where the source files or handoff live.

## Indexing Rule

Indexing and embedding require the `rag-consent` workflow.

Do not embed:

- private transcripts;
- credentials or secrets;
- school/private identity data;
- client confidential content;
- archives or raw imports that have not been reviewed.
