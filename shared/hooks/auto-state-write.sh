#!/usr/bin/env bash
set -euo pipefail

shahinkit_home="${SHAHINKIT_HOME:-.shahinkit}"
project_root="${SHAHINKIT_PROJECT_ROOT:-.}"
track="${SHAHINKIT_TRACK:-default}"
timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
safe_track="$(printf '%s' "${track}" | tr -cs 'A-Za-z0-9_.-' '-')"
state_dir="${shahinkit_home}/state"
state_path="${state_dir}/${safe_track}.md"

echo "auto-state-write: track=${track}"
echo "planned reads:"
echo "- shared/handoff/NEXT.md"
echo "- shared/handoff/BUILD_STATE.md"
echo "planned writes:"
echo "- ${state_path}"

cd "${project_root}"

if [[ "${SHAHINKIT_AUTO_STATE_WRITE:-0}" != "1" ]]; then
  echo "auto-state-write: dry run; set SHAHINKIT_AUTO_STATE_WRITE=1 to append"
  exit 0
fi

mkdir -p "${state_dir}"
{
  echo
  echo "## ${timestamp}"
  echo "- Track: ${track}"
  echo "- State: session checkpoint requested"
  echo "- Next source: shared/handoff/NEXT.md"
  echo "- Build source: shared/handoff/BUILD_STATE.md"
} >> "${state_path}"

echo "auto-state-write: appended ${state_path}"
