# Install Receipt Schema

Destination-local `.shahinkit-install-receipt.json` uses schema version `2`.
It records only alias-relative owned paths, output SHA-256 values, managed-block or
structural-change metadata, adapter, scope, selected features, receipt ID,
backup ID, and source provenance identity. `integrity_sha256` is SHA-256 of
canonical JSON for every receipt field except itself. Absolute paths, machine
labels, credentials, tokens, and source state never belong in receipt or log.
Each owned output is addressed by `root` or `home` plus normalized relative
path. `root` is selected host/project root; `home` is `$HOME` only for declared
Codex user outputs (or `<DESTINATION>/home` in isolated runs). Receipt paths are
recomputed from current verified render maps before update, uninstall, or
rollback; receipt never expands ownership. Schema v2 also retains alias-relative
exact preimages for uninstall restoration; no absolute paths are stored.

Backups live under destination `.shahinkit-backups/`, are mode `0600`, and keep
at most three records. A backup contains only changed managed files, managed
blocks, or an absent-file marker. Rollback first verifies every owned output is
unchanged, then restores that exact preimage and previous receipt (or removes
first-install receipt). It never guesses ownership.

`uninstall` also verifies every owned output digest before removing a full
owned file, a delimited block, or safely-added structural JSON entries. Any
user modification stops operation and reports path. `update` rechecks receipt
integrity, current ownership, render integrity, provenance, and conflicts.
