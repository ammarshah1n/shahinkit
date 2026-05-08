---
name: rag-consent
description: Consent gate for retrieval indexing that shows proposed files, private-data exclusions, approval record, and revoke or rebuild instructions.
---

# rag-consent

Use before embedding, indexing, syncing, or rebuilding a retrieval corpus from local or private files.

Do not index anything until explicit approval is given.

## Consent Packet

Show the user:

- Exact files and folders proposed for indexing.
- File counts and major file types.
- Destination index or corpus name.
- Whether content leaves the machine or stays local.
- Private-data exclusions.
- Revoke and rebuild instructions.

## Private-Data Exclusions

Exclude by default unless the user explicitly approves:

- Secrets, keys, tokens, credentials, and `.env` files.
- Financial, medical, legal, identity, and account records.
- Private messages, emails, chat exports, and transcripts.
- Personal photos, scans, and signed documents.
- Dependency folders, build output, caches, and generated binaries.

## Approval

Ask for explicit approval with the exact scope, for example:

`Approve indexing these listed paths into the named corpus?`

Accepted responses must clearly approve the scope. Ambiguous replies require a follow-up question.

## Consent Record

After approval, write a consent record containing:

- Date.
- Approved files and folders.
- Exclusions.
- Index or corpus name.
- Storage location or service class.
- Revoke instructions.
- Rebuild instructions.

Use relative paths where possible. Do not include private local paths, personal names, secrets, or transcript content.

## Revoke And Rebuild

Document how to:

- Delete the index or corpus.
- Remove generated embeddings.
- Rebuild from the approved source list.
- Re-run indexing after exclusions change.
