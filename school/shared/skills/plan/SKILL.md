---
name: plan
description: Plan one non-trivial change or new capability. Classifies idea versus change, retrieves memory first, selects research, writes a dependency-ordered plan, obtains adversarial review, and waits for explicit GO before implementation.
---

# Plan

Use for one non-trivial request. This skill plans; it does not implement before explicit GO.

## Anchor and intake

1. Write an `ANCHOR`: outcome, proof-user, success evidence, and reject condition. Treat it as a test for every decision.
2. Challenge framing: state no-build, buy, reuse, or smaller alternatives and evidence that would reverse the proposed direction.
3. Retrieve canonical project context and durable memory before repository research or external research. Record relevant decisions, constraints, age, and gaps.
4. Classify work:
   - `IDEA`: net-new or immature surface. Run idea front.
   - `CHANGE`: identifiable existing surface. Run change front.
   - If unclear, inspect enough to classify and state decision.
5. Select `research=none|fast|deep|hybrid`. Record a Research Decision Table: unknown, why it changes plan, source, mode, owner, and lock condition. `none` requires local stable evidence; it is invalid for integrity-critical API, pricing, limits, legal, compliance, auth, sync, data-loss, or architecture assumptions.

## Fronts

### Idea front

Define proposition, proof-user, adoption evidence, and kill criterion. Research whether to build before designing how. Check reuse, integration, fork, and buy alternatives. Produce a concise PRD/build context with non-goals.

Validation may end with `DON'T-BUILD` or `NOT-NOW`. Do not force a build plan when adoption, differentiation, or evidence fails.

### Change front

Map relevant files, callers, tests, dependencies, shared state, side effects, and high-risk boundaries. Scale mapping to blast radius. Verify index results against live source. For broad or unfamiliar changes, use scoped parallel exploration and merge findings into one codebase map before planning.

## Shared planning spine

1. Compare credible approaches, including simplest path. State trade-offs, failure modes, and recommendation.
2. Draft concise plan with:
   - anchor, scope, locked decisions, open forks, and research evidence;
   - dependency graph containing every step;
   - parallel-batch schedule; serialize only real dependencies;
   - per-step owner role: `controller`, `research`, `implementation`, `review`, or `mechanical`;
   - acceptance criteria and automated verification; integrity-critical steps include explicit failure-path invariants;
   - named human actions for real-world blockers.
3. No estimates. No deferrals. Resolve work in scope or name exact human blocker.
4. Before review, produce:
   - spec-drift table: user request versus anchor versus evidence versus plan;
   - delete/merge table: existing and proposed components, remove/merge/keep decision, and reason.
   Contradiction, unjustified scope, or duplicate abstraction blocks GO.
5. Obtain independent adversarial review for plan gaps, failure modes, user-outcome fit, and over-engineering. Controller adjudicates every finding; reviewers do not merge changes.
6. Re-run structural checks after revisions: no estimates, no deferrals, complete dependency graph, parallel batches, acceptance criteria, and verification gates.

## Correctness gate

For each integrity-critical guarantee, define testable invariants before implementation. Include relevant partial failure, duplicate, empty, oversized, out-of-order, concurrency, cleanup, and recovery cases. A different reviewer verifies executed results. Author claims alone are `UNVERIFIED`. Every confirmed bug gains regression coverage.

## GO gate

Present final reviewed plan, claim-verification ledger, unresolved forks, named human actions, spec-drift table, and delete/merge table. Wait for explicit `GO` before implementation. Re-check anchor at GO. If host lacks an approval mechanism, explicit chat `GO` is required.

## Adapter capability contract

Host adapters may provide memory retrieval, source search, current-fact research, isolated workers, plan linting, artifact rendering, and approval UI. Missing capability must be recorded as unavailable; never replace it with an unsupported claim.
