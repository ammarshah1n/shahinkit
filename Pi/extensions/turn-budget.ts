// Circuit breaker for unattended auto-chaining. Human input starts a fresh budget.
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export type Limits = { msgs: number; cost: number; minutes: number; turns: number };
export const DEFAULTS: Limits = { msgs: 250, cost: 40, minutes: 90, turns: 12 };
export const CHEAPER_MODEL_DEFAULTS: Limits = { msgs: 125, cost: 20, minutes: 45, turns: 6 };
const CONFIG = join(process.env.PI_CODING_AGENT_DIR || join(homedir(), ".pi", "agent"), "turn-budget.json");
const USAGE_LIMIT_RE = /usage limit|quota|insufficient.*credit|rate.?limit.*exceeded/i;

type State = { enabled: boolean; since: number; msgs: number; cost: number; turns: number; tripped?: string; warned: boolean; lastWasHuman: boolean };
export type Budget = { exhausted(): string | undefined; state(): Readonly<State>; limits(modelId?: string): Limits };
type Config = { enabled?: boolean; limits?: Partial<Limits>; cheaperModelPattern?: string; cheaperLimits?: Partial<Limits> };

function readConfig(): Config {
  try { return existsSync(CONFIG) ? JSON.parse(readFileSync(CONFIG, "utf8")) : {}; } catch { return {}; }
}
export function limitsFor(modelId: string | undefined, cfg: Config = readConfig()): Limits {
  let cheaper = false;
  try { cheaper = Boolean(cfg.cheaperModelPattern && new RegExp(cfg.cheaperModelPattern, "i").test(modelId ?? "")); } catch { /* Invalid optional pattern: use standard limits. */ }
  return cheaper
    ? { ...CHEAPER_MODEL_DEFAULTS, ...(cfg.cheaperLimits ?? {}) }
    : { ...DEFAULTS, ...(cfg.limits ?? {}) };
}
export function fresh(enabled = true): State { return { enabled, since: Date.now(), msgs: 0, cost: 0, turns: 0, warned: false, lastWasHuman: true }; }
export function over(s: State, l: Limits, now = Date.now()): string | undefined {
  if (!s.enabled) return undefined;
  if (s.tripped) return s.tripped;
  const mins = (now - s.since) / 60_000;
  if (s.msgs >= l.msgs) return `${s.msgs} assistant messages since your last prompt (limit ${l.msgs})`;
  if (s.cost >= l.cost) return `$${s.cost.toFixed(0)} spent since your last prompt (limit $${l.cost})`;
  if (mins >= l.minutes) return `${Math.round(mins)} min without your input (limit ${l.minutes} min)`;
  if (s.turns >= l.turns) return `${s.turns} auto-chained turns since your last prompt (limit ${l.turns})`;
  return undefined;
}
export function fraction(s: State, l: Limits, now = Date.now()): number {
  return Math.max(s.msgs / l.msgs, s.cost / l.cost, (now - s.since) / 60_000 / l.minutes, s.turns / l.turns);
}
export function summary(s: State, l: Limits, now = Date.now()): string {
  return `${s.msgs}/${l.msgs} msgs · $${s.cost.toFixed(0)}/$${l.cost} · ${Math.round((now - s.since) / 60_000)}/${l.minutes}m · ${s.turns}/${l.turns} chained`;
}

export default function turnBudget(pi: ExtensionAPI) {
  const cfg = readConfig();
  let s = fresh(cfg.enabled !== false);
  let modelId: string | undefined;
  let ui: any;
  const budget: Budget = { exhausted: () => over(s, limitsFor(modelId, cfg)), state: () => s, limits: (m) => limitsFor(m ?? modelId, cfg) };
  (globalThis as any).__piTurnBudget = budget;
  const publish = () => {
    if (!ui) return;
    if (!s.enabled) return ui.setStatus("budget", "budget: off");
    ui.setStatus("budget", `${s.tripped ? "⏸ budget: PAUSED — " : "budget: "}${summary(s, limitsFor(modelId, cfg))}`);
  };
  const reset = () => { s = fresh(s.enabled); publish(); };
  const trip = (ctx: any, reason: string) => {
    const first = !s.tripped;
    s.tripped = reason;
    publish();
    if (first) ctx.ui?.notify?.(`turn-budget: paused — ${reason}. Running jobs can finish; their results wait. Type anything to resume, or /budget off to disable.`, "warning");
    try { ctx.abort?.(); } catch { /* Abort is best-effort. */ }
  };
  pi.on("input", async () => { s.lastWasHuman = true; reset(); });
  pi.on("message_start", async (event: any) => {
    if (event.message?.role === "user" && !event.message.customType) { s.lastWasHuman = true; reset(); }
  });
  pi.on("agent_start", async (_event: any, ctx: any) => {
    ui = ctx.ui; modelId = ctx.model?.id;
    if (!s.lastWasHuman) s.turns++;
    s.lastWasHuman = false;
    const reason = over(s, limitsFor(modelId, cfg));
    if (reason) trip(ctx, reason);
    publish();
  });
  pi.on("turn_end", async (event: any, ctx: any) => {
    const m = event.message;
    if (!m || m.role !== "assistant") return;
    s.msgs++;
    s.cost += Number(m.usage?.cost?.total ?? 0) || 0;
    const l = limitsFor(modelId, cfg);
    if (m.stopReason === "error" && USAGE_LIMIT_RE.test(String(m.errorMessage ?? ""))) {
      trip(ctx, `provider reported a usage limit: ${String(m.errorMessage).slice(0, 80)}`); return;
    }
    const reason = over(s, l);
    if (reason) { trip(ctx, reason); return; }
    if (!s.warned && s.enabled && fraction(s, l) >= 0.75) {
      s.warned = true;
      pi.sendMessage({ customType: "turn-budget-warning", content: `[turn-budget] 75% of the unattended budget is used (${summary(s, l)}). Wrap up and report before auto-chaining pauses.`, display: true }, { deliverAs: "steer" });
    }
    publish();
  });
  pi.registerCommand("budget", {
    description: "Unattended-turn budget: status | off | on | reset",
    handler: async (args: string, ctx: any) => {
      ui = ctx.ui;
      const arg = (args || "").trim().toLowerCase();
      if (arg === "off") { s.enabled = false; s.tripped = undefined; publish(); return ctx.ui.notify("turn-budget OFF for this session — auto-chaining is unbounded.", "warning"); }
      if (arg === "on") { s = fresh(true); publish(); return ctx.ui.notify("turn-budget ON.", "info"); }
      if (arg === "reset") { s = fresh(s.enabled); publish(); return ctx.ui.notify("turn-budget counters reset.", "info"); }
      const l = limitsFor(modelId, cfg);
      ctx.ui.notify(`turn-budget ${s.enabled ? (s.tripped ? "PAUSED" : "on") : "OFF"} · ${summary(s, l)}${s.tripped ? ` · ${s.tripped}` : ""}`, "info");
    },
  });
}
