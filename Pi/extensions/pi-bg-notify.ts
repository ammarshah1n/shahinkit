// pi-bg-notify — adds completion delivery to the fire-and-forget `pi-bg`
// helper so controllers do not burn turns polling job state. This extension:
//   1. watches bash tool results for job ids printed by `pi-bg run`,
//   2. appends a one-line "tracked — do not poll" note to that tool result,
//   3. polls the job's pid every 5s (kill -0, same test pi-bg ls uses) and, when it
//      exits, pushes `[pi-bg <id> done]` + the final reply as a follow-up turn —
//      the same delivery the subagent tool uses for background: true.
// ponytail: pid polling, not fs.watch — jsonl is appended constantly, pid death is
// the only clean edge. Jobs started by another session are not tracked (no id seen).
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, appendFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { getAgentDir, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { sanitizeTerminalText } from "./lib/sanitize.ts";

const AGENT_DIR = getAgentDir();
const DEFAULT_BG = process.env.PI_CODING_AGENT_DIR ? join(AGENT_DIR, "bg") : join(homedir(), ".pi", "bg");
const BG = process.env.PI_BG_DIR ?? DEFAULT_BG;
const ID_RE = /^[a-z][a-z0-9-]*-\d{6}-\d+$/;
const LOG = process.env.PI_BG_NOTIFY_LOG; // test hook only
const log = (s: string) => LOG && appendFileSync(LOG, `${new Date().toISOString()} ${s}\n`);

function alive(id: string): boolean {
	try {
		const pid = Number(readFileSync(join(BG, `${id}.pid`), "utf8").trim());
		let live = false;
		try { process.kill(pid, 0); live = true; } catch {
			try { process.kill(-pid, 0); live = true; } catch { /* leader and process group are gone */ }
		}
		if (!live) return false;
		const receipt = join(BG, `${id}.process`);
		if (!existsSync(receipt)) return true; // live but identity-unknown: never announce completion
		try {
			const line = execFileSync("ps", ["-ww", "-p", String(pid), "-o", "lstart=", "-o", "command="], { encoding: "utf8" });
			const current = createHash("sha256").update(line.replace(/\n+$/, "")).digest("hex");
			if (current !== readFileSync(receipt, "utf8").trim()) return true; // live mismatch stays UNKNOWN
		} catch { return true; }
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
	out = sanitizeTerminalText(out, 6001);
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
		const task = (id: string) => {
			try { return sanitizeTerminalText(readFileSync(join(BG, `${id}.task`), "utf8"), 1000).replace(/\s+/g, " ").trim().slice(0, 70); } catch { return ""; }
		};
		// newline-separated rows → hud.ts renders a vertical block (agent\telapsed\ttask)
		ui.setStatus("pi-bg", [...tracked].map(([id, t]) => `${id.replace(/-\d{6}-\d+$/, "")} ⇢\t${fmtSecs(now - t)}\t${task(id)}`).join("\n"));
	};

	const tick = () => {
		for (const [id, started] of tracked) {
			if (alive(id)) continue;
			tracked.delete(id);
			const meta = (() => {
				try {
					return sanitizeTerminalText(readFileSync(join(BG, `${id}.meta`), "utf8"), 1000).trim();
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
