// fable-mode — when the session model is controller-tier (Fable, sol, Opus), append
// the luna fan-out doctrine (~/.pi/agent/FABLE-MODE.md) to the system prompt.
// luna/terra/etc. see nothing. Single source of truth shared with Claude Code's
// ~/.claude/hooks/fable-mode.sh.
import { readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const DOCTRINE = join(homedir(), ".pi", "agent", "FABLE-MODE.md");

export default function (pi: ExtensionAPI) {
	pi.on("before_agent_start", async (event, ctx) => {
		// Widened 2026-08-28 from Fable-only: any controller-tier model gets the fan-out doctrine.
		if (!/fable|sol|opus/i.test(ctx.model?.id ?? "")) return;
		let doctrine: string;
		try {
			doctrine = readFileSync(DOCTRINE, "utf8");
		} catch {
			return;
		}
		return { systemPrompt: `${event.systemPrompt}\n\n${doctrine}` };
	});
}
