---
name: plan
description: "Heavyweight planning engine for ONE task — a code change OR a net-new idea. Use when the user types \"/plan\", \"/idea\", \"plan this\", \"make a plan for X\", or asks to plan before implementing (use /plans instead for a BATCH of multiple plans/ideas). At intake it detects IDEA (net-new capability/surface, greenfield, like the MCP thing) vs CHANGE (modify/fix/refactor existing code), sets a research budget (`research=none|fast|deep|hybrid`; /plan default fast, /idea default hybrid), and runs the matching front — research-first idea-validation+PRD, or depth-dialled codebase discovery — then the shared spine: sets a /goal anchor, searches memory first, routes external unknowns through Comet and/or hyperresearch-codex, drafts a deep-plan-principles plan (no deferrals/estimates, dependency graph + parallel batches) with inline per-step Claude/GPT-5.5/fast execution lanes, lints it, fires GPT-5.5 via real Codex CLI (`codex exec` / `scripts/codex-worker.sh` — never codex:rescue) adversarial review, Fable/Opus adjudicates every finding, asks open questions throughout, renders the HTML reader once, gates on GO via native ExitPlanMode, then implements via feature-workflow — with an autonomous/overnight loop mode that caffeinates, self-heals (retry/workaround/tool-route), and wakes the user to a ready product or an honest blocker list. /idea is a thin alias that pins the idea front. Does NOT replace native plan mode (shift+tab) — it is the orchestrated superset."
---

# /plan — orchestrated planning flow

The heavyweight planning pipeline. Native plan mode (shift+tab) is read-only and a single approval gate — too constrained for research + multi-agent review + multi-round revision. This skill runs the loop in normal mode and only enters native plan mode at the very end so the native approval card + the `ExitPlanMode` principle-gate hook fire on the **final, reviewed** plan. You lose nothing from native plan mode; you gain every layer below.

**Efficiency doctrine:** hide latency behind work, keep cheap work off Opus, never render or review before the plan is structurally valid, and skip machinery that a small task doesn't need. The quality floor (memory-first, lint→0, ≥1 adversarial review *with specific findings* (Phase 4 validity bar — a stub or all-generics wave does not count), Opus adjudication of every finding, the GO gate, deep-plan escalation triggers) is non-negotiable and stays on every path.

## Non-negotiable principles (the six planning principles — `AGENTS.md` §Planning Architecture)

Every plan MUST satisfy all six:
1. **Parallelize by default** given the dependency graph. Serial only where strict dependency forces it.
2. **No deferrals.** Every blocker addressed inline OR surfaced as a NAMED human action with the exact step. Never "later / next session / future work".
3. **No time estimates anywhere.** Sequence work; don't predict duration.
4. **Output a dependency graph + parallel-batch schedule** with per-step acceptance criteria — not a serial todo list.
5. **Verification gates between batches are automated**, never a human-pause checkpoint. Only human pause = final plan acceptance + a real-world BLOCKED_ON_HUMAN action.
6. **"Get shit done" velocity.** Brief structural artifact, not an essay.

The mechanical subset (no estimates, no deferrals, dep-graph present) is enforced by `plan_lint.py` in Phase 3 and again by the `ExitPlanMode` hook in Phase 6. The linter is a floor, never the bar: it matches vocabulary, not meaning. Never reword a deferral to dodge the regex — "queue for a subsequent slate" is still a deferral, and the word "parallel" appearing somewhere is not a dependency graph. The semantic check (is every blocker really addressed inline? are the batch edges real?) is yours, on every pass.

## Path selection (decided in Phase 0c)

| Path | When | Effect |
|------|------|--------|
| **FAST** | small/familiar: ≤5 files, no high-blast-radius surface, OR `/plan --light` | collapses discovery+brainstorm into one pass, one merged review wave, skips nothing load-bearing — see § Fast path |
| **FULL** | non-trivial but not high-risk | full pipeline, dual review only if the plan is large |
| **DEEP** | >5 files / unfamiliar / refactor / touches auth, RLS, billing, sync, intelligence engine, OR `/plan --deep` | FULL + deep-plan's exhaustive Phase 0B–0F map + Map Completeness Checklist before brainstorm |

Any high-blast-radius trigger **forbids** the FAST path — it escalates to DEEP even if the file count is small.

## Research budget (decided in Phase 0d)

Accept `research=none|fast|deep|hybrid` or `--research none|fast|deep|hybrid`.

| Mode | Engine | When |
|------|--------|------|
| **none** | local files + memory only | no external facts; no current docs/pricing/API/legal assumptions |
| **fast** | `/comet` | default for `/plan`; urgent lookups, current facts, source discovery, competitor/API browsing |
| **deep** | `hyperresearch-codex` | load-bearing decisions needing provenance/adversarial critique: model routing, pricing/limits, API behavior, legal/compliance, architecture tradeoffs, workflow design |
| **hybrid** | `/comet` then `hyperresearch-codex` | default for `/idea`; high-blast `/plan`; Comet discovers breadth, HyperResearch produces the decision-grade synthesis |

Fable/Opus owns escalation. GPT-5.5 agents may enumerate external unknowns and write research specs from the code map, but any fact that changes architecture, routing, integrity-critical code, cost/limit policy, or final product direction must be read and adjudicated by Fable/Opus before it lands in the plan.

Guardrails:
- `research=none` is invalid for DEEP plans or integrity-critical surfaces when an external fact could change API behavior, routing, compliance, pricing/limits, auth, sync, billing, or data-loss guarantees.
- If `research=fast` is still pending, continue only with `[UNVERIFIED — Comet pending]` annotations. A load-bearing architecture/routing/integrity claim cannot lock until captured or escalated to HyperResearch.
- If memory or direct official docs resolve the unknown, de-escalate from `deep`/`hybrid` and state why.

## TodoWrite

Create one todo per phase at the start so progress is visible.

---

## Phase 0 — Intake, memory, path, front-fire research

