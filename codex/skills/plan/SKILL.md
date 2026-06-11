---
name: plan
description: Plan one non-trivial change or one validated idea with memory, file grounding, review, and an approval gate.
---

# Plan

Use this for one non-trivial feature, fix, refactor, or implementation plan.

## Codex Adaptation

Codex invokes this skill by name in plain text. Do not depend on Claude-only slash commands or approval primitives. Ask concise plain-text questions only when a decision materially changes the plan and cannot be discovered locally.

## Principles

- Ground the plan in real files and current state.
- Parallelize by dependency graph, not enthusiasm.
- No duration estimates.
- No vague deferrals.
- Verification must be explicit.
- Stop before implementation until the plan is approved.

## Phase 0: Intake

Capture:

- goal;
- proof user;
- success criteria;
- rejection criteria;
- constraints;
- whether the user wants planning only or approved-plan execution.

Classify the work:

- `IDEA`: new surface or immature repo. Use the idea front.
- `CHANGE`: existing code or established project. Use the change front.

## Phase 1: Discovery

For `IDEA`:

- retrieve configured memory;
- inspect existing repo/scaffold if any;
- identify alternatives and reasons not to build;
- write PRD/build-context notes if the idea survives.

For `CHANGE`:

- retrieve configured memory;
- inspect instructions, manifests, entry points, tests, and relevant source files;
- build a file/symbol map;
- identify side effects and shared state.

Ask only questions that materially change the plan and cannot be answered from local context.

## Phase 2: Draft

The plan must include:

- summary;
- affected interfaces or behavior;
- dependency graph;
- parallel batch schedule;
- execution lane per batch;
- verification commands;
- named human actions when needed.

## Cost-Aware Execution Lanes

- `INLINE`: lead agent does it directly. Use for small or tightly coupled work.
- `CHEAP_WORKER`: deterministic extraction, inventory, or bulk mechanical edits.
- `STRONG_WORKER`: contained implementation from a clear spec.
- `LEAD_ONLY`: architecture, high-risk correctness, migrations, auth, payment, data loss, or ambiguous requirements.

Do not use strong workers for small mechanical tasks.

## Phase 3: Review

Review the plan for:

- missed files or call sites;
- missing verification;
- data loss or partial failure;
- security and privacy issues;
- overengineering;
- user outcome mismatch.

Fix accepted findings before presenting the final plan.

## Phase 4: Approval Gate

Present the final plan in chat. If the host supports a plan-rendering block, use it. Wait for explicit approval unless the user has already pasted an approved plan and asked for implementation.
