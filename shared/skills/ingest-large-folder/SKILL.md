---
name: ingest-large-folder
description: Safely inventory and route large folders, OneDrive exports, zip files, course folders, and project archives before moving, extracting, embedding, or indexing.
---

# ingest-large-folder

Use when asked to ingest or organize a large folder, archive, export, or course/project bundle.

Always inventory first. Ask before moving, deleting, extracting, embedding, or indexing.

## Supported Inputs

- OneDrive or cloud-storage exports.
- Zip and compressed archives.
- Course or university folders.
- Project archives.
- Mixed document folders.

## Workflow

1. Inventory first.
   - List top-level folders and file counts.
   - Identify file types, large files, duplicate-looking names, and archive files.
   - Detect obvious sensitive categories without opening unnecessary content.

2. Propose a route.
   - Use the development vault for code, specs, product notes, and engineering references.
   - Use the school or university vault for coursework, assignments, readings, and academic admin.
   - Ask one specific question if the route is unclear.

3. Ask before irreversible or expensive actions.
   - Moving files.
   - Deleting files.
   - Extracting archives.
   - Embedding or indexing content.
   - Renaming large batches.

4. Create `_INDEX.md`.
   - Include source label, received date, inventory summary, chosen route, exclusions, and actions taken.
   - Include relative paths only.
   - Do not include private local paths, personal names, secrets, or raw transcript text.

5. Process only after approval.
   - Preserve original content unless the user approves changes.
   - Keep generated indexes separate from source files.
   - Record skipped files and reasons.

## Output

Report:

- Inventory summary.
- Proposed destination route.
- Actions needing approval.
- `_INDEX.md` location when created.
