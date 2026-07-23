#!/usr/bin/env node
// shahinkit-reflect.mjs — post-session reflection loop (added 2026-07-23 v2).
//
// Reads recently-finished PRIMARY OpenCode sessions from the sqlite store,
// digests each (duration, dispatch count, stalls, abort errors, frustrated
// user messages, final state), asks GPT-5.5 via `codex exec` to extract
// failure candidates, and appends them to corrections/pending.md.
//
// Promotion filter (Anthropic memory doctrine): a failure CLASS seen on >=2
// distinct days gets a ready-to-paste rule proposed under PROPOSED PROMOTIONS
// — the user approves by moving it into AGENTS.md. Nothing self-installs.
//
// Sundays: appends a WEEKLY EYEBALL section — the 3 worst moments for a
// one-minute human review (automated judges miss systematic bias).
//
// Usage: node shahinkit-reflect.mjs [--dry]   (--dry: digest only, no LLM, no append)
// Scheduled: launchd your scheduler of choice (launchd, cron).

import { execFileSync, execSync } from "node:child_process"
import { readFileSync, writeFileSync, appendFileSync, existsSync, mkdirSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

const HOME = homedir()
const DB = join(HOME, ".local/share/opencode/opencode.db")
const OUT_DIR = join(HOME, ".config/opencode/corrections")
const PENDING = join(OUT_DIR, "pending.md")
const PROCESSED = join(OUT_DIR, ".processed")
const DRY = process.argv.includes("--dry")

mkdirSync(OUT_DIR, { recursive: true })
const processed = new Set(existsSync(PROCESSED) ? readFileSync(PROCESSED, "utf8").split("\n").filter(Boolean) : [])

const sql = (q) => execFileSync("sqlite3", ["-separator", "", DB, q], { encoding: "utf8" }).trim()

// Primary sessions, finished (no update for 30+ min), touched in last 36h, non-trivial.
const rows = sql(`
  select s.id, s.title,
    (s.time_updated - s.time_created)/60000,
    (select count(*) from session c where c.parent_id = s.id),
    (select count(*) from message m where m.session_id = s.id and json_extract(m.data,'$.role')='assistant')
  from session s
  where s.parent_id is null
    and s.time_updated > (strftime('%s','now')*1000 - 36*3600*1000)
    and s.time_updated < (strftime('%s','now')*1000 - 30*60*1000)
`).split("\n").filter(Boolean).map((l) => {
  const [id, title, mins, children, turns] = l.split("")
  return { id, title, mins: +mins, children: +children, turns: +turns }
}).filter((s) => !processed.has(s.id) && (s.turns >= 10 || s.children >= 5))

if (!rows.length) { console.log("shahinkit-reflect: nothing new to reflect on"); process.exit(0) }

function digest(s) {
  const userMsgs = sql(`
    select substr(coalesce(json_extract(p.data,'$.text'),''),1,300)
    from message m join part p on p.message_id = m.id
    where m.session_id='${s.id}' and json_extract(m.data,'$.role')='user'
      and json_extract(p.data,'$.type')='text' order by m.time_created
  `).split("\n").filter(Boolean)
  const gaps = sql(`
    with t as (select time_created, lag(time_created) over (order by time_created) prev
               from message where session_id='${s.id}')
    select datetime(prev/1000,'unixepoch','localtime')||' -> '||((time_created-prev)/60000)||'min'
    from t where (time_created-prev) > 30*60000
  `).split("\n").filter(Boolean)
  const lastTexts = sql(`
    select substr(coalesce(json_extract(p.data,'$.text'),''),1,400)
    from message m join part p on p.message_id = m.id
    where m.session_id='${s.id}' and json_extract(m.data,'$.role')='assistant'
      and json_extract(p.data,'$.type')='text' and json_extract(p.data,'$.text') != ''
    order by m.time_created desc limit 5
  `).split("\n").filter(Boolean)
  return { title: s.title, minutes: s.mins, subagent_dispatches: s.children, turns: s.turns,
           stalls_over_30min: gaps, user_messages: userMsgs, final_assistant_texts: lastTexts }
}

const digests = rows.map((s) => ({ id: s.id, ...digest(s) }))

if (DRY) { console.log(JSON.stringify(digests, null, 2)); process.exit(0) }

const prompt = `You are a post-mortem analyst for AI agent sessions. Below are digests of finished OpenCode orchestrator sessions (title, duration, dispatch counts, >30min stalls, all user messages, final assistant texts).

Extract FAILURE CANDIDATES only — places the agent wasted time, ignored the user, stalled, over-dispatched, looped, made stale claims, or needed repeated user pushes. User frustration (profanity, "continue", "are you done", repeated commands) is a strong failure signal at that timestamp.

Return STRICT JSON array, no prose: [{"session":"<id>","slug":"<kebab-failure-class>","evidence":"<one sentence w/ timestamp or quote>","proposed_rule":"<one imperative doctrine sentence that would have prevented it>"}]. Empty array if a session was genuinely clean.

${JSON.stringify(digests, null, 1)}`

let findings = []
try {
  const raw = execSync("codex exec --sandbox read-only -", { input: prompt, encoding: "utf8", timeout: 300000 })
  const m = raw.match(/\[[\s\S]*\]/)
  if (m) findings = JSON.parse(m[0])
} catch (e) {
  console.error("shahinkit-reflect: codex pass failed:", String(e).slice(0, 200))
  process.exit(1) // don't mark processed — retry tomorrow
}

const today = new Date().toISOString().slice(0, 10)
let block = `\n## ${today}\n`
for (const f of findings) block += `- [${f.slug}] (${f.session}) ${f.evidence}\n  - rule: ${f.proposed_rule}\n`
if (!findings.length) block += `- clean: no failure candidates in ${rows.length} session(s)\n`
appendFileSync(PENDING, block)

// Promotion: slug seen on >=2 distinct days -> propose.
const pending = readFileSync(PENDING, "utf8")
const daysBySlug = new Map()
for (const m of pending.matchAll(/^## (\d{4}-\d{2}-\d{2})$|^- \[([a-z0-9-]+)\]/gm)) { /* two-pass below */ }
let day = ""
for (const line of pending.split("\n")) {
  const d = line.match(/^## (\d{4}-\d{2}-\d{2})/); if (d) { day = d[1]; continue }
  const s = line.match(/^- \[([a-z0-9-]+)\]/)
  if (s && day) {
    if (!daysBySlug.has(s[1])) daysBySlug.set(s[1], new Set())
    daysBySlug.get(s[1]).add(day)
  }
}
const promoted = [...daysBySlug.entries()].filter(([, d]) => d.size >= 2).map(([slug]) => slug)
const alreadyProposed = new Set([...pending.matchAll(/^- PROMOTE \[([a-z0-9-]+)\]/gm)].map((m) => m[1]))
const newPromotions = promoted.filter((s) => !alreadyProposed.has(s))
if (newPromotions.length) {
  let p = `\n## PROPOSED PROMOTIONS (${today}) — recurred on 2+ days; paste approved rules into AGENTS.md\n`
  for (const slug of newPromotions) {
    const rule = [...pending.matchAll(new RegExp(`^- \\[${slug}\\][^\\n]*\\n  - rule: (.+)$`, "gm"))].map((m) => m[1]).pop()
    p += `- PROMOTE [${slug}]: ${rule ?? "(see entries above)"}\n`
  }
  appendFileSync(PENDING, p)
}

// Sunday: weekly eyeball — 3 worst moments for human review.
if (new Date().getDay() === 0 && findings.length) {
  const worst = findings.slice(0, 3)
  appendFileSync(PENDING, `\n## WEEKLY EYEBALL (${today}) — 60-second human review\n` +
    worst.map((f) => `- ${f.evidence}\n`).join(""))
}

appendFileSync(PROCESSED, rows.map((r) => r.id).join("\n") + "\n")
console.log(`shahinkit-reflect: ${findings.length} finding(s) from ${rows.length} session(s); promotions proposed: ${newPromotions.length}`)
try {
  execFileSync("osascript", ["-e",
    `display notification "${findings.length} findings, ${newPromotions.length} promotion(s) proposed" with title "Sol reflection"`])
} catch {}
