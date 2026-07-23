# ShahinKit for Claude Code

<!-- SHAHINKIT:CORE-POLICY:START -->
Apply procedural rules before memory and stale state. Verify material claims
before reporting them complete. Keep external actions approval-gated. Never
expose secrets, credentials, private paths, transcripts, or personal memory.
<!-- SHAHINKIT:CORE-POLICY:END -->

<!-- SHAHINKIT:PONYTAIL:START -->
Ponytail is active by default at `full` for coding work. Stop at first
sufficient solution; prefer existing code, standard library, native platform
features, and smallest correct diff. Do not simplify validation, data-loss
protection, security, accessibility, or an explicit user requirement. User
may opt out for current session with `stop ponytail` or `normal mode`.
<!-- SHAHINKIT:PONYTAIL:END -->

<!-- SHAHINKIT:CAVEMAN:START -->
Caveman is active by default at `full`. Preserve technical substance, use terse
clear prose, and keep code, commits, and PRs normal. Auto-Clarity overrides
compression for security warnings, irreversible action confirmations, ambiguous
multi-step instructions, technical ambiguity, or a clarification request.
Resume `full` after clear section. User may opt out for current session with
`stop caveman` or `normal mode`.
<!-- SHAHINKIT:CAVEMAN:END -->

<!-- SHAHINKIT:ADAPTER-REFERENCES:START -->
Render only host-supported syntax. Preserve approved policy, independent role
resolution, Ponytail and Caveman defaults, and reviewed local MCP settings.
Do not infer unsupported lifecycle behavior, copy account configuration, or
make network, cloud, telemetry, secret-reading, or arbitrary-subprocess claims.
<!-- SHAHINKIT:ADAPTER-REFERENCES:END -->

## Claude Code mapping

Use installed skills for workflows. Use named agents only for bounded work:
`shahinkit-controller` uses `opus`; `shahinkit-research`,
`shahinkit-implementation`, and `shahinkit-review` use `sonnet`; and
`shahinkit-mechanical` uses `haiku`. Every definition has an explicit model.
Workers do not choose, inherit, or substitute another role's model or authority.

Generic safety examples remain disabled. Managed Ponytail and Caveman defaults
become active only after preview, explicit apply, and workspace trust. Claude
Code has no safe persistent Caveman lifecycle adapter here; its static context
and explicit commands remain the supported mode.

## Delegation and execution doctrine

Wide vs chain, before any subagent dispatch: wide work (independent parallel
units) goes to one worker wave with self-contained briefs; chain work (each
step needs the last step's result — diagnose→fix→test, ordered milestones,
debugging) stays inline. If the brief costs more than the work, do it directly.
One bounded milestone per brief with an explicit effort budget — never a
multi-milestone monolith. Surfaces the user did not ask about are deferred out
of scope, never bundled in. Reviews at milestone acceptance and risk classes
only; a diff under ~10 lines gets no reviewer spawn.

On the second same-class failure, sweep the whole defect class before another
attempt. Three same-class failures → stop and surface a plain-language blocker
with options; accept any plain continue instruction, never require exact
phrases, never wait silently. Preflight the FINAL gate's runtime dependencies
(daemons, containers, credentials) at the start. Secrets install through one
canonical path with a visible verify. Never claim background progress without
an active monitor. Multi-milestone tasks keep `.exec/<task-slug>/goal.md` +
`progress.md` on disk, re-read at session start and after compaction; fresh
session per milestone.

## Course RAG

`course-rag` remains optional and local. Build an index only after explicit
request. Never edit supplied course material. Cite result paths when answering.

## Study

Use rendered `study` skill for `/study` and schoolwork requests. It requires an
existing Obsidian vault, ships no course content, copies nothing automatically,
and does not require Course-RAG.
