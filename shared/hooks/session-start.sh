#!/usr/bin/env bash
set -euo pipefail

shahinkit_home="${SHAHINKIT_HOME:-.shahinkit}"
project_root="${SHAHINKIT_PROJECT_ROOT:-.}"
track="${SHAHINKIT_TRACK:-default}"

handoff_next="shared/handoff/NEXT.md"
build_state="shared/handoff/BUILD_STATE.md"
memory_routing="shared/memory/memory-routing.md"

echo "session-start: track=${track}"
echo "planned reads:"
echo "- ${handoff_next}"
echo "- ${build_state}"
echo "- ${memory_routing}"
echo "- ${shahinkit_home}/state/${track}.md"
echo "planned writes: none"

cd "${project_root}"

for path in "${handoff_next}" "${build_state}" "${memory_routing}"; do
  if [[ -f "${path}" ]]; then
    echo "available: ${path}"
  else
    echo "missing: ${path}"
  fi
done

if [[ -f "${shahinkit_home}/state/${track}.md" ]]; then
  echo "available: ${shahinkit_home}/state/${track}.md"
else
  echo "missing: ${shahinkit_home}/state/${track}.md"
fi
