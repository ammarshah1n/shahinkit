#!/usr/bin/env bash
# fable-mode.sh — SessionStart. If the session model is Claude Fable 5, inject
# ~/.pi/agent/FABLE-MODE.md as additional context. Other models: no-op.
set -uo pipefail
INPUT="$(cat)"
model="$(printf '%s' "$INPUT" | python3 -c 'import json,sys
try: d=json.load(sys.stdin)
except Exception: d={}
print(d.get("model") or d.get("session",{}).get("model") or "")' 2>/dev/null)"
case "$model" in *fable*|*Fable*|*opus*|*Opus*) ;; *) exit 0;; esac  # widened 2026-08-28
f="$HOME/.pi/agent/FABLE-MODE.md"
[ -f "$f" ] || exit 0
python3 - "$f" <<'PY'
import json,sys
print(json.dumps({"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":open(sys.argv[1]).read()}}))
PY
