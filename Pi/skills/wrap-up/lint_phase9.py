#!/usr/bin/env python3
"""
lint_phase9.py — guards Phase 9 of the wrap-up SKILL.md against the eight
named failure modes that historically caused Haiku verify false negatives.

Reads this skill's SKILL.md by default, extracts the Phase 9 section
(between '## Phase 9' and '## Phase 10'), and greps for the
anti-patterns documented in § "Why Haiku fails this class of rubric".

Exit codes:
  0  clean — no anti-patterns detected
  1  one or more anti-patterns present (drift)
  2  SKILL.md not found or Phase 9 section not parseable

Usage:
  python3 lint_phase9.py
  python3 lint_phase9.py --path /custom/SKILL.md

When to run:
  - After editing § Phase 9 in SKILL.md
  - As a pre-commit hook on the dotfiles repo if SKILL.md is tracked
  - Periodically when wrap-up cost regresses past the 30K target

The lint enforces structure, not wording. It will not catch a semantically
broken rubric that happens to avoid the eight anti-pattern strings. For that
you still need a real wrap-up dry run.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DEFAULT_PATH = Path(__file__).with_name("SKILL.md")
DEFAULT_PROJECT_PATH = Path.cwd() / ".pi" / "skills" / "wrap-up" / "SKILL.md"

# ─── Anti-pattern definitions ───────────────────────────────────────────
# Each rule names what to detect, why it's a problem, and the prompt fix.
# Detection regexes are conservative — they target *the prompt body of
# Phase 9*, not the explanatory § "Why Haiku fails" subsection (which
# legitimately discusses these patterns).

PHASE_HEADER = re.compile(r"^## Phase 9\b", re.MULTILINE)
NEXT_PHASE_HEADER = re.compile(r"^## Phase 10\b", re.MULTILINE)
WHY_FAILS_START = re.compile(r"^### Why Haiku fails this class of rubric", re.MULTILINE)
RETRY_TRIAGE_START = re.compile(r"^### Retry triage", re.MULTILINE)

# The verify prompt block lives in a fenced code block inside Phase 9.
# We scan ONLY that block for anti-patterns 1, 3, 4, 5, 6. Anti-pattern 2
# (positive framing of staged-not-committed) is a presence check across
# the whole Phase 9 prose.
PROMPT_BLOCK_START = re.compile(
    r"^\**\s*Use this prompt template verbatim.*?\n```", re.MULTILINE | re.DOTALL
)
CODE_FENCE = re.compile(r"```")


def slice_section(md: str, start_re: re.Pattern[str], end_re: re.Pattern[str]) -> tuple[str, int] | None:
    """Return (section_text, start_line) or None if not found."""
    s = start_re.search(md)
    if not s:
        return None
    e = end_re.search(md, s.end())
    end = e.start() if e else len(md)
    section = md[s.start():end]
    start_line = md[: s.start()].count("\n") + 1
    return section, start_line


def slice_prompt_block(phase9: str, phase9_start_line: int) -> tuple[str, int] | None:
    """Find the verify-prompt fenced code block inside Phase 9.

    Returns (block_text, absolute_start_line) — block_text excludes the fence
    delimiters. start_line is 1-indexed against the whole SKILL.md file.
    """
    m = PROMPT_BLOCK_START.search(phase9)
    if not m:
        return None
    after_open_fence = m.end()
    # Find the matching closing fence
    closer = CODE_FENCE.search(phase9, after_open_fence)
    if not closer:
        return None
    block = phase9[after_open_fence:closer.start()]
    # Compute absolute start line for reporting
    lines_before = phase9[:after_open_fence].count("\n")
    block_start_line = phase9_start_line + lines_before
    return block, block_start_line


def find_with_lines(text: str, regex: re.Pattern[str], start_line: int) -> list[tuple[int, str]]:
    """Return list of (absolute_line_number, match_excerpt) for each hit."""
    hits: list[tuple[int, str]] = []
    for m in regex.finditer(text):
        line_offset = text[:m.start()].count("\n")
        # Show the matched line, not just the substring
        line_start = text.rfind("\n", 0, m.start()) + 1
        line_end = text.find("\n", m.end())
        if line_end == -1:
            line_end = len(text)
        excerpt = text[line_start:line_end].strip()[:120]
        hits.append((start_line + line_offset, excerpt))
    return hits


# ─── Anti-pattern rules ─────────────────────────────────────────────────

# 1. Contextual hedging — "if applicable" / "either … or …" / "when applicable"
RULE_1 = re.compile(
    r"\b(if applicable|either\s+\w[\s\S]{0,40}?\s+or\s+\w|when applicable)\b",
    re.IGNORECASE,
)

# 3. Compound AND-with-OR — "PASS … AND … (X OR Y)"
RULE_3 = re.compile(
    r"PASS\s.{0,200}?\bAND\b.{0,300}?\([^)]{0,80}?\bOR\b[^)]{0,80}?\)",
    re.IGNORECASE | re.DOTALL,
)

# 4. Footnote / "Note for X" inline in the rubric
RULE_4 = re.compile(r"^\s*\*{0,2}Note for\s+[A-Za-z]", re.MULTILINE)

# 5. Anti-pattern absent — must contain literal anti-pattern guidance
RULE_5_PRESENCE = re.compile(
    r"(anti.?pattern|Do NOT report|auto.?FAIL)", re.IGNORECASE
)

# 6. Word-cap creep — "Under N words" or "N words" in the prompt; cap > 150
RULE_6 = re.compile(r"\bUnder\s+(\d+)\s+words\b", re.IGNORECASE)

# 7. Implicit search-pattern ambiguity — bare "grep <path>" instructions
#    without an explicit -E or pattern. Haiku will pick a too-narrow pattern.
#    Match: line that says "grep" + a path-looking token (.json or absolute /)
#    BUT does NOT have an `-E` flag or a quoted pattern earlier on the line.
RULE_7 = re.compile(
    r"^\s*-?\s*(?:bash:\s*)?grep\s+(?!-E\b)(?:[^'\"\n]*?)(/[^\s'\"]+\.\w+)",
    re.MULTILINE,
)

# 8. Tool-call fan-out — multiple separate tool invocations in the prompt body.
#    Each Haiku tool turn re-sends cumulative input as a triangular series:
#    Σ over turns(base prompt + sum of prior tool results). 6 turns of ~3K
#    new context per turn → ~63K billed input. Collapse to ONE compound bash.
#
#    Hardened 2026-05-04 after Codex review:
#    - Tool detection is now content-anywhere, not just hyphen-bullet lines:
#      catches `* Read`, `1. Read`, `Use Read for...`, bare `Read NEXT.md`,
#      and `Read \`...\`` formats.
#    - The "Run THIS ONE BASH COMMAND" marker is NOT an unconditional bypass.
#      Even with the marker, additional Read/MCP mentions or multiple bash:
#      blocks still FAIL — this prevents marker-cheese (add the marker
#      ceremonially while leaving multi-tool fan-out below it).
#    - Three independent checks:
#        8a. `Read ` / `Open ` mentioned anywhere in the prompt block → FAIL
#        8b. `mcp__<server>__<tool>` mentioned anywhere → FAIL
#        8c. More than one `bash:` directive (newline-anchored) → FAIL
RULE_8A_READ = re.compile(
    # `Read ` or `Open ` followed by a path-ish token or backtick — covers the common
    # ways a verify prompt would invoke the Read tool. Excludes prose like
    # "you have already Read the …" via the requirement that the next char
    # be `\`` or `~/` or `/` or an alpha that starts a backtick-less path.
    r"\b(?:Read|Open)\s+(?:`|~/|/|[A-Za-z_][\w./-]*\.md\b)",
)
RULE_8B_MCP = re.compile(
    # `mcp__<server>__<tool>` — the canonical MCP tool reference syntax in
    # Claude Code prompts. Anywhere in the prompt block. Server names may
    # include hyphens (e.g. `basic-memory`, `chrome-devtools`); tool names
    # use underscores. Both halves accept hyphens for safety.
    r"mcp__[a-z][a-z0-9_-]*__[a-z][a-z0-9_-]*",
    re.IGNORECASE,
)
RULE_8C_BASH = re.compile(
    # Newline-anchored `bash:` (the directive that prefaces a tool-call
    # block in the verify prompt). Multiple occurrences = multi-call.
    r"^\s*bash:\s*$",
    re.MULTILINE,
)

# 2. Positive framing of staged-not-committed — the bold preamble must
#    appear in Phase 9 prose. Detect by absence.
RULE_2_PRESENCE = re.compile(
    r"(staged is\s+(?:correct|the expected|expected)|"
    r"never pushes.{0,80}?(staged|expected)|"
    r"\*\*[^*]*staged[^*]*expected[^*]*\*\*)",
    re.IGNORECASE | re.DOTALL,
)


def scan_rule8(
    text: str,
    start_line: int,
    findings: list[str],
    context: str,
    max_bash_directives: int,
) -> None:
    """Scan a prompt/override body for tool fan-out patterns."""
    for line_no, excerpt in find_with_lines(text, RULE_8A_READ, start_line):
        findings.append(
            f"[8a] file tool referenced in {context} at line {line_no}: {excerpt}\n"
            f"     fix: Phase 9 verify must use a single bash compound command. Drop Read/Open; the bash should emit bounded DATA lines instead.\n"
            f"     Rationale: each Haiku tool turn re-sends cumulative input as a triangular series. 6 turns of ~3K each → ~63K billed."
        )

    for line_no, excerpt in find_with_lines(text, RULE_8B_MCP, start_line):
        findings.append(
            f"[8b] MCP tool referenced in {context} at line {line_no}: {excerpt}\n"
            f"     fix: Drop MCP from the verify path. The bash output is sufficient to grade retrieval checks."
        )

    bash_directives = RULE_8C_BASH.findall(text)
    if len(bash_directives) > max_bash_directives:
        lines = []
        for m in RULE_8C_BASH.finditer(text):
            lines.append(start_line + text[: m.start()].count("\n"))
        findings.append(
            f"[8c] {len(bash_directives)} `bash:` directives in {context} at lines {lines}\n"
            f"     fix: keep project checks inside the global single bash command. Each separate bash invocation is a Haiku tool turn."
        )


def run_lint(path: Path, project_path: Path | None = None) -> int:
    if not path.exists():
        print(f"ERROR: SKILL.md not found at {path}", file=sys.stderr)
        return 2
    md = path.read_text()

    sliced = slice_section(md, PHASE_HEADER, NEXT_PHASE_HEADER)
    if not sliced:
        print("ERROR: could not find '## Phase 9' / '## Phase 10' anchors", file=sys.stderr)
        return 2
    phase9, phase9_line = sliced

    # The anti-pattern regexes only scan the verify prompt's fenced code
    # block — never the surrounding prose. The "Why Haiku fails" + "Retry
    # triage" subsections legitimately quote anti-patterns by name to
    # explain them. Searching the prompt block exclusively avoids
    # false-positive hits on the explanatory text.
    prompt_sliced = slice_prompt_block(phase9, phase9_line)
    if not prompt_sliced:
        print(
            "ERROR: could not find 'Use this prompt template verbatim' fenced block",
            file=sys.stderr,
        )
        return 2
    prompt_block, prompt_line = prompt_sliced

    findings: list[str] = []

    # Rule 1 — contextual hedging
    for line_no, excerpt in find_with_lines(prompt_block, RULE_1, prompt_line):
        findings.append(
            f"[1] contextual hedging at line {line_no}: {excerpt}\n"
            f"    fix: state rubric as a flat AND-list; absorb conditional inline at point of decision"
        )

    # Rule 3 — compound AND…(OR)
    for line_no, excerpt in find_with_lines(prompt_block, RULE_3, prompt_line):
        findings.append(
            f"[3] compound AND-with-OR at line {line_no}: {excerpt}\n"
            f"    fix: rewrite OR-branch as 'is yes' + state-irrelevance clause"
        )

    # Rule 4 — Note for X footnote
    for line_no, excerpt in find_with_lines(prompt_block, RULE_4, prompt_line):
        findings.append(
            f"[4] 'Note for X' footnote at line {line_no}: {excerpt}\n"
            f"    fix: inline the constraint at its point of application; never use footnotes in a verify rubric"
        )

    # Rule 5 — anti-pattern guidance MUST be present
    if not RULE_5_PRESENCE.search(prompt_block):
        findings.append(
            f"[5] no anti-pattern list in the verify prompt (block starting line {prompt_line})\n"
            f"    fix: include literal 'Anti-patterns (auto-FAIL these in your own verdict)' block"
        )

    # Rule 6 — word cap creep
    for m in RULE_6.finditer(prompt_block):
        cap = int(m.group(1))
        if cap > 150:
            line_no = prompt_line + prompt_block[: m.start()].count("\n")
            excerpt = m.group(0)
            findings.append(
                f"[6] word cap > 150 at line {line_no}: '{excerpt}'\n"
                f"    fix: hard cap ≤150 forces decision density"
            )

    # Rule 7 — bare grep without explicit -E pattern
    for line_no, excerpt in find_with_lines(prompt_block, RULE_7, prompt_line):
        findings.append(
            f"[7] bare 'grep <path>' without explicit pattern at line {line_no}: {excerpt}\n"
            f"    fix: provide exact pattern, e.g. `grep -E '\"d_num\":\\s*<XXXX>\\b' /path/to/file.json`"
        )

    # Rule 8 — single-tool-call discipline. THREE independent checks; any
    # one tripping is a FAIL. The "Run THIS ONE BASH COMMAND" marker is NOT
    # an unconditional bypass (Codex review 2026-05-04 flagged that vector).
    # If you legitimately need multi-tool, document why and split the prompt
    # into two phases — never silence this rule with the marker alone.

    scan_rule8(
        prompt_block,
        prompt_line,
        findings,
        "global verify prompt",
        max_bash_directives=1,
    )

    if project_path and project_path.exists():
        try:
            same_file = project_path.resolve() == path.resolve()
        except FileNotFoundError:
            same_file = False
        if not same_file:
            project_md = project_path.read_text()
            project_sliced = slice_section(project_md, PHASE_HEADER, NEXT_PHASE_HEADER)
            if project_sliced:
                project_phase9, project_line = project_sliced
                scan_rule8(
                    project_phase9,
                    project_line,
                    findings,
                    f"project Phase 9 override ({project_path})",
                    max_bash_directives=0,
                )

    # Rule 2 — positive framing must be present in Phase 9 prose (anywhere)
    if not RULE_2_PRESENCE.search(phase9):
        findings.append(
            f"[2] missing positive framing of 'staged but not committed' as expected state\n"
            f"    fix: add bold preamble in Phase 9 — 'Wrap-up never pushes — staged is the expected state'"
        )

    if not findings:
        print(f"OK — Phase 9 prompt block clean (path: {path})")
        return 0

    print(f"FAIL — {len(findings)} anti-pattern(s) detected in {path}\n")
    for f in findings:
        print(f"  {f}\n")
    print(
        "See § 'Why Haiku fails this class of rubric' in the same SKILL.md for the failure-mode catalogue."
    )
    return 1


def main() -> int:
    p = argparse.ArgumentParser(description="Lint Phase 9 of wrap-up SKILL.md.")
    p.add_argument("--path", type=Path, default=DEFAULT_PATH, help="Path to SKILL.md")
    p.add_argument(
        "--project-path",
        type=Path,
        default=None,
        help="Optional project wrap-up SKILL.md override to scan for Phase 9 tool fan-out",
    )
    args = p.parse_args()
    project_path = args.project_path
    if project_path is None and DEFAULT_PROJECT_PATH.exists():
        project_path = DEFAULT_PROJECT_PATH
    return run_lint(args.path, project_path=project_path)


if __name__ == "__main__":
    sys.exit(main())
