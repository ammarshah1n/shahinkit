import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, existsSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { execFileSync, spawn } from "node:child_process";

const BG = mkdtempSync(join(tmpdir(), "shahinkit-bg-notify-"));
process.env.PI_BG_DIR = BG;
process.env.PI_BG_NOTIFY_LOG = join(BG, "log");
const PI_ROOT = process.env.PI_PACKAGE_ROOT || join(execFileSync("npm", ["root", "-g"], { encoding: "utf8" }).trim(), "@earendil-works/pi-coding-agent");
const { createJiti } = await import(pathToFileURL(join(PI_ROOT, "node_modules/jiti/lib/jiti.mjs")).href);
const jiti = createJiti(import.meta.url, { alias: { "@earendil-works/pi-coding-agent": PI_ROOT } });
const here = dirname(fileURLToPath(import.meta.url));
const mod = await jiti.import(resolve(here, "../extensions/pi-bg-notify.ts"), { default: true });

const live = spawn("sleep", ["60"], { stdio: "ignore" });
const dead = spawn("true", [], { stdio: "ignore" });
await new Promise((resolve) => dead.once("exit", resolve));
const ME = "session-current";
const OTHER = "session-other";
function job(id, { owner = ME, pid = dead.pid, meta = true, notified = false } = {}) {
	const put = (ext, text) => writeFileSync(join(BG, `${id}.${ext}`), text);
	if (meta) put("meta", "worker | test | LOCAL:/tmp\n");
	put("pid", `${pid}\n`);
	put("task", `task ${id}\n`);
	put("jsonl", JSON.stringify({ type: "message_end", message: { role: "assistant", content: [{ type: "text", text: `answer ${id}` }] } }) + "\n");
	if (owner !== null) put("owner", `${owner}\n`);
	if (notified) put("notified", "already\n");
}
const handlers = {};
const sent = [];
const commands = {};
const notices = [];
const pi = {
	on: (event, fn) => { handlers[event] = fn; },
	sendMessage: (message, options) => sent.push({ message, options }),
	registerCommand: (name, spec) => { commands[name] = spec; },
};
const ctx = {
	ui: { setStatus() {}, notify: (message, level) => notices.push({ message, level }) },
	sessionManager: { getSessionId: () => ME },
};
mod(pi);

job("worker-000001-1");
job("worker-000002-2", { owner: OTHER });
job("worker-000003-3", { notified: true });
job("worker-000004-4", { meta: false });
await handlers.session_start({}, ctx);
assert.equal(sent.length, 1, "sweep announces only owned dead jobs with meta/pid and no prior notice");
assert.match(sent[0].message.content, /^\[pi-bg worker-000001-1 done\]/);
assert.match(sent[0].message.content, /answer worker-000001-1/);
assert.equal(sent[0].options.triggerTurn, true, "no turn-budget extension uses normal follow-up delivery");
assert.ok(existsSync(join(BG, "worker-000001-1.notified")));
await handlers.session_start({}, ctx);
assert.equal(sent.length, 1, "notified marker prevents duplicate announcement");

job("worker-000011-1", { pid: live.pid });
job("worker-000012-2", { pid: live.pid });
const launch = { toolName: "bash", input: { command: "pi-bg run worker" } };
const result = await handlers.tool_result({ ...launch, content: [{ type: "text", text: "worker-000011-1 worker-000012-2\n" }] }, ctx);
assert.match(result.content.at(-1).text, /tracking worker-000011-1, worker-000012-2/, "space-separated ids are recognized");
const lost = await handlers.tool_result({ ...launch, content: [{ type: "text", text: "worker-000013-3\n" }] }, ctx);
assert.match(lost.content.at(-1).text, /NOT TRACKED worker-000013-3/);
assert.equal(await handlers.tool_result({ ...launch, input: { command: "pi-bg ls" } }, ctx), undefined);

job("worker-000021-1", { pid: live.pid });
job("worker-000022-2", { owner: OTHER, pid: live.pid });
await commands.bg.handler("", ctx);
assert.equal(notices.at(-1).level, "info");
assert.match(notices.at(-1).message, /RUNNING.*worker-000021-1/);
assert.doesNotMatch(notices.at(-1).message, /worker-000022-2/);

await handlers.session_shutdown({}, ctx);
live.kill();
rmSync(BG, { recursive: true, force: true });
console.log("pi-bg-notify: PASS (sweep, once-only delivery, tokens, missing pid, /bg, graceful budget absence)");
