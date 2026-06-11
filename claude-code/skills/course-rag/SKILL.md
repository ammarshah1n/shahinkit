---
name: course-rag
description: Build and search a local SQLite course-content index from a user-provided course folder.
---

# Course RAG

Use this when the user wants to drag in course content, point Claude Code at a subject folder, or answer questions from local course files.

## Rules

- Never edit the source course folder.
- Never upload course content.
- Index locally with SQLite FTS.
- Ask for the source folder only if the user did not provide it.
- Search before answering course-content questions.
- Cite source paths from search results.

## Build

```bash
python3 claude-code/course-rag/scripts/build.py --subject "SUBJECT" --source "/path/to/course-folder"
```

The index is written under `claude-code/course-rag/indexes/` by default.

## Search

```bash
python3 claude-code/course-rag/scripts/search.py "SUBJECT" "query" --limit 8
```

## Supported Inputs

The builder extracts text from plain text, Markdown, CSV, JSON, HTML, DOCX, PPTX, XLSX, and PDF when `pdftotext` is installed. Unsupported files are skipped and reported.
