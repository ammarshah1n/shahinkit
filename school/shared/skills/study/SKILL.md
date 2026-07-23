---
name: study
description: Set up or resolve a user-owned existing Obsidian study vault for school, course, subject, homework, lesson, or study requests. Resolve and read a valid Study.md mapping before using schoolwork folders. `/study` sets up when no valid mapping exists; `/study setup` reconfigures a valid mapping.
---

# Study

Use for `/study`, schoolwork, courses, subjects, homework, lessons, or study
requests. It requires an existing Obsidian vault and ships no subjects, course
material, examples, RAG, index, database, plugin, import pipeline, or executable.

## Modes

- `/study`: resolve a valid mapping. If none exists, run initial setup.
- `/study setup`: reconfigure only an already valid mapping.
- Any later schoolwork request: resolve vault and validate/read mapping first.
  Stop without using any mapping content if validation fails.

## Resolve Vault Before Reading or Writing

Independently resolve both available candidates:

1. Current note path: start at its parent directory.
2. Working directory: start at that directory.

For each candidate, walk upward to nearest ancestor containing `.obsidian`.
Before accepting it, use `lstat` on `.obsidian`, root, and every existing path
component traversed from filesystem root to root. Each must be a real
non-symlink directory. Canonicalize the root only after those checks; retain
that canonical root for every later containment check. Do not treat a file,
missing path, symlinked root/component, or nearby `.obsidian` as valid.

- If both roots resolve and differ, stop: ask user to choose one vault.
- If neither resolves, stop: ask user to open or select intended **existing**
  Obsidian vault. Create no vault, `.obsidian`, folder, or mapping.
- Mapping root is only resolved vault root. Never use a parent, child, current
  repository, or guessed vault.

## Canonical Mapping Contract

Only `<vault-root>/Study.md` is a mapping. Do not use alternate names,
pointers, redirects, or search results.

Before reading it, require `Study.md` to be a regular non-symlink file. A valid
mapping has all of following:

1. YAML frontmatter opens at line 1 with `---` and contains exactly one
   `shahinkit_study: 1` and exactly one `vault_root: .` field.
2. Immediately after closing frontmatter, exact standalone version marker:
   `<!-- shahinkit-study:v1 -->`.
3. Exactly one complete owned block after that marker, with these exact
   standalone markers:
   `<!-- shahinkit-study:begin -->` and `<!-- shahinkit-study:end -->`.
4. A parseable YAML mapping inside owned block with `subjects` list. Each item
   has non-empty `display_name`, `folder`, and `course_content.status`.
5. Before reconfiguration or later schoolwork uses any subject, validate every
   mapped `folder`: safely YAML-decode it to a scalar string; require a valid
   subject name; reject absolute paths, `.`, `..`, traversal, `/`, `\\`, and
   control characters; and require case-insensitive uniqueness across every
   mapped folder. Resolve it only as a direct child of canonical vault root,
   then require `lstat` to show an existing real non-symlink directory whose
   canonical/real path remains contained by that root. Reject missing,
   non-directory, symlink, duplicate/case-duplicate, or outside-root entries.
   On any failure, do not use any mapping content.

Canonical generated shape; placeholders are schema only, never bundled content:

```markdown
---
shahinkit_study: 1
vault_root: .
---
<!-- shahinkit-study:v1 -->
<!-- shahinkit-study:begin -->
subjects: []
<!-- shahinkit-study:end -->
```

Reject duplicate, missing, reordered, nested, or malformed owned markers;
duplicate frontmatter fields; malformed YAML; a version marker outside its
canonical position; non-canonical location; or any nonregular/symlink
`Study.md`. Stop without using its contents.

Initial setup never opens an existing `Study.md`. Any existing `Study.md`—even
if it appears generated—blocks initial setup. Never read, rename, delete, or
overwrite it. `/study setup` may read only a valid mapping and otherwise stops.

## Setup Interview

Ask all before preview:

1. Subject display names.
2. Whether folders for each subject already exist.
3. For each subject, course-content status and, only if supplied by user, its
   location. Record `not-supplied-yet` explicitly when user provides none.

