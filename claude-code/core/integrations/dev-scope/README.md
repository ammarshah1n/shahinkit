# dev-scope

Optional local, read-only stdio MCP for explicitly configured source roots. Requires Node 18+.

## Setup

1. Copy `config.example.json` to `config.json`.
2. Set each root's stable `id`, relative `path`, approved `locations`, and readable `extensions`.
3. Install locked dependencies with `npm ci`.
4. Start with `node index.js`. Optional `DEV_SCOPE_CONFIG` selects another local config file.

`config.json` is operator-local and intentionally not included. It must contain only fixed, explicit roots; inputs select a root ID plus a relative path. Root filesystem paths are never returned by tools.

## Safety boundary

Tools only list projects, overview approved locations, read/list/search approved text, and obtain read-only Git metadata. Pathname-reading Git commands are intentionally unavailable: portable Node cannot safely bind later reads to verified file identity without stronger sandbox or snapshot support. There is no shell tool, environment loading, network transport, write operation, or command execution tool. Standard output is reserved for MCP stdio protocol; diagnostics use stderr.

Paths reject empty, absolute, dot, dot-dot, backslash, and malformed components. Every operation performs pre/post `lstat` + `realpath` + inode identity checks for canonical root, parents, and final path; regular files also use `O_NOFOLLOW` where platform supports it before opened-object identity recheck. Files with more than one hard link are denied before read/search. Directory walks stream through `opendir`, use `lstat`, and do not follow symlinks. Node does not expose descriptor-backed inode enumeration for `opendir`, so detected path/root mutation fails closed; code does not claim directory enumeration is race-free. Secret-named files are denied; shell exports, embedded JS/JSON/YAML properties, multiline YAML values, Authorization and common sensitive HTTP headers, cookie headers, header setter calls, and detected secret tokens are redacted while surrounding safe fields remain visible.

These checks reduce races but cannot make a hostile same-user rename or hard-link race-free: a root can change between checks without operating-system isolation. Use a read-only OS sandbox/mount for every hostile root, or only trusted roots.

Search is literal only and bounded by configured depth, file count, per-file bytes, total bytes, matches, output bytes, and elapsed time. Pruned eligible descendants and skipped work from file, byte, or time budgets mark results partial. Every response, including combined truncation/search-limit markers, stays within `maxOutputBytes`; partial matched results remain labeled. Git resolves only compiled-in system git locations, uses a sanitized environment, fixed read-only arguments, and disables fsmonitor, hooks, pager, external diff, text conversion, and option injection with `--` before requested pathspecs.
