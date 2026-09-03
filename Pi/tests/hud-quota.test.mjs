// Verify the HUD quota parsers against representative provider headers.
import { execFileSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
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

const now = Math.floor(Date.now() / 1000);
const ANTHROPIC = {
	"anthropic-ratelimit-unified-5h-reset": String(now + 4 * 60 * 60),
	"anthropic-ratelimit-unified-5h-status": "allowed",
	"anthropic-ratelimit-unified-5h-utilization": "0.03",
	"anthropic-ratelimit-unified-7d-reset": String(now + 6 * 24 * 60 * 60),
	"anthropic-ratelimit-unified-7d-status": "allowed",
	"anthropic-ratelimit-unified-7d-utilization": "0.22",
	"anthropic-ratelimit-unified-representative-claim": "five_hour",
	"anthropic-ratelimit-unified-status": "allowed",
};
const CODEX = {
	"x-codex-active-limit": "premium",
	"x-codex-plan-type": "pro",
	"x-codex-primary-reset-after-seconds": "502810",
	"x-codex-primary-used-percent": "8",
	"x-codex-primary-window-minutes": "10080",
	"x-codex-secondary-reset-after-seconds": "0",
	"x-codex-secondary-used-percent": "0",
	"x-codex-secondary-window-minutes": "0",
};

const themeColors = new Set(["accent","border","borderAccent","borderMuted","success","error","warning","muted","dim","text","thinkingText","selectedBg","scrollbarThumb","searchMatchBg","searchMatchText","userMessageBg","userMessageText","customMessageBg","customMessageText","customMessageLabel","toolPendingBg","toolSuccessBg","toolErrorBg","toolTitle","toolOutput","mdHeading","mdLink","mdLinkUrl","mdCode","mdCodeBlock","mdCodeBlockBorder","mdQuote","mdQuoteBorder","mdHr","mdListBullet","toolDiffAdded","toolDiffRemoved","toolDiffContext","syntaxComment","syntaxKeyword","syntaxFunction","syntaxVariable","syntaxString","syntaxNumber","syntaxType","syntaxOperator","syntaxPunctuation","thinkingOff","thinkingMinimal","thinkingLow","thinkingMedium","thinkingHigh","thinkingXhigh","thinkingMax","bashMode"]);
const theme = {
	fg(c, t) { if (!themeColors.has(c)) throw new Error(`UNKNOWN THEME COLOR: ${c}`); return t; },
	bold: (t) => t,
};
const usage = (o = {}) => ({ input: o.input ?? 0, output: o.output ?? 0, cacheRead: o.cacheRead ?? 0, cacheWrite: o.cacheWrite ?? 0, cost: { total: o.cost ?? 0 } });
const branch = [
	{ type: "message", message: { role: "assistant", usage: usage({ input: 27000, output: 123000, cacheRead: 37400000, cost: 0.412 }) } },
	{ type: "message", message: { role: "toolResult", toolName: "bash", isError: false } },
];
const footerData = { getGitBranch: () => "unified", getExtensionStatuses: () => new Map(), onBranchChange: () => () => {} };
const tui = { requestRender: () => {} };
let factory;
const ctx = {
	hasUI: true, mode: "tui", cwd: "/tmp/shahinkit-test",
	model: { id: "claude-opus-5", provider: "anthropic", contextWindow: 200000, reasoning: true },
	thinkingLevel: "high",
	getContextUsage: () => ({ tokens: 70000, contextWindow: 200000, percent: 35 }),
	sessionManager: { getBranch: () => branch, getCwd: () => "/tmp/shahinkit-test", getSessionName: () => null },
	ui: { setFooter: (f) => { factory = f; }, notify: () => {} },
};

const handlers = {};
mod({ on: (e, fn) => { handlers[e] = fn; }, registerCommand: () => {} });
await handlers.session_start({}, ctx);
const footer = factory(tui, theme, footerData);
const line2 = () => footer.render(120)[1].trim().replace(/\s+/g, " ");

let fail = 0;
const check = (label, cond, got) => { console.log(`${cond ? "PASS" : "FAIL"}  ${label}\n        ${got}`); if (!cond) fail++; };

check("no headers yet → Usage gauge omitted, nothing invented", !line2().includes("Usage"), line2());

handlers.after_provider_response({ headers: ANTHROPIC });
const a = line2();
check("anthropic → 3% on the 5h window (representative claim honoured)", /Usage .*3%\/5h/.test(a), a);
check("anthropic → shows a reset countdown", /resets \d/.test(a), a);

handlers.after_provider_response({ headers: CODEX });
const c = line2();
check("codex → 8% on the 1w window", /Usage .*8%\/1w/.test(c), c);
check("codex → reset ~5d away", /resets 5d/.test(c), c);
check("codex → zero-width secondary tier ignored", !/0%/.test(c.split("Usage")[1]), c);

handlers.after_provider_response({ headers: { ...ANTHROPIC, "anthropic-ratelimit-unified-representative-claim": "", "anthropic-ratelimit-unified-7d-utilization": "0.91" } });
const w = line2();
check("no claim hint → picks the hardest-binding window (91%/7d)", /Usage .*91%\/7d/.test(w), w);

handlers.after_provider_response({ headers: { "x-codex-plan-type": "pro", "x-codex-primary-window-minutes": "abc", "x-codex-primary-used-percent": "xyz" } });
const g = line2();
check("garbage headers → stale quota cleared, no NaN", !/Usage|NaN|undefined/.test(g), g);
handlers.after_provider_response({ headers: ANTHROPIC });
handlers.after_provider_response({ headers: undefined });
check("missing headers object → stale quota cleared", !line2().includes("Usage"), line2());

footer.dispose();
console.log(fail ? `\nRESULT: ${fail} FAILED` : "\nRESULT: ALL PASS");
process.exitCode = fail ? 1 : 0;
rmSync(TEST_AGENT_DIR, { recursive: true, force: true });