Normalize display name only by trimming outer whitespace and collapsing internal
whitespace. Keep spelling, casing, and punctuation otherwise. Use normalized
display name as direct folder name unless user explicitly supplies a different
folder name and it passes same checks.

Reject and ask again for empty names, `.` or `..`, absolute paths, `/` or `\`,
traversal, control characters, and case-insensitive duplicates. For every
folder destination, use lstat and require direct child of vault root only:

- Existing destination must be a real non-symlink directory.
- Missing destination may be created only after confirmation.
- Symlink target, non-directory collision, or resolved destination outside
  vault root stops setup.

Never inspect, create, change, or overwrite files inside a subject folder.

## YAML Serialization

Serialize every user-controlled `display_name`, `folder`, and `location` with
a defined safe YAML scalar encoder: JSON-style double-quoted YAML scalar using
correct JSON escaping. JSON strings are valid YAML scalars. Never interpolate,
hand-escape, or emit raw user text into YAML. Fixed keys and enum/status values
remain controlled literals. If an available host tool cannot safely encode and
round-trip each scalar, stop and ask user; do not write a mapping.

## Course-Content References

Record only locations and statuses user explicitly supplies. Prefer a
vault-relative location after validating it remains inside vault root and does
not traverse a symlink. Do not infer a location from folder contents.

For a source outside vault, write both:

```yaml
status: user-authorised-external
location_kind: external
```

plus exact user-supplied `location`. Do not open, copy, index, ingest, or
otherwise process external source unless current user task explicitly names and
authorises that source. This skill never invokes or depends on Course-RAG.

For no supplied course content, write only:

```yaml
status: not-supplied-yet
```

## Preview, Confirmation, Write

After interview and validation, show exact preview immediately before writing:

- resolved vault root;
- each subject folder as `CREATE` or `EXISTS — untouched`;
- exact `Study.md` create content, or exact owned-block replacement diff;
- explicit statement that subject files and unsupplied/external content remain
  untouched.

Ask exact confirmation: `Confirm this exact preview? Reply CONFIRM STUDY SETUP.`
Do not write after a vague assent, prior confirmation, or any other action.

After confirmation, re-resolve vault and re-check every target state. Stop if
vault roots conflict, `Study.md` state changed, folder state changed, a symlink
appeared, or any destination no longer meets this contract.

Initial setup creates only missing subject directories and new canonical
`Study.md`. Reconfiguration requires valid current mapping and replaces only
text between one owned block's markers, preserving every byte outside block.
It never creates missing `Study.md`, changes frontmatter, or overwrites subject
files. On malformed/duplicate markers or changed targets, stop with no writes.

## Fail-Closed Write Contract

This is a portable fail-closed contract, not claim of perfect race elimination.
Use it only when host tools provide every guarantee below; otherwise stop and
ask user rather than weakening it.

- Initial setup creates new `Study.md` with no-follow, exclusive-create
  semantics. If it already exists or appears at any recheck, stop; never open
  or replace it.
- Create a missing subject directory only with a no-follow create operation. If
  target appears during creation, fail closed, then revalidate it as required
  real direct-child directory before proceeding. Never reuse an unvalidated
  collision.
- Before reconfiguration, record canonical root, marker structure, original
  `Study.md` file identity, and digest. Build complete replacement bytes while
  preserving every byte outside owned block.
- Write those bytes to a newly exclusive-created, same-directory, non-symlink
  temporary file; fsync file and directory when host supports it. Recheck root,
  markers, original identity, and digest immediately before atomic
  same-directory replacement. Replacement must not follow a symlink.
- Clean a temporary file only when it is safely identified as this operation's
  non-symlink temporary file. On target swap, validation failure, or any
  unsupported no-follow/exclusive/identity/atomic-replace guarantee, stop with
  no mapping write.

## Later Schoolwork

Resolve vault, validate canonical `Study.md`, then use subject-folder mapping
only. Treat `not-supplied-yet` as no available course content. Treat external
references as labels, not permission to open them. Ask user for source when
needed; do not silently use a similarly named folder, file, alternate mapping,
or Course-RAG index.
