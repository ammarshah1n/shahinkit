# Mac map — where everything is

Last updated **22 September 2026**, written for the laptop swap.

> ⚠️ **This repo is public.** So is this file. It names repos and paths but
> contains **no** credentials, IPs, tokens or endpoints. If you want the
> full version with infrastructure detail, it belongs in a private repo.

Every file has exactly one home. Three of them:

1. **GitHub** — code, notes, documents. Versioned, instant, free.
2. **OneDrive `_HANDOFF`** — anything Git cannot hold: audio, video, big binaries.
3. **Nothing** — the gaps. Listed in §5.

---

## 1. Repositories

All under `github.com/ammarshah1n/` unless noted. Every one verified
**`ahead: 0`** (nothing unpushed) on 22 Sep 2026.

| Repo | Visibility | Local path | What it holds |
|---|---|---|---|
| `School` | private | `~/School` | Year 11 schoolwork — the Obsidian vault. Also `.sessions/` (98 AI transcripts) |
| `school-system` | private | `~/school-system` | School automation, transcriber ingest, subject vault mirror |
| `pi-sessions` | private | — | 33 non-school pi transcripts. Archive only, no working copy |
| `facilitated` | private | `~/facilitated` | Facilitated brand and client work |
| `facilitated-context` | private | `~/facilitated-context` | Context repo for all Facilitated AI tools |
| `AIF-Decisions-Vault` | private | `~/AIF-Decisions-Vault` | 420 AIF decision records |
| `time-manager-desktop` | private | `~/time-manager-desktop` | Time manager app. Branch **`unified`**, not `main` |
| `shahinkit` | **PUBLIC** | `~/shahinkit` | This repo — Claude/Codex/pi config kit |
| `llm-poker` | private | `~/llm-poker` | LLM poker experiment |
| `grantmate` | private | `~/Documents/grantmate` | GrantMate / Granto grant-discovery platform |
| `stratos` | private | `~/Documents/stratos` | STRATOS — PRD only so far |
| `remotely` | private | `~/Documents/remotely` | macOS remote app, notarisation CI |
| `PFF-Brain` | private | `~/Documents/PFF-Brain` | PFF due-diligence brain |
| `PFF-DD-V3` | private | `~/Documents/PFF-DD-V3` | PFF due-diligence v3 |
| `pff-legal-brain` | private | `~/Documents/pff-legal-brain` | PFF legal knowledge base |
| `yasser-claude` | private | `~/tmp-context/yasser-claude` | PA pack for Karen. **`YS-270/yasser-claude`**, branch **`pa-pack`** |

### Branch traps

- `time-manager-desktop` → **`unified`**, not `main`
- `yasser-claude` → **`pa-pack`**, not `main`, and `pa-pack` is not merged
- `shahinkit` is the only **public** one. Triple-check before pushing anything here.

### Repos with no remote

| Path | Size | Note |
|---|---|---|
| `~/Documents/vpn` | 52 KB | The school-wifi proxy stack. **No Git, no backup.** Repaired Mac's copy is better — do not overwrite |
| `~/Transcriber` | 7.9 GB | Remote is `pffteam/transcriber` (shared org). Local state is broken — see §5 |

### Unpushed-count trap

`git log @{u}..` reports **zero** when no upstream is configured — it does
not error. That hid three weeks of uncommitted work in `School`.

```sh
git rev-list --count origin/main..main    # use this
```

---

## 2. OneDrive handoff bundle — 16 GB

```
OneDrive-PrinceAlfredCollege/School/_HANDOFF/2026-09-22/
├── HANDOFF.md                  ← READ FIRST. What's done, what's in flight
├── SETUP-NEW-MAC.md            ← clone commands, brew list, what to re-log-in
├── SESSION-SUMMARY.md          ← what the 59 AI sessions were doing
├── EXPOSURE-NOTE.md            ← brief public exposure of session archive
├── RE-SYNC-AFTER-LESSON.md     ← one outstanding action
├── media/
│   ├── transcriber-recordings/     87 files,  6.2 GB  lecture audio
│   ├── english-lit-film/          204 files,  9.1 GB  AT2 footage + audio
│   └── school-system-audio/        45 files,  854 MB  vault/_Other/99 Assets
└── local-only/
    ├── downloads-school/            8 files  school docs from Downloads
    ├── photo-booth/                21 files  Photo Booth images
    └── PROMPT-FOR-DAD.md
```

All three media folders were verified **byte-exact** against source.

### Why these are here and not in Git

GitHub hard-caps files at 100 MB, so every repo `.gitignore`s video and
audio. Roughly 16 GB of your material therefore cannot live in Git at
all. It only exists in this folder.

---

## 3. Everything in Git, by subject

`School` and `school-system` were the two repos with real backlogs.

