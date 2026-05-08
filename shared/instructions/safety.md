# Safety Policy

ShahinKit must be safe to copy into a personal, school, or client workspace.

## Destructive Operations

Ask before running or recommending operations that delete, move, overwrite, reset, force push, drop data, or change live config.

Examples that require approval:

- deleting files or folders;
- moving or renaming user content;
- overwriting Claude or Codex config;
- exporting private material;
- indexing or embedding a vault;
- pushing to a remote branch;
- force operations in Git.

## Secrets And Private Data

Reusable templates must not contain:

- API keys, tokens, passwords, credentials, or secrets;
- private repo names or private URLs;
- personal phone numbers, emails, addresses, IDs, or session identifiers;
- raw Claude or Codex transcripts;
- school-specific student data;
- client-specific documents or facts.

Use `{{VARIABLES}}` for user-specific values.

## Indexing And Export

Indexing, embedding, transcript export, and public export are deny-by-default.

Before indexing:

1. show the exact files or folders proposed for indexing;
2. show exclusions;
3. ask for explicit consent;
4. record consent;
5. provide a revoke/rebuild path.

Before public export:

1. use an allowlist;
2. run the private-data checklist;
3. ask for approval;
4. export only approved files.

## Hooks

Hooks must be opt-in. A hook may print guidance by default, but it must not mutate files unless the user has enabled the relevant environment flag or install option.
