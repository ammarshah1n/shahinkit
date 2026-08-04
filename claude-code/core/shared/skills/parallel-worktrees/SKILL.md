---
name: parallel-worktrees
description: Use when independent git changes need isolated workspaces and can be reviewed separately.
---

# Parallel Worktrees

1. Confirm work is independent, paths do not overlap, and each unit has a bounded acceptance check.
2. Check git worktree support and cleanly identify current branch and existing workspaces before proposing isolation.
3. Assign one narrow change per workspace, preserve unrelated work, then compare each result against its stated scope.
4. If git worktrees are unavailable or changes overlap, use one workspace and explain why parallel work would be unsafe.
5. Never automatically install, commit, push, publish, submit, send, book, pay, delete, or mutate an external system. Require explicit user approval.
