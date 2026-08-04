# Delegation

## Controller-Controlled Workflow Default

- The controller ({{CONTROLLER_MODEL}}) owns creative brainstorming, architecture calls, routing, final synthesis, final quality/taste review, and final acceptance.
- Delegation is allowed only when the result is bounded and can be independently checked before use.
- Delegate safely: repo maps, unknown enumeration, source extraction, bounded implementation from an exact spec, deterministic plumbing, tests from explicit invariants, and adversarial review.
- Never delegate: open-ended creativity, product taste, architecture decisions, final synthesis, final acceptance, integrity-critical code/data-loss/privacy/legal/security decisions, or anything where a mistake cannot be caught by deterministic checks.
- Cheap fan-out uses approved real worker routes through `{{WORKER_CMD}}`; do not use fake aliases that only look like workers.

## Lanes

| Lane | Owns | Route |
|---|---|---|
| Controller | Architecture, taste, final synthesis, acceptance, integrity-critical judgement | `{{CONTROLLER_MODEL}}` in the main session |
| Executor | Bounded implementation, review, tests, deterministic plumbing from exact spec | `{{WORKER_CMD}}` |
| Grunt | Mechanical extraction, mapping, formatting, search, repetitive edits | `{{GRUNT_MODEL}}` |
| Research | Reading/current facts/source discovery | `{{RESEARCH_MODEL}}` |

## Spec-Drift STOP Rule

Before GO, produce:
1. Spec-drift table comparing user ask vs anchor vs code facts vs plan.
2. Delete/merge table for abstractions/components.

Contradictions or unjustified components block GO.

## Context Isolation Rationale

Token savings come from:
- Cheaper model on grunt work.
- Context isolation: a worker burns its own context and returns only a conclusion.

Context isolation is not a license to outsource judgement. Controller reads the returned conclusion, checks it against the source/spec, and decides what lands.

## Worker Acceptance

- Subagent output = raw conclusions/data, not narration.
- Re-verify subagent "done"/"tests pass" claims before accepting.
- The instance/model that authored the code does NOT declare it GREEN.
- A step is "done" only when it clears the gate: failure-path invariant tests exist, executed, and passed; bugs turned into regression tests.
- Any claim without an observed result is labelled `UNVERIFIED` and cannot support GO/done.

## Research Rule

`research=none` is invalid for integrity-critical assumptions about APIs, pricing, limits, legal/compliance, auth, sync, data loss, or architecture.