**`School`** — 3 weeks uncommitted, pushed 22 Sep (`cd35dd3`, 400 files):
AIF (full reference library), Economics (AD-AS revision, exam prep),
English Literary Studies, General Mathematics (basketball folio),
IB History (Kings Speech, Japan/Tojo), Legal Studies, Society & Culture.

**`school-system`** — pushed 22 Sep (`e8c9562`, 83 files): subject
material under `vault/03 School`, plus a stranded OCR-planner commit.

**`PFF-DD-V3`** — pushed 22 Sep (`ce69540`): session log, build state,
corrections log, two new files.

**AI transcripts** — split by ownership:
- `School/.sessions/` — 98 transcripts (12 pi, 86 Claude Code), by subject
- `pi-sessions` — the other 33 pi transcripts (tooling, vpn, grantmate, cars)

Both base64-stripped: 633 MB → 50 MB, all conversation text intact.

---

## 4. What to bring when you switch

**Nothing by hand.** Everything is in GitHub or OneDrive. On the new Mac:

```sh
# 1. Clone (see SETUP-NEW-MAC.md for the loop)
# 2. Check for work that exists ONLY on the repaired Mac
git status && git rev-list --count origin/main..main
# 3. Pull the OneDrive bundle down and leave it — it's already synced
```

**Clone, never clone over.** If a repo already exists on the repaired
Mac, `git pull` and check `git status` first. It may hold work that
exists nowhere else — `cc pff` / team-tools and `SANXT` were found on
neither this Mac nor GitHub.

### Order of operations

1. **Check the repaired Mac first** for `cc pff`, team-tools, `SANXT`
2. **Plug in `/Volumes/the drive`** — never scanned, see §5
3. Clone the repos, `git status` each one
4. Copy `~/bin` scripts and `.zshrc` across (review, they hardcode paths)
5. Copy `~/.pi/agent` (agents, skills, extensions, themes) — **not** `auth.json`
6. Re-log-in to every provider by hand
7. Verify OneDrive finished uploading the 16 GB bundle

---

## 5. Gaps — not backed up anywhere

| What | Size | Why it matters |
|---|---|---|
| `/Volumes/the drive/Facilitated` | ? | Cursor workspaces on an external disk. **Never connected during any scan.** Biggest unknown |
| `~/Pictures/Photos Library` | 16 GB | iCloud syncs it via your Apple ID — not a handoff item, but not in this bundle either |
| `~/Transcriber` source state | — | 10 tracked files show as DELETED locally vs the `pffteam/transcriber` remote. Committing would push deletions into a **shared** repo. Recordings are safe in the bundle regardless — resolve this before touching |
| `cc pff`, team-tools, `SANXT` | ? | Absent on this Mac and on GitHub. If they exist, the repaired Mac is the only copy |

---

## 6. Never copy these — re-log-in instead

| Path | What |
|---|---|
| `~/.pi/agent/auth.json` | pi provider tokens |
| `~/.codex/auth.json` | Codex auth |
| `~/.claude.json` | Claude Code auth |
| `~/.config/exa/api_key` | Exa search key |
| `~/.ssh/id_ed25519` | SSH private key — generate a **new** one per machine |
| `~/Transcriber/.env` | live API keys |
| `~/.claude/settings.local.json`, `mcp.json` | may hold endpoints and tokens |
| `~/.claude/history.jsonl`, all `sessions/`, `~/.codex/memories/` | contain pasted secrets |
| `.zsh_history` | same |

### Rotate these — found during the scan, none copied anywhere

1. **Token embedded in the `PFF-DD-V3` git remote URL** — a
   password-equivalent in plain text in `.git/config`. Revoke, reissue,
   set the remote without it.
2. **A credential pasted into an AI session transcript** earlier in the
   week. Never rotated. Assume compromised. It did **not** appear in the
   archived sessions.
3. **`~/Transcriber/.env`** — if it was ever shared.

---

## 7. Known hazards on this machine

- **`codex` bypasses its own sandbox.** `.zshrc` aliases it to
  `--dangerously-bypass-approvals-and-sandbox`. Typing `codex` runs with
  approvals and sandboxing **off**. `codex-raw` is the safe one.
- **`shahinkit` is public.** The session archive was briefly pushed there
  and force-removed. See `EXPOSURE-NOTE.md` in `pi-sessions`.
- **VPN is not to be touched.** Repaired Mac's copy is better. Don't copy
  `~/bin/vpn`, `~/.config/vpn/` or the `com.ammar.vpn-*` LaunchAgents over.
- **Never restart privoxy or the tunnel while AI sessions are live** — it
  tears down every in-flight connection.
- **`2026-09-22_1040_aif.wav`** was copied mid-recording. Re-sync it — see
  `RE-SYNC-AFTER-LESSON.md`.
