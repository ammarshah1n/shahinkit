# Swift Testing Pro provenance and reconciliation

## Locked upstream

- Repository: `https://github.com/twostraws/Swift-Testing-Agent-Skill.git`
- Release tag: `1.0.0` (source version `1.0`)
- Commit: `29921fb187f1165cb8975791c7e11fbb23d03398`
- Tree: `6e46bd7a966ba2e832af3ab7a702800eec7476b4`
- License: MIT; the full MIT notice is preserved verbatim in `LICENSE`.

## Local installed source verification

Before adapting this snapshot, a recursive SHA-256 manifest of all nine
locally installed Swift Testing Pro payload files matched the upstream checkout
at the locked commit path-for-path. The verified payload included the skill,
five references, agent metadata, and two icons; installed aliases resolved to
the same payload. The installed payload is evidence only and is not copied as
an installation dependency.

## Selected portable scope

The portable payload contains the upstream `LICENSE`,
`swift-testing-pro/SKILL.md`, and five reference documents. `LOCK.json` records
both their original upstream hashes and the reconciled shipped-file hashes.

Excluded upstream files:

- `agents/openai.yaml` and icon assets: host metadata and presentation assets
  are unnecessary for a portable documentation skill.
- Root README, code of conduct, and ignore file: repository material outside
  the skill payload.

## Reconciliation

1. `SKILL.md` frontmatter is limited to `name` and `description`.
2. The project configuration and installed toolchain are authoritative. A
   missing Swift Testing capability must be reported as unavailable; toolchains,
   dependencies, and project configuration remain unchanged without explicit
   approval.
3. The exact portable safety sentence is included. The skill does not install,
   commit, push, or mutate external systems automatically.
4. UI-test creation and GUI automation are unavailable for this portable skill.
5. References no longer direct users to companion skills, include live-network
   examples, or demonstrate reads or writes to persistent user settings.
6. Attachment guidance is approval-gated and limited to synthetic,
   non-sensitive test output.
7. `.serialized` guidance now matches Swift Testing semantics: parameterized
   cases and suite-contained tests can be serialized; a lone non-parameterized
   test has no useful parallel work to serialize.
8. The full MIT notice remains unchanged and is also copied beside the installed
   skill so downstream users retain the notice with the artifact.

## Static audit

Pass, completed before local tests. The selected payload is declarative
Markdown plus the MIT license and a local integrity test. It contains no
installer, package lifecycle, network client, external command launcher,
environment or private-config reader, telemetry, persistent runtime state,
live-network example, GUI automation, or automatic external write. Tests read
only the vendored files and do not contact the network.

`LOCK.json` excludes its own digest because a manifest cannot stably hash
itself. Every other file under this vendor root is locked and verified by
`tests/test_vendor.py`.
