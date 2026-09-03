#!/usr/bin/env python3
"""Build ShahinKit's self-contained beginner skill catalog."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[3]
OUTPUT = ROOT / "SKILLS.html"
CATEGORIES = {
    "Start and finish": {"prime", "checkpoint", "session-handoff", "miniwrap", "wrap-up"},
    "Plan and decide": {"idea", "plan", "plans", "mission", "deep-idea", "deep-plan", "triage"},
    "Memory and learning": {"memory", "context-router", "corrections", "reflect", "self-improve"},
    "Research and review": {"research", "audit-tool", "collab", "graphify", "taste-gate", "watch"},
    "Build and coordinate": {"delegation-routing", "parallel-worktrees", "skill-builder", "output-style"},
    "Study": {"study", "course-rag"},
    "Apple development": {"swift-testing-pro", "swiftdata-pro", "swiftui-pro"},
    "Modes": {"ponytail", "ponytail-audit", "ponytail-debt", "ponytail-gain", "ponytail-help", "ponytail-review", "caveman", "caveman-commit", "caveman-help", "caveman-review"},
}


def metadata(path: Path) -> tuple[str, str]:
    text = path.read_text()
    frontmatter = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not frontmatter:
        raise ValueError(f"missing frontmatter: {path}")
    lines = frontmatter.group(1).splitlines()
    values = {}
    for index, line in enumerate(lines):
        if line[:1].isspace():
            continue
        key, separator, value = line.partition(":")
        if separator:
            value = value.strip()
            if value in (">", "|"):
                continuation = []
                for next_line in lines[index + 1:]:
                    if next_line and not next_line[0].isspace():
                        break
                    if next_line.strip():
                        continuation.append(next_line.strip())
                value = (" " if value == ">" else "\n").join(continuation)
            values[key.strip()] = value.strip('"')
    name, description = values.get("name"), values.get("description")
    if not name or not description:
        raise ValueError(f"missing skill metadata: {path}")
    return name, description


def safe_vendor_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str):
        raise ValueError("vendor manifest path must be a string")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise ValueError(f"unsafe vendor manifest path: {relative!r}")
    repository = root.resolve()
    allowed = (root / "claude-code" / "core" / "third_party").resolve()
    candidate = (root / Path(*pure.parts)).resolve()
    try:
        allowed.relative_to(repository)
        candidate.relative_to(allowed)
    except ValueError as error:
        raise ValueError(f"vendor manifest path escapes third_party: {relative!r}") from error
    return candidate


def vendor_skill_paths(root: Path = ROOT) -> list[Path]:
    render = json.loads((root / "claude-code" / "render-manifest.json").read_text())
    paths = []
    for vendor, names in render.get("vendor_skills", {}).items():
        for name in names:
            paths.append(safe_vendor_path(root, f"claude-code/core/third_party/{vendor}/skills/{name}/SKILL.md"))
    for item in render.get("copies", []):
        source = item.get("source")
        if isinstance(source, str) and source.startswith("claude-code/core/third_party/") and source.endswith("/SKILL.md"):
            paths.append(safe_vendor_path(root, source))
    for mapping in render.get("vendor_file_mappings", []):
        paths.append(safe_vendor_path(root, f"{mapping.get('source_root', '')}/SKILL.md"))
    return list(dict.fromkeys(paths))


def skills(root: Path = ROOT) -> list[dict[str, str]]:
    paths = list((root / "claude-code" / "core" / "shared" / "skills").glob("*/SKILL.md"))
    paths.extend(path for path in vendor_skill_paths(root) if path.is_file())
    paths.append(root / "claude-code" / "skills" / "course-rag" / "SKILL.md")
    result = []
    for path in paths:
        name, description = metadata(path)
        category = next((label for label, names in CATEGORIES.items() if name in names), "More tools")
        result.append({"name": name, "description": description, "category": category})
    return sorted(result, key=lambda item: (list(CATEGORIES).index(item["category"]) if item["category"] in CATEGORIES else 99, item["name"]))


def card(item: dict[str, str]) -> str:
    name = html.escape(item["name"])
    description = html.escape(item["description"])
    category = html.escape(item["category"])
    return f'''<article class="card" data-search="{name.lower()} {description.lower()} {category.lower()}">
      <div class="card-top"><code>/{name}</code><span>{category}</span></div>
      <p>{description}</p>
      <div class="hosts"><b>Works in</b><i>Claude Code</i><i>Codex</i><i>OpenCode</i></div>
    </article>'''


def rendered() -> bytes:
    items = skills()
    cards = "\n".join(card(item) for item in items)
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ShahinKit skill guide</title>
<style>
:root{{--ink:#171713;--muted:#66665d;--paper:#f5f1e8;--card:#fffdf8;--line:#d9d2c3;--accent:#2b5f4b}}*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 ui-sans-serif,system-ui,-apple-system,sans-serif}}main{{width:min(1120px,calc(100% - 32px));margin:auto;padding:64px 0 96px}}h1{{font:700 clamp(42px,7vw,84px)/.95 ui-serif,Georgia,serif;letter-spacing:-.045em;margin:0 0 20px;max-width:850px}}h2{{font:700 28px/1.1 ui-serif,Georgia,serif;margin:0 0 14px}}.lede{{font-size:20px;max-width:760px;color:var(--muted)}}.count{{color:var(--accent);font-weight:700}}.path{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);margin:42px 0}}.step{{background:var(--card);padding:22px}}.step b{{display:block;margin-bottom:7px}}.step code,.card code{{color:var(--accent);font-weight:800}}.note{{border-left:4px solid var(--accent);padding:4px 0 4px 18px;margin:32px 0;color:var(--muted)}}.toolbar{{position:sticky;top:0;background:color-mix(in srgb,var(--paper) 92%,transparent);backdrop-filter:blur(12px);padding:16px 0;z-index:2}}input{{width:100%;border:1px solid var(--line);border-radius:12px;padding:15px 17px;background:var(--card);font:inherit;color:inherit}}.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:18px}}.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:19px;min-height:190px;display:flex;flex-direction:column}}.card-top{{display:flex;gap:12px;justify-content:space-between;align-items:start}}.card-top span{{font-size:12px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);text-align:right}}.card p{{color:var(--muted)}}.hosts{{display:flex;gap:7px;flex-wrap:wrap;margin-top:auto;font-size:12px}}.hosts b{{width:100%;color:var(--muted)}}.hosts i{{font-style:normal;border:1px solid var(--line);border-radius:99px;padding:3px 8px}}.hidden{{display:none}}footer{{margin-top:50px;color:var(--muted);border-top:1px solid var(--line);padding-top:20px}}@media(max-width:800px){{main{{padding-top:36px}}.path,.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<p class="count">{len(items)} bundled skills · one guide · three hosts</p>
<h1>Know what to ask for—and when.</h1>
<p class="lede">ShahinKit gives Claude Code, Codex, and OpenCode the same portable workflows. Skills are instructions, not background services: invoke one by name or describe the job naturally.</p>
<section class="path"><div class="step"><b>Starting or resuming?</b><code>/prime</code><br>Loads only useful project state.</div><div class="step"><b>Planning real work?</b><code>/plan</code> or <code>/deep-plan</code><br>Maps dependencies before edits.</div><div class="step"><b>Tiny task finished?</b><code>/miniwrap</code><br>Closes without heavy ceremony.</div><div class="step"><b>Meaningful session finished?</b><code>/wrap-up</code><br>Verifies and writes a handoff.</div></section>
<p class="note"><b>HANDOFF.md in human English:</b> it is a note from the previous session to the next one—what changed, what passed, what remains, and the exact restart point. Prime reads it; Wrap Up writes it.</p>
<section><h2>Find a skill</h2><div class="toolbar"><input id="search" type="search" placeholder="Try: research, video, plan, memory, review…" aria-label="Search skills"></div><div class="grid" id="skills">{cards}</div></section>
<footer>Generated from Claude Code canonical skill files. Codex and OpenCode adapters are checked against the same inventory. Optional tools are used only when available and approved.</footer>
</main><script>const q=document.querySelector('#search');const cards=[...document.querySelectorAll('.card')];q.addEventListener('input',()=>{{const v=q.value.trim().toLowerCase();cards.forEach(c=>c.classList.toggle('hidden',v&&!c.dataset.search.includes(v)))}});</script></body></html>'''
    return document.encode()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    output = rendered()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_bytes() != output:
            print("catalog: stale", file=sys.stderr)
            return 1
        print(f"catalog: current ({len(skills())} skills)")
        return 0
    OUTPUT.write_bytes(output)
    print(f"catalog: wrote {len(skills())} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
