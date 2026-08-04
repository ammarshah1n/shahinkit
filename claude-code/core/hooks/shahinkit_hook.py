"""Portable, advisory lifecycle context for ShahinKit hosts."""

import json
import sys


CONTEXT = {
    "SessionStart": "Prime is available; inspect visible PROJECT_STATE/NEXT/HANDOFF for meaningful work. Continue current session; never require a fresh session.",
    "SubagentStart": "Worker scope bounded, no controller authority, return evidence.",
}


def main():
    try:
        payload = json.loads(sys.stdin.read())
        event = (payload.get("hook_event_name") or payload.get("hookEventName")) if isinstance(payload, dict) else None
        context = CONTEXT.get(event)
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
