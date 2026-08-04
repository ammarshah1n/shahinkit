// shahinkit-guard.mjs — runtime guardrails for the ShahinKit OpenCode kit.
//
// Three protections, all fail-open (a guard error never breaks the session):
//   1. Bash wall-clock clamp: every bash call gets a timeout (10 min default,
//      30 min ceiling) so one hung command cannot eat hours.
//   2. Context hygiene: measured context use at or above 60% adds one optional
//      fresh-session recommendation without stopping work.
//   3. Notifications (macOS best-effort, silently skipped elsewhere): primary
//      session going idle and permission asks surface instead of silent stalls.

const BASH_DEFAULT_TIMEOUT_MS = 600_000
const BASH_MAX_TIMEOUT_MS = 1_800_000
const RECOMMEND_AT_PERCENT = 60
const IDLE_NOTIFY_DEBOUNCE_MS = 300_000

const contextUse = new Map()
const contextLimits = new Map()
const advised = new Set()
const idleNotifiedAt = new Map()
const primed = new Set()

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
      const sid = String(input?.sessionID ?? "")
      if (sid && !primed.has(sid)) {
        primed.add(sid)
        output.system.push(
          "[PRIME — OPTIONAL] Prime is available; inspect visible PROJECT_STATE/NEXT/HANDOFF for meaningful work. Continue current session; never require a fresh session.",
        )
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
