#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
status=0

ok() {
  printf 'ok: %s\n' "$1"
}

warn() {
  printf 'warn: %s\n' "$1"
}

fail() {
  printf 'fail: %s\n' "$1"
  status=1
}

check_command() {
  local name="$1"
  if command -v "${name}" >/dev/null 2>&1; then
    ok "command ${name}"
  else
    fail "missing command ${name}"
  fi
}

check_optional_command() {
  local name="$1"
  local label="$2"
  if command -v "${name}" >/dev/null 2>&1; then
    ok "optional ${label}: ${name}"
  else
    warn "optional ${label} not found: ${name}"
  fi
}

check_dir() {
  local path="$1"
  if [[ -d "${repo_root}/${path}" ]]; then
    ok "directory ${path}"
  else
    fail "missing directory ${path}"
  fi
}

check_file() {
  local path="$1"
  if [[ -f "${repo_root}/${path}" ]]; then
    ok "file ${path}"
  else
    fail "missing file ${path}"
  fi
}

printf 'ShahinKit doctor\n'
printf 'repo: %s\n' "${repo_root}"

for command_name in git bash find sed rg; do
  check_command "${command_name}"
done

for required_dir in shared clients templates scripts bin; do
  check_dir "${required_dir}"
done

check_file "README.md"
check_file "shared/instructions/core.md"
check_file "shared/instructions/safety.md"
check_file "shared/instructions/memory-protocol.md"
check_file "shared/instructions/handoff-protocol.md"
check_file "shared/skills/deep-idea/SKILL.md"
check_file "shared/skills/new-idea/SKILL.md"
check_file "shared/skills/deep-plan/SKILL.md"
check_file "shared/skills/skill-builder/SKILL.md"
check_file "shared/memory/basic-memory.config.template.json"
check_file "shared/memory/claude-mem.config.template.md"

check_optional_command "codex" "Codex CLI"
check_optional_command "claude" "Claude Code CLI"
check_optional_command "basic-memory" "Basic Memory CLI"
check_optional_command "claude-mem" "Claude Memory CLI"

if [[ "${status}" -eq 0 ]]; then
  ok "doctor passed"
else
  fail "doctor found required issues"
fi

exit "${status}"