0a. **Set the session goal with `/goal` — first action.** Run the native `/goal` command with the one-line goal + success definition (persisted under `~/.pi/agent/plans/`). Resolve any scope/success ambiguity BEFORE setting it — ask now (AskUserQuestion); cheap before, expensive after. Re-check the goal at the GO gate AND at the autonomy-readiness check (6b). The goal is the north star — every phase below serves it; if a phase's output doesn't move the goal forward, cut it.

   **Frame the goal as a user-outcome end-state, not a task list.** "The proof-user opens the product and solves the problem in 5 clicks" — not "ship the memory backend". The whole plan is judged against whether the *end-state* is reached, so capture the end-state (who does what, how few steps, what "solved" looks like) in the goal itself. A plan that loses sight of the user-outcome becomes a redundant pile of tasks.

   **Write a one-line GOAL ANCHOR and keep it in scope the entire run:**
   ```
   ANCHOR: <end-state outcome> · proof-user: <who must succeed> · rejects-if: <what makes them bounce>
   e.g. ANCHOR: the proof-user solves the problem in ≤5 clicks · proof-user: non-technical user · rejects-if: any CLI / install script / "sketchy"-looking step / zero-config not met
   ```
   The anchor is a **TEST every design choice must pass**, not a slogan. This is the single most important guard against bad plans: the lesson from prior planning sessions is that the agent drifts toward developer-grade complexity (daemons, install scripts, terminal steps) that is technically impressive but the proof-user can never onboard — which makes the entire plan redundant because the proof-user can't run it. Re-assert the ANCHOR at the top of Phase 1 (brainstorm), Phase 4 (review), and 6b. At each, ask: **"Would the proof-user actually use this as-built, or is this developer-grade drift?"** If a step fails the test, it's wrong even if it works (this is the consumer-grade-not-hack-grade rule from `AGENTS.md` § Build Methodology, applied at plan time).

   **Frame challenge before planning.** Before Phase 1, write three lines: (1) strongest reason the user's framing is the wrong problem, (2) simplest no-build / buy / fork answer, (3) evidence that would reverse the plan. If any line is material, resolve it before drafting. Do not agree with the user's framing just because it is stated confidently.

   **Persist the ANCHOR — context is not storage.** The anchor lives on disk, not just in conversation: write it into the `/goal` artifact now, and as an `**Anchor:**` pill at the top of `plan.md` the moment that file exists. Long runs WILL compact the conversation — re-read the anchor from disk at every phase boundary. And include it verbatim in EVERY subagent prompt this run dispatches (planner, reviewers, triage, workers, sweep agents): a reviewer who never sees the anchor critiques internal consistency instead of judging against the proof-user test.

   **Phase checkpoint ledger.** At the end of each phase, append/update a compact ledger in `plan.md`: `phase`, `decision locked`, `evidence path`, `open fork`, `next gate`. At the start of the next phase, re-read this ledger from disk. Conversation memory is not the source of truth on long runs.

0a-bis. **Classify execution mode — INTERACTIVE vs AUTONOMOUS.** Read the goal for autonomy intent ("while I sleep", "wake up and it's done", "caffeinate and go to bed", "unattended", "overnight", "/loop it"):
   - **INTERACTIVE (default)** — a human is present to answer questions + hit the GO gate. Proceed normally.
   - **AUTONOMOUS** — the run must reach the done-state with NO human in the loop. This changes the whole flow:
     1. **Front-load every decision now.** Resolve all forks via AskUserQuestion BEFORE the human leaves — there can be no mid-run question (nothing will answer it). If a fork genuinely can't be pre-resolved, the goal is not fully autonomous; surface that.
     2. The plan must have **zero human-pause gates** except named real-world blockers (and those become hard stops — see 6b).
     3. It will run under **`/loop`** (self-paced) so batches chain to completion without re-prompting.
     4. **Caffeinate** the laptop for the duration (6b / Phase 7).
     5. **Design every batch to be loop-resilient.** Each step carries, in the plan, (a) an automated verification (test/command/observable check) that proves it actually worked, and (b) a retry/workaround policy so a failure doesn't halt the night. Steps must be ordered so independent batches can keep progressing while one is stuck — no single failure freezes the whole run.
   Carry the mode forward; it drives the 6b check and the Phase 7 AFK loop.

