// shahinkit-guard.mjs — runtime guardrails for the ShahinKit OpenCode kit.
//
// Three protections, all fail-open (a guard error never breaks the session):
//   1. Bash wall-clock clamp: every bash call gets a timeout (10 min default,
//      30 min ceiling) so one hung command cannot eat hours.
//   2. Session budget tripwire: past 25 worker dispatches or 4h wall clock,
//      a system-prompt directive forces a plain go/no-go checkpoint with the
//      user before any further dispatch.
//   3. Notifications (macOS best-effort, silently skipped elsewhere): primary
//      session going idle, permission asks, and tripwire hits surface as
//      desktop notifications instead of silent stalls.

const BASH_DEFAULT_TIMEOUT_MS = 600_000
const BASH_MAX_TIMEOUT_MS = 1_800_000
const DISPATCH_LIMIT = 25
const WALL_CLOCK_LIMIT_MS = 4 * 60 * 60 * 1000
const IDLE_NOTIFY_DEBOUNCE_MS = 300_000

const dispatchCount = new Map()
const firstSeen = new Map()
const tripNotified = new Set()
const idleNotifiedAt = new Map()

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
      const sid = String(input?.sessionID ?? "")
      if (sid && !firstSeen.has(sid)) firstSeen.set(sid, Date.now())
      const tool = (input?.tool ?? "").toLowerCase()
      if (tool === "bash") {
        const args = output?.args ?? {}
        const requested = Number(args.timeout)
        args.timeout = Number.isFinite(requested) && requested > 0
          ? Math.min(requested, BASH_MAX_TIMEOUT_MS)
          : BASH_DEFAULT_TIMEOUT_MS
        if (output) output.args = args
      }
      if (sid && (tool === "task" || tool === "agent")) {
        dispatchCount.set(sid, (dispatchCount.get(sid) ?? 0) + 1)
      }
    },

    "experimental.chat.system.transform": async (input, output) => {
      const sid = String(input?.sessionID ?? "")
      if (!sid) return
      const dispatches = dispatchCount.get(sid) ?? 0
      const ageMs = Date.now() - (firstSeen.get(sid) ?? Date.now())
      if (dispatches < DISPATCH_LIMIT && ageMs < WALL_CLOCK_LIMIT_MS) return
      const why = dispatches >= DISPATCH_LIMIT
        ? `${dispatches} worker dispatches`
        : `${Math.round(ageMs / 360000) / 10}h wall clock`
      output.system.push(
        `[SESSION BUDGET TRIPWIRE] This session has consumed ${why} — past its budget. ` +
        `Before ANY further work: update the task progress file, present the user a plain go/no-go checkpoint ` +
        `(done / left / continue here or fresh session), and wait for their answer. Recommend a fresh session.`,
      )
      if (!tripNotified.has(sid)) {
        tripNotified.add(sid)
        notify("Session budget hit", `${why} — go/no-go checkpoint forced`)
      }
    },

    "permission.ask": async (input) => {
      notify("Agent needs a decision", String(input?.title ?? input?.type ?? "permission request"))
    },

    event: async ({ event }) => {
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
