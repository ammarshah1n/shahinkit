// pi-bg-notify — completion notices for pi-bg jobs, plus recovery of owned jobs
// after extension reloads or missed launch output.
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, readFileSync, readdirSync, statSync, appendFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { getAgentDir, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { sanitizeTerminalText } from "./lib/sanitize.ts";

const AGENT_DIR = getAgentDir();
const DEFAULT_BG = process.env.PI_CODING_AGENT_DIR ? join(AGENT_DIR, "bg") : join(homedir(), ".pi", "bg");
const BG = process.env.PI_BG_DIR ?? DEFAULT_BG;
const ID_RE = /^[a-z][a-z0-9-]*-\d{6}-\d+$/;
const SWEEP_MS = 30_000;
const SWEEP_WINDOW_MS = 24 * 3600_000;
const LOG = process.env.PI_BG_NOTIFY_LOG; // test hook only
const log = (s: string) => LOG && appendFileSync(LOG, `${new Date().toISOString()} ${s}\n`);
const pathFor = (id: string, ext: string) => join(BG, `${id}.${ext}`);
const read = (file: string) => { try { return readFileSync(file, "utf8"); } catch { return ""; } };
const mtime = (file: string) => { try { return statSync(file).mtimeMs; } catch { return undefined; } };
const tokens = (text: string) => text.split(/\s+/).filter((token) => ID_RE.test(token));

function alive(id: string): boolean {
	try {
		const pid = Number(readFileSync(pathFor(id, "pid"), "utf8").trim());
		let live = false;
		try { process.kill(pid, 0); live = true; } catch {
			try { process.kill(-pid, 0); live = true; } catch { /* leader and process group are gone */ }
		}
		if (!live) return false;
		const receipt = pathFor(id, "process");
		if (!existsSync(receipt)) return true;
		try {
			const line = execFileSync("ps", ["-ww", "-p", String(pid), "-o", "lstart=", "-o", "command="], { encoding: "utf8" });
			const current = createHash("sha256").update(line.replace(/\n+$/, "")).digest("hex");
			if (current !== readFileSync(receipt, "utf8").trim()) return true;
		} catch { return true; }
		return true;
	} catch { return false; }
}

function finalReply(id: string): string {
	let out = "(no output)";
	for (const line of read(pathFor(id, "jsonl")).split("\n")) {
		if (!line.includes('"message_end"')) continue;
		try {
			const e = JSON.parse(line);
			if (e.type !== "message_end" || e.message?.role !== "assistant") continue;
			const text = (e.message.content ?? []).filter((c: any) => c.type === "text").map((c: any) => c.text).join("\n");
			if (text.trim()) out = text;
		} catch {}
	}
	if (out === "(no output)") {
		const err = read(pathFor(id, "err")).trim().split("\n").slice(-5).join("\n");
		if (err) out = `(no output) stderr:\n${err}`;
	}
	out = sanitizeTerminalText(out, 6001);
	return out.length > 6000 ? `${out.slice(0, 6000)}\n…[truncated; pi-bg get ${id} for full]` : out;
}

export default function (pi: ExtensionAPI) {
	const tracked = new Map<string, number>();
	let me = process.env.PI_SESSION_ID ?? "";
	let timer: NodeJS.Timeout | undefined;
	let sweepTimer: NodeJS.Timeout | undefined;
	let ui: { setStatus(key: string, text: string | undefined): void } | undefined;
	const fmtSecs = (ms: number) => (ms < 60_000 ? `${Math.round(ms / 1000)}s` : `${Math.floor(ms / 60_000)}m${String(Math.round((ms % 60_000) / 1000)).padStart(2, "0")}s`);
	const publish = () => {
		if (!ui) return;
		if (tracked.size === 0) return ui.setStatus("pi-bg", undefined);
		const now = Date.now();
		const task = (id: string) => sanitizeTerminalText(read(pathFor(id, "task")), 1000).replace(/\s+/g, " ").trim().slice(0, 70);
		ui.setStatus("pi-bg", [...tracked].map(([id, started]) => `${id.replace(/-\d{6}-\d+$/, "")} ⇢\t${fmtSecs(now - started)}\t${task(id)}`).join("\n"));
	};
	const announce = (id: string, secs: number) => {
		writeFileSync(pathFor(id, "notified"), `${new Date().toISOString()}\n`);
		// Optional integration: absent turn-budget extension means normal delivery.
		const paused = (globalThis as any).__piTurnBudget?.exhausted?.() as string | undefined;
		const meta = sanitizeTerminalText(read(pathFor(id, "meta")), 1000).trim();
		pi.sendMessage({
			customType: "pi-bg-result",
			content: `[pi-bg ${id} done] ${meta} ${secs}s${paused ? ` (turn-budget paused: ${paused})` : ""}\n` +
				`Collect work with \`pi-bg diff ${id}\` (worktree jobs) — apply and re-verify locally.\n\n` + finalReply(id),
			display: true,
			details: { id, meta, secs },
		}, paused ? { deliverAs: "nextTurn" } : { triggerTurn: true, deliverAs: "followUp" });
	};
	const tick = () => {
		for (const [id, started] of tracked) {
			if (alive(id)) continue;
			tracked.delete(id);
			log(`done ${id}`);
			announce(id, Math.round((Date.now() - started) / 1000));
		}
		publish();
		if (tracked.size === 0 && timer) { clearInterval(timer); timer = undefined; }
	};
	const sweep = () => {
		if (!me) return;
		let files: string[];
		try { files = readdirSync(BG); } catch { return; }
		for (const file of files) {
			if (!file.endsWith(".owner")) continue;
			const id = file.slice(0, -".owner".length);
			if (!ID_RE.test(id) || tracked.has(id) || read(pathFor(id, "owner")).trim() !== me) continue;
			if (existsSync(pathFor(id, "notified")) || !existsSync(pathFor(id, "meta")) || !existsSync(pathFor(id, "pid")) || alive(id)) continue;
			const started = mtime(pathFor(id, "pid")) ?? Date.now();
			const ended = mtime(pathFor(id, "jsonl")) ?? Date.now();
			if (Date.now() - ended > SWEEP_WINDOW_MS) continue;
			log(`sweep ${id}`);
			announce(id, Math.max(0, Math.round((ended - started) / 1000)));
		}
	};
	const ownJobs = () => {
		let files: string[] = [];
		try { files = readdirSync(BG); } catch {}
		return files.filter((file) => file.endsWith(".owner") && me && read(join(BG, file)).trim() === me)
			.map((file) => file.slice(0, -".owner".length)).filter((id) => ID_RE.test(id))
			.sort((a, b) => (mtime(pathFor(b, "pid")) ?? 0) - (mtime(pathFor(a, "pid")) ?? 0)).slice(0, 15)
			.map((id) => {
				const state = alive(id) ? "RUNNING" : existsSync(pathFor(id, "notified")) ? "done" : "done · notice pending";
				const agent = sanitizeTerminalText(read(pathFor(id, "meta")).split("|")[0]?.trim() || "?", 100);
				const task = sanitizeTerminalText(read(pathFor(id, "task")), 1000).replace(/\s+/g, " ").trim().slice(0, 60);
				return `${state.padEnd(22)} ${id}  ${agent}  ${task}`;
			});
	};

	pi.on("session_start", async (_event, ctx) => {
		me = ctx.sessionManager?.getSessionId?.() || process.env.PI_SESSION_ID || "";
		sweep();
		if (!sweepTimer) sweepTimer = setInterval(sweep, SWEEP_MS);
	});
	pi.registerCommand("bg", {
		description: "pi-bg jobs launched by this session, with live state (no model turn)",
		handler: async (_args, ctx) => {
			if (!me) return ctx.ui.notify("pi-bg: no session id, cannot tell which jobs are yours", "warning");
			const rows = ownJobs();
			ctx.ui.notify(rows.length ? rows.join("\n") : "no pi-bg jobs launched by this session", "info");
		},
	});
	pi.on("tool_result", async (event, ctx) => {
		if (event.toolName !== "bash" || !String((event.input as any)?.command ?? "").includes("pi-bg run")) return;
		const text = event.content.map((c: any) => c.type === "text" ? c.text : "").join("\n");
		const found = [...new Set(tokens(text))];
		if (!found.length) return;
		const newly = found.filter((id) => existsSync(pathFor(id, "pid")) && !tracked.has(id));
		const lost = found.filter((id) => !existsSync(pathFor(id, "pid")));
		for (const id of newly) tracked.set(id, Date.now());
		const notes: string[] = [];
		if (newly.length) {
			ui = ctx.ui; publish(); log(`tracking ${newly.join(",")}`);
			if (!timer) timer = setInterval(tick, 5000);
			notes.push(`pi-bg-notify: tracking ${newly.join(", ")}. Each completion arrives as a [pi-bg <id> done] follow-up message with the final reply — keep working, do NOT sleep/poll \`pi-bg ls\`.`);
		}
		if (lost.length) {
			log(`NOT TRACKED ${lost.join(",")}`);
			notes.push(`pi-bg-notify: NOT TRACKED ${lost.join(", ")} (no pid file — launch failed). Do not wait for a notice.`);
		}
		if (!notes.length) return;
		return { content: [...event.content, { type: "text", text: `\n${notes.join("\n")}` }] };
	});
	pi.on("session_shutdown", async () => {
		if (timer) clearInterval(timer);
		if (sweepTimer) clearInterval(sweepTimer);
		timer = sweepTimer = undefined;
	});
}
