---
name: delegation-routing
description: Route bounded research, implementation, review, and mechanical work through portable role policy. Use before delegating work or accepting worker output.
---

# Delegation Routing

Read shared delegation and tier policy first. This skill applies those policies; it does not override them.

## Roles

| Role | Owns | May delegate |
|---|---|---|
| `controller` | architecture, product judgement, routing, synthesis, integrity decisions, acceptance | bounded work only |
| `research` | current facts, source discovery, evidence extraction | no final decision |
| `implementation` | exact bounded change and tests | no architecture or acceptance |
| `review` | independent adversarial critique and verification | no merge rights |
| `mechanical` | exact extraction, mapping, formatting, repetitive edits | deterministic work only |

Resolve every role independently through shared role schema. Never inherit one worker role's model or authority from another.

## Route

1. Keep controller-owned: architecture, product taste, final synthesis, final acceptance, privacy/legal/security/data-loss judgement, and mistakes not catchable through deterministic checks.
2. Route source reading and current external facts to `research`; include source, uncertainty, and what decision result changes.
3. Route exact bounded implementation and invariant-based tests to `implementation`.
4. Route independent critique and verification to `review`; author cannot self-grade GREEN.
5. Route enumeration, file maps, formatting, and repetitive deterministic work to `mechanical`.
6. Default downward. Controller-tier delegation requires literal `[CONTROLLER-TIER-JUSTIFIED: reason]` in dispatch prompt and remains controller-reviewed.

## Dispatch and acceptance

Every dispatch states anchor, bounded scope, inputs, allowed writes, expected output, verification command or evidence, and stop condition. Use only approved host adapter worker routes. Do not use aliases that merely resemble worker routes.

Workers return conclusions and evidence, not authority. Re-verify completion and test claims independently. A result is `UNVERIFIED` without observed proof. Integrity guarantees require executed failure-path invariant tests and independent review. Bugs gain regression coverage.

## Research decision

Use `research=none|fast|deep|hybrid`. `none` requires local stable facts. It is invalid for integrity-critical API, pricing, limits, legal, compliance, auth, sync, data-loss, or architecture assumptions. `fast` obtains bounded current facts; `deep` produces decision-grade synthesis; `hybrid` uses breadth then synthesis.

## Adapter capability contract

Host adapters map roles to concrete workers, models, research tools, and review mechanisms. Adapter mappings must preserve role boundaries, independent model resolution, and controller acceptance.
