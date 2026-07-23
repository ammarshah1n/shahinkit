# Enforcement Specs

## D7 Dispatch Gate

Trigger point: before any Agent/Task/subagent dispatch.

Decision logic:
```text
read dispatch JSON
if JSON missing/unreadable/malformed -> allow
if tool is not Agent/Task/subagent -> allow
extract prompt, requested model, dispatched agent name
resolve effective model:
  requested model if present
  else pinned model from agent definition if readable
  else unset
if effective model is unset -> block
if effective model equals session model or {{CONTROLLER_MODEL}} or is controller-tier:
  if prompt contains "[CONTROLLER-TIER-JUSTIFIED:" -> allow
  else block with instruction to justify or route to {{RESEARCH_MODEL}}/{{GRUNT_MODEL}}
if effective model is {{RESEARCH_MODEL}} and prompt matches mechanical verbs:
  warn suggesting {{GRUNT_MODEL}}, allow
allow
```

Fail-open rule: malformed JSON, missing hook input, unreadable agent definitions, or hook runtime errors must allow rather than brick dispatch. A valid dispatch with unset model is not fail-open; block it.

Test payloads:
- controller-tier + no marker -> block.
- controller-tier + marker -> allow.
- unset model + no pinned agent -> block.
- pinned cheaper agent + no requested model -> allow.
- {{RESEARCH_MODEL}} + "catalog/list files/extract/rename/find all/enumerate/map the" -> warn allow.
- malformed JSON -> allow.

## Plan-Principles Gate

Trigger point: final plan approval through `{{PLAN_GATE_MECHANISM}}`.

Decision logic:
```text
read plan from tool payload
if no plan text -> allow
if linter unavailable -> allow
run plan linter
block if plan contains estimates
block if plan defers work to later/next session/future work
block if dependency graph missing
block if parallel-batch schedule missing
block if verification gates between batches missing
allow only after lint passes
```

Fail-open rule: missing linter, unreadable payload, or no plan text allows. A readable plan that fails lint blocks.

Test payloads:
- clean plan with dependency graph, parallel batches, verification gates -> allow.
- plan with "2 hours" or similar estimate -> block.
- plan with "later/next session/future work" deferral -> block.
- plan with serial todo list and no dependency graph -> block.
- malformed JSON -> allow.

## Verification-Before-Done

Trigger point: before final "done" claim, before accepting worker output, and before reporting test/build success.

Decision logic:
```text
collect material claims:
  shipped/fixed/done
  tests pass/build pass
  worker says complete
  visual artifact accepted
for each claim require:
  proof command/source
  observed result
  verifier different from author where worker-produced
if proof absent -> mark UNVERIFIED and do not claim done
if visual output matters and no rendered/visual proof -> block done
if tests are happy-path only for an integrity guarantee -> block GREEN
allow done only when every material claim has observed proof
```

Fail-open rule: if no mechanical hook exists, do not block ordinary chat; require the final response/report to label unverified claims explicitly. Never convert an unverified claim into "done".

Test payloads:
- worker says "done/tests pass" with no output -> block done.
- command output observed and verifier recorded -> allow.
- visual deliverable accepted from raw file checks only -> block done.
- author self-grades worker output GREEN -> block done.
- no completion claim -> allow.
