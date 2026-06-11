# Course RAG

Course RAG builds a local SQLite full-text index from a subject folder. It is designed for course notes, slides, assignment sheets, readings, and exported Markdown.

It does not upload files and does not edit the source folder.

## Build An Index

```bash
python3 claude-code/course-rag/scripts/build.py --subject "Biology" --source "$HOME/Desktop/Biology Course"
```

By default, indexes are written to:

```text
claude-code/course-rag/indexes/
```

## Search

```bash
python3 claude-code/course-rag/scripts/search.py "Biology" "photosynthesis" --limit 8
```

Use the returned source paths when answering course-content questions.

## Supported Files

- Plain text, Markdown, CSV, JSON, HTML, and common code/text files.
- DOCX, PPTX, and XLSX through built-in ZIP/XML extraction.
- PDF when `pdftotext` is installed on the machine.

Unsupported files are skipped and listed in the build output.
