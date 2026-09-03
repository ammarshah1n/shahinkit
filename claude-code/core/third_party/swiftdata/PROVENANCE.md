# SwiftData Pro provenance and reconciliation

## Locked upstream

- Repository: `https://github.com/twostraws/SwiftData-Agent-Skill.git`
- Source skill: `swiftdata-pro` v1.0
- Commit: `be7db1864a3a27f0fc1fa7a21d55536370f37818`
- Tree: `d2d5ad0172937c0ccb43fa8f6e76218e33258c19`
- License: MIT; exact upstream notice is preserved in `LICENSE`.

A fresh detached checkout was verified at the locked commit and tree before adaptation. `LOCK.json` records SHA-256 digests of the selected upstream files and every shipped file. Its own digest is excluded because a manifest cannot stably hash itself.

## Selected portable scope

The selected upstream source is `swiftdata-pro/SKILL.md` and its five Markdown references: core rules, predicates, CloudKit, indexing, and class inheritance. The full upstream MIT notice is retained unchanged and copied beside the installed skill so attribution travels with the artifact.

Excluded upstream material: repository documentation, code-of-conduct text, agent configuration, and branding assets. None is required for the portable skill. The shipped payload is declarative Markdown plus a local verification test; it has no executable installer, package lifecycle, network client, secret/config reader, telemetry, GUI automation, or persistent state.

## Derived changes

1. Frontmatter is reduced to the canonical `name` and `description` fields.
2. The project's declared deployment target and existing architecture govern all advice. The upstream Swift 6.2 baseline is not imposed.
3. Indexing, model inheritance, and `#Unique` remain version-gated. When an API is unavailable for the declared target, the skill states the constraint and uses a compatible alternative rather than raising the target.
4. CloudKit guidance applies only to projects already configured for it; it does not enable capabilities or create external resources.
5. References to separate SwiftUI or Swift-concurrency skills are removed. This vendor has no companion-skill dependency.
6. Installation, external action, network, GUI-automation, machine-path, credential, and personal-project content is absent. The skill retains the repository's exact portable safety sentence.

## Static-audit result

Pass. The local test verifies the upstream pin and selected-file digests, full license digest, complete shipped-file digest map, canonical frontmatter, version/architecture guards, unavailable-capability handling, portable safety sentence, and absence of companion-skill, installation, GUI-automation, network-execution, machine-path, and credential patterns.
