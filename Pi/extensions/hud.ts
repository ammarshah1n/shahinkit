/**
 * pi HUD — a Claude-Code-style status block in place of pi's two-line footer.
 *
 * Lines:
 *   1  [model]  project  git:(branch*)  weather                    thinking: high
 *   2  Context ███████░░░░░ 35%  ·  Cache ██░░░ 14%  ·  $0.412
 *   3  ✓ bash ×19  ·  ✓ read ×4  ·  ✗ edit ×1
 *   3b   ◐ scout       42s  map repo layout for cars.js      (one row per running subagent, only while running)
 *   4  Tokens 37.5M (in 27k · out 123k · cache 37.4M)  ·  5m 55s
 *   5  ~/path/to/cwd                              <extension statuses>
 *
 * /hud toggles it off/on. Weather is cached on disk and refreshed at most
 * every 30 min in a detached curl, so render stays synchronous and instant.
 */

import { spawn } from "node:child_process";
import { existsSync, readFileSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join } from "node:path";
import type { AssistantMessage, ToolResultMessage } from "@earendil-works/pi-ai";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

/** Subscription quota scraped from provider response headers. */
type Quota = { percent: number; resetAt: number | null; window: string };

/** Anthropic sends fractional utilization (0..1) per window, and names the binding one. */
function parseAnthropicQuota(h: Record<string, string>): Quota | null {
	const claim = h["anthropic-ratelimit-unified-representative-claim"];
	const pick = claim === "seven_day" ? "7d" : claim === "five_hour" ? "5h" : null;
	const windows: [string, string][] = pick ? [[pick, pick]] : [["5h", "5h"], ["7d", "7d"]];
	let best: Quota | null = null;
	for (const [key, label] of windows) {
		const util = Number.parseFloat(h[`anthropic-ratelimit-unified-${key}-utilization`] ?? "");
		if (!Number.isFinite(util)) continue;
		const reset = Number.parseInt(h[`anthropic-ratelimit-unified-${key}-reset`] ?? "", 10);
		const q: Quota = { percent: util * 100, resetAt: Number.isFinite(reset) ? reset * 1000 : null, window: label };
		if (!best || q.percent > best.percent) best = q;
	}
	return best;
}

/** Codex sends whole percents plus a window length; show whichever window binds hardest. */
function parseCodexQuota(h: Record<string, string>): Quota | null {
	let best: Quota | null = null;
	for (const tier of ["primary", "secondary"]) {
		const minutes = Number.parseInt(h[`x-codex-${tier}-window-minutes`] ?? "", 10);
		if (!Number.isFinite(minutes) || minutes <= 0) continue;
		const used = Number.parseFloat(h[`x-codex-${tier}-used-percent`] ?? "");
		if (!Number.isFinite(used)) continue;
		const after = Number.parseInt(h[`x-codex-${tier}-reset-after-seconds`] ?? "", 10);
		const q: Quota = {
			percent: used,
			resetAt: Number.isFinite(after) ? Date.now() + after * 1000 : null,
			window: minutes >= 10080 ? `${Math.round(minutes / 10080)}w` : minutes >= 1440 ? `${Math.round(minutes / 1440)}d` : `${Math.round(minutes / 60)}h`,
		};
		if (!best || q.percent > best.percent) best = q;
	}
	return best;
}

const WEATHER_CACHE = join(homedir(), ".pi", "agent", "hud-weather.txt");
const WEATHER_MAX_AGE_MS = 30 * 60 * 1000;
const TICK_MS = 10_000;

const THINKING_COLOR: Record<string, string> = {
	off: "thinkingOff",
	minimal: "thinkingMinimal",
	low: "thinkingLow",
	medium: "thinkingMedium",
	high: "thinkingHigh",
	xhigh: "thinkingXhigh",
	max: "thinkingMax",
};

