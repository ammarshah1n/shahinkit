// shahinkit-guard.mjs — runtime guardrails for the ShahinKit OpenCode kit.
//
// Three protections, all fail-open (a guard error never breaks the session):
//   1. Bash wall-clock clamp: every bash call gets a timeout (10 min default,
//      30 min ceiling) so one hung command cannot eat hours.
//   2. Context hygiene: measured context use at or above 60% adds one optional
//      fresh-session recommendation without stopping work.
//   3. Notifications (macOS best-effort, silently skipped elsewhere): primary
//      session going idle and permission asks surface instead of silent stalls.

// `require` does not exist in an ES module, so these must be static imports:
// resolving them lazily made every read below throw ReferenceError into the
// fail-open catch, silently disabling the path opt-out.
import { existsSync, readFileSync } from "node:fs"
import { resolve, dirname, join, sep } from "node:path"
import { fileURLToPath } from "node:url"

const BASH_DEFAULT_TIMEOUT_MS = 600_000
const BASH_MAX_TIMEOUT_MS = 1_800_000
const RECOMMEND_AT_PERCENT = 60
const IDLE_NOTIFY_DEBOUNCE_MS = 300_000

const contextUse = new Map()
const contextLimits = new Map()
const advised = new Set()
const idleNotifiedAt = new Map()
const primed = new Set()
const asked = new Set()

const PLAIN_INSTRUCTION =
  "[PLAIN-ENGLISH MODE ACTIVE] Expand every technical term on first use, say what each command, file, error, and recommendation does and why it matters, and leave no bare jargon unexplained. Plain wording overrides Caveman compression and never removes substance, warnings, or uncertainty; code, commands, and paths stay exact."

const EXPLAIN_ASK =
  "[EXPLANATION LEVEL UNSET] Ask the user once this session whether they have written code before or want plain-English explanations, then record `plain` or `technical` in the `explain-mode` file inside this install's `.shahinkit-data` directory. Ask once; never ask again once it exists."

// Explanation level, parity with the Python lifecycle hook: read per turn
// because the user can switch mid-session, and because static instruction
// context decays. `plain`/`technical` is a recorded answer, `null` is an
// install that has not answered yet, and `undefined` is no install data
// directory at all, which stays silent.
function explainMode() {
  try {
    const here = dirname(fileURLToPath(import.meta.url))
    for (const base of [dirname(here), dirname(dirname(here)), here]) {
      const directory = join(base, ".shahinkit-data")
      if (!existsSync(directory)) continue
      let raw
      try {
        raw = readFileSync(join(directory, "explain-mode"), "utf8")
      } catch {
        return null
      }
      const value = raw.trim().toLowerCase()
      return value === "plain" || value === "technical" ? value : null
    }
  } catch {}
  return undefined
}

// Path opt-out, parity with the Python lifecycle hook: when the working
// directory sits at or under a listed prefix, ShahinKit stays silent here.
function optedOut() {
  try {
    const here = dirname(fileURLToPath(import.meta.url))
    for (const base of [dirname(here), dirname(dirname(here)), here]) {
      let raw
      try {
        raw = readFileSync(join(base, ".shahinkit-data", "opt-out"), "utf8")
      } catch {
        continue
      }
      const cwd = resolve(process.cwd())
      return raw
        .split("\n")
        .map((line) => line.split("#")[0].trim())
        .filter(Boolean)
        .some((entry) => {
          const prefix = resolve(entry)
          return cwd === prefix || cwd.startsWith(prefix + sep)
        })
    }
  } catch {}
  return false
}

async function contextLimit(client, providerID, modelID) {
  const key = `${providerID}/${modelID}`
  const cached = contextLimits.get(key)
  if (cached) return cached
  try {
    const response = await client.config.providers()
    const data = response?.data ?? response
    const provider = (data?.providers ?? []).find((item) => item?.id === providerID)
    const models = provider?.models ?? {}
    const model = models[modelID] ?? Object.values(models).find((item) => item?.id === modelID)
    const limit = Number(model?.limit?.context)
    if (Number.isFinite(limit) && limit > 0) {
      contextLimits.set(key, limit)
      return limit
    }
  } catch {}
  return 0
}

