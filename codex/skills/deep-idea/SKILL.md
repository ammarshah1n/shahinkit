---
name: deep-idea
description: Research-first planning for greenfield ideas, immature repos, and pre-code product work.
---

# Deep Idea

Use this when there is no mature codebase to map.

## Project Modes

- `NO_REPO`: nothing exists yet.
- `SCAFFOLD_ONLY`: config exists but app shape is not stable.
- `IMMATURE_REPO`: some code exists, but patterns and tests are not stable.
- `MATURE_REPO`: use `deep-plan` instead.

## Artifacts

When artifacts are appropriate, create:

- `docs/research/IDEA_BRIEF.md`;
- `docs/research/INTERVIEW.md`;
- `docs/research/RESEARCH_BRIEF.md`;
- `docs/research/OPEN_SOURCE_MAP.md` when relevant;
- `docs/PRD.md`;
- `docs/BUILD_CONTEXT.md`;
- implementation plan only after the PRD is reviewed.

Do not write implementation source files in this skill.

## Phase I: Capture

Run memory retrieval, idea capture, and cheap scaffold orientation in parallel where possible.

Capture:

- user;
- job to be done;
- constraints;
- success criteria;
- non-goals;
- existing alternatives;
- assumptions.

## Phase II: Interview Gate

Ask only high-impact questions that change the product, scope, or build path.

## Phase III: Research

Run only the lanes needed for the decision:

- user workflow;
- alternatives;
- technical feasibility;
- privacy and data handling;
- integration options;
- open-source candidates.

Each lane must end in a decision or a named uncertainty.

## Phase IV: Synthesis

Write the research brief and PRD. Include:

- problem statement;
- target users;
- core workflows;
- out of scope;
- success metrics;
- technical constraints;
- open decisions.

## Phase V: Graduation

Graduate to `plan` or `deep-plan` only when:

- PRD is coherent;
- build context is specific;
- major unknowns are closed or named;
- implementation can be planned without inventing product decisions.
