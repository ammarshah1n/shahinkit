#!/usr/bin/env bash
set -euo pipefail

shahinkit_home="${SHAHINKIT_HOME:-.shahinkit}"
project_root="${SHAHINKIT_PROJECT_ROOT:-.}"
track="${SHAHINKIT_TRACK:-default}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
safe_track="$(printf '%s' "${track}" | tr -cs 'A-Za-z0-9_.-' '-')"
snapshot_dir="${shahinkit_home}/snapshots"
snapshot_path="${snapshot_dir}/${timestamp}-${safe_track}.md"

echo "precompact-snapshot: track=${track}"
echo "planned reads:"
echo "- shared/handoff/NEXT.md"
echo "- shared/handoff/BUILD_STATE.md"
echo "- shared/handoff/SESSION_LOG.md"
echo "planned writes:"
echo "- ${snapshot_path}"

cd "${project_root}"

if [[ "${SHAHINKIT_WRITE_SNAPSHOT:-0}" != "1" ]]; then
  echo "precompact-snapshot: dry run; set SHAHINKIT_WRITE_SNAPSHOT=1 to write"
  exit 0
fi

mkdir -p "${snapshot_dir}"
{
  echo "# Precompact Snapshot"
  echo
  echo "- Track: ${track}"
  echo "- Created UTC: ${timestamp}"
  echo "- Reviewed sources:"
  echo "  - shared/handoff/NEXT.md"
  echo "  - shared/handoff/BUILD_STATE.md"
  echo "  - shared/handoff/SESSION_LOG.md"
  echo
  echo "## Resume Point"
  echo "- Next action: TODO"
  echo "- Open decision: TODO"
  echo "- Verification needed: TODO"
} > "${snapshot_path}"

echo "precompact-snapshot: wrote ${snapshot_path}"
