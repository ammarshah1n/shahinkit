#!/usr/bin/env python3
import argparse
import csv
import json
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX_DIR = Path("{{SHAHINKIT_DATA_DIR}}/course-rag")

TEXT_EXTENSIONS = {
    ".c",
    ".cpp",
    ".css",
    ".csv",
    ".go",
    ".h",
    ".html",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".py",
    ".r",
    ".rb",
    ".rs",
    ".rst",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

OFFICE_EXTENSIONS = {".docx", ".pptx", ".xlsx"}
SKIP_DIRS = {".git", ".hg", ".svn", "__pycache__", ".venv", "venv", "node_modules"}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        data = data.strip()
        if data:
            self.parts.append(data)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "course"


def clean_text(value: str) -> str:
    value = value.replace("\x00", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def read_text(path: Path) -> str:
    data = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".xml"}:
        parser = TextExtractor()
        parser.feed(data)
        return "\n".join(parser.parts)
    if path.suffix.lower() == ".json":
        try:
            return json.dumps(json.loads(data), indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            return data
    if path.suffix.lower() == ".csv":
        try:
            with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                rows = csv.reader(handle)
                return "\n".join(" | ".join(cell.strip() for cell in row) for row in rows)
        except csv.Error:
            return data
    return data


def read_office(path: Path) -> str:
    wanted_prefixes = {
        ".docx": ("word/",),
        ".pptx": ("ppt/",),
        ".xlsx": ("xl/",),
    }[path.suffix.lower()]

    parts: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith(".xml"):
                continue
            if not name.startswith(wanted_prefixes):
                continue
            try:
                root = ElementTree.fromstring(archive.read(name))
            except ElementTree.ParseError:
                continue
            text = " ".join(part.strip() for part in root.itertext() if part.strip())
            if text:
                parts.append(text)
    return "\n\n".join(parts)


def read_pdf(path: Path) -> str:
    if shutil.which("pdftotext") is None:
        raise RuntimeError("pdftotext not installed")
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def extract(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return read_text(path)
    if suffix in OFFICE_EXTENSIONS:
        return read_office(path)
    if suffix == ".pdf":
        return read_pdf(path)
    raise RuntimeError(f"unsupported extension {suffix or '<none>'}")


def chunk_text(text: str, max_words: int = 220, overlap: int = 30) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(len(words), start + max_words)
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = max(0, end - overlap)
    return chunks


def iter_files(source: Path):
    for path in sorted(source.rglob("*")):
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(source)
        except (OSError, ValueError):
            continue
        yield resolved


def reset_db(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            subject TEXT NOT NULL,
            source_root TEXT NOT NULL,
            relpath TEXT NOT NULL,
            path TEXT NOT NULL,
            file_type TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE VIRTUAL TABLE chunks_fts USING fts5(
            subject,
            relpath,
            path,
            content,
            content='documents',
            content_rowid='id'
        )
        """
    )
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    return conn


def insert_chunk(
    conn: sqlite3.Connection,
    subject: str,
    source_root: Path,
    path: Path,
    relpath: str,
    chunk_index: int,
    content: str,
) -> None:
    cur = conn.execute(
        """
        INSERT INTO documents (subject, source_root, relpath, path, file_type, chunk_index, content)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (subject, str(source_root), relpath, str(path), path.suffix.lower(), chunk_index, content),
    )
    rowid = cur.lastrowid
    conn.execute(
        "INSERT INTO chunks_fts(rowid, subject, relpath, path, content) VALUES (?, ?, ?, ?, ?)",
        (rowid, subject, relpath, str(path), content),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local course SQLite FTS index.")
    parser.add_argument("--subject", required=True, help="Subject name, for example Biology")
    parser.add_argument("--source", required=True, help="Course folder to read")
    parser.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR), help="Directory for generated indexes")
    args = parser.parse_args()

    subject = args.subject.strip()
    source = Path(args.source).expanduser().resolve()
    index_dir = Path(args.index_dir).expanduser().resolve()

    if not source.exists() or not source.is_dir():
        print(f"source folder not found: {source}", file=sys.stderr)
        return 2

    db_path = index_dir / f"{slugify(subject)}.sqlite"
    conn = reset_db(db_path)
    indexed_files = 0
    indexed_chunks = 0
    skipped: list[str] = []

    with conn:
        conn.execute("INSERT INTO meta(key, value) VALUES (?, ?)", ("subject", subject))
        conn.execute("INSERT INTO meta(key, value) VALUES (?, ?)", ("source_root", str(source)))
        for path in iter_files(source):
            relpath = str(path.relative_to(source))
            try:
                text = clean_text(extract(path))
            except Exception as exc:  # Build report should continue on unreadable course files.
                skipped.append(f"{relpath}: {exc}")
                continue
            chunks = chunk_text(text)
            if not chunks:
                skipped.append(f"{relpath}: no extractable text")
                continue
            indexed_files += 1
            for index, chunk in enumerate(chunks):
                insert_chunk(conn, subject, source, path, relpath, index, chunk)
                indexed_chunks += 1
        conn.execute("INSERT INTO meta(key, value) VALUES (?, ?)", ("indexed_files", str(indexed_files)))
        conn.execute("INSERT INTO meta(key, value) VALUES (?, ?)", ("indexed_chunks", str(indexed_chunks)))

    print(f"subject: {subject}")
    print(f"source: {source}")
    print(f"index: {db_path}")
    print(f"indexed files: {indexed_files}")
    print(f"indexed chunks: {indexed_chunks}")
    if skipped:
        print("skipped:")
        for item in skipped[:40]:
            print(f"- {item}")
        if len(skipped) > 40:
            print(f"- ... {len(skipped) - 40} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
