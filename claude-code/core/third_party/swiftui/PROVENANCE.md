# SwiftUI Pro provenance and reconciliation

## Locked upstream

- Repository: `https://github.com/twostraws/SwiftUI-Agent-Skill.git`
- Commit: `36163743db0f7bc6d64723f0bc0a8fa69d08fc4b`
- Historical skill version: `1.0`
- Author: Paul Hudson
- License: MIT; exact notice in `LICENSE`

The selected upstream source is the `swiftui-pro` skill and its nine reference
files. Before reconciliation, the installed v1.0 source was checked against
the immutable upstream selection recorded in `LOCK.json`: the selected-file
SHA-256 values match. The repository `main` branch is not used for this vendor
because it later changed the skill metadata to v1.1.

## Selected portable scope

Vendored source is limited to declarative Markdown guidance:

```text
skills/swiftui-pro/SKILL.md
skills/swiftui-pro/references/{accessibility,api,data,design,hygiene,navigation,performance,swift,views}.md
```

Upstream `agents/` configuration and icon assets are excluded. They are
host-specific metadata or presentation assets, not portable review guidance.
No upstream executable, installer, package lifecycle, network client,
subprocess launcher, environment/config reader, telemetry, cache, or persistent
state is vendored.

## Derived changes

1. `SKILL.md` frontmatter is reduced to canonical `name` and `description`.
2. The project deployment target, supported platforms, toolchain, architecture,
   conventions, and approved dependencies are authoritative. API suggestions
   are availability-gated; no future platform or toolchain is assumed.
3. Preview rendering and documentation lookup are optional and unavailable-safe:
   use them only when available and approved, otherwise review source and state
   the verification limit. GUI applications are never launched or automated.
4. Companion-skill links and requirements are removed. This skill is complete
   on its own.
5. Guidance removes implicit network activity, external mutation, automatic
   installation, personal paths/data, credentials, and host-specific tooling.
6. The portable approval sentence is retained verbatim in `SKILL.md`.
7. `RoundedRectangle` guidance follows the supported SDK declarations, whose
   public initializers default to continuous cornering, while preserving the
   project's target/toolchain as authority.
8. The unchanged MIT notice is copied beside the installed skill so attribution
   travels with the artifact.

`LOCK.json` records the original selected-file hashes and hashes every shipped
file except itself. `tests/test_vendor.py` verifies both sets and the portable
scope. The lock excludes its own digest because a manifest cannot stably hash
itself.

## Static-audit result

Pass. The shipped payload is Markdown only. Its test rejects platform/toolchain
assumptions, remote links and command examples, companion-skill references,
personal paths, secrets, GUI automation, package installation, and implicit
external activity.