0b. **Memory-first (hard rule).** Before any research/web/comet call:
```
Use the configured memory-search tool for the active project and the current problem.
Use the configured research-report search tool for the current problem.
```
If the vault already answers a sub-question, use it — do NOT re-research it. (Use the repository's routing rules; choose the active project for local work.)

0b-bis. **Classify the work — IDEA vs CHANGE (front selector).** This picks which FRONT runs in Phase 1. Both fronts feed the same spine (Phase 2 onward) — detection, both fronts, and the spine all live in THIS skill (single source of truth; no hand-off to another skill).
   - **CHANGE** — modify / fix / refactor / extend code that already exists, with identifiable call-sites. → run the **CHANGE front** (0c + Phase 1 codebase discovery).
   - **IDEA** — net-new capability, product, or surface; no or immature existing implementation; "build a new X", "what if Timed could…", a fresh integration like the MCP thing; greenfield. → run the **IDEA front** (Phase 1-IDEA below). Skip 0c/depth-dial — there's little code to map. (`/idea` is a thin alias that arrives here with IDEA pinned.)
   - **Ambiguous** → if discovery would find substantial relevant existing code, treat as CHANGE; if the repo is scaffold-only / the surface doesn't exist yet, treat as IDEA. Force with `/plan --change` or `/plan --idea` (or just call `/idea`). INTERACTIVE: may ask. AUTONOMOUS: decide by the code-exists test and state the call.

0c. **(CHANGE front only) Assess scale → pick the path** (FAST / FULL / DEEP per the table above). State the path + one-line reason. This gates how Phase 1 runs. (IDEA front skips this.)

0d. **Set research budget + front-fire external-fact research (M1).** Default `/plan` to `research=fast` unless the user specified otherwise; default `/idea` to `research=hybrid`. Identify only the **external-fact** unknowns now — API/library behaviour, current best practice, regulatory/landscape facts: things a brainstorm cannot dissolve. Also scan for load-bearing triggers: auth, RLS, billing, sync, migrations, legal/compliance, pricing/limits, model routing, API quotas, third-party behavior, and any guarantee that can silently lose or double data. For FULL/DEEP plans, dispatch a GPT-5.5 research-spec pass if useful: it reads the mini-map/code map and returns question / why it matters / which plan step it grounds / what answer changes the plan / CRITICAL vs USEFUL. Fable/Opus then chooses the engine:
   - `research=none`: no external jobs unless a CRITICAL integrity assumption appears; then escalate before planning.
   - `research=fast`: dispatch `/comet` per external unknown **immediately** (the `comet` skill submits via CDP and returns a `handoff_path` + `/search/<id>` URL instantly — it does NOT block).
   - `research=deep`: run `hyperresearch-codex` for decision-grade synthesis; no plan locks a load-bearing assumption before Fable/Opus reads the relevant section.
   - `research=hybrid`: use `/comet` first for breadth/source discovery, then run one consolidated `hyperresearch-codex` job to audit and synthesize the claims that change the plan.
   Log each URL/report path. Research should cook while discovery + brainstorm + draft continue where safe.
   - Do NOT front-fire **architecture-choice** unknowns — those may dissolve in brainstorm; they stay gated until after Phase 1.
   - If there are no external-fact unknowns, note "no front-fire research" and continue.

---

## Phase 1 — Front (one of two, picked in 0b-bis)

### Phase 1-IDEA — research-first idea front (net-new work)

Run this instead of codebase discovery when 0b-bis classified IDEA. There's little/no code to map; the risk is building the wrong thing well, so the front validates *what* and *whether* before the spine plans *how*. Built to the same quality bar as the CHANGE front — it then feeds the identical spine (Phase 2 onward), so review/tiering/autonomy/loop all apply unchanged.

1. **Sharpen the idea into a testable proposition.** What capability, for whom, replacing what today? Tie it to the GOAL ANCHOR's proof-user — the idea is only good if the proof-user actually adopts it.
2. **Validate (memory + research).** Memory-first already ran (0b); now fill the gaps. `/idea` defaults to `research=hybrid`: Comet handles landscape/market/tool discovery — does this exist, who does it, why would ours win? — and HyperResearch handles the "should we build this?" synthesis before PRD. Capture findings to basic-memory.
   - Explicitly minor/stable-tech ideas may use `research=fast`, but research is still mandatory before PRD. If the evidence becomes load-bearing or the idea is major/ambiguous, escalate to `hybrid`.

   **Kill criterion — validation must be able to fail.** If the evidence says the proof-user wouldn't adopt it, an existing tool already solves it well enough to not be worth beating, or "why ours wins" can't be said in one sentence — the correct output is a **DON'T-BUILD / NOT-NOW verdict**: write the evidence to basic-memory, present the verdict, stop. No plan. An idea front that always ends in a build plan is theater, not validation.
3. **OSS-to-fork/integrate scan.** Before designing from scratch, scan for existing repos/packages/templates to fork or integrate (this is where `deep-idea`'s technique pays off — invoke `deep-idea` for the heavy repo-research + PRD synthesis rather than duplicating it here; this skill consumes its output). Verify each candidate exists (GitHub API) — never design around an unverified tool.
4. **Produce a PRD / build-context** — the net-new equivalent of a codebase map: the chosen approach, the integration/fork decision, the surfaces it touches, the data model, the "5-click" user path to the proof-user end-state, and the explicit non-goals. This is the input the spine drafts the plan against.

   **PRD gate — attack the WHAT before the spine plans the HOW.** One adversarial wave (dispatch per Phase 4) on the PRD itself, with PRODUCT lenses, not code lenses: right problem? right scope? does the 5-click path survive the proof-user test? is there a 10× simpler buy/fork answer? The Phase 4 plan review carries code lenses (RLS, rollback, migrations) and lands after the PRD has already locked the approach — this gate is the only point where the WHAT gets attacked. Fold findings before step 5.
5. **Brainstorm 2–3 build approaches** (fork X vs build vs integrate Y), trade-offs, failure modes, recommended path — same depth as the CHANGE-front brainstorm.

Then continue to **Phase 2** (the shared spine) with the PRD/build-context standing in for the codebase map.

### Phase 1-CHANGE — discovery + brainstorm (depth-dialled)

**Graphify soft prefilter — CHANGE front, before broad grep/read.** If `graphify-out/GRAPH_REPORT.md` exists, use it as the first-pass repo index before expanding context:
- Read the report summary/god-node/community section only, not the whole graph.
- Run `graphify query "<TASK>" --budget 1200` for FAST/FULL, or let `deep-plan` run the larger query on DEEP.
- Treat Graphify as a candidate-file and side-effect finder only. Do not make architecture decisions from Graphify output until `rg` and direct `Read` verify the live files.
- Filter or mark stale any paths under `.graphifyignore` patterns such as `_native_archive/`, `dist.noindex/`, `docs-archive/`, `.swiftpm/`, `.build/`, or `DerivedData/`. If those dominate the result, note `GRAPHIFY_STALE_OR_POLLUTED`, run `graphify update .` when safe, and fall back to direct `rg`/`Read` for the current plan.
- The mini-map / `CODEBASE_MAP.md` must state `Retrieval: Graphify prefilter + direct verification` or `Retrieval: direct verification only — <reason>`.

**FAST path — one combined pass.** A single Opus pass that reads the relevant files (Grep/Glob/Read) AND outputs 2 approaches with a one-line failure-mode each + the recommended path. Discovery and brainstorm are the same cognitive act here; don't split them into two token-burning passes.

**FULL / DEEP path — split, full strength.**
- **FULL only — scoped discovery (most tasks land here; this step is load-bearing, never skip it):** build a mini-map before brainstorming. Start with the Graphify soft prefilter when available, then Glob the touched area; Grep the call-sites of every symbol the change touches; Read each file to be edited plus its direct callers; list the side-effect surfaces the change brushes (hooks, cron, RLS, Edge Functions, migrations). Fan out `Explore` subagents in parallel for independent areas — **explicit `model: "haiku"` (or `"sonnet"` if judgment needed); never let them inherit the session model**. Output a compact mini-map (files → call-sites → risks) that travels with the plan — the brainstorm, the planner subagent (2a), and the reviewers (Phase 4) all consume it. A FULL plan brainstormed on ad-hoc reading is built on sand.
- **DEEP only:** first run `deep-plan`'s Phase 0B–0F as a sub-step — scope manifest → XREF registry → per-directory explorer subagents → side-effect/`[ALERT]` discovery → merged `docs/CODEBASE_MAP.md` — and pass its **Map Completeness Checklist**. Use deep-plan's cost-tiered subagents (haiku map / sonnet explore) so the mapping is cheap. Do NOT hand-wave native discovery on a big refactor — that's exactly where it under-finds call-sites and the review ends up critiquing a plan built on an incomplete map.
- **FULL + DEEP:** then run the full `superpowers:brainstorming` — intent, 2–3 genuinely different approaches, trade-offs, failure modes, recommended path. Be thorough so later phases refine rather than rebuild.

**Steelman bar (both fronts).** Every alternative must be written so a reviewer could plausibly pick it — each carries one line on "what would make THIS the winner". The reflex failure is one real approach plus two strawmen ratifying a predetermined choice. If no credible second approach exists, say "no credible alternative — here's why" instead of inventing filler.

**Approach choice waits for load-bearing research.** If a front-fired report (0d) bears on WHICH approach wins, don't finalize the recommendation while it cooks: capture it now (one `ScheduleWakeup` re-check) or mark the recommendation **PROVISIONAL — flips if <specific finding>** and re-adjudicate at capture (2b). Locking the architecture before the evidence lands anchors every later phase to a guess.

**After brainstorm — gated research (M1 second wave).** If an architecture-choice unknown survived brainstorm and is still research-worthy, route it through the selected research budget now. Integrity-critical or route-changing assumptions require `research=deep` or `hybrid`, not a compressed cheap-model summary.

---

## Phase 2 — Draft the plan (lanes inline)

2a. **Draft in a clean context — the planner subagent (FULL/DEEP; FAST drafts inline).** By this point the session is full of orchestration chatter — memory searches, comet dispatches, todos, lint output — and 200+ lines of process rules are competing for attention with the design itself. Drafting here is why `/plan` output has run shallower than native plan mode, whose entire context serves one sustained investigate-then-write pass. Recreate that focus deliberately: assemble a **planning brief** and hand it to ONE fresh `Plan` subagent (**explicit `model: "opus"` — the single Agent call allowed to cost real Claude tokens**) whose only job is to write `plan.md`. The brief contains:
   - the GOAL ANCHOR verbatim + the goal/success definition,
   - the mini-map or `CODEBASE_MAP.md` (CHANGE) / the PRD (IDEA),
   - the brainstorm output — chosen approach AND the rejected alternatives with reasons,
   - captured research findings,
   - the six principles, the lane rubric (below), and the exemplar (§ Exemplar) as the format spec.

   Tell it: *"Read every file on the map you need — trust the code over the brief. Write the complete plan.md in ONE sustained pass. Anything unresolvable goes in an OPEN QUESTIONS block — never guess silently."* The orchestrator session owns gates, triage, and merging — not drafting. (FAST path keeps inline drafting: at ≤5 files the context pollution is small and the round-trip isn't worth it.)

   `plan.md` (sibling to the work or under `docs/plans/`) MUST contain:
- **Goal** + one-line success definition.
- **Dependency graph** — which steps block which.
- **Parallel-batch schedule** — Batch 1 (parallel), Batch 2 (depends on B1), … Two steps not dependency-blocked go in the SAME batch.
- **Per-step acceptance criteria** — with **artifact weight following risk**: full failure-path contracts (§Correctness Gate) only for integrity-critical / high-blast steps; a mechanical `[fast]` step gets ONE acceptance line. A plan where every step carries five artifacts buries the reviewer — principle 6 dies and review recall with it.
- **Per-step execution lane, tagged inline as you write each step** — `[Claude]`, `[GPT-5.5]`, or `[fast]`. Don't make this a separate sweep; you already know while authoring a step whether it's mechanical or subtle. Three lanes by task intelligence:

  | Lane | Model · effort | Task shape |
  |------|----------------|------------|
  | **`[Claude]`** (author) | Opus 4.8 | genuine reasoning, cross-file judgment, high blast-radius (auth, RLS, billing, sync, intelligence engine), active auth (`feedback_dont_touch_active_auth`), prompt/model-routing logic, ambiguous spec — **and ALL integrity-critical code** (see below) |
  | **`[GPT-5.5]`** | gpt-5.5 · effort matched | real implementation from a clear spec — contained logic that is NOT integrity-critical |
  | **`[fast]`** | gpt-5.4-mini · low | deterministic, **zero-reasoning** bulk: renames, type/field plumbing, test stubs from a signature, template boilerplate, doc/string edits, format/lint fixes, repetitive find-replace |

  **INTEGRITY-CRITICAL ⇒ `[Claude]` authors, always.** If a step can **silently lose data, corrupt state, mishandle money/auth, or break a claimed guarantee** — data capture, dedup, watermarks/cursors, migrations, sync, ingest, idempotency logic, anything with a "must never miss / must never double" promise — Opus *authors* it. Review cannot undo a flawed design it's anchored to; remove the risk at the source. (The O2 watermark bug shipped because this exact class was mis-tiered to a worker.) When unsure whether something is integrity-critical, treat it as `[Claude]`.

  **Default bias = quality, not cost.** Workers (`[GPT-5.5]`/`[fast]`) are for work whose correct output is *mechanical and verifiable*. They are NOT the default for anything with design or correctness weight. Cost-saving is the exception you justify per step, not the rule. (Earlier framing of "GPT-5.5-with-review as the strong default" was wrong for a quality-first product — corrected here.)

  **Effort principle — "what does the job it's given" (quality is the constraint, speed is the bonus).** Default contained implementation workers to **high**; use **xhigh** for adversarial review, high-blast ambiguity, route-changing analysis, or when high does not do that specific job as well. Never a blanket downgrade or upgrade. Per-step `effort:` via `CODEX_EFFORT`.

  **`[fast]` guardrails:** only exact, deterministic specs with nothing to reason about. ANY ambiguity bumps up. When unsure between `[fast]` and `[GPT-5.5]`, pick `[GPT-5.5]`; when unsure between `[GPT-5.5]` and `[Claude]`, pick `[Claude]`.

  **Every worker diff passes the §Correctness Gate below before it counts as done** — and the gate, not the author, declares GREEN.

- **Named human actions** for any real-world blocker (OAuth, cert, payment, "run X yourself") — never deferred.
- Renderer-friendly conventions: `**Key:** value` pill lines near the top, `#### M0 — title` / `#### H1 — title` for missions/human-actions.

2b. **Capture selected research on-demand (M2).** When the draft actually needs a finding, capture it then — do NOT block on a fixed timer earlier. For `fast`/Comet, run the `comet` skill's bounded "Capture the completed report" path (it runs on **haiku** — summarization, not reasoning) and fold the returned tight findings block. For `deep`/HyperResearch, fold the report's cited conclusions and keep the report path in the plan. Fable/Opus never lets a cheap model compress the fact the plan pivots on: anything that decides an architecture choice, route, cost policy, or integrity-critical step is read directly from the Comet handoff or HyperResearch report. If a report isn't ready yet, do ONE short `ScheduleWakeup` (~300s) re-check rather than pre-committing a long wait, and keep drafting meanwhile. After capture, write durable findings to the configured memory store.

(No HTML render yet — render happens once, after the plan settles. M4.)

---

## Correctness Gate — the GREEN bar (every step, every lane)

The integrity backbone of the whole flow. "GREEN" is **earned by executed tests of the claimed guarantee, graded by something other than the author** — never declared by the implementer, never inferred from a happy-path smoke. A step that hasn't cleared this gate is NOT done, no matter how clean the diff looks.

1. **Contract first (written in the plan step).** State the guarantee as **testable invariants, including the failure cases** — not vague adjectives. "Idempotent" is not a contract; *"if the POST fails → no cursor advances; if input > cap → nothing is silently dropped; empty/truncated/concurrent input is safe"* is. Most bugs hide in the gap between the guarantee the code claims and the property anyone actually tested. Enumerate the failure-mode invariants explicitly: partial failure, network/IO error, empty/oversized/duplicate/out-of-order input, truncation, concurrency, resource cleanup.
2. **Test the contract — red→green, actually executed.** Each invariant (especially the failure-path ones) has a test that runs and passes. A test that *simulates the failure and asserts the invariant holds* must exist. **Done ⇔ the failure-path tests exist and pass** — `node --check` + a happy-path run is NOT done. If you can't test an invariant, say so explicitly and treat the step as unverified, not green.
3. **Independent grading — no self-marked homework.** The instance/model that authored the code does NOT declare it GREEN. A different reviewer runs the tests and signs off. The verdict is "the invariant tests passed," never "the author says so."
4. **Adversarial review hunts the classes tests miss** (this is Phase 4's job, applied per step too): silent data loss, partial-failure state, overflow/truncation, idempotency-under-failure, off-by-one, leaks, scope creep/bloat. For integrity-critical steps the reviewer is Opus.
5. **Compound — every bug becomes a permanent regression test.** When any bug is found (in review, in the loop, in prod), add a test that would have caught it before fixing. The same class can never reship. Log it to the project's learnings.

**The bar, stated plainly:** *code that violates its own stated guarantee cannot ship GREEN, because the guarantee has an executed test.* This is achievable and non-negotiable. ("Zero bugs ever" is not achievable — you can't test invariants nobody imagined; layers 4–5 shrink that residue over time.) In AUTONOMOUS mode this gate is what a worker's output must clear before commit — a worker diff that lacks failure-path tests is PARKED, not committed green.

## Phase 3 — Lint (before any render)

```bash
python3 <path-to-plan-lint.py> <plan.md>
```
- Exit 0 → proceed. Exit 2 → relay violations, rewrite inline to remove every estimate/deferral and add the dep-graph/batch schedule, re-run until exit 0. Never advance a plan that fails the linter. Lint is a deterministic Python script — it costs ~nothing; run it freely, never gate it behind reasoning.

---

## Phase 4 — GPT-5.5 adversarial review

⛔ **DISPATCH MECHANICS (2026-06-10 incident — read before any fan-out).** GPT-5.5 means the **Codex CLI via Bash** — `codex exec` with `CODEX_EFFORT=xhigh` (in a repository with one: `bash scripts/codex-worker.sh`) — running on the Codex subscription, ZERO Claude tokens. Named Agent-tool aliases used to be **Claude agents wearing Codex names** that inherited the session model — one run dispatched "Codex" agents that were all Claude and burned 85% of the Claude limit, including Fable as a discovery agent. They are now haiku-pinned shims that forward to `codex exec`, but **direct Bash `codex exec` is canonical** (one less hop, no shim tax). Rules: (1) EVERY Agent-tool call passes an explicit `model:` — `haiku` for mechanical map/inventory/extraction, `sonnet` for mid-depth exploration, `opus` only for the planner/judgment — **inheriting the session model is a bug**; (2) **never `codex:codex-rescue` for reviews or sweeps** — forwarder stubs (2026-06-09). This section is the canonical dispatch rule; `/plans` and `/mission` defer to it. Fan out reviews in parallel via multiple background Bash `codex exec` calls.

Every review prompt MUST include:
1. the **GOAL ANCHOR verbatim** — reviewers judge every step against the proof-user test, not just internal consistency;
2. the **context the plan was built on** — the mini-map / `CODEBASE_MAP.md` excerpt (CHANGE) or the PRD (IDEA). A reviewer without context can only produce generic findings;
3. the full `plan.md` inline;
4. the framing: *"You ARE the executor — do the review yourself, now. Your FINAL REPLY IS the review content (the sandbox blocks file writes); return findings as a structured list. Do not forward, defer, or punt."*

**Findings validity bar.** A finding counts only if it cites a specific step / file / contract and says what breaks. Generic findings ("consider edge cases", "add error handling") don't count toward the quality floor. If a wave returns only generics or a stub, the review did NOT happen — re-dispatch once with sharper framing; if it fails again, run the wave yourself as Claude and say so honestly.

**How many waves — by size, not by reflex:**
- **Small plan (≤5 steps, no high-blast-radius lane) →** ONE merged wave. A single prompt carries BOTH contracts: (A) attack the plan — edge cases, error paths, data volume, concurrency, security, RLS, auth, rollback, missing steps, load-bearing unverified assumptions; (B) over-engineering — what's bloated/gold-plated, what to cut/merge, is there a 10× simpler path, AND audit the lane tags (anything `[Claude]` a worker could do under review? anything `[GPT-5.5]` actually too subtle?).
- **Large / DEEP plan →** TWO parallel waves: Wave A = the adversarial/gap contract, Wave B = the over-engineering/simplification + lane-audit contract. Separating concerns improves recall where there's more to find.

Never cut the **first** adversarial wave — the gap-finding ("you forgot the migration / the RLS policy") is cheap (GPT-5.5) and high-catch. Only the *second* wave is conditional.

---

## Phase 5 — Triage + questions (Opus adjudicates everything)

5a. **Opus triages directly — no delegate has merge rights into the plan.** Finding sets are small; dedupe, map each finding to its plan step, and rule on every one: **accept / reject (one-line why) / ask-the-user**. The old cheap-triage design let a delegate's "accept" fold into the plan unseen — but folding a WRONG accept silently mutates the plan (reviewer noise and scope creep walk straight in), so accepts get the same Opus eyes as rejects. Only when the merged set exceeds ~20 findings, pre-sort with ONE cheap subagent (haiku — mechanical dedupe/grouping only, labels advisory); Opus still rules every item. Bias toward the simplification cuts — simpler plans ship.

5b. **Fold rulings into `plan.md`** — re-dispatch the planner subagent with the brief + the rulings when the edits are structural (keep the drafting context clean); edit inline when cosmetic.

5c. **Ask the user about any genuine forks** with `AskUserQuestion` — and you may ask at ANY point in this flow when a real decision is the user's (architecture call, scope trade-off, a fork the critics surfaced). Don't batch trivia; do surface anything that changes what gets built.

5d. Re-run `plan_lint.py` after edits → exit 0. Loop Phase 4–5 once more ONLY if the first wave found structural (not cosmetic) problems.

---

## Phase 6 — Render + GO gate

6a. **Render the HTML reader once, now** that the plan has settled (M4): `~/bin/plan-html <plan.md>`. One render of the final version — no wasted renders on lint/review iterations.

6b-0. **Claim-verification ledger.** Before the autonomy verdict or any final "done" claim, list every material claim as `claim -> proof command/source -> observed result -> verifier`. Any claim without an observed result is labelled `UNVERIFIED` and cannot support GO/done.

6b. **Autonomy-readiness check (final goal check).** Before the GO gate, answer one question out loud: **"If the human caffeinates the laptop and goes to bed now, does this plan reach the goal's end-state unattended — and is the end-state actually what the goal asked for (e.g. the proof-user solves the problem in N clicks)?"** Check, in order:
   - **End-state match:** does the last batch's acceptance criteria equal the goal's user-outcome (not just "code shipped")? If the plan ships the backend but nobody wires the proof-user's 5-click path, it does NOT meet the goal — say so and add the missing steps inline (no deferral).
   - **No mid-run human gates:** every step is dispatchable without human input. Any `AskUserQuestion` left unresolved = NOT autonomy-ready.
   - **Named human actions:** are any real-world blockers (OAuth grant, cert, payment, Apple login) required *before* the end-state? If yes, the "wake up and it's done" goal is **not fully achievable** unattended — state plainly: "X blocks full autonomy; do X before sleeping, then it runs to done" (or "this needs you awake for X"). Don't pretend.
   - **Run mode:** if multi-batch and AUTONOMOUS, the plan runs under **`/loop`** — state the exact `/loop` invocation. Give your verdict: **fully autonomous / autonomous-after-human-action-X / not autonomous (needs you present for …)**. This is the direct answer to "can I sleep and wake up to it done, or do I need /loop?"

6c. **GO gate.** Present the final plan via a real **`ExitPlanMode`** call — fires the native approval card AND the `plan-principles-gate.sh` hook on the finished artifact, so the in-built plan's approval + enforcement are preserved end-to-end. Include the 6b autonomy verdict. Confirm the plan still serves the `/goal` from 0a. Wait for explicit approval ("GO"). Until then, do not touch implementation files.

---

## Phase 7 — Implement

**AUTONOMOUS mode — caffeinate at the start, uncaffeinate on done.** If 0a-bis set AUTONOMOUS, keep the laptop awake for the whole unattended run and release it the moment the run finishes:
```bash
# start: keep display+disk+system awake; record the pid
caffeinate -dimsu & echo $! > /tmp/plan-caffeinate.pid
```
Run the implementation under `/loop` so batches chain without re-prompting. On completion (all batches green + end-state verified) OR on a hard stop, tear it down:
```bash
kill "$(cat /tmp/plan-caffeinate.pid)" 2>/dev/null; rm -f /tmp/plan-caffeinate.pid
```
Always kill caffeinate in both the success and the abort path — never leave the laptop pinned awake after the run ends. (INTERACTIVE mode skips this entirely.)

### AFK loop lens — self-heal toward the goal, don't stall

**Safety line (hard — read the host's autonomy guardrails before unattended work):** reversible/scoped actions proceed auto; **irreversible / financial / outward-facing / prod-mutating** actions ESCALATE (never auto). Credentials come via `timed-secret get <name>` — auto-tier returns the value, gated/unknown → escalate. Blocker-solver ladder: (1) credential → `timed-secret`; (2) web service → stored API token first, CDP browser-login fallback, 2FA→escalate; (3) Fedora → SSH diagnose + restart own non-prod service (never port 3000 prod); (4) stuck/any 🚫 action → `timed-escalate "<what's blocked + exact human step>"`, mark BLOCKED, keep other tasks moving. Never halt the whole loop for one blocker; never push to main; never touch prod.

While the human is asleep/AFK there is nobody to unstick anything, so the loop must be **agentic and resilient**, not fragile. On every step:

1. **Verify via the §Correctness Gate, don't assume.** A step is "done" only when it clears the gate: failure-path invariant tests exist + executed + passed, graded by a *different* instance than the worker that wrote it (no self-marked GREEN), bugs turned into regression tests. A passing happy-path smoke is NOT green. A worker diff lacking failure-path tests is PARKED, not committed. Re-assert the GOAL ANCHOR each batch — build toward the *proof-user end-state*, not "code compiles".
2. **Fail → retry → work around (bounded agentic loop).** On failure: diagnose root cause (`superpowers:systematic-debugging`), retry with the fix. If it fails again, try a *different approach* (a workaround) — don't repeat the same failing move. Bound it (≈3 attempts / escalating effort) so it can't spin forever on one step.
3. **Route tools autonomously by failure type:**
   - **Anything on the web** (unknown API behaviour, an error you don't recognise, a library/version question, a doc lookup) → route through the plan's research budget: `fast` uses **`/comet`** (or Pro Search for quick facts), `deep` uses **`hyperresearch-codex`**, and `hybrid` uses Comet breadth plus HyperResearch synthesis when the answer changes architecture/routing/integrity. Fold the answer and retry.
   - **Anything coding** (implement / fix / refactor a step) → dispatch **agents**: `[fast]`/`[GPT-5.5]` workers via `codex-worker.sh` (or `feature-workflow` for a batch); Claude reviews the diff.
   - **A blocked build/test** → `superpowers:systematic-debugging` to isolate, then re-dispatch the fix.
4. **Isolate, don't freeze.** If a step is still blocked after the bounded loop, mark it BLOCKED, **skip to the next independent batch**, and keep the night productive. Never let one stuck step halt the whole run.
5. **Escalate only real-world blockers.** A named human action (OAuth grant, Apple login, payment, cert) genuinely cannot be worked around autonomously — log it loudly to the wake-up report and continue everything that doesn't depend on it.
6. **A NEW architectural fork discovered mid-run is never decided silently.** 0a-bis front-loaded the KNOWN forks; one that surfaces at 3am gets: park the steps that depend on it as BLOCKED-ON-FORK, record the fork + options + your recommendation in the wake-up report, keep every independent batch moving. Exception: if one branch is cheap, reversible, AND clearly anchor-aligned, build it behind an easy revert and flag the decision loudly in the report. Silent 3am architecture decisions are where overnight quality dies.
7. **End-of-run bug sweep BEFORE exit (mandatory gate).** When all batches are green/parked, do NOT declare done yet. Run a final adversarial sweep over the *combined* diff of the whole run — this catches the class per-step review structurally can't: cross-step interactions (step A broke a contract step B relied on). Spawn ~3 fresh agents (different instances than any author — **no self-audit**; via Bash `codex exec`, or Agent tool with explicit `model: "sonnet"` — never inherited), each a distinct lens: **(L1) integrity/data-loss** (silent loss, partial-failure, cursor/watermark-on-failure, idempotency-under-failure, overflow/truncation); **(L2) cross-step interaction** (read the full combined diff + each step's contract); **(L3) correctness/regression vs stated invariants + bloat**. Adversarially **verify** each finding (real vs noise) before acting; real findings → contract-first fix tasks (integrity-critical = Claude-authored) → fix under the §Correctness Gate → add a regression test → **re-sweep**. Loop-until-dry, bounded to **2 consecutive clean sweeps** (convergence guard).
8. **Then exit honestly.** Done only when the sweep is clean AND every batch green + the **end-state verified against the ANCHOR** (product actually ready), or no further unblocked progress is possible. Write a wake-up report: what shipped, what's BLOCKED and why, the exact human action(s) needed, sweep result, and whether the proof-user end-state is met. Tear down caffeinate. Never report "done" if the ANCHOR end-state isn't actually reached or the sweep isn't clean.

Honor the per-step lanes — the token-economy payoff:
- **`[GPT-5.5]` steps** → GPT-5.5 workers at the step's matched effort (`CODEX_EFFORT=xhigh` default, `high` where annotated). **≥3 files** route the batch through the `feature-workflow` skill (CC-plans → GPT-5.5 workers in worktrees + Phase 3.5 multi-provider review + Phase 5 dock reinstall); pass the approved `plan.md` with lanes intact. A **lone step** → one Bash `codex exec` call directly (never car-name Agent types, never `codex:rescue`).
- **`[fast]` steps** → `gpt-5.4-mini` workers (`CODEX_MODEL=gpt-5.4-mini CODEX_EFFORT=low` via `codex-worker.sh`). Batch the deterministic bulk here so it runs fast and cheap.
- **`[Claude]` steps** → Claude authors directly. Don't fan these out.
- **1–2 files / typo-class** → implement inline, then run the project's test loop.

**Claude reviews + edits + fixes EVERY `[GPT-5.5]` and `[fast]` diff before it counts as done.** If a plan is ALL `[Claude]`, you mis-tiered — re-check 2a's lane rule.

**Compound after each step.** When a step lands an architectural decision or non-obvious resolution:
```
Write the decision to the configured memory store with its rationale and constraints.
```

**Plan postmortem — the feedback loop (mandatory, ~10 lines).** Before closing, diff plan-vs-actual: steps added or cut mid-run, mis-tiered lanes, call-sites the map missed, review findings that proved wrong (and bugs the review missed), research that arrived too late to matter. Append the deltas to the configured memory store, and when a delta implicates the pipeline itself (a phase that systematically under-delivers), append one line to this skill's `POSTMORTEM.md` for the maintainer to review. Nothing in this flow improves unless its misses are recorded somewhere a future edit reads.

After all steps, follow the project's session-close protocol (`/skill:wrap-up`) and complete any explicitly requested task if one maps.

---

## Fast path (small/familiar — `/plan --light` or auto)

Selected in 0c when ≤5 files, familiar, and no high-blast-radius surface. Any blast-radius trigger bails to DEEP.

```
FP0  /goal + memory search                                   (0a+0b — cheap, high ROI, unchanged)
FP1  route external-fact unknowns by research= budget        (0d — async where Comet, gated where deep)
FP2  ONE combined Opus pass: scout files + 2 approaches
     + per-approach failure-mode + recommended path          (Phase 1 collapsed)
FP3  draft plan.md WITH inline lane tags;
     capture selected research on-demand                     (Phase 2, 2a+2b)
FP4  plan_lint.py → exit 0                                    (Phase 3)
FP5  ONE merged GPT-5.5 review wave                           (Phase 4 small-plan branch)
FP6  Fable/Opus adjudicates every finding directly;
     AskUserQuestion on genuine forks                         (Phase 5)
FP7  render HTML once                                         (Phase 6a)
FP8  GO gate via ExitPlanMode                                 (Phase 6b — never skipped)
FP9  implement by lane; Claude reviews every diff;
     write decisions to basic-memory; session-close          (Phase 7)
```

Quality floor on the fast path is held by: memory-first, lint→0, ≥1 adversarial GPT-5.5 review, Opus-only rejection of findings, and the unchanged GO gate.

---

## Exemplar — the target form (abbreviated)

What a good plan looks like (condensed from the real handbook-wipe plan, 2026-05-27). Match this **density**: structure is load-bearing, prose is minimal, every step carries its lane + acceptance, contract weight follows risk. The planner subagent gets this section verbatim as its format spec.

````markdown
**Goal:** Any user wipes their handbook data from Settings and watches it complete.
**Anchor:** a proof-user clicks the action → real progress bar → done, safe to close the tab mid-operation · proof-user: non-technical user · rejects-if: terminal step, silent failure, stuck spinner
**Path:** FULL · **Mode:** INTERACTIVE

Dependency graph: B1 → B2 → B3 (S3 blocked by S1's migration; B3 blocked by S2+S3)

#### Batch 1 (parallel)
- **S1 `[Claude]`** Migration: `handbook_wipe_jobs` (status, phase, per-phase counters, resumable cursor).
  Contract (integrity-critical): job claim is atomic — two drains can never claim one job; cursor advances only after the batch it covers is durably deleted; re-run after crash resumes clean, never re-deletes.
  Accept: failure-path tests pass (crash mid-batch → resume; concurrent claim → one winner).
- **S2 `[GPT-5.5]`** `handbook-wipe-status` Edge Function returning `{phase, percent, status}`.
  Accept: correct shape for queued / running / done / no-job.

#### Batch 2 (depends on B1)
- **S3 `[Claude]`** pg_cron drain: time-bounded batches, cursor saved between invocations.
  Contract: respects the 150s wall clock; partial failure leaves the job resumable, never marked done.
- **S4 `[fast]`** Wire `handbook-wipe-my-data` enqueue (existing job-table pattern, zero reasoning).
  Accept: returns `{wipe_job_id}` in <500ms.

#### Batch 3 (depends on B2)
- **S5 `[GPT-5.5]`** Settings UI: poll every 2s, real progress bar, "safe to close this tab" copy, auto-resume on reload.
  Accept: reload mid-wipe re-attaches to the running job; error state visible, never a stuck spinner.

#### Human actions
None — no real-world blocker.
````

Note what is NOT here: no time estimates, no "later", no per-step essay. S4 gets one acceptance line; S1 gets a full failure-path contract — artifact weight follows risk, which is how principle 6 (brief) coexists with the §Correctness Gate. The anchor sits at the top and every step survives its test.

## When to use this vs the other planners

`/plan` is the **default heavyweight planner** and the superset — it brainstorms, researches, adversarially reviews, tiers execution, and *escalates into* deep-plan's mapping via the Phase 0c path selector when the change is big. Reach for the others only when:

| Use | When |
|-----|------|
| **`/plan`** (this) | Default for any non-trivial feature/refactor wanting brainstorm + research + GPT-5.5 critique + execution tiering. Auto-sizes discovery + review depth. |
| **`deep-plan` / `deep-plan-timed`** | You want *only* the exhaustive map + plan with zero research/critique overhead — or it's being called as the Phase 1 DEEP sub-step. `deep-plan-timed` pre-loads the Timed vault. |
| **`plan-feature`** | Existing Timed feature-planning skill; `/plan` covers it with more layers. |

If two could fire, prefer `/plan` — it contains the others' rigor as sub-steps.

## Notes

- Orchestrated superset of native plan mode, not a replacement. Native shift+tab plan mode still exists for quick read-only planning.
- Project-agnostic: use the repository's configured memory project and test loop; skip optional integrations that are unavailable.
- `--deep` / `--light` flags force the path; default auto-decides on scale + blast radius in 0c.
- If Comet is down or nothing is research-worthy, research degrades gracefully to in-session reasoning — state it skipped, don't block.