function notify(title, body) {
  try {
    if (process.platform !== "darwin") return
    const esc = (s) => String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"').slice(0, 200)
    Bun.spawn(["osascript", "-e",
      `display notification "${esc(body)}" with title "${esc(title)}" sound name "Glass"`,
    ], { stdout: "ignore", stderr: "ignore" })
  } catch {}
}

export const ShahinkitGuard = async ({ client }) => {
  return {
    "tool.execute.before": async (input, output) => {
      const tool = (input?.tool ?? "").toLowerCase()
      if (tool === "bash") {
        const args = output?.args ?? {}
        const requested = Number(args.timeout)
        args.timeout = Number.isFinite(requested) && requested > 0
          ? Math.min(requested, BASH_MAX_TIMEOUT_MS)
          : BASH_DEFAULT_TIMEOUT_MS
        if (output) output.args = args
      }
    },

    "experimental.chat.system.transform": async (input, output) => {
      if (optedOut()) return
      const sid = String(input?.sessionID ?? "")
      if (sid && !primed.has(sid)) {
        primed.add(sid)
        output.system.push(
          "[PRIME — OPTIONAL] Prime is available; inspect visible PROJECT_STATE/NEXT/HANDOFF for meaningful work. Continue current session; never require a fresh session.",
        )
      }
      const level = explainMode()
      if (level === "plain") output.system.push(PLAIN_INSTRUCTION)
      else if (level === null && sid && !asked.has(sid)) {
        asked.add(sid)
        output.system.push(EXPLAIN_ASK)
      }
      const percent = contextUse.get(sid) ?? 0
      if (!sid || percent < RECOMMEND_AT_PERCENT || advised.has(sid)) return
      advised.add(sid)
      output.system.push(
        `[CONTEXT HYGIENE — OPTIONAL] Measured context use is ${percent}%. ` +
        `At the next natural checkpoint, briefly offer a fresh session as an option. ` +
        `Continue automatically; never stop, wait, or imply a reset is required unless a real safety, technical, or user-decision blocker exists.`,
      )
    },

    "permission.ask": async (input) => {
      notify("Agent needs a decision", String(input?.title ?? input?.type ?? "permission request"))
    },

    event: async ({ event }) => {
      if (event?.type === "session.deleted") {
        const sid = String(event?.properties?.sessionID ?? "")
        contextUse.delete(sid)
        advised.delete(sid)
        asked.delete(sid)
        idleNotifiedAt.delete(sid)
        primed.delete(sid)
        return
      }
      if (event?.type === "message.updated") {
        const info = event?.properties?.info
        if (info?.role !== "assistant" || !info?.finish) return
        const sid = String(info?.sessionID ?? "")
        const providerID = String(info?.providerID ?? "")
        const modelID = String(info?.modelID ?? "")
        const input = Number(info?.tokens?.input)
        if (!sid || !providerID || !modelID || !Number.isFinite(input) || input <= 0) return
        const limit = await contextLimit(client, providerID, modelID)
        if (limit) contextUse.set(sid, Math.min(100, Math.round((input / limit) * 100)))
        return
      }
      if (event?.type !== "session.idle") return
      const sid = String(event?.properties?.sessionID ?? "")
      const now = Date.now()
      if (!sid || now - (idleNotifiedAt.get(sid) ?? 0) < IDLE_NOTIFY_DEBOUNCE_MS) return
      try {
        const s = await client.session.get({ path: { id: sid } })
        const info = s?.data ?? s
        if (info && !info.parentID && !info.parent_id) {
          idleNotifiedAt.set(sid, now)
          notify("Agent stopped", String(info.title ?? sid).slice(0, 120))
        }
      } catch {}
    },
  }
}
