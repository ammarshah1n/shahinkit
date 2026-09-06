"""Portable, advisory lifecycle context for ShahinKit hosts."""

import json
import os
import sys
from pathlib import Path


CONTEXT = {
    "SessionStart": "Prime is available; inspect visible PROJECT_STATE/NEXT/HANDOFF for meaningful work. Continue current session; never require a fresh session.",
    "SubagentStart": "Worker scope bounded, no controller authority, return evidence.",
}

# Re-stated every turn because static instruction context decays across a long
# session; a one-shot statement at SessionStart does not hold style behaviour.
CAVEMAN_REMINDER = (
    "Caveman is active: terse clear prose, full technical substance preserved, "
    "code and commits normal. Auto-Clarity suspends compression for security "
    "warnings, irreversible-action confirmation, and ambiguous instructions."
)

PLAIN_REMINDER = (
    "Plain-English mode is active: expand every technical term on first use, "
    "say what each command, file, error, and recommendation does and why it "
    "matters, and leave no bare jargon unexplained. Plain wording overrides "
    "Caveman compression and never removes substance, warnings, or uncertainty; "
    "code, commands, and paths stay exact."
)

# An existing install has no explain-mode file, so updating to this version
# makes the next session ask once. Answering writes the file and ends the ask.
EXPLAIN_ASK = (
    "Explanation level is unset: ask the user once this session whether they "
    "have written code before or want plain-English explanations, then record "
    "`plain` or `technical` in the `explain-mode` file inside this install's "
    "`.shahinkit-data` directory. Ask once; never ask again once it exists."
)


def data_dir():
    """The hook is copied verbatim, so it resolves its own data directory at
    runtime rather than relying on render substitution."""
    here = Path(__file__).resolve().parent
    for base in (here.parent, here.parent.parent, here):
        candidate = base / ".shahinkit-data"
        if candidate.is_dir():
            return candidate
    return None


def config(directory):
    """Install-owned settings. Rewritten on every render."""
    if directory is None:
        return {}
    try:
        loaded = json.loads((directory / "hook-config.json").read_text(encoding="utf-8"))
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def opt_out_paths(directory):
    """User-owned path list, one prefix per line, `#` comments ignored. Not
    installer-owned, so a hand-edited list survives every re-render."""
    if directory is None:
        return []
    try:
        text = (directory / "opt-out").read_text(encoding="utf-8")
    except Exception:
        return []
    entries = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            entries.append(line)
    return entries


def opted_out(directory, cwd):
    if not cwd:
        return False
    entries = opt_out_paths(directory)
    if not entries:
        return False
    try:
        current = Path(cwd).resolve()
    except Exception:
        return False
    for entry in entries:
        try:
            prefix = Path(os.path.expanduser(entry)).resolve()
        except Exception:
            continue
        if current == prefix or prefix in current.parents:
            return True
    return False


def explain_mode(directory):
    """User-owned, one word. Absent or unrecognised means unset, which is what
    makes an already-installed kit ask once after an update."""
    if directory is None:
        return None
    try:
        value = (directory / "explain-mode").read_text(encoding="utf-8").strip().lower()
    except Exception:
        return None
    return value if value in ("plain", "technical") else None


def context_for(event, settings, mode, ask):
    if event == "UserPromptSubmit":
        parts = [CAVEMAN_REMINDER] if settings.get("caveman") else []
        if mode == "plain":
            parts.append(PLAIN_REMINDER)
        return " ".join(parts) or None
    context = CONTEXT.get(event)
    if event == "SessionStart" and ask:
        return context + " " + EXPLAIN_ASK
    return context


def main():
    try:
        payload = json.loads(sys.stdin.read())
        payload = payload if isinstance(payload, dict) else {}
        event = payload.get("hook_event_name") or payload.get("hookEventName")
        directory = data_dir()
        mode = explain_mode(directory)
        context = (
            None
            if opted_out(directory, payload.get("cwd"))
            else context_for(event, config(directory), mode, directory is not None and mode is None)
        )
        output = (
            {"hookSpecificOutput": {"hookEventName": event, "additionalContext": context}}
            if context
            else {}
        )
    except Exception:
        output = {}
    try:
        sys.stdout.write(json.dumps(output))
    except Exception:
        pass


if __name__ == "__main__":
    main()
