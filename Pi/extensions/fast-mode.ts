// fast-mode — Codex-style Fast mode for the openai-codex provider.
// Wraps the built-in provider so requests carry service_tier: "priority"
// (faster processing, higher usage burn — same dial as Codex's Fast mode).
// Toggle with /fast, /fast on, /fast off, /fast status. State persists.
// Use Pi's supported aggregate provider entrypoint; the extension loader maps
// this path across Pi's bundled and Node runtimes.
import { builtinProviders } from "@earendil-works/pi-ai/providers/all";
import { readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const STATE_PATH = join(homedir(), ".pi", "agent", "fast-mode.json");

function loadState(): boolean {
  try {
    return JSON.parse(readFileSync(STATE_PATH, "utf8")).fast === true;
  } catch {
    return false;
  }
}

let fast = loadState();

export default function (pi: ExtensionAPI) {
  const provider = builtinProviders().find((candidate) => candidate.id === "openai-codex");
  if (!provider) throw new Error("OpenAI Codex provider is unavailable in this Pi build");
  const api = provider.api;
  const inject = (options: any) => (fast ? { ...options, serviceTier: "priority" } : options);
  provider.api = {
    ...api,
    stream: (model: any, context: any, options: any) => api.stream(model, context, inject(options)),
    streamSimple: (model: any, context: any, options: any) => api.streamSimple(model, context, inject(options)),
  };
  pi.registerProvider(provider);

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
