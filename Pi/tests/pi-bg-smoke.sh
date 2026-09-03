#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd -P)
BG=$(mktemp -d)
trap 'rm -rf "$BG"' EXIT
id=worker-123456-123
printf 'worker | test | LOCAL:%s\n' "$ROOT" > "$BG/$id.meta"
printf '%s\n' "$$" > "$BG/$id.pid"
printf 'task\n' > "$BG/$id.task"
line=$(ps -ww -p "$$" -o lstart= -o command=)
token=$(printf '%s' "$line" | python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())')
printf '%s\n' "$token" > "$BG/$id.process"

out=$(PI_BG_DIR="$BG" "$ROOT/Pi/bin/pi-bg" ls)
[[ $out == RUNNING* ]]
if PI_BG_DIR="$BG" "$ROOT/Pi/bin/pi-bg" diff "$id" >/dev/null 2>&1; then
  echo "diff accepted a running job" >&2; exit 1
fi
rm "$BG/$id.process"
out=$(PI_BG_DIR="$BG" "$ROOT/Pi/bin/pi-bg" ls)
[[ $out == UNKNOWN* ]]
if PI_BG_DIR="$BG" "$ROOT/Pi/bin/pi-bg" diff "$id" >/dev/null 2>&1; then
  echo "diff accepted an identity-unknown job" >&2; exit 1
fi
printf 'wrong\n' > "$BG/$id.process"
out=$(PI_BG_DIR="$BG" "$ROOT/Pi/bin/pi-bg" ls)
[[ $out == UNKNOWN* ]]
printf '%s\n' 999999 > "$BG/$id.pid"
out=$(PI_BG_DIR="$BG" "$ROOT/Pi/bin/pi-bg" ls)
[[ $out == done* ]]

printf '%s\n' '{"type":"message_end","message":{"role":"assistant","content":[{"type":"text","text":"safe\u001b]0;owned\u0007\u001b[31mred\u001b[0m\r"}]}}' > "$BG/$id.jsonl"
out=$(PI_BG_DIR="$BG" "$ROOT/Pi/bin/pi-bg" get "$id")
[[ $out == safered ]]
[[ $out != *$'\033'* ]]

AG=$(mktemp -d); BIN=$(mktemp -d); BG2=$(mktemp -d)
trap 'rm -rf "$BG" "$AG" "$BIN" "$BG2"' EXIT
mkdir -p "$AG/agents" "$AG/extensions"
printf '%s\n' '---' 'name: worker' 'model: test/model' '---' 'SYSTEM PRIVATE WORDS' > "$AG/agents/worker.md"
: > "$AG/extensions/fast-mode.ts"
cat > "$BIN/pi" <<'EOF'
#!/usr/bin/env bash
sleep 30 &
printf '%s\n' "$!" > "$CAPTURE_CHILD"
exit 0
EOF
chmod +x "$BIN/pi"
if PATH="$BIN:$PATH" PI_CODING_AGENT_DIR="$AG" PI_BG_DIR="$BG2" "$ROOT/Pi/bin/pi-bg" run worker --local --no-wt 'TASK PRIVATE WORDS' >/dev/null 2>&1; then
  echo "pi-bg accepted task text in argv" >&2; exit 1
fi
job=$(printf '%s\n' 'TASK PRIVATE WORDS' | CAPTURE_CHILD="$BG2/child.pid" PATH="$BIN:$PATH" PI_CODING_AGENT_DIR="$AG" PI_BG_DIR="$BG2" "$ROOT/Pi/bin/pi-bg" run worker --local --no-wt)
pid=$(cat "$BG2/$job.pid")
command=$(ps -p "$pid" -o command=)
[[ $command != *'TASK PRIVATE WORDS'* && $command != *'SYSTEM PRIVATE WORDS'* ]]
out=$(PI_CODING_AGENT_DIR="$AG" PI_BG_DIR="$BG2" "$ROOT/Pi/bin/pi-bg" ls)
[[ $out == RUNNING* ]]
child=$(cat "$BG2/child.pid")
kill -0 "$child"
PI_CODING_AGENT_DIR="$AG" PI_BG_DIR="$BG2" "$ROOT/Pi/bin/pi-bg" kill "$job" >/dev/null
sleep 0.1
! kill -0 "$pid" 2>/dev/null
[ -z "$child" ] || ! kill -0 "$child" 2>/dev/null

echo "pi-bg safety smoke: pass"
