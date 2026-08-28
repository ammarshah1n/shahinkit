import { createJiti } from "/opt/homebrew/lib/node_modules/@earendil-works/pi-coding-agent/node_modules/jiti/lib/jiti.mjs";

const PKG = "/opt/homebrew/lib/node_modules/@earendil-works/pi-coding-agent/node_modules";
const jiti = createJiti(import.meta.url, {
	alias: {
		"@earendil-works/pi-tui": `${PKG}/@earendil-works/pi-tui`,
		"@earendil-works/pi-ai": `${PKG}/@earendil-works/pi-ai`,
	},
});
const mod = await jiti.import("/Users/integrale/.pi/agent/extensions/hud.ts", { default: true });

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
		hasUI: true, mode: "tui", cwd: "/Users/integrale/time-manager-desktop",
		model, thinkingLevel: "high",
		getContextUsage: () => ctxUsage,
		sessionManager: {
			getBranch: () => branch,
			getCwd: () => "/Users/integrale/time-manager-desktop",
			getSessionName: () => name,
		},
		ui: { setFooter: (f) => { ctxHolder.factory = f; }, notify: () => {} },
	};
}
const ctxHolder = {};

const footerData = {
	getGitBranch: () => "unified",
	getExtensionStatuses: () => new Map([
		["a", "● subagent running"], ["b", "herdr idle"],
		// multi-line status = vertical subagent block (agent\telapsed\ttask), added 2026-08-28
		["subagents", "scout bg1\t42s\tmap repo layout for cars.js and the ranking UI so the worker brief is exact\nworker bg2\t1m12s\timplement data/cars.js + validator"],
		["pi-bg", "mechanical ⇢\t7s\tcopy 22 candidate photos into assets/"],
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
await scenario("context critical + session name", fullBranch, { ctxUsage: { tokens: 190000, contextWindow: 200000, percent: 95 }, name: "Whats ion handoff" });
await scenario("non-reasoning model", fullBranch, { model: { id: "gpt-4o", provider: "openai", contextWindow: 128000, reasoning: false } });
await scenario("tiny terminal", fullBranch, {}, [30, 20]);

console.log("\ntheme tokens used:", [...usedColors].sort().join(", "));
console.log(process.exitCode ? "\nRESULT: FAIL (overflow)" : "\nRESULT: PASS (no throw, no overflow)");
