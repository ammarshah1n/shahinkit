---
name: swiftdata-pro
description: Review or improve SwiftData code while preserving the project's declared deployment target and data architecture. Use when reading, writing, or reviewing SwiftData code.
---

Write and review SwiftData code for correctness, modern API usage, and project conventions. Report only genuine problems; do not nitpick or invent issues.

## Operating boundaries

- Read the project's declared deployment targets, supported platforms, and existing data architecture before making a recommendation. The project's declared deployment target and architecture are authoritative.
- Do not raise a deployment target, migrate persistence, add a dependency, or restructure the data layer unless the user explicitly asks.
- Apply version-gated guidance only when the project's declared target supports it. If a needed capability is unavailable for that target, state the constraint and offer a compatible alternative; do not claim it is available.
- Use only CLI tools and project files. Do not automate GUI applications; the human opens apps.
- Do not make network calls or mutate external systems unless the user explicitly approves that action.
- Never automatically install, commit, push, publish, submit, send, book, pay, delete, or mutate an external system. Require explicit user approval.

## Review process

1. Check core SwiftData concerns using `references/core-rules.md`.
2. Check that predicates are safe and supported using `references/predicates.md`.
3. If the project is already configured for CloudKit, check its constraints using `references/cloudkit.md`.
4. Only when the declared target supports the required platform version, check indexing with `references/indexing.md` and class inheritance with `references/class-inheritance.md`.

For partial work, load only the relevant reference files.

## Core instructions

- Use SwiftData where the existing project architecture uses it or the user requests it. Do not propose a storage migration solely to apply this skill.
- Use the project's established concurrency and feature structure. Do not introduce third-party frameworks without explicit user approval.
- Prefer explicit saves when correctness depends on persistence; follow the project's error-handling conventions.

## Output format

For a review, organize findings by file. For each issue:

1. State the file and relevant line(s).
2. Name the rule being violated.
3. Show a brief before/after code fix.

Skip files with no issues. End with a prioritized summary of the most impactful changes to make first.

For code changes, apply the same rules directly and report the changed files and any target-version constraint.

## References

- `references/core-rules.md` — autosaving, relationships, delete rules, property restrictions, and fetch optimization.
- `references/predicates.md` — supported predicate operations, runtime hazards, and unsupported methods.
- `references/cloudkit.md` — constraints for projects already configured to use CloudKit.
- `references/indexing.md` — conditional database indexing for supported deployment targets.
- `references/class-inheritance.md` — conditional model subclassing for supported deployment targets.
