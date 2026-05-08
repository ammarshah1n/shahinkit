#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
client=""
output=""
force=0

usage() {
  cat <<'USAGE'
Usage:
  scripts/render-client-config.sh --client <claude-cli|codex-app|claude-code-desktop> --output <path> [--force]

Renders a ShahinKit client package into a reviewable output folder.
Refuses to overwrite an existing output folder unless --force is provided.
USAGE
}

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --client)
      client="${2:-}"
      shift 2
      ;;
    --output)
      output="${2:-}"
      shift 2
      ;;
    --force)
      force=1
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

if [[ -z "${output}" ]]; then
  printf 'missing --output\n' >&2
  usage >&2
  exit 2
fi

if [[ -e "${output}" && "${force}" -ne 1 ]]; then
  printf 'refusing to overwrite existing output: %s\n' "${output}" >&2
  printf 'rerun with --force after reviewing the path\n' >&2
  exit 3
fi

if [[ -e "${output}" ]]; then
  rm -rf -- "${output}"
fi

mkdir -p "${output}"
mkdir -p "${output}/client"

cp -R "${repo_root}/shared" "${output}/shared"
cp -R "${repo_root}/clients/${client}/." "${output}/client/"

cat > "${output}/SHAHINKIT_RENDER.md" <<EOF
# ShahinKit Render

- Client: \`${client}\`
- Source: ShahinKit repository
- Includes:
  - \`shared/\`
  - \`client/\`

Review these files before installing. This render does not modify live Claude,
Codex, desktop, memory, or vault configuration.
EOF

printf 'rendered %s adapter to %s\n' "${client}" "${output}"
printf 'review %s/SHAHINKIT_RENDER.md before installing\n' "${output}"