function fmtTokens(n: number): string {
	if (n < 1000) return `${n}`;
	if (n < 10_000) return `${(n / 1000).toFixed(1)}k`;
	if (n < 1_000_000) return `${Math.round(n / 1000)}k`;
	if (n < 10_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
	return `${Math.round(n / 1_000_000)}M`;
}

/** "2h 8m" / "12m" / "3d" — coarse, because a quota reset never needs seconds. */
function fmtUntil(ms: number): string {
	const m = Math.round(ms / 60000);
	if (m <= 0) return "now";
	if (m < 60) return `${m}m`;
	const h = Math.floor(m / 60);
	if (h < 24) return m % 60 ? `${h}h ${m % 60}m` : `${h}h`;
	return `${Math.floor(h / 24)}d ${h % 24}h`;
}

function fmtElapsed(ms: number): string {
	const s = Math.floor(ms / 1000);
	if (s < 60) return `${s}s`;
	const m = Math.floor(s / 60);
	if (m < 60) return `${m}m ${s % 60}s`;
	return `${Math.floor(m / 60)}h ${m % 60}m`;
}

/** Read the weather cache, kicking off a detached refresh when it is stale. */
function weather(): string {
	let text = "";
	let stale = true;
	try {
		if (existsSync(WEATHER_CACHE)) {
			text = readFileSync(WEATHER_CACHE, "utf8").trim();
			stale = Date.now() - statSync(WEATHER_CACHE).mtimeMs > WEATHER_MAX_AGE_MS;
		}
	} catch {
		/* cache unreadable — fall through to refresh */
	}
	if (stale) {
		try {
			const child = spawn(
				"/bin/sh",
				["-c", `curl -s --max-time 8 'https://wttr.in/?format=%c%t' > ${JSON.stringify(WEATHER_CACHE)}.tmp && mv ${JSON.stringify(WEATHER_CACHE)}.tmp ${JSON.stringify(WEATHER_CACHE)}`],
				{ detached: true, stdio: "ignore" },
			);
			child.unref();
		} catch {
			/* offline — keep showing the stale value */
		}
	}
	return text.replace(/\s+/g, " ").trim();
}

export default function (pi: ExtensionAPI) {
	let installed = false;
	let startedAt = Date.now();
	let dirty = false;
	let quota: Quota | null = null;

	// Subscription usage is only knowable from provider response headers. Anthropic
	// sends them on its normal path; Codex only sends them over the SSE transport
	// (the WebSocket transport never reaches the header hook), so on transport=auto
	// Codex yields nothing and the HUD simply omits the gauge rather than guessing.
	pi.on("after_provider_response", (event: any) => {
		const h = event?.headers as Record<string, string> | undefined;
		if (!h) return;
		const next = h["anthropic-ratelimit-unified-status"] ? parseAnthropicQuota(h) : h["x-codex-plan-type"] ? parseCodexQuota(h) : null;
		if (next) quota = next;
	});

	/** Cheap async git-dirty probe; result is read synchronously during render. */
	function refreshDirty(cwd: string) {
		try {
			const git = spawn("git", ["status", "--porcelain", "-uno"], { cwd, stdio: ["ignore", "pipe", "ignore"] });
			let out = "";
			git.stdout.on("data", (c) => {
				out += c;
			});
			git.on("close", () => {
				dirty = out.trim().length > 0;
			});
			git.on("error", () => {
				dirty = false;
			});
		} catch {
			dirty = false;
		}
	}

	// biome-ignore lint/suspicious/noExplicitAny: extension ctx type is not exported
	function install(ctx: any) {
		ctx.ui.setFooter((tui: any, theme: any, footerData: any) => {
			const unsubBranch = footerData.onBranchChange(() => tui.requestRender());
			const timer = setInterval(() => {
				refreshDirty(ctx.cwd);
				tui.requestRender();
			}, TICK_MS);
			refreshDirty(ctx.cwd);

			const bar = (percent: number | null, cells: number, fillColor: string): string => {
				if (percent === null) return theme.fg("dim", "░".repeat(cells));
				const clamped = Math.max(0, Math.min(100, percent));
				const filled = Math.round((clamped / 100) * cells);
				return theme.fg(fillColor, "█".repeat(filled)) + theme.fg("dim", "░".repeat(cells - filled));
			};

			const dot = theme.fg("dim", " · ");

			const join2 = (left: string, right: string, width: number): string => {
				const gap = width - visibleWidth(left) - visibleWidth(right);
				if (gap < 2) return truncateToWidth(left, width, theme.fg("dim", "…"));
				return left + " ".repeat(gap) + right;
			};

			return {
				dispose() {
					unsubBranch();
					clearInterval(timer);
				},
				invalidate() {},
				render(width: number): string[] {
					// ---- gather -------------------------------------------------
					let input = 0;
					let output = 0;
					let cacheRead = 0;
					let cacheWrite = 0;
					let cost = 0;
					const toolOk = new Map<string, number>();
					const toolErr = new Map<string, number>();

					for (const e of ctx.sessionManager.getBranch()) {
						if (e.type !== "message") continue;
						if (e.message.role === "assistant") {
							const m = e.message as AssistantMessage;
							input += m.usage.input;
							output += m.usage.output;
							cacheRead += m.usage.cacheRead;
							cacheWrite += m.usage.cacheWrite;
							cost += m.usage.cost.total;
						} else if (e.message.role === "toolResult") {
							const m = e.message as ToolResultMessage;
							const target = m.isError ? toolErr : toolOk;
							target.set(m.toolName, (target.get(m.toolName) ?? 0) + 1);
							if (m.usage) cost += m.usage.cost.total;
						}
					}

					const usage = ctx.getContextUsage();
					const ctxPercent = usage?.percent ?? null;
					const ctxWindow = usage?.contextWindow ?? ctx.model?.contextWindow ?? 0;

					// ---- line 1: identity --------------------------------------
					const modelId = ctx.model?.id ?? "no-model";
					const project = basename(ctx.sessionManager.getCwd()) || "/";
					const branch = footerData.getGitBranch();

					// mdHeading/mdLink are the theme's "prominent warm" pair; accent stays the
					// UI colour (cursor, selection, input border) so the badge can differ from it.
					let l1 = theme.bold(theme.fg("mdHeading", `[${modelId}]`)) + " " + theme.bold(theme.fg("text", project));
					if (branch) {
						l1 +=
							" " +
							theme.fg("dim", "git:(") +
							theme.fg("mdLink", branch) +
							(dirty ? theme.fg("warning", "*") : "") +
							theme.fg("dim", ")");
					}
					const sessionName = ctx.sessionManager.getSessionName();
					if (sessionName) l1 += dot + theme.fg("muted", sessionName);
					const w = weather();
					if (w) l1 += dot + theme.fg("mdLink", w);

					const level = ctx.thinkingLevel ?? "off";
					const right1 = ctx.model?.reasoning
						? theme.fg(THINKING_COLOR[level] ?? "dim", `thinking: ${level}`)
						: theme.fg("dim", ctx.model?.provider ?? "");

					// ---- line 2: gauges ----------------------------------------
					const cells = width >= 90 ? 16 : width >= 60 ? 10 : 6;
					const ctxColor = ctxPercent === null ? "dim" : ctxPercent > 90 ? "error" : ctxPercent > 70 ? "warning" : "success";
					let l2 =
						theme.fg("dim", "Context ") +
						bar(ctxPercent, cells, ctxColor) +
						" " +
						theme.fg(ctxColor, ctxPercent === null ? "?" : `${ctxPercent.toFixed(0)}%`) +
						theme.fg("dim", `/${fmtTokens(ctxWindow)}`);
					if (quota) {
						const uColor = quota.percent > 90 ? "error" : quota.percent > 70 ? "warning" : "accent";
						l2 +=
							dot +
							theme.fg("dim", "Usage ") +
							bar(quota.percent, cells, uColor) +
							" " +
							theme.fg(uColor, `${quota.percent.toFixed(0)}%`) +
							theme.fg("dim", `/${quota.window}`);
						if (quota.resetAt) l2 += theme.fg("dim", ` resets ${fmtUntil(quota.resetAt - Date.now())}`);
					}
					const right2 = cost > 0 ? theme.fg("warning", `$${cost.toFixed(3)}`) : "";

					// ---- line 3: tool tally ------------------------------------
					const toolNames = [...new Set([...toolOk.keys(), ...toolErr.keys()])].sort(
						(a, b) => (toolOk.get(b) ?? 0) + (toolErr.get(b) ?? 0) - ((toolOk.get(a) ?? 0) + (toolErr.get(a) ?? 0)),
					);
					const l3 = toolNames
						.map((name) => {
							const ok = toolOk.get(name) ?? 0;
							const err = toolErr.get(name) ?? 0;
							const mark = err > 0 ? theme.fg("error", "✗") : theme.fg("success", "✓");
							return `${mark} ${theme.fg("muted", name)} ${theme.fg("dim", `×${ok + err}`)}`;
						})
						.join(theme.fg("dim", " · "));

					// ---- line 4: tokens ----------------------------------------
					const total = input + output + cacheRead + cacheWrite;
					const l4 =
						theme.fg("dim", "Tokens ") +
						theme.fg("muted", fmtTokens(total)) +
						theme.fg(
							"dim",
							` (in ${fmtTokens(input)} · out ${fmtTokens(output)} · cache ${fmtTokens(cacheRead + cacheWrite)})`,
						);
					const right4 = theme.fg("dim", fmtElapsed(Date.now() - startedAt));

					// ---- line 5: cwd + extension statuses ----------------------
					const home = process.env.HOME ?? homedir();
					const cwd = ctx.sessionManager.getCwd();
					const shortCwd = cwd.startsWith(home) ? `~${cwd.slice(home.length)}` : cwd;
					// A status containing newlines is a vertical block: one row per
					// running subagent, fields "agent\telapsed\twhat it is doing".
					// Rendered under the tool tally, only while something runs.
					const allStatuses = [...footerData.getExtensionStatuses().entries()].sort(([a], [b]) => a.localeCompare(b));
					const agentRows: string[] = [];
					for (const [, text] of allStatuses) {
						if (!text.includes("\n")) continue;
						for (const row of text.split("\n")) {
							if (!row.trim()) continue;
							const [agent = "", elapsed = "", task = ""] = row.split("\t");
							agentRows.push(
								truncateToWidth(
									`  ${theme.fg("warning", "◐")} ${theme.fg("text", agent.padEnd(10))} ${theme.fg("dim", elapsed.padStart(6))}  ${theme.fg("muted", task)}`,
									width,
									theme.fg("dim", "…"),
								),
							);
						}
					}
					const statuses = allStatuses
						.filter(([, text]) => !text.includes("\n"))
						.map(([, text]) => text.replace(/[\r\n\t]+/g, " ").trim())
						.join(" ");
					const l5 = join2(theme.fg("dim", shortCwd), statuses, width);

					const lines = [join2(l1, right1, width), join2(l2, right2, width)];
					if (l3) lines.push(truncateToWidth(l3, width, theme.fg("dim", "…")));
					lines.push(...agentRows);
					lines.push(join2(l4, right4, width), l5);
					return lines;
				},
			};
		});
	}

	pi.on("session_start", async (_event, ctx) => {
		startedAt = Date.now();
		if (!ctx.hasUI || ctx.mode !== "tui") return;
		install(ctx);
		installed = true;
	});

	pi.registerCommand("hud", {
		description: "Toggle the pi HUD footer",
		handler: async (_args, ctx) => {
			// Tracks what is actually mounted, so /hud works immediately after
			// /reload — where the extension re-registers but session_start does not fire.
			if (installed) {
				ctx.ui.setFooter(undefined);
				installed = false;
				ctx.ui.notify("HUD off — default footer restored", "info");
			} else {
				install(ctx);
				installed = true;
				ctx.ui.notify("HUD on", "info");
			}
		},
	});
}
