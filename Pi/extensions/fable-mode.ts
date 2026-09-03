// fable-mode — append the Luna fan-out doctrine for controller-tier sessions.
import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { CONFIG_DIR_NAME, getAgentDir, type ExtensionAPI } from "@earendil-works/pi-coding-agent";

const USER_DOCTRINE = join(getAgentDir(), "FABLE-MODE.md");

function doctrinePath(cwd: string, projectTrusted: boolean): string {
	if (projectTrusted) {
		let current = cwd;
		while (true) {
			const candidate = join(current, CONFIG_DIR_NAME, "FABLE-MODE.md");
			if (existsSync(candidate)) return candidate;
			const parent = dirname(current);
			if (parent === current) break;
			current = parent;
		}
	}
	return USER_DOCTRINE;
}

export default function (pi: ExtensionAPI) {
	pi.on("before_agent_start", async (event, ctx) => {
		if (!/fable|sol|opus/i.test(ctx.model?.id ?? "")) return;
		try {
			const doctrine = readFileSync(doctrinePath(ctx.cwd, ctx.isProjectTrusted()), "utf8");
			return { systemPrompt: `${event.systemPrompt}\n\n${doctrine}` };
		} catch {
			return;
		}
	});
}
