// fast-mode — Codex-style Fast mode for the openai-codex provider.
// Stamps service_tier: "priority" onto every openai-codex request body via the
// before_provider_request hook (faster processing, higher usage burn — same dial
// as Codex's Fast mode). Toggle with /fast, /fast on, /fast off, /fast status.
// State persists in ~/.pi/agent/fast-mode.json and is read at load, so
// `-p` children started with `--no-extensions -e fast-mode.ts` inherit it.
//
// 2026-08-27: rewritten off the provider-wrapping approach. Importing
// pi-ai's openai-codex.js by absolute path created a second module instance
// whose keep-alive handle stopped `pi -p` children from ever exiting.
// Set PI_FAST_LOG=<file> to append one line per stamped request (debug).
import { appendFileSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const STATE_PATH = join(homedir(), ".pi", "agent", "fast-mode.json");

function loadState(): boolean {
  try {
    return JSON.parse(readFileSync(STATE_PATH, "utf8")).fast !== false;
  } catch {
    return true;
  }
}

let fast = loadState();

export default function (pi: ExtensionAPI) {
  pi.on("before_provider_request", async (event, ctx) => {
    if (!fast) return;
    if (ctx.model?.provider !== "openai-codex") return;
    const body = event.payload as Record<string, unknown> | null;
    if (!body || typeof body !== "object") return;
    body.service_tier = "priority";
    const log = process.env.PI_FAST_LOG;
    if (log) {
      try {
        appendFileSync(log, `${JSON.stringify({ model: body.model, service_tier: body.service_tier })}\n`);
      } catch {}
    }
    return body;
  });

  pi.registerCommand("fast", {
    description: "Toggle Fast mode (OpenAI priority tier — faster, uses more of your plan)",
    handler: async (args: string, ctx: any) => {
      const arg = (args || "").trim().toLowerCase();
      if (arg === "status") {
        ctx.ui.notify(`Fast mode is ${fast ? "ON" : "OFF"}`, "info");
        return;
      }
      fast = arg === "on" ? true : arg === "off" ? false : !fast;
      writeFileSync(STATE_PATH, JSON.stringify({ fast }));
      ctx.ui.notify(
        fast
          ? "Fast mode ON — priority tier, faster answers, burns more usage"
          : "Fast mode OFF — standard tier",
        "info",
      );
    },
  });
}
