---
name: deep-plan
description: Exhaustive codebase-grounded planning for non-trivial mature-repo work.
---

# Deep Plan

Use this when the main risk is codebase understanding: cross-module changes, refactors, high-risk features, or work touching more than a few files.

## Model And Cost Policy

- Use low effort for project detection, structure listing, and literal symbol searches.
- Use medium effort for scope routing and side-effect exploration.
- Use high effort for plan synthesis.
- Use high or xhigh only when the reasoning itself is the bottleneck.
- Do not use expensive workers for mechanical mapping that a direct shell command can do.

## Phase M: Memory And Project Identity

- Detect project identity from instructions and manifests.
- Retrieve configured memory.
- Record unavailable memory sources explicitly.
- Write or update `docs/MEMORY_CONTEXT.md` only when the project already uses docs artifacts or the user asked for an artifact.

## Phase 0A: Index-First Orientation

Inspect, in parallel where possible:

- architecture index if present;
- repository structure;
- manifests;
- likely entry points;
- tests;
- key symbol hits.

Prefer existing maps before raw broad search.

## Phase 0B: Scope Manifest

Produce a scope manifest containing:

- included directories and why;
- excluded directories and why;
- key symbols to track;
- uncertainty flags;
- confidence.

If confidence is low, broaden scope before planning.

## Phase 0C: Cross-References

Search callers, imports, and reverse dependencies once. Reuse the registry during exploration instead of repeating broad searches.

## Phase 0D: Targeted Exploration

For each included area, record:

- relevant files;
- exported symbols and interfaces;
- imports within scope;
- external dependencies;
- side effects;
- related tests;
- files that should be added to scope.

## Phase 0F: Map Completeness Gate

Before planning, confirm:

- entry points are known;
- write paths and side effects are known;
- test surface is known;
- uncertain scope is either resolved or named.

## Phase 1: Plan

Write a plan with:

- dependency graph;
- parallel batch schedule;
- execution lane per batch;
- exact verification commands;
- risk and rollback notes for high-impact changes.

Stop for review before implementation.
