#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd -P)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/bin" "$TMP/agent/extensions"
: > "$TMP/agent/extensions/fast-mode.ts"
cat > "$TMP/bin/pi" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "$CAPTURE.args"
for arg in "$@"; do
  case "$arg" in @*) path=${arg#@}; printf '%s\n' "$path" > "$CAPTURE.path"; cat "$path" > "$CAPTURE.body";; esac
done
printf 'safe\033]0;owned\007\033[31mred\033[0m\r\n'
sleep 0.3
EOF
chmod +x "$TMP/bin/pi"
out=$(printf '%s\n' 'TASK PRIVATE WORDS' | CAPTURE="$TMP/capture" PATH="$TMP/bin:$PATH" PI_CODING_AGENT_DIR="$TMP/agent" \
  "$ROOT/Pi/bin/luna")
[ "$out" = safered ]
! grep -q 'TASK PRIVATE WORDS' "$TMP/capture.args"
grep -q '^Task: TASK PRIVATE WORDS$' "$TMP/capture.body"
prompt=$(cat "$TMP/capture.path")
[ ! -e "$prompt" ]
if CAPTURE="$TMP/reject" PATH="$TMP/bin:$PATH" PI_CODING_AGENT_DIR="$TMP/agent" \
  "$ROOT/Pi/bin/luna" 'TASK PRIVATE WORDS' >/dev/null 2>&1; then
  echo "luna accepted task text in argv" >&2; exit 1
fi
printf '%s\n' 'SECOND PRIVATE TASK' | CAPTURE="$TMP/second" PATH="$TMP/bin:$PATH" PI_CODING_AGENT_DIR="$TMP/agent" \
  "$ROOT/Pi/bin/luna" >/dev/null &
wrapper=$!
sleep 0.05
command=$(ps -ww -p "$wrapper" -o command=)
[[ $command != *'SECOND PRIVATE TASK'* ]]
wait "$wrapper"
echo "luna prompt-file smoke: pass"
