import { execFileSync } from "node:child_process";
import { chmodSync, existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const TEST_AGENT_DIR = mkdtempSync(join(tmpdir(), "shahinkit-hud-"));
process.env.PI_CODING_AGENT_DIR = TEST_AGENT_DIR;
writeFileSync(join(TEST_AGENT_DIR, "hud-weather.txt"), "☀️ +20°C\n");

const PI_ROOT = process.env.PI_PACKAGE_ROOT || join(
	execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(),
	"@earendil-works/pi-coding-agent",
);
const PKG = join(PI_ROOT, "node_modules");
const { createJiti } = await import(pathToFileURL(join(PKG, "jiti/lib/jiti.mjs")).href);
const jiti = createJiti(import.meta.url, {
	alias: {
		"@earendil-works/pi-coding-agent": PI_ROOT,
		"@earendil-works/pi-tui": join(PKG, "@earendil-works/pi-tui"),
		"@earendil-works/pi-ai": join(PKG, "@earendil-works/pi-ai"),
	},
});
const here = dirname(fileURLToPath(import.meta.url));
const mod = await jiti.import(resolve(here, "../extensions/hud.ts"), { default: true });

// --- theme mock: tags instead of ANSI so we can eyeball structure + width math
const themeColors = new Set([
	"accent","border","borderAccent","borderMuted","success","error","warning","muted","dim","text",
	"thinkingText","selectedBg","scrollbarThumb","searchMatchBg","searchMatchText","userMessageBg",
	"userMessageText","customMessageBg","customMessageText","customMessageLabel","toolPendingBg",
	"toolSuccessBg","toolErrorBg","toolTitle","toolOutput","mdHeading","mdLink","mdLinkUrl","mdCode",
	"mdCodeBlock","mdCodeBlockBorder","mdQuote","mdQuoteBorder","mdHr","mdListBullet","toolDiffAdded",
	"toolDiffRemoved","toolDiffContext","syntaxComment","syntaxKeyword","syntaxFunction","syntaxVariable",
	"syntaxString","syntaxNumber","syntaxType","syntaxOperator","syntaxPunctuation","thinkingOff",
	"thinkingMinimal","thinkingLow","thinkingMedium","thinkingHigh","thinkingXhigh","thinkingMax","bashMode",
]);
const usedColors = new Set();
const theme = {
	fg(color, text) {
		if (!themeColors.has(color)) throw new Error(`UNKNOWN THEME COLOR: ${color}`);
		usedColors.add(color);
		return `\x1b[38;5;2m${text}\x1b[39m`;
	},
	bold: (t) => `\x1b[1m${t}\x1b[22m`,
};

const usage = (o = {}) => ({
	input: o.input ?? 0, output: o.output ?? 0, cacheRead: o.cacheRead ?? 0,
	cacheWrite: o.cacheWrite ?? 0, cost: { total: o.cost ?? 0 },
});

function makeCtx(branch, { model = { id: "claude-opus-5", provider: "anthropic", contextWindow: 200000, reasoning: true }, ctxUsage = { tokens: 70000, contextWindow: 200000, percent: 35 }, name = null } = {}) {
	return {
		hasUI: true, mode: "tui", cwd: "/tmp/shahinkit-test",
		model, thinkingLevel: "high",
		getContextUsage: () => ctxUsage,
		sessionManager: {
			getBranch: () => branch,
			getCwd: () => "/tmp/shahinkit-test",
			getSessionName: () => name,
		},
		ui: { setFooter: (f) => { ctxHolder.factory = f; }, notify: () => {} },
	};
}
const ctxHolder = {};

const footerData = {
	getGitBranch: () => "unified",
	getExtensionStatuses: () => new Map([
		["a", "● subagent running"], ["b", "memory idle"],
		// multi-line status = vertical subagent block (agent\telapsed\ttask)
		["subagents", "scout bg1\t42s\tmap repository layout for the parser and ranking UI\nworker bg2\t1m12s\timplement data/items.js + validator"],
		["pi-bg", "mechanical ⇢\t7s\tcopy 22 assets into the fixture directory"],
	]),
	onBranchChange: () => () => {},
};
const tui = { requestRender: () => {} };

// --- capture handlers
const handlers = {};
const commands = {};
mod({
	on: (evt, fn) => { handlers[evt] = fn; },
	registerCommand: (name, def) => { commands[name] = def; },
});

const { visibleWidth } = await jiti.import(`${PKG}/@earendil-works/pi-tui`);
const strip = (s) => s.replace(/\x1b\[[0-9;]*m/g, "");

async function scenario(label, branch, opts, widths = [120, 80, 50]) {
	const ctx = makeCtx(branch, opts);
	await handlers.session_start({}, ctx);
	if (!ctxHolder.factory) throw new Error("setFooter was never called");
	const footer = ctxHolder.factory(tui, theme, footerData);
	console.log(`\n===== ${label} =====`);
	for (const w of widths) {
		const lines = footer.render(w);
		console.log(`-- width ${w} --`);
		for (const l of lines) {
			const vis = strip(l);
			const vw = visibleWidth(l);
			const over = vw > w ? `  <<< OVERFLOW ${vw}>${w}` : "";
			console.log(`|${vis}|${over}`);
			if (over) process.exitCode = 1;
			if (l.includes("\x1b]")) {
				console.error("FAIL: raw OSC control sequence reached HUD output");
				process.exitCode = 1;
			}
		}
	}
	footer.dispose();
}

const fullBranch = [
	{ type: "message", message: { role: "user", content: "hi" } },
	{ type: "message", message: { role: "assistant", usage: usage({ input: 27000, output: 123000, cacheRead: 37400000, cacheWrite: 12000, cost: 0.412 }) } },
	...Array.from({ length: 19 }, () => ({ type: "message", message: { role: "toolResult", toolName: "bash", isError: false } })),
	...Array.from({ length: 4 }, () => ({ type: "message", message: { role: "toolResult", toolName: "read", isError: false } })),
	{ type: "message", message: { role: "toolResult", toolName: "edit", isError: true } },
];

await scenario("typical session", fullBranch, {});
await scenario("empty session (no messages, no model)", [], { model: null, ctxUsage: undefined });
await scenario("post-compaction (unknown tokens)", fullBranch, { ctxUsage: { tokens: null, contextWindow: 200000, percent: null } });
await scenario("context critical + session name", fullBranch, { ctxUsage: { tokens: 190000, contextWindow: 200000, percent: 95 }, name: "handoff review" });
await scenario("non-reasoning model", fullBranch, { model: { id: "gpt-4o", provider: "openai", contextWindow: 128000, reasoning: false } });
await scenario("tiny terminal", fullBranch, {}, [30, 20]);

writeFileSync(join(TEST_AGENT_DIR, "hud-weather.txt"), `\x1b]52;c;clipboard\x07${"x".repeat(500)}\n`);
await scenario("weather cache sanitization", fullBranch, {}, [120]);

// A missing weather cache must not cause network egress without explicit opt-in.
const sentinel = join(TEST_AGENT_DIR, "curl-ran");
const fakeCurl = join(TEST_AGENT_DIR, "curl");
writeFileSync(fakeCurl, `#!/bin/sh\ntouch ${JSON.stringify(sentinel)}\nprintf '☀️ +20°C\\n'\n`);
chmodSync(fakeCurl, 0o700);
process.env.PATH = `${TEST_AGENT_DIR}:${process.env.PATH}`;
delete process.env.PI_HUD_WEATHER;
rmSync(join(TEST_AGENT_DIR, "hud-weather.txt"), { force: true });
await scenario("weather network opt-out", fullBranch, {}, [80]);
await new Promise((resolveDelay) => setTimeout(resolveDelay, 100));
if (existsSync(sentinel)) {
	console.error("FAIL: HUD started curl without PI_HUD_WEATHER=1");
	process.exitCode = 1;
}

console.log("\ntheme tokens used:", [...usedColors].sort().join(", "));
console.log(process.exitCode ? "\nRESULT: FAIL (overflow)" : "\nRESULT: PASS (no throw, no overflow)");
rmSync(TEST_AGENT_DIR, { recursive: true, force: true });
