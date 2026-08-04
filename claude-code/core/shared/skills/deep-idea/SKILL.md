---
name: deep-idea
description: Research-first planning for a new product, greenfield project, scaffold-only repository, or immature codebase where a codebase map would mislead. Produces validated build context and an explicit graduation gate.
---

# Deep Idea

Use when no mature implementation exists. For established code with real patterns and tests, use `deep-plan`.

## Pre-code workflow

1. Classify repository state: no repository, scaffold-only, immature, or mature. Mature routes to `deep-plan`.
2. Write goal anchor. Retrieve durable memory, inspect only scaffold constraints, and identify decision-blocking unknowns.
3. Run independent orientation, memory retrieval, and idea capture in parallel when supported. Use a source ledger to deduplicate research.
4. Ask only questions external research cannot answer. Start independent research lanes while answers are pending.
5. Research uncertain decision-blocking lanes. Prefer direct and current sources. Evaluate reuse candidates for capability, license, maintenance, security posture, integration cost, and exit risk.
6. Synthesize evidence into research brief, PRD, and build context. Include stack decision, data/state model, integrations, non-goals, open decisions, repository bootstrap needs, dependency graph notes, and source confidence.
7. Run product and over-engineering review. Validation may conclude `DON'T-BUILD` or `NOT-NOW`.

## Planning and graduation

For an approved build proposition, create plan with dependency graph, parallel batches, role assignments, acceptance criteria, verification gates, spec-drift, delete/merge, adversarial review, and explicit GO. No implementation source is written before GO.

Graduation requires: committed build context, specific first milestone, explicit repository/bootstrap state, and evidence whether enough real source exists for `deep-plan`. If not eligible, name exact next action; do not fabricate a codebase map.

## Adapter capability contract

Host adapters may provide memory, isolated research lanes, artifact rendering, and durable artifact storage. Use portable markdown artifacts when richer capabilities are absent.
