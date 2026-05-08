---
name: skill-builder
description: Build a reusable personal, school, work, or life-management skill from a voice transcript, rough description, or existing workflow.
---

# Skill Builder

Use this when someone wants an agent skill for a recurring area of life or work: study, projects, health, finance, property, travel, business, family admin, hobbies, operations, or any custom domain.

The goal is to turn a rough description into a portable skill folder that another Claude or Codex user can install, understand, and improve over time.

## Phase 1: Intake

Ask for or read the rough transcript, note, or description.

Capture:

- domain name;
- who uses it;
- common tasks;
- frustrating or slow parts;
- existing files or sources;
- hard rules and preferences;
- what a perfect output looks like;
- what the assistant must never do.

Ask only the questions needed to close important gaps. Use plain language.

## Phase 2: Blueprint

Before building, present a short blueprint:

- skill name;
- when it should activate;
- files that will be created;
- reference files it needs;
- workflow phases;
- source documents, if any;
- memory or reflection behavior, if any;
- install target and safety constraints.

Wait for approval before writing files.

## Phase 3: Build

Create the smallest useful skill package:

```text
skills/<skill-name>/
  SKILL.md
  references/
  checklists/
  templates/
  source/
  sessions/
```

Only create folders that the skill actually needs.

`SKILL.md` should include:

- trigger description;
- purpose;
- required inputs;
- workflow phases;
- reference file index;
- safety rules;
- output format;
- update/reflection notes.

Reference files should use placeholders and examples, not private data.

## Phase 4: Test

Run a trigger test:

- Give one example phrase that should activate the skill.
- Give one example task the skill should handle.
- Check that required files are easy to find.
- Check that private data, local paths, and source documents are not copied into public templates.

## Rules

- Keep it portable: no private local paths, personal identifiers, or machine-specific config.
- Ask before reading source documents, copying files, installing tools, or writing into a live agent config.
- If source documents are provided, treat them as the source of truth and keep generated summaries separate.
- Use placeholders for user-specific details.
- Prefer one clear skill over a sprawling multi-domain skill.
- Include a simple update path so the skill can improve after real use.
