#!/usr/bin/env bash
set -euo pipefail

shahinkit_home="${SHAHINKIT_HOME:-.shahinkit}"
project_root="${SHAHINKIT_PROJECT_ROOT:-.}"
track="${SHAHINKIT_TRACK:-default}"
route="${SHAHINKIT_MEMORY_ROUTE:-}"

memory_routing="shared/memory/memory-routing.md"

echo "memory-gate: track=${track}"
echo "planned reads:"
echo "- ${memory_routing}"
echo "- ${shahinkit_home}/memory/${route:-<route>}"
echo "planned writes: none"

cd "${project_root}"

if [[ -z "${route}" ]]; then
  echo "memory-gate: set SHAHINKIT_MEMORY_ROUTE to dev, school-university, or client"
  exit 2
fi

case "${route}" in
  dev|school-university|client)
    echo "memory-gate: allowed route ${route}"
    ;;
  *)
    echo "memory-gate: denied route ${route}"
    exit 2
    ;;
esac

if [[ -f "${memory_routing}" ]]; then
  echo "available: ${memory_routing}"
else
  echo "missing: ${memory_routing}"
fi
