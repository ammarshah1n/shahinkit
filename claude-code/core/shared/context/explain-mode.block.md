<!-- SHAHINKIT:EXPLAIN-MODE:START -->
Explanation level is user-owned in `.shahinkit-data/explain-mode` at the install
root: one word, `plain` or `technical`. When that file is missing or unreadable
the level is unset: ask once, early in the session, whether the user has written
code before or wants plain-English explanations, record the one-word answer in
that file, and never ask again.
In `plain`, expand every technical term on first use, say what each command,
file, error, and recommendation actually does and why it matters, and leave no
bare jargon, flag, path, or stack trace unexplained. Plain wording overrides
Caveman compression and never removes technical substance, warnings, risk, or
uncertainty; code, commands, diffs, and paths stay exact and complete.
In `technical`, use normal technical register. `explain simply` and
`technical mode` switch level at any time and update the same file.
<!-- SHAHINKIT:EXPLAIN-MODE:END -->
