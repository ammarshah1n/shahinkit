---
name: audit-tool
description: Use when evaluating an external tool, plugin, service, or repository before adding it.
---

# Audit Tool

1. Identify source, maintainer, license, permissions, data flow, dependencies, install hooks, network targets, and recent maintenance from available evidence.
2. Inspect supplied files or approved public sources for executable downloads, credential access, unsafe command execution, opaque binaries, telemetry, and abandoned dependencies.
3. Separate verified facts, unknowns, and risk level. Recommend accept, reject, or investigate further with concrete reasons.
4. If required command or service access is unavailable, report that limitation honestly; do not claim an audit passed.
5. Never automatically install, commit, push, publish, submit, send, book, pay, delete, or mutate an external system. Require explicit user approval.
