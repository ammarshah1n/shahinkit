#!/usr/bin/env bash
set -euo pipefail

shahinkit_home="${SHAHINKIT_HOME:-.shahinkit}"
project_root="${SHAHINKIT_PROJECT_ROOT:-.}"
track="${SHAHINKIT_TRACK:-default}"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
safe_track="$(printf '%s' "${track}" | tr -cs 'A-Za-z0-9_.-' '-')"
export_dir="${shahinkit_home}/exports"
export_path="${export_dir}/${timestamp}-${safe_track}-manifest.md"

echo "post-session-export: track=${track}"
echo "planned reads:"
echo "- shared/privacy/PUBLIC_EXPORT_CHECKLIST.md"
echo "- shared/privacy/PRIVATE_DATA_EXCLUSIONS.md"
echo "- shared/rag-indexing/REDACTION_CHECKLIST.md"
echo "planned writes:"
echo "- ${export_path}"

cd "${project_root}"

if [[ "${SHAHINKIT_EXPORT_TRANSCRIPT:-0}" != "1" ]]; then
  echo "post-session-export: dry run; set SHAHINKIT_EXPORT_TRANSCRIPT=1 to export"
  exit 0
fi

mkdir -p "${export_dir}"
{
  echo "# Post-Session Export Manifest"
  echo
  echo "- Track: ${track}"
  echo "- Created UTC: ${timestamp}"
  echo "- Transcript content: not included"
  echo "- Required checks:"
  echo "  - Redaction checklist completed"
  echo "  - Private data exclusions applied"
  echo "  - Export allowlist confirmed"
} > "${export_path}"

echo "post-session-export: wrote ${export_path}"
