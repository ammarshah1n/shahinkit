---
name: plan
description: "Plan one non-trivial code change or net-new capability before implementation. Establishes a goal anchor, selects a research budget, maps the codebase, resolves user-visible forks, writes a dependency-ordered plan, runs adversarial review, and waits for explicit GO."
---

# Plan

Plan one task. Do not implement until the user gives explicit `GO`, unless the
original request already clearly authorized end-to-end autonomous execution.

## Invariants

- The controller owns architecture, product taste, privacy, security, legal,
  data-loss decisions, synthesis, and final acceptance.
- Ask about ambiguous **intent** before planning: user-visible behavior, scope,
  or success criteria. Decide mechanics yourself after inspecting the code.
- No estimates, “later” deferrals, speculative abstractions, or unrequested
  dependencies.
- No GUI automation. Research and verification use CLI/files; otherwise give
  the human click instructions.
- Never commit, push, deploy, pay, book, message, or mutate external systems
  without explicit approval.

## 0. Anchor

Write one sentence describing the user-visible end state. Add concrete
completion checks directly implied by the request.

If `/goal` is available and the user asked to persist a goal, use the native
goal drafting/review flow. Otherwise keep the anchor in `plan.md`; do not invent
a durable goal from an ordinary task.

Classify the task:

- **CHANGE** — modify, fix, or refactor an existing system.
- **IDEA** — introduce a new capability or surface.

Choose and state a research budget near the top of the plan:

| Budget | Use |
|---|---|
| `none` | All load-bearing facts are local, stable, and verified. Never use for API, pricing, auth, sync, legal, migration, or data-loss assumptions. |
| `fast` | A few current facts through a separately configured `web` command on `PATH`. |
| `deep` | One bounded `researcher` subagent for cited multi-source synthesis. |
| `hybrid` | Fast source discovery, then one `researcher` synthesis on the unresolved decision. |

## 1. Load current truth

1. Read repository instructions and the newest `HANDOFF.md` or
   `BUILD_STATE.md` when present.
2. Inspect Git status before attributing dirty files to this session.
3. Search configured local memory when available; treat dated notes as stale
   until checked against current code.
4. For CHANGE work, trace the real flow end to end: entry point, callers,
   persistence, errors, tests, and user-visible surface.
5. For IDEA work, identify the smallest useful slice, existing primitives to
   reuse, and the assumptions that require evidence.

Token-heavy read work may go to up to five independent background `scout`
agents. Each brief must fit one paragraph and request a concrete output shape.
Never delegate architecture or a question that may require user interaction.

## 2. Resolve forks

Ask the user one bundled question only when the answer changes what they will
see, the scope, or the acceptance criteria. Do not ask about filenames,
libraries, naming, test layout, or implementation mechanics; inspect and decide.

Record each decision in the plan. Unknown load-bearing facts stay marked
`UNKNOWN` until verified—never convert uncertainty into a confident assumption.

## 3. Research

Run only the selected budget.

- `fast`: use `web search` for authoritative sources; fetch only pages whose
  snippets do not contain enough detail.
- `deep`: dispatch `researcher` with the exact question, date/version boundary,
  required sources, and uncertainty format.
- `hybrid`: use fast research for breadth, then give the researcher only the
  unresolved decision and candidate sources.

A tool failure is not a research finding. Cite every current external claim in
`plan.md`. Stop researching when each load-bearing decision has enough evidence.

## 4. Draft `plan.md`

Write or replace one plan with this structure:

```markdown
# <task>

**Anchor:** <one user-visible end state>
**Type:** CHANGE | IDEA
**Research:** none | fast | deep | hybrid

## Acceptance criteria
- [ ] <observable completion check>

## Current state
- <verified path/function/contract>

## Decisions and constraints
- <decision — why>

## Dependency graph
- S1 → S2
- S1 → S3
- S2 + S3 → S4

## Steps
### S1 — <outcome> [controller|worker|mechanical]
- Files: `exact/path`
- Change: <specific behavior and contract>
- Depends on: none | Sx
- Verify: `<command>` and <observable result>
- Rollback/data safety: <when relevant>

## Risks and unknowns
- <risk, mitigation, owner>

## GO gate
Reply `GO` to implement this plan, or name changes.
```

Every step names exact files or explicitly marks a file as new. Steps must be
small enough to verify independently. Independent write steps may run in
parallel only when they touch disjoint files. Migrations, auth, money, data-loss,
and external mutations remain controller-owned.

Use the `planner` agent only when a clean context materially improves a long
plan. Its task must contain a complete brief and the controller must review the
result; the planner does not own architecture or acceptance.

## 5. Adversarial review

Dispatch `plan-reviewer` with:

- the path to `plan.md`;
- the exact anchor;
- relevant codebase map or evidence;
- a request for pre-mortem, Ponytail cuts, missing failure paths, ordering
  defects, and unverified assumptions.

The controller adjudicates every finding. Apply valid corrections, reject noisy
ones, and rerun review once only if blocking changes materially altered the
plan. A reviewer never grants GO.

Before presenting the plan, check:

- every acceptance criterion maps to a step and verification;
- every step serves the anchor;
- dependency order is executable;
- no two parallel writes touch the same file;
- rollback/data safety is explicit where needed;
- all external claims are sourced;
- no required work is hidden under “follow-up” or “later.”

## 6. GO and execution

Present the final `plan.md` path, a short scope summary, and the GO gate. Wait for
explicit approval unless autonomous implementation was already authorized.

After GO:

1. Execute dependency order; use `subagent` for bounded work and `pi-bg` for
   parallel worktree-isolated writes.
2. Apply worker patches in the controller checkout and re-verify locally.
3. Run the smallest relevant checks after each step, then the full affected
   suite at the end.
4. Run an independent review for broad or risky diffs.
5. Compare implementation with every acceptance criterion and report evidence,
   not confidence.
6. Update durable handoff/state only when the project’s close protocol requires
   it. Do not commit or push unless explicitly requested.

If implementation exposes a user-visible scope fork, stop and ask. If only a
mechanical detail changes, update `plan.md`, state the assumption, and continue.

## 7. Pipeline feedback

When the plan and implementation diverge because this workflow missed a
systematic planning need—not merely because the code revealed a normal detail—
append one line to `POSTMORTEM.md`:

```text
- [YYYY-MM-DD] <plan slug> — <which phase failed and how> — <candidate fix>
```

Do not write raw transcripts or project-sensitive details into the postmortem.
