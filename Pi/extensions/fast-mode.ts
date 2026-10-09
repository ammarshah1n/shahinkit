// Fast mode: opt-in Codex priority tier and separately opt-in Anthropic fast mode.
// State is stored in the active Pi config directory; both modes default off.
import { appendFileSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { getAgentDir, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const STATE_PATH = join(getAgentDir(), "fast-mode.json");
const FAST_BETA = "fast-mode-2026-02-01";
const ANTHROPIC_FAST_MODELS = /^claude-opus-(?:5|4-8)(?:$|[.:])/;
const NEVER_FAST = /^gpt-.*-astra(?:$|[-.:])/i;

function readState(): { fast: boolean; claude: boolean } {
  try {
    const raw = JSON.parse(readFileSync(STATE_PATH, "utf8"));
    return { fast: raw.fast === true, claude: raw.claude === true };
  } catch {
    return { fast: false, claude: false };
  }
}

let { fast, claude } = readState();

function anthropicFast(ctx: any): boolean {
  return ctx?.model?.provider === "anthropic"
    && ANTHROPIC_FAST_MODELS.test(String(ctx.model?.id ?? ""))
    && readState().claude;
}

export default function (pi: ExtensionAPI) {
  pi.on("before_provider_headers", async (event, ctx: any) => {
    if (!anthropicFast(ctx)) return;
    const compat = ctx.model?.compat ?? {};
    const betas = ["claude-code-20250219", "oauth-2025-04-20"];
    if (compat.supportsEagerToolInputStreaming === false) betas.push("fine-grained-tool-streaming-2025-05-14");
    if ((compat.allowedFallbackModels?.length ?? 0) > 0) betas.push("server-side-fallback-2026-07-01");
    betas.push(FAST_BETA);
    event.headers["anthropic-beta"] = betas.join(",");
  });

  pi.on("before_provider_request", async (event, ctx) => {
    const body = event.payload as Record<string, unknown> | null;
    if (!body || typeof body !== "object") return;
    if (ctx.model?.provider === "anthropic") {
      if (anthropicFast(ctx)) body.speed = "fast";
      else delete body.speed;
      return body;
    }
    if (ctx.model?.provider !== "openai-codex") return;
    if (NEVER_FAST.test(String(ctx.model?.id ?? "")) || NEVER_FAST.test(String(body.model ?? ""))) {
      delete body.service_tier;
      return body;
    }
    ({ fast, claude } = readState());
    if (!fast) return;
    body.service_tier = "priority";
    const log = process.env.PI_FAST_LOG;
    if (log) {
      try { appendFileSync(log, `${JSON.stringify({ model: body.model, service_tier: body.service_tier })}\n`); } catch {}
    }
    return body;
  });

  pi.registerCommand("fast", {
    description: "Toggle Fast mode; Claude fast mode is separately opt-in and billed as extra usage",
    handler: async (args: string, ctx: any) => {
      const arg = (args || "").trim().toLowerCase();
      ({ fast, claude } = readState());
      if (arg === "status") {
        ctx.ui.notify(`Fast mode is ${fast ? "ON" : "OFF"}. Claude fast mode is ${claude ? "ON" : "OFF"}.`, "info");
        return;
      }
      if (arg.startsWith("claude")) {
        const sub = arg.slice("claude".length).trim();
        claude = sub === "on" ? true : sub === "off" ? false : !claude;
        writeFileSync(STATE_PATH, JSON.stringify({ fast, claude }));
        ctx.ui.notify(claude
          ? "Claude fast mode ON — supported Opus models only; this bills as extra usage, not your plan."
          : "Claude fast mode OFF — Claude models run on the plan as usual.", "warning");
        return;
      }
      fast = arg === "on" ? true : arg === "off" ? false : !fast;
      writeFileSync(STATE_PATH, JSON.stringify({ fast, claude }));
      ctx.ui.notify(fast
        ? "Fast mode ON — Codex priority tier; astra models stay standard."
        : "Fast mode OFF — standard tier.", "info");
    },
  });
}
