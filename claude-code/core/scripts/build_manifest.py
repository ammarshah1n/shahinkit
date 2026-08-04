#!/usr/bin/env python3
"""Build ShahinKit's deterministic source-integrity manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / ".shahinkit-manifest.json"
EXCLUDED_PARTS = {"tests", "__pycache__", "node_modules"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files(root: Path, *, exclude_core: bool = False) -> list[Path]:
    files = []
    for path in root.rglob("*"):
        if not path.is_file() or path.name in {".DS_Store"} or path.suffix == ".pyc":
            continue
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if exclude_core and relative.parts and relative.parts[0] == "core":
            continue
        current = root
        for part in relative.parts:
            current /= part
            if stat.S_ISLNK(current.lstat().st_mode):
                raise ValueError(f"symlinked manifest input: {path}")
        files.append(path)
    return sorted(files)


def category(path: str) -> str:
    if path in {"README.md", "INSTALL.md", "SKILLS.html"}:
        return "documentation"
    if "/third_party/" in path:
        return "vendor-payload"
    for marker, value in (
        ("/skills/", "skill"),
        ("/hooks/", "hook"),
        ("/memory/", "memory-template"),
        ("/mcp/", "mcp-template"),
        ("/policies/", "policy"),
        ("/models/", "model-schema"),
        ("/context/", "context-block"),
        ("/integrations/", "integration"),
        ("/scripts/", "manager-tool"),
        ("/docs/", "documentation"),
    ):
        if marker in path:
            return value
    return "core"


def build() -> dict:
    previous = json.loads(MANIFEST.read_text())
    root_files = [ROOT / name for name in ("README.md", "INSTALL.md", "SKILLS.html")]
    owned = root_files + source_files(ROOT / "claude-code" / "core")
    entries = []
    for path in sorted(owned):
        relative = path.relative_to(ROOT).as_posix()
        digest = sha256(path)
        entries.append({
            "path": relative,
            "category": category(relative),
            "source_sha256": digest,
            "render_sha256": digest,
            "ownership": "vendored" if "/third_party/" in relative else "shared",
        })
    adapter_inputs = {}
    for host in ("claude-code", "codex", "opencode"):
        host_root = ROOT / host
        adapter_inputs[host] = {
            path.relative_to(host_root).as_posix(): sha256(path)
            for path in source_files(host_root, exclude_core=host == "claude-code")
        }
    return {
        "manifest_version": 1,
        "manager": previous["manager"],
        "path_rules": previous["path_rules"],
        "owned_files": entries,
        "adapter_inputs": adapter_inputs,
    }


def rendered() -> bytes:
    return (json.dumps(build(), indent=2, sort_keys=False) + "\n").encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    output = rendered()
    if args.check:
        if MANIFEST.read_bytes() != output:
            print("manifest: stale", file=sys.stderr)
            return 1
        print("manifest: current")
        return 0
    MANIFEST.write_bytes(output)
    print(f"manifest: wrote {len(build()['owned_files'])} owned files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
