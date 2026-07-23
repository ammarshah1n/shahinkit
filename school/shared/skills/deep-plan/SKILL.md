---
name: deep-plan
description: Plan a non-trivial feature or refactor in a mature repository through memory-first, evidence-backed codebase mapping, scoped parallel exploration, review, and explicit GO before implementation.
---

# Deep Plan

Use for mature repositories, unfamiliar or high-blast changes, and substantial refactors. This skill plans; it does not implement before explicit GO.

## Mapping workflow

1. Set goal anchor. Detect project identity and retrieve canonical project context and durable memory.
2. Orient from available index, repository structure, manifests, and bounded symbol search. Verify index candidates against live source.
3. Produce scope manifest: included directories, exclusions, tracked symbols, uncertainty flags, and confidence. Exclude generated, vendor, build-output, and cache paths unless request requires them.
4. Build one shared cross-reference registry for symbols, callers, imports, reverse dependencies, tests, and boundary crossings.
5. Explore included areas in parallel. Each explorer records relevant files, exported interfaces, imports, shared state, side effects, tests, and scope alerts. Explorers consume shared registry rather than repeating broad search.
6. Escalate uncovered alert areas in bounded rounds. Low confidence triggers broader mapping. Merge findings into codebase map.
7. Pass map completeness gate: every proposed touched existing file is mapped; dependency chain, side effects, tests, alerts, confidence, and unresolved uncertainty are explicit. Do not plan from incomplete map.

## Planning workflow

1. Select `research=none|fast|deep|hybrid` and resolve external decision-changing unknowns before locking affected decisions. `research=none` requires stable local evidence and is prohibited for integrity-critical or route-changing facts, including API, pricing, limits, legal, compliance, auth, sync, data-loss, or architecture assumptions.
2. Compare approaches and choose simplest anchor-aligned path.
3. Draft plan with dependency graph, parallel-batch schedule, role assignments, acceptance criteria, failure-path invariants for integrity-critical work, automated verification gates, and named human actions.
4. Produce spec-drift and delete/merge tables. Contradiction, unjustified component, or missing mapped dependency blocks GO.
5. Obtain independent adversarial review; controller adjudicates every finding. Revalidate no estimates, no deferrals, complete graph, parallelism, and verification after revisions.
6. Present map, plan, review evidence, claim ledger, and explicit GO gate. Implementation starts only after GO.

## Adapter capability contract

Host adapters may provide code indexes, isolated explorers, plan linting, and approval UI. Missing capability narrows claims, never verification standards.
