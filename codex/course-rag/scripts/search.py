#!/usr/bin/env python3
import argparse
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INDEX_DIR = ROOT / "indexes"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "course"


def build_match_query(query: str) -> str:
    phrases = re.findall(r'"([^"]+)"', query)
    remainder = re.sub(r'"[^"]+"', " ", query)
    terms = phrases + re.findall(r"[A-Za-z0-9_'-]+", remainder)
    terms = [term.replace('"', "").strip() for term in terms if term.strip()]
    if not terms:
        raise ValueError("empty query")
    return " OR ".join(f'"{term}"' for term in terms)


def main() -> int:
    parser = argparse.ArgumentParser(description="Search a local course SQLite FTS index.")
    parser.add_argument("subject", help="Subject name used when building the index")
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR), help="Directory containing generated indexes")
    parser.add_argument("--limit", type=int, default=8, help="Maximum result count")
    args = parser.parse_args()

    subject = args.subject.strip()
    query = " ".join(args.query)
    index_dir = Path(args.index_dir).expanduser().resolve()
    db_path = index_dir / f"{slugify(subject)}.sqlite"

    if not db_path.exists():
        print(f"index not found: {db_path}", file=sys.stderr)
        print("build it first with scripts/build.py", file=sys.stderr)
        return 2

    try:
        match_query = build_match_query(query)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT
                relpath,
                snippet(chunks_fts, 3, '[', ']', ' ... ', 32) AS snippet,
                rank
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (match_query, args.limit),
        ).fetchall()

    if not rows:
        print("No hits.")
        return 0

    for index, (relpath, snippet, _rank) in enumerate(rows, 1):
        print(f"{index}. {relpath}")
        print(f"   {snippet}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
