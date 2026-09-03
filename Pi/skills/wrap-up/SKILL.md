---
name: wrap-up
description: Close a Pi coding session safely: verify work, update the local handoff, and perform only explicitly approved git or external actions. Use when the user says wrap up, end session, session done, or equivalent.
---

# Safe session wrap-up

Run this workflow without inventing authority. A generic wrap-up request permits
local inspection and local handoff updates only. It does **not** authorize a
commit, push, task creation, memory-service write, upload, publication, or any
other external mutation.

## 1. Capture authorization

From the current user request, record these independent booleans:

- `commit_approved`
- `push_approved`
- `task_write_approved`
- `memory_write_approved`
- `other_external_action_approved`

Each defaults to false. Approval for one action never implies another. Never
prompt halfway through wrap-up; skip an unapproved action and report it.

## 2. Inspect and verify

1. Read repository guidance and the current `git status --short --branch`.
2. Identify changed, staged, untracked, and deleted files. Do not assume every
   dirty file belongs to this session.
3. Run the smallest authoritative test/build/lint commands for the touched
   surface. Record exact commands and results.
4. Scan the intended handoff and any approved external payload for credentials,
   tokens, private endpoints, personal data, raw transcripts, and unnecessary
   absolute paths. Redact or omit sensitive material.

## 3. Classify conservatively

- `SHIPPED`: requested work is complete and all required verification passes.
- `PARKED`: work is incomplete but the tree is recoverable.
- `INTERRUPTED`: verification fails or the tree is broken.

Ambiguity defaults to `PARKED`, never `SHIPPED`.

## 4. Write the local handoff atomically

Use the repository-root `HANDOFF.md` unless repository guidance names another
local canonical state file. Never write outside the repository merely because a
host integration exists.

The handoff contains:

- state: `SHIPPED`, `PARKED`, or `INTERRUPTED`;
- completed work;
- exact verification results;
- remaining work and blockers;
- one concrete resume instruction;
- relevant repository-relative paths and commit IDs.

Protect concurrent sessions:

1. Use a lock directory inside the repository's Git common directory, with a
   random session suffix recorded in its owner file.
2. Acquire with one atomic `mkdir`. If acquisition fails, do not enter the
   critical section, do not remove the existing lock, and report the conflict.
3. Create the replacement with `mktemp` in the destination directory, write and
   fsync it, then atomically rename it over `HANDOFF.md`.
4. Remove only the lock whose owner token matches this session, in a `finally`
   path.

Do not create second-resolution per-session filenames or overwrite `NEXT.md`
outside this lock. Prefer one canonical handoff over a parallel registry unless
the repository already provides a tested collision-safe mechanism.

## 5. Optional durable-memory or task writes

Skip unless the corresponding current-request approval flag is true and the
approved tool is already configured.

Before writing:

- list or search existing records to avoid duplicates;
- send only the minimum distilled fact or explicit unfinished commitment;
- remove secrets, raw errors containing credentials, private paths, client
  identifiers, source bodies, and transcript text;
- never auto-complete, delete, reprioritize, or rewrite existing tasks.

A configured tool is capability, not consent. Tool availability never changes
an approval flag.

## 6. Git mutation gate

- Never stage or commit `PARKED` or `INTERRUPTED` work automatically.
- If `commit_approved` is false, leave the index and commits untouched.
- If `commit_approved` is true, require `SHIPPED`, review the exact staged file
  list and staged diff, then create one conventional commit.
- If `push_approved` is false, never push—even after an approved commit.
- If `push_approved` is true, verify the branch, upstream, and non-force refspec;
  then push only the approved branch. Never infer tag/release approval.

## 7. Final verification and report

Re-run the required checks after any approved mutation. Report:

```text
State: SHIPPED | PARKED | INTERRUPTED
Handoff: <repository-relative path or skipped reason>
Checks: <exact commands and pass/fail>
Commit: <hash or skipped—not approved>
Push: <remote/ref or skipped—not approved>
External writes: <each approved action, or none>
Resume: <one concrete instruction>
```

Never claim a push, publication, task write, memory write, or clean tree without
verifying it directly.
