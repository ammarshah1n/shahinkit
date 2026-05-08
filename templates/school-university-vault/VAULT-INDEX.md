# Vault Index

## Read Order
1. `Working-Context/school-state.md`
2. `Current-Term/index.md`
3. Relevant subject index.
4. Relevant assignment `_INDEX.md`.
5. Source notes only as needed.

## Current Term
- Term: {{CURRENT_TERM}}
- Start: {{TERM_START}}
- End: {{TERM_END}}

## Subjects
- `Subjects/Subject 1/` through `Subjects/Subject 5/`: rename these to your real subjects.
- If you do not want to rename manually, tell your agent your subject list and ask it to rename the folders.
- Use `Lessons/`, `Readings/`, `Notes/`, `Sources/`, and `Assessment/` consistently.

## Assignments
- `Assignments/ASSIGNMENT_TEMPLATE/`: copy for each assignment.
- Keep brief, rubric, sources, drafts, feedback, and handoff together.

## Import Holding Folder
- `OneDrive-Imports/`: temporary holding area for imported files before sorting.
- Give the agent a large school folder, zip, or export and ask it to run `ingest-large-folder`.
- The agent should inventory it first, ask before installing indexing tools, ask before embedding, then build the approved school RAG corpus.

## Agent Read Order
- Start with school state, then current term, then the relevant subject or assignment.
- Do not read drafts, archive, or import folders unless needed for the task.
