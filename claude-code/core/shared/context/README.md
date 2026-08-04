# Shared Context Blocks

These bounded blocks are canonical portable insertions for future host adapters.
Adapters copy each block unchanged between its start and end marker. They may add
host syntax outside markers, but may not add personal data, paths, credentials,
transcripts, private memory, or repository-relative references inside a block.

Every block stands alone after installation. It states its policy directly and
does not require source-checkout files to be present at destination.

| Block | Purpose |
|---|---|
| `core-policy.block.md` | Policy precedence and canonical rule references. |
| `ponytail-default.block.md` | Ponytail `full` default and opt-out contract. |
| `caveman-default.block.md` | Caveman `full` default and Auto-Clarity contract. |
| `adapter-references.block.md` | Portable references an adapter may render. |

Do not treat these blocks as executable hooks or hard enforcement. Host trust,
activation, lifecycle registration, and rendered configuration belong to later
adapter and manager work.
