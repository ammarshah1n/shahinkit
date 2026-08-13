---
name: ship
description: "Full pipeline for one task: dependency-graph plan, ponytail-gated scope, then parallel subagent execution with review. Use when asked to ship/build/implement a feature end-to-end with pi as the head agent."
---

# ship — graph plan → subagent fan-out → verify

You are the head agent. You plan and adjudicate; subagents execute.

## 1. Scout
Spawn the `scout` subagent to map the relevant code (files, entry points,
conventions, risks). For trivial single-file tasks, skip scouting and skip
straight to doing the work yourself — a brief that costs more than the work
is waste.

## 2. Graph plan
Write `PLAN.md` in the repo (or task dir):
- Steps as a dependency graph, grouped into WAVES: everything in a wave is
  independent and runs in parallel; wave N+1 may depend only on waves ≤ N.
- Per step: goal, exact files in scope, done-check (a command or observable
  the head agent can verify without trusting the worker's word).
- Ponytail gate on every step before it enters the plan: does it need to
  exist at all → stdlib/native → existing dep → one line → minimum code.
  Cut speculative steps; note cuts in one line each. Never cut validation,
  data-loss protection, security, accessibility, or explicit requirements.
- Mermaid graph of the waves at the top (```mermaid flowchart TD```).
Show the plan and WAIT for the user's go unless they already said to run
without stopping.

## 3. Execute
Per wave: spawn one `worker` subagent per step, in parallel, each with a
self-contained brief (goal + scope files + done-check + relevant scout
context). Workers only touch their scope. Chain-work (diagnose→fix→test on
the same state) stays in ONE worker or in the head agent — never split a
chain across parallel workers.

## 4. Verify + review
After each wave: run every step's done-check yourself. Failures go back to a
fresh worker with the failure output, max 2 retries; on the 2nd same-class
failure, sweep the whole class before retrying. Diffs over ~10 lines get one
`reviewer` subagent pass at the end; apply only findings you judge real.

## 5. Report
Done-checks that passed (with the commands), what was cut by the ponytail
gate, anything source-complete but not shipped. Never claim verified work
that wasn't.
