#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
client=""
target=""
dry_run=1

usage() {
  cat <<'USAGE'
Usage:
  scripts/install.sh --client <claude-cli|codex-app|claude-code-desktop> --target <path> [--dry-run] [--yes]

Default mode is --dry-run.
Use --yes only after reviewing the planned writes.
The installer copies rendered ShahinKit files into the target folder; it does not edit live app config files in place.
USAGE
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --client)
      client="${2:-}"
      shift 2
      ;;
    --target)
      target="${2:-}"
      shift 2
      ;;
    --dry-run)
      dry_run=1
      shift
      ;;
    --yes)
      dry_run=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "${client}" in
  claude-cli|codex-app|claude-code-desktop)
    ;;
  "")
    printf 'missing --client\n' >&2
    usage >&2
    exit 2
    ;;
  *)
    printf 'unsupported client: %s\n' "${client}" >&2
    exit 2
    ;;
esac

if [[ -z "${target}" ]]; then
  printf 'missing --target\n' >&2
  usage >&2
  exit 2
fi

printf 'ShahinKit install plan\n'
printf 'client: %s\n' "${client}"
printf 'target: %s\n' "${target}"
printf 'planned writes:\n'
printf -- '- %s/shared\n' "${target}"
printf -- '- %s/client\n' "${target}"
printf -- '- %s/SHAHINKIT_RENDER.md\n' "${target}"

if [[ "${dry_run}" -eq 1 ]]; then
  printf 'dry-run: no files written\n'
  printf 'rerun with --yes after reviewing the target\n'
  exit 0
fi

if [[ -e "${target}" ]]; then
  printf 'refusing to install into existing target: %s\n' "${target}" >&2
  printf 'choose an empty path or render manually with scripts/render-client-config.sh\n' >&2
  exit 3
fi

"${repo_root}/scripts/render-client-config.sh" --client "${client}" --output "${target}"

printf 'installed render to %s\n' "${target}"
