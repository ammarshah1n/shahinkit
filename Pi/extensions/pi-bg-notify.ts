// pi-bg-notify — closes the gap that made sol sleep-poll `pi-bg ls` 20× in the
// Cars session (2026-08-28): `~/bin/pi-bg` is fire-and-forget with no completion
// signal, so the controller burned turns waiting. This extension:
//   1. watches bash tool results for job ids printed by `pi-bg run`,
//   2. appends a one-line "tracked — do not poll" note to that tool result,
//   3. polls the job's pid every 5s (kill -0, same test pi-bg ls uses) and, when it
//      exits, pushes `[pi-bg <id> done]` + the final reply as a follow-up turn —
//      the same delivery the subagent tool uses for background: true.
// ponytail: pid polling, not fs.watch — jsonl is appended constantly, pid death is
// the only clean edge. Jobs started by another session are not tracked (no id seen).
import { existsSync, readFileSync, appendFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const BG = process.env.PI_BG_DIR ?? join(homedir(), ".pi", "bg");
const ID_RE = /^[a-z][a-z-]*-\d{6}-\d+$/;
const LOG = process.env.PI_BG_NOTIFY_LOG; // test hook only
const log = (s: string) => LOG && appendFileSync(LOG, `${new Date().toISOString()} ${s}\n`);

function alive(id: string): boolean {
	try {
		process.kill(Number(readFileSync(join(BG, `${id}.pid`), "utf8").trim()), 0);
		return true;
	} catch {
		return false;
	}
}

// Same query as `pi-bg get`: last assistant text in the --mode json stream.
function finalReply(id: string): string {
	let out = "(no output)";
	try {
		for (const line of readFileSync(join(BG, `${id}.jsonl`), "utf8").split("\n")) {
			if (!line.includes('"message_end"')) continue;
			try {
				const e = JSON.parse(line);
				if (e.type !== "message_end" || e.message?.role !== "assistant") continue;
				const t = (e.message.content ?? []).filter((c: any) => c.type === "text").map((c: any) => c.text).join("\n");
				if (t.trim()) out = t;
			} catch {}
		}
	} catch {}
	if (out === "(no output)") {
		try {
			const err = readFileSync(join(BG, `${id}.err`), "utf8").trim().split("\n").slice(-5).join("\n");
			if (err) out = `(no output) stderr:\n${err}`;
		} catch {}
	}
	return out.length > 6000 ? `${out.slice(0, 6000)}\n…[truncated; pi-bg get ${id} for full]` : out;
}

export default function (pi: ExtensionAPI) {
	const tracked = new Map<string, number>(); // id -> startedAt
	let timer: NodeJS.Timeout | undefined;
	let ui: { setStatus(key: string, text: string | undefined): void } | undefined;
	const fmtSecs = (ms: number) => (ms < 60_000 ? `${Math.round(ms / 1000)}s` : `${Math.floor(ms / 60_000)}m${String(Math.round((ms % 60_000) / 1000)).padStart(2, "0")}s`);
	// HUD line 5 renders extension statuses; show pi-bg jobs only while they run.
	const publish = () => {
		if (!ui) return;
		if (tracked.size === 0) return ui.setStatus("pi-bg", undefined);
		const now = Date.now();
		const parts = [...tracked].map(([id, t]) => `${id.replace(/-\d{6}-\d+$/, "")} ${fmtSecs(now - t)}`);
		ui.setStatus("pi-bg", `◐ pi-bg ${parts.length}: ${parts.join(" · ")}`);
	};

	const tick = () => {
		for (const [id, started] of tracked) {
			if (alive(id)) continue;
			tracked.delete(id);
			const meta = (() => {
				try {
					return readFileSync(join(BG, `${id}.meta`), "utf8").trim();
				} catch {
					return "";
				}
			})();
			const secs = Math.round((Date.now() - started) / 1000);
			log(`done ${id} ${secs}s`);
			pi.sendMessage(
				{
					customType: "pi-bg-result",
					content:
						`[pi-bg ${id} done] ${meta} ${secs}s\n` +
						`Collect work with \`pi-bg diff ${id}\` (worktree jobs) — apply and re-verify locally.\n\n` +
						finalReply(id),
					display: true,
					details: { id, meta, secs },
				},
				{ triggerTurn: true, deliverAs: "followUp" },
			);
		}
		publish();
		if (tracked.size === 0 && timer) {
			clearInterval(timer);
			timer = undefined;
		}
	};

	pi.on("tool_result", async (event, ctx) => {
		if (event.toolName !== "bash") return;
		const cmd = String((event.input as any)?.command ?? "");
		if (!cmd.includes("pi-bg run")) return;
		const text = event.content.map((c: any) => (c.type === "text" ? c.text : "")).join("\n");
		const ids = text
			.split("\n")
			.map((l) => l.trim())
			.filter((l) => ID_RE.test(l) && existsSync(join(BG, `${l}.pid`)) && !tracked.has(l));
		if (ids.length === 0) return;
		for (const id of ids) tracked.set(id, Date.now());
		ui = ctx.ui; publish();
		log(`tracking ${ids.join(",")}`);
		if (!timer) timer = setInterval(tick, 5000);
		return {
			content: [
				...event.content,
				{
					type: "text",
					text: `\npi-bg-notify: tracking ${ids.join(", ")}. Each completion arrives as a [pi-bg <id> done] follow-up message with the final reply — keep working, do NOT sleep/poll \`pi-bg ls\`.`,
				},
			],
		};
	});

	pi.on("session_shutdown", async () => {
		if (timer) clearInterval(timer);
	});
}
