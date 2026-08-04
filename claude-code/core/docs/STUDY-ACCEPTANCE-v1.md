# Study Acceptance Checklist v1

Run each case in a disposable **existing** Obsidian vault. Inputs shown as
placeholders are user-provided values, not bundled school content. Before every
write, inspect preview; write only after exact `CONFIRM STUDY SETUP`.

| Case | Interview inputs | Preview / confirmation | Expected filesystem state |
|---|---|---|---|
| Clean vault | One or more valid `<subject>` names; folders `no`; each status `not-supplied-yet` | Shows each `CREATE`, new `Study.md`, exact generated content; no write before confirmation | After confirmation: only listed direct folders and canonical regular `Study.md`; no subject files |
| Existing folders/files | Valid `<subject>`; folder `yes`; no content supplied | Shows `EXISTS — untouched`; exact new `Study.md` | Existing directories and every pre-existing file byte unchanged; only `Study.md` added |
| Unmarked Study.md collision | Any valid interview inputs; pre-create ordinary `Study.md` | Stop before preview/confirmation | No folder or file changes; existing file never opened or changed |
| Malformed or duplicate markers | `/study setup`; pre-create regular generated-looking invalid `Study.md` | Stop before preview/confirmation | No changes; invalid mapping not used |
| Study.md symlink or nonregular | `/study` or `/study setup`; pre-create symlink, directory, FIFO, or device named `Study.md` | Stop before preview/confirmation | No changes; target never followed |
| Subject symlink or non-directory | Valid `<subject>` collides with symlink or regular file | Stop before confirmation | No changes; collision never followed or replaced |
| Traversal or duplicate | Names include empty, `.`, `..`, absolute, separator, traversal, control character, or case-insensitive duplicate | Reject input; no preview until corrected | No changes |
| Existing mapping traversal | Later schoolwork or `/study setup`; valid-looking owned block maps folder to `../x`, absolute path, separator path, or outside-root real path | Stop before using any subject or previewing reconfiguration | No mapping content used; no changes |
| Existing mapping symlink folder | Later schoolwork or `/study setup`; mapped direct child is symlink | Stop before using any subject or previewing reconfiguration | Symlink never followed; no changes |
| Existing mapping duplicate folder | Later schoolwork or `/study setup`; map two folders equal after case-folding | Stop before using any subject or previewing reconfiguration | No mapping content used; no changes |
| Existing mapping missing or non-directory | Later schoolwork or `/study setup`; mapped folder is missing or regular file | Stop before using any subject or previewing reconfiguration | No mapping content used; no changes |
| YAML scalar escaping round-trip | Display name, folder, or location contains `:`, `#`, quotes, backslash, newline-like text, or YAML-looking value | Preview contains JSON-style double-quoted scalars; parse and compare decoded scalar values | Decoded values exactly equal approved user inputs; no raw interpolation |
| No content yet | Valid `<subject>`; `not supplied yet` explicitly | Preview mapping shows only `status: not-supplied-yet` for subject | No content copied/indexed/opened; only confirmed folders and Study.md created |
| External reference | Valid `<subject>`; user explicitly supplies external location | Preview shows `status: user-authorised-external`, `location_kind: external`, exact supplied location | No external source opened, copied, indexed, or ingested; only confirmed vault changes |
| Reconfigure preserves outside notes | `/study setup`; valid mapping with text before/after owned block; revised valid inputs | Preview shows owned-block-only replacement diff | After confirmation every byte outside block unchanged; subject files untouched |
| Target changes after confirmation | Valid preview; before confirmation recheck, alter folder or Study.md state | Confirmation received, then recheck stops | No writes from setup/reconfiguration; changed target remains untouched by skill |
| Symlinked vault root component | Current note or cwd reaches vault through root, parent, or `.obsidian` symlink | Stop before reading `Study.md` or previewing writes | No mapping content used; no changes |
| Reconfiguration target swap | After initial identity/digest check, swap `Study.md`, root, markers, or owned block before replacement | Stop before replacement | Original/replacement target untouched; only safely identified temporary may be cleaned |
| Unsupported safe write tools | Host lacks no-follow exclusive create, file identity, non-symlink temporary, or atomic same-directory replace guarantee | Stop and ask user before confirmation/write | No folder or mapping write; contract never silently weakens |
| Conflicting note/cwd roots | Current note under existing vault A; cwd under existing vault B | Stop and ask user to choose; no confirmation | No changes to either vault |

Manual static review: confirm frontmatter opens line 1 and contains exactly one
`shahinkit_study: 1` and `vault_root: .`; then exact version marker, then one
owned block. Confirm no Course-RAG call, bundled subject/course payload, or
alternate mapping name, and only shared skill plus thin OpenCode wrapper render.
Confirm existing mappings validate every decoded folder as a contained real
direct-child directory before any subject is used.
