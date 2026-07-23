---
name: course-rag
description: Build and search a local SQLite course-content index from a user-provided course folder.
---

# Course RAG

Use for local course content. Never edit source folder or upload course material.
Build local SQLite FTS index, search before answering, and cite returned source paths.

```bash
python3 "{{SHAHINKIT_DATA_DIR}}/course-rag/scripts/build.py" --subject "<SUBJECT>" --source "<SOURCE_FOLDER>"
python3 "{{SHAHINKIT_DATA_DIR}}/course-rag/scripts/search.py" "<SUBJECT>" "<QUERY>" --limit 8
```

Unsupported files are skipped and reported. PDF extraction requires local `pdftotext`.
